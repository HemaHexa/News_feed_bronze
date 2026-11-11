
import calendar
import requests
import feedparser
import truststore

from datetime import datetime, timedelta, timezone

from config.companies import COMPANIES
from config.rss_sources import RSS_FEEDS
from config.settings import HTTP_TIMEOUT_SECONDS

from producers.news.company_filter import find_matching_companies
from producers.news.financial_filter import evaluate_financial_news


# ============================================================
# CONFIGURATION
# ============================================================

truststore.inject_into_ssl()

FINANCIAL_NEWS_TERMS = (
    'earnings OR revenue OR profit OR "financial results" '
    'OR acquisition OR contract OR expansion OR investment '
    'OR dividend OR fundraising OR regulatory OR order '
    'OR partnership OR merger OR debt OR "market share" '
    'OR analyst OR brokerage OR "target price" '
    'OR "shares rise" OR "shares fall"'
)

SEARCH_OVERLAP_HOURS = 24

HEADERS = {
    "User-Agent": "FinTel-NewsPipeline/1.0"
}


# ============================================================
# GOOGLE NEWS CONFIGURATION
# ============================================================

def get_google_news_config():
    for source in RSS_FEEDS:
        if (
            source["source"] == "Google News RSS"
            and source["enabled"]
        ):
            return source

    raise ValueError("Google News RSS is not enabled.")


# ============================================================
# QUERY GENERATION
# ============================================================

def build_company_query(symbol, company, since=None):

    company_name = company["name"]

    if symbol == "ITC":
        company_query = '"ITC Limited" OR "ITC Ltd"'
    else:
        company_query = f'"{company_name}"'

    query = (
        f'({company_query}) '
        f'({FINANCIAL_NEWS_TERMS})'
    )

    if since is not None:
        overlap_start = since - timedelta(
            hours=SEARCH_OVERLAP_HOURS
        )

        query += (
            f' after:{overlap_start.strftime("%Y-%m-%d")}'
        )

    return query


# ============================================================
# DATE PARSING
# ============================================================

def parse_published_time(entry):

    published_parsed = entry.get("published_parsed")

    if not published_parsed:
        return None

    timestamp = calendar.timegm(published_parsed)

    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc
    ).isoformat()


# ============================================================
# FETCH GOOGLE NEWS
# ============================================================

def fetch_google_news_for_company(
    symbol,
    company,
    since=None,
    timeout=HTTP_TIMEOUT_SECONDS
):

    source_config = get_google_news_config()

    query = build_company_query(
        symbol,
        company,
        since
    )

    params = {
        "q": query,
        "hl": "en-IN",
        "gl": "IN",
        "ceid": "IN:en"
    }

    response = requests.get(
        source_config["url"],
        params=params,
        headers=HEADERS,
        timeout=timeout
    )

    response.raise_for_status()

    parsed_feed = feedparser.parse(response.content)

    articles = []

    for entry in parsed_feed.entries:

        publisher = entry.get("source", {})

        publisher_name = (
            publisher.get("title", "Unknown")
            if isinstance(publisher, dict)
            else "Unknown"
        )

        article = dict(entry)

        article["retrieved_via"] = "Google News RSS"
        article["publisher"] = publisher_name
        article["company_symbol"] = symbol
        article["company_name"] = company["name"]
        article["search_query"] = query
        article["published_at"] = parse_published_time(entry)

        articles.append(article)

    return articles


# ============================================================
# ARTICLE RELEVANCE AND QUALITY VALIDATION
# ============================================================

def validate_article(article, expected_symbol):

    headline = article.get("title", "")
    description = article.get("summary", "")
    publisher = article.get("publisher", "")

    # Step 1: Validate target company.
    matching_companies = find_matching_companies(
        headline,
        description
    )

    if expected_symbol not in matching_companies:

        return False, {
            "category": "company_mismatch",
            "score": 0,
            "reason": (
                "Article does not sufficiently identify "
                "the expected company."
            )
        }

    # Step 2: Validate financial-news quality.
    result = evaluate_financial_news(
        headline,
        description,
        publisher
    )

    if not result.accepted:
        return False, {
            "category": result.category,
            "score": result.score,
            "reason": result.reason
        }

    return True, {
        "category": result.category,
        "score": result.score,
        "reason": result.reason
    }


