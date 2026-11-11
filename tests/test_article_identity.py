from producers.news.article_identity import generate_article_id
 
 
def test_same_guid_same_id():
    id1 = generate_article_id(
        guid="article-123",
        url="https://example.com/article"
    )
 
    id2 = generate_article_id(
        guid="article-123",
        url="https://example.com/updated-url"
    )
 
    assert id1 == id2
    print("GUID identity test passed!")
 
 
def test_url_fallback():
    id1 = generate_article_id(
        url="https://example.com/article?utm_source=rss"
    )
 
    id2 = generate_article_id(
        url="https://example.com/article"
    )
 
    assert id1 == id2
    print("URL fallback test passed!")
 
 
def test_unique_articles():
    id1 = generate_article_id(guid="article-1")
    id2 = generate_article_id(guid="article-2")
 
    assert id1 != id2
    print("Unique article ID test passed!")
 
 
if __name__ == "__main__":
    test_same_guid_same_id()
    test_url_fallback()
    test_unique_articles()