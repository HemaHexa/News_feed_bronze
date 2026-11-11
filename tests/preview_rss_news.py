from collections import Counter
 
from config.rss_sources import RSS_FEEDS
from config.settings import HTTP_TIMEOUT_SECONDS
from config.companies import COMPANIES
 
from producers.news.rss_fetcher import fetch_feed
from producers.news.rss_parser import parse_article
from producers.news.company_filter import find_matching_companies
 
 
def preview_news():
 
    total_articles = 0
    relevant_articles = 0
    company_counts = Counter()
    source_counts = Counter()
 
    print("\n========== FINTEL LIVE RSS VERIFICATION ==========\n")
 
    for feed in RSS_FEEDS:
 
        if not feed["enabled"]:
            continue
 
        print(f"\nSOURCE: {feed['source']}")
        print("-" * 80)
 
        try:
            entries = fetch_feed(
                feed["url"],
                timeout=HTTP_TIMEOUT_SECONDS
            )
 
            print(f"Articles received: {len(entries)}")
 
            for entry in entries:
 
                total_articles += 1
 
                article = parse_article(
                    entry,
                    feed["source"]
                )
 
                matches = find_matching_companies(
                    article["headline"],
                    article["full_text"]
                )
 
                if not matches:
                    continue
 
                relevant_articles += 1
                source_counts[feed["source"]] += 1
 
                for symbol in matches:
                    company_counts[symbol] += 1
 
                print("\n[RELEVANT NEWS]")
                print("Headline:", article["headline"])
                print("Source:", article["source"])
                print("Published:", article["published_at"])
 
                print("Matched companies:")
 
                for symbol in matches:
                    name = COMPANIES[symbol]["name"]
                    print(f"  {name} ({symbol})")
 
                print("URL:", article["url"])
 
        except Exception as error:
            print(f"Feed error: {error}")
 
    print("\n========== COMPANY-WISE SUMMARY ==========")
 
    for symbol, details in COMPANIES.items():
        print(
            f"{details['name']} ({symbol}): "
            f"{company_counts[symbol]} articles"
        )
 
    print("\n========== SOURCE SUMMARY ==========")
 
    for feed in RSS_FEEDS:
        if feed["enabled"]:
            print(
                f"{feed['source']}: "
                f"{source_counts[feed['source']]} relevant articles"
            )
 
    print("\n========== OVERALL SUMMARY ==========")
    print("Total articles fetched:", total_articles)
    print("Relevant articles:", relevant_articles)
    print("Unrelated articles:", total_articles - relevant_articles)
 
 
if __name__ == "__main__":
    preview_news()