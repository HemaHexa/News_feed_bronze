from pathlib import Path
import json
import pyarrow.parquet as pq

BRONZE_FOLDER = Path("shared_data/bronze/news")

EXPECTED_COLUMNS = [
    "kafka_key",
    "raw_json",
    "topic",
    "partition",
    "offset",
    "kafka_ts"
]

EXPECTED_JSON_FIELDS = {
    "article_id",
    "published_at",
    "source",
    "headline",
    "full_text",
    "url",
    "ingested_at"
}


def show_parquet():

    print("\n" + "=" * 70)
    print("          FINTEL - BRONZE PARQUET VIEWER")
    print("=" * 70)

    files = sorted(BRONZE_FOLDER.glob("*.parquet"))

    if not files:
        print("\nNo Parquet files found in:", BRONZE_FOLDER)
        return

    print("\nAVAILABLE PARQUET FILES:")

    for index, file in enumerate(files, start=1):
        print(f"{index}. {file.name}")

    print("\n" + "-" * 70)

    filename = input(
        "\nEnter the Parquet filename or file number to view: "
    ).strip()

    # Allow selection by number or filename
    if filename.isdigit():
        selected_index = int(filename) - 1

        if selected_index < 0 or selected_index >= len(files):
            print("Invalid file number.")
            return

        selected_file = files[selected_index]

    else:
        if not filename.lower().endswith(".parquet"):
            filename += ".parquet"

        selected_file = BRONZE_FOLDER / filename

        if not selected_file.is_file():
            print("File not found:", filename)
            return

    print("\n" + "=" * 70)
    print("SELECTED FILE:", selected_file.name)
    print("=" * 70)

    try:
        table = pq.read_table(selected_file)

        print("\n1. PARQUET SCHEMA")
        print("-" * 70)
        print(table.schema)

        print("\n2. COLUMN VERIFICATION")
        print("-" * 70)
        print("Expected:", EXPECTED_COLUMNS)
        print("Actual:  ", table.column_names)
        print("Schema matches:", table.column_names == EXPECTED_COLUMNS)

        print("\n3. TOTAL RECORDS")
        print("-" * 70)
        print(table.num_rows)

        rows = table.to_pylist()

        for index, row in enumerate(rows, start=1):

            print("\n" + "=" * 70)
            print(f"RECORD {index}")
            print("=" * 70)

            print("\n4. KAFKA METADATA")
            print("-" * 70)
            print("Kafka key :", row.get("kafka_key"))
            print("Topic     :", row.get("topic"))
            print("Partition :", row.get("partition"))
            print("Offset    :", row.get("offset"))
            print("Kafka time:", row.get("kafka_ts"))

            print("\n5. RAW JSON")
            print("-" * 70)

            try:
                payload = json.loads(row["raw_json"])

                print(json.dumps(
                    payload,
                    indent=4,
                    ensure_ascii=False
                ))

                actual_fields = set(payload.keys())

                print("\n6. JSON VALIDATION")
                print("-" * 70)
                print("Missing fields:",
                      EXPECTED_JSON_FIELDS - actual_fields)
                print("Unexpected fields:",
                      actual_fields - EXPECTED_JSON_FIELDS)

                print("\n7. REQUIRED FIELD CHECK")
                print("-" * 70)

                print("Article ID:",
                      bool(payload.get("article_id")))

                print("URL:",
                      bool(payload.get("url")))

                print("Headline or full text:",
                      bool(payload.get("headline") or
                           payload.get("full_text")))

                print("Kafka key matches article ID:",
                      row.get("kafka_key") == payload.get("article_id"))

            except (json.JSONDecodeError, TypeError, KeyError) as error:
                print("Invalid JSON:", error)

        print("\n" + "=" * 70)
        print("PARQUET VIEW COMPLETED")
        print("=" * 70)

    except Exception as error:
        print("Unable to read Parquet file:", error)


if __name__ == "__main__":
    show_parquet()