 
from producers.news.metrics import NewsMetrics
 
 
def test_news_metrics():
 
    metrics = NewsMetrics()
 
    metrics.increment("articles_discovered", 50)
    metrics.increment("relevant_articles", 12)
    metrics.increment("articles_rejected", 38)
    metrics.increment("kafka_published", 12)
 
    assert metrics.counters["articles_discovered"] == 50
    assert metrics.counters["relevant_articles"] == 12
    assert metrics.counters["articles_rejected"] == 38
    assert metrics.counters["kafka_published"] == 12
 
    print("Metrics counter tests passed!")
 
    metrics.record_feed_fetch(
        source="Moneycontrol",
        duration=1.25,
        status="success"
    )
 
    assert metrics.counters["feeds_fetched"] == 1
    assert metrics.counters["feeds_success"] == 1
 
    print("Feed metrics tests passed!")
 
    metrics.report()
 
 
if __name__ == "__main__":
    test_news_metrics()
 