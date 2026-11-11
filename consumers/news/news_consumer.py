 
import json
import time
 
from datetime import datetime, timezone
 
from kafka import KafkaConsumer, TopicPartition
from kafka.errors import KafkaError
 
from config.settings import (
    KAFKA_BOOTSTRAP_SERVERS,
    NEWS_TOPIC
)
 
from spark_jobs.bronze_news_sink import BronzeNewsSink
 
 
# ============================================================
# FINTEL BRONZE NEWS CONSUMER
# ============================================================
 
class NewsConsumer:
 
    def __init__(self):
 
        self.consumer = KafkaConsumer(
            NEWS_TOPIC,
 
            bootstrap_servers=(
                KAFKA_BOOTSTRAP_SERVERS.split(",")
            ),
 
            group_id="fintel-bronze-news-consumer",
 
            # Commit only after successful Parquet storage.
            enable_auto_commit=False,
 
            # Read earlier messages if this group has no offset.
            auto_offset_reset="earliest",
 
            # JSON deserialization.
            value_deserializer=lambda value: json.loads(
                value.decode("utf-8")
            ),
 
            key_deserializer=lambda key: (
                key.decode("utf-8") if key else None
            )
        )
 
        self.bronze_sink = BronzeNewsSink()
 
        print("\n==========================================")
        print("       FINTEL BRONZE NEWS CONSUMER")
        print("==========================================")
        print(f"Kafka topic   : {NEWS_TOPIC}")
        print(f"Bootstrap     : {KAFKA_BOOTSTRAP_SERVERS}")
        print("Consumer group: fintel-bronze-news-consumer")
        print("Auto commit   : Disabled")
        print("==========================================\n")
 
    # ========================================================
    # CONSUME KAFKA MESSAGES
    # ========================================================
 
    def process_messages(self):
 
        records = self.consumer.poll(
            timeout_ms=5000,
            max_records=100
        )
 
        messages = []
 
        for topic_partition, records_list in records.items():
 
            for record in records_list:
 
                # Kafka timestamp is epoch milliseconds.
                # Convert it to an aware UTC datetime.
                kafka_timestamp = None
 
                if record.timestamp is not None and record.timestamp >= 0:
 
                    kafka_timestamp = datetime.fromtimestamp(
                        record.timestamp / 1000,
                        tz=timezone.utc
                    )
 
                messages.append({
 
                    "key": record.key,
 
                    "value": record.value,
 
                    "topic": record.topic,
 
                    "partition": record.partition,
 
                    "offset": record.offset,
 
                    "timestamp": kafka_timestamp
                })
 
        if not messages:
            return 0
 
        print(
            f"\n[KAFKA] Received "
            f"{len(messages)} messages."
        )
 
        # ----------------------------------------------------
        # WRITE TO BRONZE
        # ----------------------------------------------------
 
        try:
 
            output_file = self.bronze_sink.write_batch(
                messages
            )
 
            if output_file is None:
                raise RuntimeError(
                    "Bronze sink did not produce an output file."
                )
 
        except Exception:
 
            # Rewind each affected partition to the first
            # record in this batch. Do not commit failed data.
            first_offsets = {}
 
            for message in messages:
 
                tp = TopicPartition(
                    message["topic"],
                    message["partition"]
                )
 
                if (
                    tp not in first_offsets
                    or message["offset"] < first_offsets[tp]
                ):
                    first_offsets[tp] = message["offset"]
 
            for tp, offset in first_offsets.items():
                self.consumer.seek(tp, offset)
 
            print(
                "[BRONZE ERROR] Write failed. "
                "Offsets were not committed; batch will be retried."
            )
 
            raise
 
        # ----------------------------------------------------
        # COMMIT AFTER SUCCESSFUL BRONZE WRITE
        # ----------------------------------------------------
 
        self.consumer.commit()
 
        print(
            f"\n[KAFKA] Successfully committed "
            f"offsets for {len(messages)} messages."
        )
 
        print(
            f"[BRONZE] Stored at: {output_file}"
        )
 
        return len(messages)
 
    # ========================================================
    # CONSUMER LOOP
    # ========================================================
 
    def run(self):
 
        print("[CONSUMER] Waiting for Kafka messages...")
 
        try:
 
            while True:
 
                try:
 
                    self.process_messages()
 
                except KafkaError as error:
 
                    print(
                        f"[KAFKA ERROR] {error}"
                    )
 
                    time.sleep(3)
 
                except Exception as error:
 
                    print(
                        f"[CONSUMER ERROR] {error}"
                    )
 
                    time.sleep(3)
 
        except KeyboardInterrupt:
 
            print(
                "\n[CONSUMER] Stopping Bronze News Consumer..."
            )
 
        finally:
 
            self.consumer.close()
 
            print(
                "[CONSUMER] Kafka consumer closed."
            )
 
 
# ============================================================
# MAIN
# ============================================================
 
if __name__ == "__main__":
 
    consumer = NewsConsumer()
 
    consumer.run()
 