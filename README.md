FinTel – Real-Time Financial News & Market Streaming Pipeline

1. Project Overview

FinTel is a real-time financial news ingestion pipeline designed to collect and stream financial news related to selected Indian companies.

The pipeline uses Google News RSS as its news source, Apache Kafka for message streaming, and Apache Parquet for Bronze-layer storage.

The producer polls RSS feeds every 15 minutes, filters relevant financial news, generates stable article IDs, and publishes new articles to Kafka. A continuous Kafka consumer reads these messages and stores them as immutable Parquet batch files.

The Bronze Parquet dataset is the input for the downstream Silver processing component.

Key Features

- Targeted financial news collection for 13 Indian companies.
- Automated RSS polling every 15 minutes.
- Company relevance and financial-news filtering.
- Stable article ID generation.
- Producer-side duplicate prevention.
- Incremental collection using company-specific checkpoints.
- Kafka-based message streaming.
- Disk-based buffering during Kafka publishing failures.
- Continuous Kafka consumption.
- Immutable, batch-based Bronze Parquet storage.
- Manual Kafka offset commits after successful Parquet writes.

---

2. System Architecture

             Google News RSS
                    |
                    v
              News Producer
                    |
          Company Relevance Filter
                    |
          Financial News Filter
                    |
           Article ID Generation
                    |
              Deduplication
                    |
              Kafka Publisher
                    |
                    v
          Kafka: raw-news-events
                    |
                    v
          Bronze Kafka Consumer
                    |
                    v
            Bronze Parquet Sink
                    |
                    v
       shared_data/bronze/news_v2/
                    |
                    v
          Member 3 - Silver Layer
                    |
             +------+------+
             |             |
             v             v
        silver/news   silver/news_by_ticker

---

3. Technology Stack

Component| Technology
Programming language| Python
News source| Google News RSS
RSS parsing| Feedparser
HTTP requests| Requests
HTML processing| BeautifulSoup
Message streaming| Apache Kafka
Kafka client| kafka-python
Storage format| Apache Parquet
Parquet processing| PyArrow
Data processing| Pandas
Serialization| JSON
Compression| Snappy
Environment| Python virtual environment

---

4. Target Companies

The pipeline collects financial news for the following 13 Indian companies.

Symbol| Company
RELIANCE| Reliance Industries
TCS| Tata Consultancy Services
INFY| Infosys
HDFCBANK| HDFC Bank
ICICIBANK| ICICI Bank
TATASTEEL| Tata Steel
SBIN| State Bank of India
ITC| ITC
SUNPHARMA| Sun Pharmaceutical
BHARTIARTL| Bharti Airtel
ADANIENT| Adani Enterprises
COALINDIA| Coal India
BAJFINANCE| Bajaj Finance

---

5. News Collection Workflow

The News Producer performs targeted Google News RSS searches for each configured company.

Initial Run

- Searches for news related to all 13 companies.
- Applies company relevance and financial-news filters.
- Selects at most one latest valid article per company in a collection cycle.
- Generates a stable article ID.
- Checks previously processed article IDs.
- Publishes new articles to Kafka.

Subsequent Runs

- Runs every 15 minutes.
- Uses company-specific checkpoints.
- Searches incrementally with an overlap window.
- Selects eligible new articles after the relevant checkpoint.
- Prevents previously published article IDs from being republished.
- Updates producer state and checkpoints.

Article ID Behaviour

An article ID identifies an individual article, not a company.

For example:

Time| Article| Article ID
10:00 AM| TCS announces an AI partnership| ID_A
11:00 AM| TCS announces quarterly results| ID_B
11:15 AM| Same AI partnership article appears again| ID_A

Different articles receive different IDs. Repeated copies of the same article are identified using their stable article ID.

---

6. Kafka Configuration

Setting| Value
Kafka topic| "raw-news-events"
Bootstrap server| "localhost:9092"
Consumer group| "fintel-bronze-news-consumer"
Message key| "article_id"
Message value| JSON article payload
Producer acknowledgement| "acks=all"
Consumer auto commit| Disabled

