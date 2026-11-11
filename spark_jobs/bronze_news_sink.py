import hashlib
import json
import uuid

from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from config.settings import BASE_DIR


# ============================================================
# BRONZE STORAGE CONFIGURATION
# ============================================================

BRONZE_NEWS_DIR = (
    BASE_DIR / "shared_data" / "bronze" / "news_v2"
)


# ============================================================
# ARTICLE NORMALIZATION
# ============================================================

def normalize_article(article):
    """
    Convert an incoming news event into the agreed
    seven-field Silver integration JSON structure.

    Original HTML in full_text is preserved.
    """

    headline = (
        article.get("headline")
        or article.get("title")
    )

    full_text = (
        article.get("full_text")
        or article.get("description")
        or article.get("summary")
    )

    url = (
        article.get("url")
        or article.get("link")
    )

    # URL is mandatory.
    if not url:
        raise ValueError("Article rejected: URL is missing.")

    # At least one content field is mandatory.
    if not headline and not full_text:
        raise ValueError(
            "Article rejected: Both headline and full_text are missing."
        )

    # Preserve an existing stable ID.
    # Generate one from the URL if it is unavailable.
    article_id = article.get("article_id")

    if not article_id:
        article_id = hashlib.sha256(
            url.strip().encode("utf-8")
        ).hexdigest()

    # Prefer the publisher name over the feed provider name.
    source = article.get("publisher") or article.get("source")

    if source == "Google News RSS" and article.get("publisher"):
        source = article["publisher"]

    # Preserve the original article collection timestamp.
    ingested_at = (
        article.get("ingested_at")
        or datetime.now(timezone.utc).isoformat()
    )

    normalized = {
        "article_id": str(article_id),
        "published_at": article.get("published_at"),
        "source": source,
        "headline": headline,
        "full_text": full_text,
        "url": url,
        "ingested_at": ingested_at
    }

    return normalized


# ============================================================
# BRONZE NEWS SINK
# ============================================================

class BronzeNewsSink:

    def __init__(self):

        self.output_dir = Path(BRONZE_NEWS_DIR)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def write_batch(self, messages):
        """
        Write Kafka messages into the agreed Bronze Parquet schema.

        Kafka metadata:
            kafka_key
            raw_json
            topic
            partition
            offset
            kafka_ts
        """

        if not messages:
            print("[BRONZE] No messages to write.")
            return None

        rows = []

        for message in messages:

            article = normalize_article(message["value"])

            raw_json = json.dumps(
                article,
                ensure_ascii=False
            )

            rows.append({
                "kafka_key": message.get("key"),
                "raw_json": raw_json,
                "topic": message["topic"],
                "partition": message["partition"],
                "offset": message["offset"],
                "kafka_ts": message.get("timestamp")
            })

        # ----------------------------------------------------
        # EXACT AGREED PARQUET SCHEMA
        # ----------------------------------------------------

        schema = pa.schema([
            ("kafka_key", pa.string()),
            ("raw_json", pa.string()),
            ("topic", pa.string()),
            ("partition", pa.int32()),
            ("offset", pa.int64()),
            ("kafka_ts", pa.timestamp("ms", tz="UTC"))
        ])

        table = pa.Table.from_pylist(
            rows,
            schema=schema
        )

        # ----------------------------------------------------
        # FILE NAMING
        # ----------------------------------------------------

        timestamp = datetime.now(
            timezone.utc
        ).strftime("%Y%m%dT%H%M%S%fZ")

        filename = (
            f"news_{timestamp}_{uuid.uuid4().hex[:8]}.parquet"
        )

        final_path = self.output_dir / filename

        temporary_path = (
            self.output_dir / f"{filename}.tmp"
        )

        # ----------------------------------------------------
        # WRITE PARQUET ATOMICALLY
        # ----------------------------------------------------

        try:

            pq.write_table(
                table,
                temporary_path,
                compression="snappy"
            )

            temporary_path.replace(final_path)

            print("\n========== BRONZE WRITE SUCCESS ==========")
            print(f"Records written : {len(rows)}")
            print(f"File            : {final_path}")
            print("Format          : Parquet")
            print("Compression     : Snappy")
            print("\nBronze schema:")

            for field in schema:
                print(
                    f"{field.name:<15} {field.type}"
                )

            print("===========================================\n")

            return final_path

        except Exception:

            temporary_path.unlink(missing_ok=True)

            raise