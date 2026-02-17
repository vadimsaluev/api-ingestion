import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

import requests

# date format validation
def validate_date(date_str: str) -> str:
    try:
        datetime.strptime(date_str, "%Y%m%d")
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str}. Expected YYYYMMDD."
        )

# fetching one page
def fetch_page(
    url: str,
    headers: Dict[str, str],
    params: Dict[str, Any],
) -> Dict[str, Any]:
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

# dumping results
def save_json(data: Dict[str, Any], output_dir: str, page: int) -> None:
    filename = os.path.join(output_dir, f"response_page_{page}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# writing log
def write_log(message: str, log_path: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp} - {message}\n")

# main loop to fetch paginated data
def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch paginated data from Web API")
    parser.add_argument("--url", required=True, help="Base API URL")
    parser.add_argument("--api-key", required=True, help="API key for X-API-Key header")
    parser.add_argument("--date", required=True, type=validate_date, help="Date (YYYYMMDD)")
    parser.add_argument("--limit", type=int, default=100, help="Records per page")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to store raw JSON responses",
    )

    args = parser.parse_args()

    headers = {
        "X-API-Key": args.api_key,
        "Accept": "application/json",
    }

    params = {
        "date": args.date,
        "limit": args.limit,
        "page": 1,
    }

    os.makedirs(args.output_dir, exist_ok=True)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, "log.txt")

    has_next = True
    page = 1
    total_records_counted = 0

    while has_next:
        try:
            current_message = f"Fetching page {page}"
            write_log(current_message, log_path)
            print(current_message)
            
            response_json = fetch_page(args.url, headers, params)
        except requests.RequestException as exc:
            error_message = f"ERROR: Failed to fetch page {page}: {exc}"
            write_log(error_message, log_path)
            print(error_message, file=sys.stderr)
            sys.exit(1)

        save_json(response_json, args.output_dir, page)

        pagination = response_json.get("pagination")
        if not pagination:
            print("WARNING: Pagination block missing in response. Stopping.")
            break

        has_next = pagination.get("has_next", False)
        page += 1
        params["page"] = page

    #finalization
    current_message = f"total records fetched - {total_records_counted}"
    write_log(current_message, log_path)
    print(current_message)
    print("Data extraction completed successfully.")


if __name__ == "__main__":
    main()