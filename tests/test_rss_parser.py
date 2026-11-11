 
from producers.news.rss_parser import parse_article
 
 
def test_parse_article():
    entry = {
        "id": "article-123",
        "title": "Reliance Industries reports strong profits",
        "link": "https://example.com/reliance-news",
        "summary": "<p>Reliance reported strong quarterly profits.</p>"
    }
 
    article = parse_article(entry, "Economic Times")
 
    assert article["guid"] == "article-123"
    assert article["headline"] == "Reliance Industries reports strong profits"
    assert article["source"] == "Economic Times"
    assert article["url"] == "https://example.com/reliance-news"
    assert article["full_text"] == (
        "<p>Reliance reported strong quarterly profits.</p>"
    )
 
    print("RSS parser test passed!")
 
 
if __name__ == "__main__":
    test_parse_article()
 