The consumer commits Kafka offsets only after the corresponding Parquet batch has been successfully written.

This provides at-least-once delivery behaviour. If a Parquet write succeeds but the offset commit fails, a message may be delivered again. Downstream processing should therefore deduplicate using "article_id".

---

7. Bronze Parquet Storage

Storage Location

shared_data/
└── bronze/
    ├── news/
    └── news_v2/
        └── news_<timestamp>_<uuid>.parquet

The "news_v2" directory is the new Bronze output location used for the updated Parquet schema.

Batch-Based Storage Behaviour

The Bronze layer follows incremental batch-based storage.

Each Parquet file contains the Kafka messages received in one consumer batch.

Time| New articles| Kafka messages| Parquet output
10:00 AM| 1| 1| Batch 001
10:15 AM| 0| 0| No file
11:00 AM| 2| 2| Batch 002
11:15 AM| 0| 0| No file
11:30 AM| 1| 1| Batch 003

Important characteristics:

- One Parquet file is created for each non-empty received batch.
- Multiple articles can be stored in one batch file.
- No file is created when no messages are received.
- Previously generated Parquet files remain unchanged.
- Snappy compression is used.
- Temporary file writing and atomic rename are used.
- Kafka offsets are committed after successful storage.

---

8. Bronze Parquet Schema

Every Bronze Parquet file follows this six-column schema.

Column| Data type| Description
"kafka_key"| String| Kafka message key containing the article ID
"raw_json"| String| Original news payload serialized as JSON
"topic"| String| Kafka topic name
"partition"| Integer ("int32")| Kafka partition number
"offset"| Long ("int64")| Kafka message offset
"kafka_ts"| Timestamp (UTC)| Kafka message timestamp

JSON Structure Inside "raw_json"

Each article payload contains seven fields:

{
  "article_id": "abc123",
  "published_at": "2026-11-10T08:30:00Z",
  "source": "Economic Times",
  "headline": "Reliance Industries shares rise after strong quarterly results",
  "full_text": "Original RSS description or article content...",
  "url": "https://example.com/reliance-results",
  "ingested_at": "2026-11-10T08:35:00Z"
}

Article Field Contract

Field| Description
"article_id"| Stable article identifier
"published_at"| Article publication timestamp
"source"| Publisher name
"headline"| Article headline
"full_text"| RSS description or available article text
"url"| Article URL
"ingested_at"| Pipeline ingestion timestamp

The original RSS description or HTML is preserved in "full_text". Full article body extraction is not guaranteed by the RSS source.

The "raw_json" column is stored as a string in the outer Parquet schema. Downstream processing can parse it into individual fields.

---

9. Project Structure

FinTel/
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── companies.py
│   └── rss_sources.py
│
├── producers/
│   ├── __init__.py
│   └── news/
│       ├── __init__.py
│       ├── news_producer.py
│       ├── rss_fetcher.py
│       ├── rss_parser.py
│       ├── company_filter.py
│       ├── financial_filter.py
│       ├── article_identity.py
│       ├── deduplicator.py
│       ├── kafka_publisher.py
│       ├── buffer_manager.py
│       ├── metrics.py
│       └── news_state.py
│
├── consumers/
│   ├── __init__.py
│   └── news/
│       ├── __init__.py
│       └── news_consumer.py
│
├── spark_jobs/
│   └── bronze_news_sink.py
│
├── tests/
│   └── (project test and RSS utility files)
│
├── sample_data/
│   └── bronze/
│       └── news/
│           └── sample_news.parquet
│
├── view_parquet.py
├── requirements.txt
├── README.md
├── .gitignore
└── .env.example

Runtime files and generated datasets are maintained separately under "shared_data/" and are not part of the source repository.

---

10. Installation and Setup

Prerequisites

- Python 3.12 or later
- Apache Kafka 4.4.0
- Java 17
- Git

Clone the Repository

git clone <YOUR_REPOSITORY_URL>
cd FinTel

Create a Virtual Environment

python -m venv .venv

Activate it on Windows PowerShell:

.\.venv\Scripts\Activate.ps1

Install Dependencies

pip install -r requirements.txt

