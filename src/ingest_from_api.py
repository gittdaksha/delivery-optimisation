import requests                                  # library for making HTTP API calls
import pandas as pd                              # table/dataframe library
import sqlite3                                   # built-in Python SQLite driver
import json                                      # for pretty-printing JSON responses

# ── What a real delivery API call looks like ────────────────────────────────
# In production this would be:
#   GET https://api.deliveryplatform.com/v1/orders?status=failed&date=2024-01-15
#   Headers: {"Authorization": "Bearer YOUR_API_KEY"}
#
# Here we use JSONPlaceholder — a free public API that returns fake structured
# data so you can learn the pattern without needing real credentials.

BASE_URL = "https://jsonplaceholder.typicode.com"  # base address of the API

def fetch_from_api(endpoint: str, params: dict = None) -> list:
    """
    Make a GET request to an API endpoint and return the JSON response.
    This is the same pattern used to call BigQuery REST API, GCS API,
    Kafka REST proxy, or any logistics platform API.
    """
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params)  # GET = read/fetch data

    # Always check the status code — never assume an API call succeeded
    response.raise_for_status()   # raises an exception if status is 4xx or 5xx

    return response.json()        # .json() converts raw text response to Python dict/list

def post_to_api(endpoint: str, payload: dict) -> dict:
    """
    Make a POST request — used to send data back: update a delivery status,
    trigger a re-attempt, or write to a webhook.
    """
    response = requests.post(
        f"{BASE_URL}/{endpoint}",
        json=payload,                              # serialises dict to JSON (JavaScript Object Notation) body
        headers={"Content-Type": "application/json"}  # tells server we are sending JSON
    )
    response.raise_for_status()                   # error if server returns 4xx/5xx
    return response.json()


if __name__ == "__main__":
    # ── GET: pull records ───────────────────────────────────────────────────
    print("GET /posts (simulates pulling delivery records from an API)...")
    records = fetch_from_api("posts")             # calls GET /posts endpoint
    print(f"  Fetched {len(records)} records")
    print(f"  First record: {json.dumps(records[0], indent=2)}")  # indent=2 = pretty print

    # ── GET with query params ────────────────────────────────────────────────
    print("\nGET /posts?userId=1 (simulates filtering by delivery partner ID)...")
    partner_records = fetch_from_api("posts", params={"userId": 1})  # ?userId=1 filter
    print(f"  Fetched {len(partner_records)} records for userId=1")

    # ── POST: send data back ─────────────────────────────────────────────────
    print("\nPOST /posts (simulates writing a delivery status update)...")
    status_update = {
        "delivery_id": "abc-123",                 # ID of the delivery being updated
        "status": "FAILED",                       # new status
        "reason": "Customer unavailable",
        "attempt": 1,
        "partner_id": "P001"
    }
    result = post_to_api("posts", status_update)  # send the update to the API
    print(f"  API acknowledged with id: {result.get('id')}")  # .get() = safe key access

    # ── Load API response to SQLite (same pattern as load_to_bigquery.py) ───
    df = pd.DataFrame(records)                    # convert list of dicts to a table
    conn = sqlite3.connect("data/delivery_db.sqlite")  # open the database
    df.to_sql("api_ingested_records", conn, if_exists="replace", index=False)  # save to DB
    conn.close()                                  # close connection when done
    print(f"\nStored {len(df)} API records into SQLite table 'api_ingested_records'")

    # ── What changes when the API is real ────────────────────────────────────
    print("""
Real logistics API differences:
  - BASE_URL = "https://api.deliveryplatform.com/v1"
  - Headers include: {"Authorization": "Bearer " + os.environ["API_KEY"]}
  - Response schema differs — you parse specific fields, not assume structure
  - Pagination: most APIs return 100 records per page, you loop until no next_page
  - Rate limits: APIs cap requests per minute, you add time.sleep() between calls
  - The ingestion logic is identical — only the URL and auth header change
""")