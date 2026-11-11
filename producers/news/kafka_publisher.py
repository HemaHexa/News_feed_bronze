import json
 
from kafka import KafkaProducer
 
from config.settings import (
    KAFKA_BOOTSTRAP_SERVERS,
    NEWS_TOPIC
)
 
 
class NewsKafkaPublisher:
 
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
            acks="all",
            retries=5,
            max_in_flight_requests_per_connection=1,
            key_serializer=lambda key: key.encode("utf-8"),
            value_serializer=lambda value: json.dumps(
                value, ensure_ascii=False
            ).encode("utf-8")
        )
 
    def publish(self, article):
        article_id = article["article_id"]
 
        try:
            future = self.producer.send(
                NEWS_TOPIC,
                key=article_id,
                value=article
            )
 
            metadata = future.get(timeout=30)
 
            print(
                f"Published: {article_id} | "
                f"Partition: {metadata.partition} | "
                f"Offset: {metadata.offset}"
            )
 
            return True
 
        except Exception as error:
            print(f"Kafka publishing failed: {error}")
            return False
 
    def close(self):
        self.producer.flush()
        self.producer.close()