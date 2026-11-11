 
import json
import os
 
from datetime import datetime, timezone
 
from config.settings import (
    NEWS_CHECKPOINT_PATH,
    LATEST_NEWS_PATH
)
 
 
def current_utc_time():
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
 
 
def load_json(path, default):
    """Load JSON safely. Return default if file does not exist."""
 
    if not path.exists():
        return default
 
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
 
    except (json.JSONDecodeError, OSError):
        print(f"[WARNING] Could not read state file: {path}")
        raise
 
 
def save_json(path, data):
    """Save JSON atomically to avoid partially written state."""
 
    path.parent.mkdir(parents=True, exist_ok=True)
 
    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )
 
    with open(temporary_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )
 
    os.replace(temporary_path, path)
 
 
# ============================================================
# CHECKPOINT MANAGEMENT
# ============================================================
 
def load_checkpoints():
    """
    Load the last successful search time for each company.
 
    Example:
    {
        "TCS": "2026-11-11T10:00:00+00:00",
        "RELIANCE": "2026-11-11T10:00:00+00:00"
    }
    """
 
    return load_json(NEWS_CHECKPOINT_PATH, {})
 
 
def get_company_checkpoint(symbol):
    """Get the last successful checkpoint for a company."""
 
    checkpoints = load_checkpoints()
 
    return checkpoints.get(symbol)
 
 
def update_company_checkpoint(symbol, timestamp=None):
    """Update checkpoint only after a successful company search."""
 
    checkpoints = load_checkpoints()
 
    checkpoints[symbol] = timestamp or current_utc_time()
 
    save_json(
        NEWS_CHECKPOINT_PATH,
        checkpoints
    )
 
 
# ============================================================
# LATEST NEWS MANAGEMENT
# ============================================================
 
def load_latest_news():
    """Load the latest valid article stored for each company."""
 
    return load_json(LATEST_NEWS_PATH, {})
 
 
def get_latest_news(symbol):
    """Get the current latest article for one company."""
 
    latest_news = load_latest_news()
 
    return latest_news.get(symbol)
 
 
def update_latest_news(symbol, article):
    """
    Replace the current latest article only when the
    incoming article is newer.
    """
 
    latest_news = load_latest_news()
 
    existing_article = latest_news.get(symbol)
 
    if existing_article:
        existing_date = existing_article.get("published_at")
        new_date = article.get("published_at")
 
        if existing_date and new_date:
            if new_date <= existing_date:
                return False
 
    latest_news[symbol] = article
 
    save_json(
        LATEST_NEWS_PATH,
        latest_news
    )
 
    return True
 
 
def initialize_latest_news(articles):
    """Initialize latest-news records from initial search results."""
 
    latest_news = load_latest_news()
 
    for article in articles:
        symbol = article.get("company_symbol")
 
        if not symbol:
            continue
 
        existing = latest_news.get(symbol)
 
        if existing:
            existing_date = existing.get("published_at")
            new_date = article.get("published_at")
 
            if existing_date and new_date:
                if new_date <= existing_date:
                    continue
 
        latest_news[symbol] = article
 
    save_json(
        LATEST_NEWS_PATH,
        latest_news
    )
 
 
# ============================================================
# STATE STATUS
# ============================================================
 
def is_initial_run():
    """Check whether any company checkpoint exists."""
 
    checkpoints = load_checkpoints()
 
    return not bool(checkpoints)
 
 
def print_state_summary():
    """Display stored ingestion state."""
 
    checkpoints = load_checkpoints()
    latest_news = load_latest_news()
 
    print("\n========== FINTEL NEWS STATE ==========")
 
    print(f"Companies with checkpoints : {len(checkpoints)}")
    print(f"Companies with latest news : {len(latest_news)}")
 
    print("\nLatest stored news:")
 
    for symbol, article in latest_news.items():
        print(
            f"{symbol}: "
            f"{article.get('headline', 'N/A')}"
        )
 
    print("=======================================\n")
 