The project dependencies include:

feedparser
requests
beautifulsoup4
kafka-python
python-dotenv
truststore
pandas
pyarrow

---

11. Running the Pipeline

The pipeline uses three independent processes:

1. Kafka broker
2. Bronze Kafka consumer
3. News producer

Run them in separate terminals.

Terminal 1 – Start Kafka Broker

Navigate to the Kafka installation directory:

cd C:\kafka\kafka_2.13-4.4.0

Start the broker:

.\bin\windows\kafka-server-start.bat .\config\server.properties

Ensure the "raw-news-events" topic has been created before starting the producer and consumer.

Terminal 2 – Start Bronze Consumer

Navigate to the project directory:

cd C:\FinTel

Activate the environment:

.\.venv\Scripts\Activate.ps1

Start the consumer:

python -m consumers.news.news_consumer

The consumer continuously polls Kafka and writes received batches to Bronze Parquet storage.

Terminal 3 – Start News Producer

cd C:\FinTel
.\.venv\Scripts\Activate.ps1

Start the producer:

python -m producers.news.news_producer

The producer collects new articles every 15 minutes and publishes them to Kafka.

---

12. Viewing Bronze Parquet Files

The project includes an interactive Parquet viewer.

Run:

python view_parquet.py

The viewer displays:

- Available Parquet files
- Parquet schema
- Column names and data types
- Total record count
- Kafka metadata
- Raw JSON payload
- JSON field validation
- Required field validation
- Kafka key and article ID comparison

The viewer is configured to inspect the project's Bronze output directory.

---

13. Failure Handling and Reliability

Kafka Publishing Failure

If Kafka publishing fails, the producer stores the article in a local disk buffer.

Buffered messages are replayed when Kafka becomes available. Messages are marked as successfully published only after Kafka acknowledges them.

Bronze Write Failure

The consumer uses manual Kafka offset commits.

If a Parquet write fails, the consumer does not commit the affected batch offsets, allowing the messages to be consumed again.

Checkpoint Management

The producer maintains company-specific checkpoints and latest-news state.

These files support incremental collection and prevent unnecessary repeated processing.

Duplicate Handling

Producer-side deduplication prevents known article IDs from being republished.

Downstream Silver processing should also deduplicate using "article_id", since Kafka delivery and retry behaviour can result in repeated records.

---

14. Silver Layer Integration

The Bronze Parquet files are the input for the downstream Silver processing component.

Expected Silver Responsibilities

1. Incrementally discover new Bronze Parquet files.
2. Read the six outer Parquet columns.
3. Parse "raw_json" into individual news fields.
4. Validate article fields.
5. Route invalid records to a dead-letter location.
6. Clean HTML and normalize article text.
7. Deduplicate using "article_id".
8. Extract company ticker symbols.
9. Perform FinBERT sentiment analysis.

Expected Silver Outputs

"silver/news"

One record per unique article.

"silver/news_by_ticker"

One record per article-ticker combination.

The Silver implementation should maintain its own processed-file tracking mechanism to avoid repeatedly processing previously completed Bronze files.

---

15. Important Notes

- Do not commit ".venv/" to Git.
- Do not commit API keys, passwords, or other secrets.
- Do not commit generated producer state or runtime data.
- Bronze Parquet files are immutable batch outputs.
- Keep the agreed six-column Bronze schema stable for Silver integration.
- The producer and consumer must be running while the live pipeline is operating.
- The sample Parquet file in "sample_data/" is provided for repository demonstration and downstream schema inspection.

---

16. Project Status

Component| Status
RSS news collection| Implemented
Company relevance filtering| Implemented
Financial-news filtering| Implemented
Article ID generation| Implemented
Producer-side deduplication| Implemented
Checkpoint management| Implemented
Kafka publishing| Implemented
Disk buffering| Implemented
Bronze Kafka consumer| Implemented
Batch-based Parquet storage| Implemented
Parquet schema verification| Verified on sample output
Silver integration| Downstream component handoff

FinTel – Bronze financial news ingestion pipeline.

Core ingestion implementation and sample Parquet structure verification completed.