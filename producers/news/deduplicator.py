import json
 
from pathlib import Path
from config.settings import BASE_DIR
 
 
# Persistent JSON storage
SEEN_ARTICLES_FILE = (
    BASE_DIR / "shared_data" / "producer_state" / "seen_articles.json"
)
 
 
def initialize_database():
    """Create JSON storage if it doesn't exist."""
    SEEN_ARTICLES_FILE.parent.mkdir(
        parents=True, exist_ok=True
    )
 
    if not SEEN_ARTICLES_FILE.exists():
        SEEN_ARTICLES_FILE.write_text(
            "[]", encoding="utf-8"
        )
 
 
def load_seen_articles():
    """Load previously published article IDs."""
    initialize_database()
 
    with SEEN_ARTICLES_FILE.open(
        "r", encoding="utf-8"
    ) as file:
        return set(json.load(file))
 
 
def is_article_seen(article_id):
    """Check whether an article was already published."""
    return article_id in load_seen_articles()
 
 
def mark_article_published(article_id):
    """Save article ID after Kafka acknowledgement."""
    seen_articles = load_seen_articles()
 
    if article_id not in seen_articles:
        seen_articles.add(article_id)
 
        temp_file = SEEN_ARTICLES_FILE.with_suffix(".tmp")
 
        temp_file.write_text(
            json.dumps(sorted(seen_articles), indent=2),
            encoding="utf-8"
        )
 
        temp_file.replace(SEEN_ARTICLES_FILE)