import json
import time
import uuid
 
from pathlib import Path
from config.settings import BUFFER_DIR
 
 
class BufferManager:
 
    def __init__(self):
        self.buffer_dir = Path(BUFFER_DIR)
        self.buffer_dir.mkdir(parents=True, exist_ok=True)
 
    def save(self, article):
        """Save an unpublished article to disk."""
 
        filename = (
            f"{time.time_ns()}_{uuid.uuid4().hex}.json"
        )
 
        file_path = self.buffer_dir / filename
        temp_path = file_path.with_suffix(".tmp")
 
        temp_path.write_text(
            json.dumps(article, ensure_ascii=False),
            encoding="utf-8"
        )
 
        temp_path.replace(file_path)
 
        print(f"Article buffered: {article['article_id']}")
 
    def get_pending(self):
        """Retrieve buffered articles in creation order."""
 
        pending = []
 
        for file_path in sorted(self.buffer_dir.glob("*.json")):
            try:
                with file_path.open("r", encoding="utf-8") as file:
                    article = json.load(file)
 
                pending.append((file_path, article))
 
            except (json.JSONDecodeError, OSError) as error:
                print(f"Could not read {file_path.name}: {error}")
 
        return pending
 
    def remove(self, file_path):
        """Delete an article only after Kafka acknowledges it."""
 
        Path(file_path).unlink(missing_ok=True)