# ============================================================
# SELECT LATEST VALID ARTICLE
# ============================================================

def get_latest_valid_article(articles, symbol):

    valid_articles = []

    seen_links = set()

    for article in articles:

        article_url = article.get("link", "")

        if not article_url or article_url in seen_links:
            continue

        seen_links.add(article_url)

        if not article.get("published_at"):
            continue

        accepted, result = validate_article(
            article,
            symbol
        )

        article["filter_result"] = result

        if accepted:
            valid_articles.append(article)

    valid_articles.sort(
        key=lambda article: article["published_at"],
        reverse=True
    )

    return valid_articles


# ============================================================
# TERMINAL DISPLAY
# ============================================================

def print_article_details(article):

    print("\n" + "-" * 100)
    print("                 SELECTED LATEST VALID FINANCIAL NEWS")
    print("-" * 100)

    print(f"\nCompany       : {article.get('company_name')}")
    print(f"Symbol        : {article.get('company_symbol')}")
    print(f"Headline      : {article.get('title')}")
    print(f"Publisher     : {article.get('publisher')}")
    print(f"Retrieved Via : {article.get('retrieved_via')}")
    print(f"Published     : {article.get('published')}")
    print(f"Published UTC : {article.get('published_at')}")
    print(f"Article URL   : {article.get('link')}")

    print(f"\nDescription   : {article.get('summary', 'N/A')}")

    result = article.get("filter_result", {})

    print(f"\nNews Category : {result.get('category')}")
    print(f"Quality Score : {result.get('score')}")
    print(f"Filter Status : ACCEPTED")
    print(f"Reason        : {result.get('reason')}")

    print("-" * 100)


def print_rejected_article(article, reason):

    print("\n[REJECTED ARTICLE]")

    print(f"Headline : {article.get('title', 'N/A')}")
    print(f"Publisher: {article.get('publisher', 'Unknown')}")
    print(f"Reason   : {reason.get('reason')}")
    print(f"Category : {reason.get('category')}")


# ============================================================
# PROCESS ONE COMPANY
# ============================================================

def process_company_news(
    symbol,
    company,
    since=None,
    timeout=HTTP_TIMEOUT_SECONDS
):

    print("\n" + "=" * 100)
    print(f"COMPANY : {company['name'].upper()} ({symbol})")
    print("=" * 100)

    articles = fetch_google_news_for_company(
        symbol,
        company,
        since,
        timeout
    )

    print(f"\nRSS candidates retrieved : {len(articles)}")

    accepted_articles = []
    rejected_count = 0
    seen_links = set()

    for article in articles:

        article_url = article.get("link", "")

        if not article_url or article_url in seen_links:
            continue

        seen_links.add(article_url)

        if not article.get("published_at"):
            rejected_count += 1
            print_rejected_article(
                article,
                {
                    "reason": "Publication date unavailable",
                    "category": "invalid_date"
                }
            )
            continue

        accepted, result = validate_article(
            article,
            symbol
        )

        article["filter_result"] = result

        if accepted:
            accepted_articles.append(article)
        else:
            rejected_count += 1
            print_rejected_article(article, result)

    accepted_articles.sort(
        key=lambda article: article["published_at"],
        reverse=True
    )

    print("\n" + "-" * 100)
    print("COMPANY FILTER SUMMARY")
    print("-" * 100)

    print(f"Candidates Retrieved : {len(articles)}")
    print(f"Accepted Candidates  : {len(accepted_articles)}")
    print(f"Rejected Candidates  : {rejected_count}")

    if not accepted_articles:

        print("\nSTATUS : NO VALID FINANCIAL NEWS FOUND")

        return None

    latest_article = accepted_articles[0]

    print(f"Selected Articles    : 1")

    print_article_details(latest_article)

    return latest_article


# ============================================================
# INITIAL FULL SEARCH
# ============================================================

