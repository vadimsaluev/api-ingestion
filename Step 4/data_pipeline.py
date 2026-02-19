import argparse
import json
import os
import sys
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

import requests
from google.cloud import bigquery
import psycopg2
from psycopg2.extras import execute_values

# -------------------------
# Utils
# -------------------------

def validate_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str}. Expected YYYYMMDD."
        )

def write_log(message: str, log_path: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp} - {message}\n")

def generate_session_pk(full_visitor_id: str, visit_id: Any, date_str: str) -> str:
    raw_key = f"{full_visitor_id}_{visit_id}_{date_str}"
    return hashlib.sha256(raw_key.encode()).hexdigest()

def fetch_page(url: str, headers: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


# -------------------------
# BQ transform
# -------------------------

def transform_record_for_bq(
    record: Dict[str, Any],
    source_file_name: str,
    gdrive_path: str
) -> Dict[str, Any]:

    date_raw = record.get("date")
    date_iso = datetime.strptime(date_raw, "%Y%m%d").date().isoformat()

    session_pk = generate_session_pk(
        record.get("fullVisitorId"),
        record.get("visitId"),
        date_raw
    )

    transformed = {
        "session_pk": session_pk,
        "visitId": record.get("visitId"),
        "visitNumber": record.get("visitNumber"),
        "visitStartTime": record.get("visitStartTime"),
        "date": date_iso,
        "fullVisitorId": record.get("fullVisitorId"),
        "channelGrouping": record.get("channelGrouping"),

        "device": record.get("device"),
        "geoNetwork": record.get("geoNetwork"),
        "totals": record.get("totals"),
        "trafficSource": record.get("trafficSource"),
        "customDimensions": record.get("customDimensions", []),
        "hits_sample": record.get("hits_sample", []),

        "load_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_date": date_iso,
        "source_file_name": source_file_name,
        "source_gdrive_path": gdrive_path
    }

    return transformed

# -------------------------
# BQ load
# -------------------------

def load_to_bigquery(
    client: bigquery.Client,
    table_id: str,
    records: List[Dict[str, Any]],
):
    if not records:
        return

    errors = client.insert_rows_json(table_id, records)
    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")

# -------------------------
# Stub for PostgreSQL
# -------------------------

# uncomment this if you want to test PostgreSQL loading, and make sure that connection details are provied and table(s) are pre-created.
# see README for table schema.
"""
def load_to_postgres(
    conn,
    table_name: str,
    records: List[Dict[str, Any]],
):
    if not records:
        return

    with conn.cursor() as cursor:
        values = [(json.dumps(r),) for r in records]

        execute_values(
            cursor,
            f"INSERT INTO {table_name} (data) VALUES %s",
            values,
        )
    conn.commit()
"""

# -------------------------
# Main
# -------------------------

def main():
    parser = argparse.ArgumentParser(description="GA Sessions ingestion pipeline")

    # API
    parser.add_argument("--url", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--start-date", required=True, type=validate_date)
    parser.add_argument("--end-date", required=True, type=validate_date)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output-dir", default="output")

    # BigQuery
    parser.add_argument("--bq-project")
    parser.add_argument("--bq-dataset")
    parser.add_argument("--bq-table")
    parser.add_argument("--bq-credentials")

    # PostgreSQL
    parser.add_argument("--pg-host")
    parser.add_argument("--pg-port", type=int, default=5432)
    parser.add_argument("--pg-db")
    parser.add_argument("--pg-user")
    parser.add_argument("--pg-password")
    parser.add_argument("--pg-table")

    # Metadata
    parser.add_argument("--gdrive-path", default="")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, "log.txt")

    headers = {
        "X-API-Key": args.api_key,
        "Accept": "application/json",
    }

    # BigQuery init
    bq_client = None
    table_id = None
    if args.bq_project and args.bq_dataset and args.bq_table:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = args.bq_credentials
        bq_client = bigquery.Client(project=args.bq_project)
        table_id = f"{args.bq_project}.{args.bq_dataset}.{args.bq_table}"

    # PostgreSQL init
    # uncomment this if needed

    """
    pg_conn = None
    if args.pg_host and args.pg_db and args.pg_user and args.pg_password:
        pg_conn = psycopg2.connect(
            host=args.pg_host,
            port=args.pg_port,
            dbname=args.pg_db,
            user=args.pg_user,
            password=args.pg_password,
        )
    """
    current_date = args.start_date
    total_records_counted = 0

    write_log("Starting extraction process", log_path)

    while current_date <= args.end_date:

        date_str = current_date.strftime("%Y%m%d")
        write_log(f"Processing date {date_str}", log_path)

        page = 1
        has_next = True

        while has_next:
            params = {
                "date": date_str,
                "limit": args.limit,
                "page": page,
            }

            write_log(f"fetching page - {page} for date {date_str}", log_path)

            response_json = fetch_page(args.url, headers, params)

            file_name = f"{date_str}_page_{page}.json"
            file_path = os.path.join(args.output_dir, file_name)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(response_json, f, ensure_ascii=False, indent=2)

            records = response_json.get("records", [])
            total_records_counted += len(records)

            # transform for BigQuery
            transformed_records = [
                transform_record_for_bq(r, file_name, args.gdrive_path)
                for r in records
            ]

            if bq_client:
                load_to_bigquery(bq_client, table_id, transformed_records)

            """
            if pg_conn:
                load_to_postgres(pg_conn, args.pg_table, transformed_records)
            """

            pagination = response_json.get("pagination", {})
            has_next = pagination.get("has_next", False)

            page += 1

        # increment to fetch next date
        current_date += timedelta(days=1)

    write_log(f"total records fetched - {total_records_counted}", log_path)
    write_log("Extraction completed successfully", log_path)

    print(f"Total records fetched: {total_records_counted}")

    """
    if pg_conn:
        pg_conn.close()
    """

if __name__ == "__main__":
    main()