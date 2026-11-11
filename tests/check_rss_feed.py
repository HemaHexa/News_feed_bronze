import requests
import feedparser
import truststore
truststore.inject_into_ssl()

from config.rss_sources import RSS_FEEDS
from config.settings import HTTP_TIMEOUT_SECONDS
 
for feed in RSS_FEEDS:
    if not feed["enabled"]:
        continue
 
    print(f"\nTesting: {feed['source']}")
 
    try:
        response = requests.get(
            feed["url"],
            timeout=HTTP_TIMEOUT_SECONDS,
            headers={"User-Agent": "FinTel-NewsPipeline/1.0"}
        )
 
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
 
        print("HTTP Status:", response.status_code)
        print("Articles found:", len(parsed.entries))
 
        if parsed.entries:
            print("Sample headline:", parsed.entries[0].get("title", "No title"))
        else:
            print("No articles returned.")
 
    except requests.RequestException as error:
        print("Feed request failed:", error)