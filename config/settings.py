 
import os
from pathlib import Path
from dotenv import load_dotenv
 
 
# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
 
# Load environment variables
load_dotenv(BASE_DIR / ".env")
 
 
# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)
 
NEWS_TOPIC = os.getenv(
    "NEWS_TOPIC",
    "raw-news-events"
)
 
 
# News polling configuration
RSS_POLL_INTERVAL_SECONDS = int(
    os.getenv("RSS_POLL_INTERVAL_SECONDS", "900")
)
 
HTTP_TIMEOUT_SECONDS = int(
    os.getenv("HTTP_TIMEOUT_SECONDS", "20")
)
 
MAX_RETRIES = int(
    os.getenv("MAX_RETRIES", "3")
)
 
 
# Persistent storage paths
DATABASE_PATH = BASE_DIR / os.getenv(
    "DATABASE_PATH",
    "shared_data/producer_state/seen_articles.db"
)
 
BUFFER_DIR = BASE_DIR / os.getenv(
    "BUFFER_DIR",
    "shared_data/producer_state/buffer"
)
 
# New persistent state for incremental ingestion
NEWS_STATE_DIR = BASE_DIR / "shared_data/producer_state"
 
NEWS_CHECKPOINT_PATH = NEWS_STATE_DIR / "news_checkpoint.json"
 
LATEST_NEWS_PATH = NEWS_STATE_DIR / "latest_news.json"
 
 
# Create required directories
DATABASE_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)
 
BUFFER_DIR.mkdir(
    parents=True,
    exist_ok=True
)
 
NEWS_STATE_DIR.mkdir(
    parents=True,
    exist_ok=True
)
 