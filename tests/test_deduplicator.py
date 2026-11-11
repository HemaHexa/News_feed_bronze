 
import tempfile
from pathlib import Path
 
from producers.news import deduplicator
 
 
def test_deduplication():
    with tempfile.TemporaryDirectory() as temp_dir:
 
        # Use temporary storage so real project data is untouched
        deduplicator.SEEN_ARTICLES_FILE = (
            Path(temp_dir) / "seen_articles.json"
        )
 
        deduplicator.initialize_database()
 
        article_id = "test-article-123"
 
        assert not deduplicator.is_article_seen(article_id)
        print("New article detection passed!")
 
        deduplicator.mark_article_published(article_id)
 
        assert deduplicator.is_article_seen(article_id)
        print("Published article detection passed!")
 
        deduplicator.mark_article_published(article_id)
 
        seen = deduplicator.load_seen_articles()
 
        assert len(seen) == 1
        print("Duplicate prevention test passed!")
 
 
if __name__ == "__main__":
    test_deduplication()
 