def fetch_initial_news(timeout=HTTP_TIMEOUT_SECONDS):

    latest_articles = []
    successful_symbols = []

    print("\n\n")
    print("#" * 100)
    print("                 FINTEL INITIAL NEWS INGESTION")
    print("#" * 100)

    print("MODE           : INITIAL FULL SEARCH")
    print("SOURCE         : GOOGLE NEWS RSS")
    print(f"COMPANIES      : {len(COMPANIES)}")
    print("SELECTION      : ONE LATEST VALID ARTICLE PER COMPANY")
    print("#" * 100)

    for index, (symbol, company) in enumerate(
        COMPANIES.items(),
        start=1
    ):

        print(f"\nCOMPANY {index}/{len(COMPANIES)}")

        try:

            latest_article = process_company_news(
                symbol,
                company,
                since=None,
                timeout=timeout
            )

            successful_symbols.append(symbol)

            if latest_article:
                latest_articles.append(latest_article)

        except requests.RequestException as error:

            print(f"\n[FETCH FAILED] {symbol}: {error}")

    print("\n\n")
    print("#" * 100)
    print("                 INITIAL INGESTION SUMMARY")
    print("#" * 100)

    print(f"Companies Configured : {len(COMPANIES)}")
    print(f"Successful Searches  : {len(successful_symbols)}")
    print(f"Companies With News  : {len(latest_articles)}")
    print(
        f"Companies Without News: "
        f"{len(COMPANIES) - len(latest_articles)}"
    )

    print("\nLATEST VALID ARTICLE PER COMPANY")

    for article in latest_articles:

        print(
            f"\n{article['company_symbol']}"
            f"\n{article.get('title')}"
            f"\nPublished: {article.get('published_at')}"
        )

    print("\n" + "#" * 100)

    return latest_articles, successful_symbols


# ============================================================
# INCREMENTAL SEARCH
# ============================================================

def fetch_incremental_news(
    checkpoints,
    timeout=HTTP_TIMEOUT_SECONDS
):

    latest_new_articles = []
    successful_symbols = []

    print("\n\n")
    print("#" * 100)
    print("                 FINTEL INCREMENTAL NEWS SEARCH")
    print("#" * 100)

    for index, (symbol, company) in enumerate(
        COMPANIES.items(),
        start=1
    ):

        checkpoint_value = checkpoints.get(symbol)

        print(f"\nCOMPANY {index}/{len(COMPANIES)}: {symbol}")

        if not checkpoint_value:

            print("STATUS : NO CHECKPOINT - SKIPPED")

            continue

        try:

            checkpoint = datetime.fromisoformat(
                checkpoint_value
            )

            if checkpoint.tzinfo is None:
                checkpoint = checkpoint.replace(
                    tzinfo=timezone.utc
                )

            articles = fetch_google_news_for_company(
                symbol,
                company,
                since=checkpoint,
                timeout=timeout
            )

            print(f"RSS candidates retrieved: {len(articles)}")

            new_candidates = []

            for article in articles:

                published_at = article.get("published_at")

                if not published_at:
                    continue

                published_datetime = datetime.fromisoformat(
                    published_at
                )

                # Overlap is for retrieval only.
                # Only articles newer than the checkpoint
                # qualify as new events.
                if published_datetime > checkpoint:
                    new_candidates.append(article)

            print(
                f"Articles newer than checkpoint: "
                f"{len(new_candidates)}"
            )

            accepted_articles = get_latest_valid_article(
                new_candidates,
                symbol
            )

            successful_symbols.append(symbol)

            if not accepted_articles:

                print("STATUS : NO NEW VALID NEWS")
                print("Existing latest-news record remains unchanged.")

                continue

            latest_article = accepted_articles[0]

            print_article_details(latest_article)

            latest_new_articles.append(latest_article)

            print("STATUS : NEW VALID ARTICLE FOUND")

        except requests.RequestException as error:

            print(f"[FETCH FAILED] {symbol}: {error}")

    print("\n\n")
    print("#" * 100)
    print("                 INCREMENTAL SEARCH SUMMARY")
    print("#" * 100)

    print(f"Companies Configured : {len(COMPANIES)}")
    print(f"Successful Searches  : {len(successful_symbols)}")
    print(f"New Valid Articles   : {len(latest_new_articles)}")

    print("#" * 100)

    return latest_new_articles, successful_symbols