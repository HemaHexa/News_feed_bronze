import time
from datetime import datetime, timezone

from config.companies import COMPANIES
from config.settings import RSS_POLL_INTERVAL_SECONDS

from producers.news.rss_fetcher import (
    fetch_initial_news,
    fetch_incremental_news,
)
from producers.news.article_identity import generate_article_id
from producers.news.deduplicator import (
    initialize_database,
    is_article_seen,
    mark_article_published,
)
from producers.news.news_state import (
    is_initial_run,
    load_checkpoints,
    update_company_checkpoint,
    update_latest_news,
    print_state_summary,
)
from producers.news.kafka_publisher import NewsKafkaPublisher
from producers.news.buffer_manager import BufferManager
from producers.news.metrics import NewsMetrics


class NewsProducer:

    def __init__(self):
        initialize_database()

        self.kafka = NewsKafkaPublisher()
        self.buffer = BufferManager()
        self.metrics = NewsMetrics()

    # --------------------------------------------------------
    # ARTICLE CONVERSION
    # --------------------------------------------------------

    def prepare_article(self, article):

        url = article.get("link", "")
        guid = article.get("guid") or article.get("id")

        article_id = generate_article_id(
            guid=guid,
            url=url
        )

        filter_result = article.get("filter_result", {})

        return {
            "article_id": article_id,
            "company_symbol": article.get("company_symbol"),
            "company_name": article.get("company_name"),
            "headline": article.get("title", ""),
            "publisher": article.get("publisher", "Unknown"),
            "published": article.get("published"),
            "published_at": article.get("published_at"),
            "description": article.get("summary", ""),
            "url": url,
            "source": article.get("retrieved_via", "Google News RSS"),
            "search_query": article.get("search_query", ""),
            "news_category": filter_result.get("category", "unclassified"),
            "quality_score": filter_result.get("score", 0),
            "filter_reason": filter_result.get("reason", ""),
            "ingested_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    # --------------------------------------------------------
    # BUFFERED ARTICLE IDS
    # --------------------------------------------------------

    def get_pending_article_ids(self):

        return {
            article["article_id"]
            for _, article in self.buffer.get_pending()
        }

    # --------------------------------------------------------
    # PUBLISH ARTICLE
    # --------------------------------------------------------

    def publish_article(self, article):

        article_id = article["article_id"]

        if is_article_seen(article_id):
            print(f"[DUPLICATE] Already published: {article_id}")
            return True

        try:
            success = self.kafka.publish(article)

            if success:
                mark_article_published(article_id)

                self.metrics.increment("kafka_published")

                return True

        except Exception as error:
            print(f"[KAFKA ERROR] {error}")

        # Kafka failed. Persist the article before treating it
        # as safely queued for future delivery.
        try:
            self.buffer.save(article)

            self.metrics.increment("buffered_articles")

            print(f"[BUFFERED] {article_id}")

            return True

        except Exception as error:
            print(f"[BUFFER ERROR] {error}")

            return False

    # --------------------------------------------------------
    # REPLAY BUFFER
    # --------------------------------------------------------

    def replay_buffer(self):

        print("\n========== BUFFER REPLAY ==========")

        pending = self.buffer.get_pending()

        if not pending:
            print("No pending articles.")
            return

        print(f"Pending articles: {len(pending)}")

        for file_path, article in pending:

            article_id = article["article_id"]

            if is_article_seen(article_id):
                self.buffer.remove(file_path)
                continue

            success = self.kafka.publish(article)

            if success:
                mark_article_published(article_id)
                self.buffer.remove(file_path)

                self.metrics.increment("buffer_replayed")

            else:
                print("Kafka unavailable. Preserving buffer order.")
                break

    # --------------------------------------------------------
    # PROCESS SEARCH RESULTS
    # --------------------------------------------------------

    def process_search_results(
        self,
        articles,
        successful_symbols
    ):

        articles_by_company = {
            article["company_symbol"]: article
            for article in articles
            if article.get("company_symbol")
        }

        pending_ids = self.get_pending_article_ids()

        for symbol in successful_symbols:

            article = articles_by_company.get(symbol)

            # No new valid article for this company.
            if article is None:
                update_company_checkpoint(symbol)

                print(
                    f"[NO NEW NEWS] {symbol} | "
                    "Checkpoint updated."
                )

                continue

            kafka_article = self.prepare_article(article)
            article_id = kafka_article["article_id"]

            # Already published previously.
            if is_article_seen(article_id):

                update_latest_news(symbol, kafka_article)
                update_company_checkpoint(symbol)

                self.metrics.increment("duplicates_skipped")

                print(f"[DUPLICATE SKIPPED] {symbol}")

                continue

            # Already safely stored in the pending disk buffer.
            if article_id in pending_ids:

                update_latest_news(symbol, kafka_article)
                update_company_checkpoint(symbol)

                print(f"[ALREADY BUFFERED] {symbol}")

                continue

            # Publish or safely buffer.
            safely_stored = self.publish_article(kafka_article)

            if not safely_stored:

                print(
                    f"[STATE NOT UPDATED] {symbol} | "
                    "Kafka and disk buffering failed."
                )

                continue

            # Update latest news and checkpoint only after
            # successful Kafka acknowledgement or disk buffering.
            update_latest_news(symbol, kafka_article)
            update_company_checkpoint(symbol)

            self.metrics.increment("articles_processed")

            print(
                f"[STATE UPDATED] {symbol} | "
                f"{kafka_article['headline']}"
            )

    # --------------------------------------------------------
    # ONE INGESTION CYCLE
    # --------------------------------------------------------

    def run_once(self):

        print("\n" + "=" * 90)
        print("                 FINTEL NEWS INGESTION CYCLE")
        print("=" * 90)

        # Replay previously buffered articles first.
        self.replay_buffer()

        # Initial or incremental search.
        if is_initial_run():

            print("\nMODE: INITIAL FULL SEARCH")

            articles, successful_symbols = fetch_initial_news()

        else:

            print("\nMODE: INCREMENTAL SEARCH")

            checkpoints = load_checkpoints()

            articles, successful_symbols = fetch_incremental_news(
                checkpoints
            )

        print("\n========== SEARCH RESULTS ==========")

        print(f"Articles selected: {len(articles)}")
        print(f"Successful companies: {len(successful_symbols)}")

        # Publish selected articles and update state.
        self.process_search_results(
            articles,
            successful_symbols
        )

        print_state_summary()

        self.metrics.report()

        print("\n========== INGESTION CYCLE COMPLETED ==========")

    # --------------------------------------------------------
    # CONTINUOUS PRODUCER
    # --------------------------------------------------------

    def run(self):

        print("FinTel News Producer started.")

        print(f"Companies configured: {len(COMPANIES)}")
        print(
            f"Polling interval: "
            f"{RSS_POLL_INTERVAL_SECONDS} seconds"
        )

        try:

            while True:

                try:
                    self.run_once()

                except Exception as error:
                    print(f"[CYCLE ERROR] {error}")

                print(
                    f"\nNext ingestion cycle in "
                    f"{RSS_POLL_INTERVAL_SECONDS} seconds."
                )

                time.sleep(RSS_POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:

            print("\nStopping FinTel News Producer...")

        finally:

            self.kafka.close()

            print("FinTel News Producer stopped.")


if __name__ == "__main__":

    producer = NewsProducer()
    producer.run()