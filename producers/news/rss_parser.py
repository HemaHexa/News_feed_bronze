 
from datetime import datetime, timezone
 
 
def parse_article(entry, source):
    headline = entry.get("title", "").strip()
    url = entry.get("link", "").strip()
 
    # Preserve original HTML content
    content = entry.get("content", [])
 
    if content:
        full_text = content[0].get("value", "")
    else:
        full_text = entry.get("summary", "")
 
    # Extract publication timestamp
    published_at = None
    published = entry.get("published_parsed")
 
    if published:
        published_at = datetime(
            *published[:6],
            tzinfo=timezone.utc
        ).isoformat().replace("+00:00", "Z")
 
    return {
        "guid": entry.get("id") or entry.get("guid"),
        "published_at": published_at,
        "source": source,
        "headline": headline or None,
        "full_text": full_text or None,
        "url": url or None
    }
 