 
from unittest.mock import patch, MagicMock
 
from producers.news.kafka_publisher import NewsKafkaPublisher
 
 
def test_successful_publish():
 
    mock_producer = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.partition = 0
    mock_metadata.offset = 10
 
    mock_producer.send.return_value.get.return_value = mock_metadata
 
    with patch(
        "producers.news.kafka_publisher.KafkaProducer",
        return_value=mock_producer
    ):
        publisher = NewsKafkaPublisher()
 
        article = {
            "article_id": "test-001",
            "headline": "Reliance Industries reports strong profits"
        }
 
        result = publisher.publish(article)
 
        assert result is True
        mock_producer.send.assert_called_once()
 
        print("Kafka successful publishing test passed!")
 
 
def test_failed_publish():
 
    mock_producer = MagicMock()
 
    mock_producer.send.return_value.get.side_effect = (
        Exception("Kafka unavailable")
    )
 
    with patch(
        "producers.news.kafka_publisher.KafkaProducer",
        return_value=mock_producer
    ):
        publisher = NewsKafkaPublisher()
 
        article = {
            "article_id": "test-002",
            "headline": "HDFC Bank reports quarterly results"
        }
 
        result = publisher.publish(article)
 
        assert result is False
 
        print("Kafka failure handling test passed!")
 
 
if __name__ == "__main__":
    test_successful_publish()
    test_failed_publish()
 