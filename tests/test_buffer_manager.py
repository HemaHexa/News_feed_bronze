 
import tempfile
from pathlib import Path
 
from producers.news import buffer_manager
 
 
def test_buffer_manager():
 
    with tempfile.TemporaryDirectory() as temp_dir:
 
        buffer_manager.BUFFER_DIR = Path(temp_dir)
 
        manager = buffer_manager.BufferManager()
 
        article = {
            "article_id": "test-article-001",
            "headline": "Reliance Industries reports strong profits",
            "source": "Economic Times"
        }
 
        # Save article
        manager.save(article)
        print("Article buffering test passed!")
 
        # Retrieve pending articles
        pending = manager.get_pending()
 
        assert len(pending) == 1
        assert pending[0][1]["article_id"] == "test-article-001"
 
        print("Pending article retrieval test passed!")
 
        # Remove after successful publishing
        manager.remove(pending[0][0])
 
        assert len(manager.get_pending()) == 0
 
        print("Buffer removal test passed!")
 
 
if __name__ == "__main__":
    test_buffer_manager()
 