 
from kafka import KafkaAdminClient
 
from config.settings import (
    KAFKA_BOOTSTRAP_SERVERS,
    NEWS_TOPIC
)
 
 
def test_kafka_connection():
 
    admin = None
 
    try:
        admin = KafkaAdminClient(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
            request_timeout_ms=10000
        )
 
        print("Kafka connection successful!")
 
        topics = admin.list_topics()
 
        if NEWS_TOPIC in topics:
            print(f"Topic found: {NEWS_TOPIC}")
 
            description = admin.describe_topics([NEWS_TOPIC])[0]
 
            print(
                "Number of partitions:",
                len(description["partitions"])
            )
        else:
            print(f"ERROR: Topic not found: {NEWS_TOPIC}")
 
    except Exception as error:
        print("Kafka connection failed:", error)
 
    finally:
        if admin:
            admin.close()
 
 
if __name__ == "__main__":
    test_kafka_connection()
 