# Guide 02 — Generate & Store Raw Data

**Goal:** Create realistic synthetic delivery data using Python, then store it in a database using SQL (Structured Query Language). This is the "ingestion" layer of the pipeline.

---

## Why synthetic data?

- Real delivery data is private — companies don't share it
- But you need data to work with
- `Faker` is a Python library that generates realistic-looking fake data — names, addresses, timestamps
- This is a standard practice for building portfolio projects and for testing pipelines in development environments

---

## Git — Before You Start This Guide

Every guide begins the same way in a real office: you make sure you are on the right branch and it is up to date before touching any files.

### Step G1 — Make sure you are on develop and it is current

```bash
git checkout develop  # switch to the develop branch
```
**What this does:**
- Switches you to the develop branch
- You always create feature branches FROM develop, never from main and never from another feature branch
- No `-b` here — this switches to an existing branch. You do not use `-b` when the branch already exists

```bash
git pull origin develop  # download + merge changes from GitHub
```
**What this does:**
- Downloads any changes from GitHub that you do not have locally
- In an office, a colleague may have merged something since you last worked
- `pull` = download + merge in one command

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub

```bash
git status  # show current state of all files
```
**What this does:**
- Shows the current state
- You should see `On branch develop, nothing to commit, working tree clean`
- If you see modified files here, deal with them before moving forward — do not carry unrelated changes into a new branch
- No flags here — `git status` always shows full current state

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-02-data  # -b = create new branch and switch to it
```
**What `-b` means:**
- Create a new branch AND switch to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

**Why a new branch for every guide:**
- Each branch is one unit of work
- If something breaks, you can delete the branch and start fresh without affecting develop or main
- In an office, each feature or fix lives on its own branch for the same reason

Confirm you are on the right branch:
```bash
git branch  # list branches; * shows which one you are on
```
- You will see a `*` next to your current branch
- That `*` means "you are here"

---

## Step 2.1 — Create the project directories

```bash
mkdir src           # folder for Python scripts
mkdir sql           # folder for SQL files
mkdir data          # top-level data folder
mkdir data\raw      # raw = original unprocessed data
mkdir data\processed  # processed = cleaned / transformed data
mkdir models        # folder for ML model files
mkdir notebooks     # folder for Jupyter notebooks
```

---

## Step 2.2 — Create `src/generate_data.py`

Create the file `src/generate_data.py` with this content:

**How to create this file:**
```bash
notepad src/generate_data.py  # opens Notepad; click Yes to create the file
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

**What `generate_data.py` does and why it exists:**
- **What it does:** Generates 50,000 fake but realistic delivery records and saves them as a CSV file in `data/raw/`
- **Why separate:** Real delivery data is private — no company will share it. Without this script you have nothing to build on. Keeping data generation separate from ingestion means you can regenerate data with different parameters (different cities, different failure rates) without touching the database code.
- **Input:** None (this script generates all data from scratch using Python's Faker and random libraries)
- **Output:** `data/raw/deliveries.csv` (50,000 rows, CSV file with 13 columns per delivery record)
- **Pipeline position:** Nothing (starting point) → **this script** → `data/raw/deliveries.csv` (which `ingest.py` will load into the database)

```python
import pandas as pd                              # pd = table/dataframe library
import numpy as np                               # np = math and array library
from faker import Faker                          # generates realistic fake data
import random                                    # built-in random number tools
from datetime import datetime, timedelta         # datetime = dates, timedelta = date math
import os                                        # interact with file system

fake = Faker('en_IN')  # Indian locale for realistic addresses
np.random.seed(42)                               # seed = same data every run
random.seed(42)                                  # 42 is arbitrary; any int works

ADDRESS_TYPES = ['Apartment', 'PG/Hostel', 'House', 'Office', 'Gated Community']  # possible address categories
DELIVERY_WINDOWS = ['Morning (9-12)', 'Afternoon (12-15)', 'Evening (15-19)', 'Night (19-22)']  # time slots
FAILURE_REASONS = ['Customer Unavailable', 'Wrong Address', 'Refused Delivery', 'Building Access Denied', None]  # why fail
CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Pune', 'Chennai']  # cities in dataset

def generate_delivery_data(n_records=50000):     # default = 50000 rows
    records = []                                 # empty list, filled row by row

    for _ in range(n_records):                   # _ = loop counter we don't need
        city = random.choice(CITIES)             # pick one city at random
        address_type = random.choice(ADDRESS_TYPES)  # pick one address type
        window = random.choice(DELIVERY_WINDOWS)     # pick one time window
        # random.uniform(150, 8000) → random float between 150 and 8000, e.g. 3452.7891
        # round(..., 2)              → round to 2 decimal places → 3452.79
        order_value = round(random.uniform(150, 8000), 2)  # random Rs 150-8000

        # Business rules that affect delivery success (mirroring real-world patterns)
        success_prob = 0.78  # baseline FADR (First Attempt Delivery Rate)

        if address_type in ['Apartment', 'PG/Hostel']:
            success_prob -= 0.12  # harder to access
        if address_type == 'Office':
            success_prob += 0.10  # usually someone available
        if window == 'Morning (9-12)':
            success_prob -= 0.15  # most people at work
        if window == 'Evening (15-19)':
            success_prob += 0.08  # people returning home
        if window == 'Night (19-22)':
            success_prob += 0.12  # people at home
        if order_value > 5000:
            success_prob -= 0.05  # high value = hand-over only, stricter

        # max(0.10, min(0.97, success_prob)) is a "clamp" pattern:
        #   min(0.97, success_prob) → cap at 0.97 (never exceed 97%)
        #   max(0.10, ...)          → floor at 0.10 (never drop below 10%)
        # e.g. if success_prob computed to 1.05 → min gives 0.97 → max gives 0.97
        # e.g. if success_prob computed to 0.03 → min gives 0.03 → max gives 0.10
        success_prob = max(0.10, min(0.97, success_prob))  # clamp: keep between 10%-97%
        # random.random() → random float in [0.0, 1.0), e.g. 0.61
        # 0.61 < 0.78 → True  (delivery succeeds)
        # 0.85 < 0.78 → False (delivery fails)
        # The higher success_prob is, the more likely the random number falls below it
        is_successful = random.random() < success_prob     # True if random < threshold

        failure_reason = None                    # assume success; overwrite if failed
        if not is_successful:
            # FAILURE_REASONS = ['Customer Unavailable', 'Wrong Address', ..., None]
            # [:-1] = all items except the last one → removes None from choices
            failure_reason = random.choice(FAILURE_REASONS[:-1])  # exclude None

        # datetime.now()              → current date+time, e.g. datetime(2024, 7, 16, 14, 30)
        # random.randint(1, 365)      → random whole number, e.g. 200
        # timedelta(days=200)         → a duration of 200 days
        # datetime.now() - timedelta  → subtract 200 days → a past date
        attempt_date = datetime.now() - timedelta(days=random.randint(1, 365))  # random past date

        records.append({
            'delivery_id': fake.uuid4(),         # unique delivery ID (UUID)
            # uuid4() returns e.g. 'f47ac10b-58cc-4372-a567-0e02b2c3d479'
            # [:8] = keep first 8 chars only → 'f47ac10b'
            'customer_id': fake.uuid4()[:8],     # short 8-char customer ID
            'city': city,                        # which city
            'address_type': address_type,        # apartment / office / etc
            'delivery_window': window,           # time slot chosen
            'order_value': order_value,          # Rs value of the order
            # int(True) → 1,  int(False) → 0  (converts boolean to integer for database storage)
            'is_successful': int(is_successful), # 1 = delivered, 0 = failed
            'failure_reason': failure_reason,    # None if delivery succeeded
            # weights=[70, 22, 8] means: 70% chance→1, 22% chance→2, 8% chance→3
            # random.choices() always returns a list → [0] takes the single picked value
            'attempt_number': random.choices([1, 2, 3], weights=[70, 22, 8])[0],  # 70% first-attempt
            # strftime = string-format-time: converts a datetime object to a string
            # %Y=4-digit year, %m=2-digit month, %d=2-digit day
            # e.g. datetime(2024, 3, 5, 14, 30) → '2024-03-05'
            'attempt_date': attempt_date.strftime('%Y-%m-%d'),  # format: YYYY-MM-DD string
            # window = 'Morning (9-12)'
            # window.split('(')     → ['Morning ', '9-12)']
            # [1]                   → '9-12)'  (index 1 = second item, 0-based)
            # .split('-')           → ['9', '12)']
            # [0]                   → '9'  (index 0 = first item)
            # int('9')              → 9  (converts string to integer)
            'attempt_hour': int(window.split('(')[1].split('-')[0]),  # extract start hour from window
            'has_delivery_preference': random.choices([0, 1], weights=[60, 40])[0],  # 40% set preference
            'proximity_alert_sent': random.choices([0, 1], weights=[55, 45])[0],    # 45% got alert
        })

    return pd.DataFrame(records)                 # convert list of dicts to a table


if __name__ == '__main__':                       # only runs when called directly
    print("Generating 50,000 delivery records...")
    df = generate_delivery_data(50000)           # call the function above

    os.makedirs('data/raw', exist_ok=True)       # create folder; ok if already exists
    output_path = 'data/raw/deliveries.csv'      # where to save the file
    df.to_csv(output_path, index=False)          # index=False = don't save row numbers

    print(f"Saved to {output_path}")
    print(f"Shape: {df.shape}")                  # shape = (rows, columns) e.g. (50000, 13)
    print(f"\nOverall FADR: {df['is_successful'].mean():.2%}")  # .mean() on 0/1 column = rate
    print(f"\nFADR by address type:")
    print(df.groupby('address_type')['is_successful'].mean().sort_values())  # group → avg → sort
    print(f"\nFADR by delivery window:")
    print(df.groupby('delivery_window')['is_successful'].mean().sort_values())  # lowest FADR first
```

**Key concepts in this code:**

**What `random.seed(42)` means:**
- Setting a seed makes random number generation reproducible — every time you run this script you get the exact same 50,000 records in the same order
- The number 42 is arbitrary; any integer works
- Without a seed, each run produces different data, making debugging and comparing results harder

**What `fake.uuid4()` is:**
- A UUID (Universally Unique Identifier) is a randomly generated string like `f47ac10b-58cc-4372-a567-0e02b2c3d479`
- It is statistically guaranteed to be unique — no two deliveries share the same ID
- This is how real systems identify records without using sequential numbers that could clash

**What `pd.DataFrame(records)` is:**
- A DataFrame is a table held in memory — rows and columns, just like a spreadsheet
- `pd.DataFrame(records)` converts your list of Python dictionaries into this table
- Each row is one delivery and each column is one field (city, address_type, etc.)

**What `if __name__ == '__main__':` means:**
- This Python pattern means "only run this code if this file is executed directly — not when it is imported by another script"
- It lets `generate_delivery_data` be reused as a function in other scripts without automatically triggering the full 50,000-record generation

---

## Step 2.3 — Run the data generator

**What a CSV file is:**
- A CSV (Comma-Separated Values) file is a plain text file where each line is one row of data and values are separated by commas
- It is the simplest universal format for tabular data — any spreadsheet, database, or data tool can open it

**What this does:** Runs the data generation script and saves 50,000 synthetic delivery records to `data/raw/deliveries.csv`.

```bash
python src/generate_data.py  # run the script; creates deliveries.csv
```

**Why:**
- This creates `data/raw/deliveries.csv` with 50,000 synthetic delivery records
- You will see the overall FADR and how it breaks down by address type and delivery window — this is your first insight

Expected output:
```
Generating 50,000 delivery records...
Saved to data/raw/deliveries.csv
Shape: (50000, 13)

Overall FADR: 75.23%

FADR by address type:
address_type
PG/Hostel          0.63
Apartment          0.65
House              0.77
Gated Community    0.79
Office             0.86

FADR by delivery window:
delivery_window
Morning (9-12)     0.63
Afternoon (12-15)  0.72
Evening (15-19)    0.80
Night (19-22)      0.85
```

These numbers tell the story your LinkedIn post is about — morning deliveries fail more, apartments fail more.

---

## Step 2.4 — Create the database schema

**What SQLite is:**
- SQLite is a database that lives entirely in a single file on your computer — no separate database server to install or run
- It is perfect for learning and for development because it is simple to set up
- In production, companies use server-based databases like PostgreSQL, MySQL, or cloud warehouses like BigQuery, but the SQL you write is the same

**What this does:**
- Creates a `.sql` file that defines the structure (schema) of your database tables
- Defines what columns each table has and what type of data each column holds

Create `sql/create_tables.sql`:

**How to create this file:**
```bash
notepad sql/create_tables.sql  # opens Notepad; click Yes to create the file
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

**What `IF NOT EXISTS` means:**
- This tells the database "create this table only if it does not already exist — otherwise do nothing"
- Without it, running the script a second time would throw an error because the table already exists

**What `PRIMARY KEY` means:**
- The primary key uniquely identifies each row
- No two rows can have the same value in this column, and it cannot be empty
- Here `delivery_id` is the primary key — every delivery has exactly one unique ID

```sql
-- Raw deliveries table: one row per delivery attempt
CREATE TABLE IF NOT EXISTS deliveries (     -- IF NOT EXISTS = skip if already there
    delivery_id       TEXT PRIMARY KEY,     -- TEXT = string; PRIMARY KEY = unique ID
    customer_id       TEXT NOT NULL,        -- NOT NULL = this column must have a value
    city              TEXT NOT NULL,        -- city name e.g. Mumbai
    address_type      TEXT NOT NULL,        -- apartment / office / house etc
    delivery_window   TEXT NOT NULL,        -- time slot e.g. Morning (9-12)
    order_value       REAL NOT NULL,        -- REAL = decimal number (Rs amount)
    is_successful     INTEGER NOT NULL,     -- 1 = success, 0 = failed
    failure_reason    TEXT,                 -- NULL if successful
    attempt_number    INTEGER NOT NULL,     -- INTEGER = whole number
    attempt_date      TEXT NOT NULL,        -- stored as YYYY-MM-DD string
    attempt_hour      INTEGER NOT NULL,     -- hour extracted from window
    has_delivery_preference INTEGER NOT NULL,  -- 0 or 1 flag
    proximity_alert_sent    INTEGER NOT NULL   -- 0 or 1 flag
);

-- Summary table: FADR by city and address type
CREATE TABLE IF NOT EXISTS fadr_by_segment (
    city            TEXT,                   -- one row per city+address_type combo
    address_type    TEXT,
    total_attempts  INTEGER,                -- count of deliveries in this group
    successful      INTEGER,                -- count of successful ones
    fadr            REAL,                   -- successful / total_attempts
    PRIMARY KEY (city, address_type)        -- composite key: pair must be unique
);
```

---

## Step 2.5 — Create `src/ingest.py`

**What this does:** Reads the CSV file and loads it into the SQLite database so you can query it with SQL.

Create `src/ingest.py`:

**How to create this file:**
```bash
notepad src/ingest.py  # opens Notepad; click Yes to create the file
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

**What `ingest.py` does and why it exists:**
- **What it does:** Reads `deliveries.csv`, opens (or creates) the SQLite database file, and loads the data into it as a queryable table
- **Why separate:** `generate_data.py` only knows how to create fake data — it should not also know how to connect to a database. Splitting them means if you ever swap the data source (a real CSV from Air India instead of a fake one), you only change `ingest.py`, not the generator. Separation of concerns is a core engineering principle.
- **Input:** `data/raw/deliveries.csv` (50,000-row CSV produced by `generate_data.py`)
- **Output:** `data/delivery_db.sqlite` (SQLite database file containing the `deliveries` table with 50,000 rows and the pre-computed `fadr_by_segment` summary table)
- **Pipeline position:** `data/raw/deliveries.csv` (produced by `generate_data.py`) → **this script** → `data/delivery_db.sqlite` (the database that all SQL queries in Guide 03 will read from)

```python
import pandas as pd                              # table/dataframe library
import sqlite3                                   # built-in Python SQLite driver
import os                                        # interact with file system

DB_PATH = 'data/delivery_db.sqlite'             # path to the database file
CSV_PATH = 'data/raw/deliveries.csv'            # path to the source CSV

def load_to_db():
    print(f"Loading {CSV_PATH} into SQLite database...")

    # STEP 1 — EXTRACT: read the raw file into memory
    # SQL cannot open files — Python must read it first
    df = pd.read_csv(CSV_PATH)                   # read CSV into a DataFrame (table in memory)

    # STEP 2 — open (or create) the SQLite database file on disk
    # if the file doesn't exist, sqlite3 creates it automatically
    conn = sqlite3.connect(DB_PATH)

    # STEP 3 — LOAD raw data into database
    # if_exists='replace' = drop and recreate table if it already exists (safe re-run)
    # index=False = don't write pandas row numbers as a column in the database
    df.to_sql('deliveries', conn, if_exists='replace', index=False)
    print(f"  Loaded {len(df):,} rows into 'deliveries' table")

    # STEP 4 — TRANSFORM: pre-compute FADR summary table
    # WHY: querying 50,000 rows every time the dashboard loads is slow
    # pre-calculating and storing the summary = dashboard stays fast
    # e.g. Mumbai + Apartment → 1200 attempts, 800 successes → FADR = 0.667
    #
    # COLUMNS USED FROM df:
    # 'city'          → comes from generate_data.py → random.choice(CITIES)
    # 'address_type'  → comes from generate_data.py → random.choice(ADDRESS_TYPES)
    # 'is_successful' → comes from generate_data.py → int(is_successful) → 0 or 1
    #                   used TWICE: once for count (total attempts), once for sum (successes)
    fadr = (
        df.groupby(['city', 'address_type'])     # group rows by city + address type
        .agg(
            total_attempts=('is_successful', 'count'),  # count total rows per group
            successful=('is_successful', 'sum')         # sum of 1s = count of successes
            # e.g. [1,0,1,1,0] → count=5, sum=3
        )
        .reset_index()                           # turn group keys back into regular columns
    )
    # FADR = successes / total attempts
    # uses 'successful' and 'total_attempts' columns created by .agg() above
    # e.g. 800 / 1200 = 0.667 = 66.7% first attempt delivery rate
    fadr['fadr'] = fadr['successful'] / fadr['total_attempts']

    # STEP 5 — LOAD summary table into database (second table alongside raw data)
    fadr.to_sql('fadr_by_segment', conn, if_exists='replace', index=False)
    print(f"  Computed FADR for {len(fadr)} city/address-type segments")

    conn.close()                                 # always close the connection when done
    print(f"\nDatabase saved to {DB_PATH}")

if __name__ == '__main__':                       # only runs when called directly
    load_to_db()
```

---

## Step 2.6 — Run ingestion

**What this does:** Executes the ingestion script, which reads the CSV and writes it into the SQLite database file.

```bash
python src/ingest.py  # run ingestion: reads CSV, writes to SQLite
```

**Why:**
- This loads the CSV into a SQLite database
- SQLite is a file-based database — no server needed — perfect for learning
- In production this would be PostgreSQL, BigQuery, or Snowflake

**When to run `ingest.py`:**
- First time: after `generate_data.py` has created `data/raw/deliveries.csv`
- If you re-run `generate_data.py` and get fresh data: run `ingest.py` again to reload
- If you change `ingest.py` itself: re-run it to apply the changes
- Never run `ingest.py` before `generate_data.py` — the CSV must exist first

**Order that must always be followed:**
```
1. python src/generate_data.py   → creates deliveries.csv
2. python src/ingest.py          → loads CSV into SQLite database
3. (then SQL queries, ML, dashboard all read from the database)
```

---

## Step 2.7 — Verify the data in the database

**What this does:**
- Opens the database directly from the command line and runs two quick SQL checks
- One check counts the rows, one shows FADR grouped by address type
- The `-c` flag tells Python to run a short script written inline instead of from a file

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/delivery_db.sqlite')  # open the database file
cur = conn.cursor()                                # cursor = tool to run SQL queries
cur.execute('SELECT COUNT(*) FROM deliveries')     # count all rows
print('Rows in deliveries:', cur.fetchone()[0])    # fetchone = get one result row
cur.execute('SELECT address_type, ROUND(AVG(is_successful)*100,1) as fadr FROM deliveries GROUP BY address_type ORDER BY fadr')  # fadr per type
for row in cur.fetchall():                         # fetchall = get all result rows
    print(row)
conn.close()                                       # close connection when done
"
```

**Why:**
- Always verify data loaded correctly
- Never trust a pipeline without checking the output
- This is a habit that separates reliable data engineers from unreliable ones

---

---

## Step 2.8 — API (Application Programming Interface) ingestion (how it works in production)

In production, delivery data does not come from a CSV. It comes from an API — the order management system exposes endpoints that your pipeline calls to pull new records.

This step shows you how to write an API-based ingestion function. You will use a real public API (JSONPlaceholder — a free fake REST (Representational State Transfer) API used for exactly this kind of learning) to understand the GET/POST pattern, then map it to what a real logistics API would look like.

**Important — what JSONPlaceholder actually is:**
JSONPlaceholder only returns 4 fields: `userId`, `id`, `title`, `body`. These are NOT delivery fields — it is a generic fake API made for learning, not a logistics API.

**Why use it then?**
- We don't have a real Air India API
- The only thing this step teaches is the API call pattern:
```
requests.get(url) → .json() → DataFrame → SQLite
```
- That pattern is identical whether the API is JSONPlaceholder or a real courier system

**The missing delivery fields** (`city`, `address_type`, `is_successful` etc.) are generated by Python using `random.choice()` — same as `generate_data.py`. We add them manually to make the table look realistic. In real life, the actual API would return all these fields directly and you would not need to add them yourself.

**Think of it as:**
- JSONPlaceholder = practice dummy
- Real Air India API = the actual thing
- Same technique, different data source

Install the requests library:
```bash
pip install requests==2.32.3  # ==2.32.3 pins exact version so it always works
```

Create `src/ingest_from_api.py`:

**How to create this file:**
```bash
notepad src/ingest_from_api.py  # opens Notepad; click Yes to create the file
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

**What `ingest_from_api.py` does and why it exists:**
- **What it does:** Demonstrates how to pull data from a live REST API using HTTP GET/POST requests, then load it into SQLite — this is how real production pipelines ingest data
- **Why separate:** In production, data never arrives as a static CSV file — it comes from APIs (order management systems, CRMs, payment platforms). This file exists to teach you the GET/POST pattern that every data engineer uses constantly. If it were merged into `ingest.py`, that script would confusingly mix "read a file" logic with "call an API" logic.
- **Input:** External API URL (`https://jsonplaceholder.typicode.com/posts`) — no local file needed, data is fetched live over HTTP
- **Output:** `data/delivery_db.sqlite` (same database as `ingest.py`, adds the `api_ingested_records` table with 100 rows fetched from the API)
- **Pipeline position:** External API (JSONPlaceholder here; a real logistics API in production) → **this script** → `data/delivery_db.sqlite` table `api_ingested_records` (same destination as `ingest.py`, different source)

```python
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
```

Run it:
```bash
python src/ingest_from_api.py  # run the API ingestion script
```

**What this teaches:**
- GET fetches data into your pipeline
- POST sends updates back (triggering a re-delivery, marking a status)
- Every data engineer writes this pattern constantly — pulling from CRM APIs, ERP APIs, payment APIs
- The requests library and the response-to-DataFrame flow is the same regardless of which API you call

---

## Checkpoint

You now have:
- `data/raw/deliveries.csv` — 50,000 synthetic records (local dev source)
- `data/delivery_db.sqlite` — structured database with 2 tables
- `src/ingest_from_api.py` — GET/POST pattern for real API-based ingestion
- First insight: **FADR is lowest for apartments and morning windows**

---

## Git Checkpoint — End of Guide 02

- This is the full Git workflow you do at the end of every guide
- In a real office this is called "raising a PR (Pull Request)"
- You will do this 13 times — by the third time it feels automatic

---

### Step G3 — Check what changed

```bash
git status  # show which files changed since last commit
```
**What to look for:** Files listed in red under "Changes not staged for commit" — these are files you modified. Files in red under "Untracked files" — these are new files Git has never seen before. Nothing should be green yet — you have not staged anything.

**In an office:**
- Before staging anything, always read `git status` first
- It shows you exactly what you are about to commit
- Committing blindly is how secrets (passwords, API keys) accidentally get pushed to GitHub

---

### Step G4 — Review your changes line by line

```bash
git diff  # show exact line-by-line changes not yet staged
```
**What this shows:**
- The exact lines you added (in green with `+`) and deleted (in red with `-`) in every modified file
- This is your chance to review your own work before anyone else sees it

**What to check:**
- Did I accidentally leave a `print("test123")` debugging line?
- Did I hardcode a password anywhere?
- Does the change make sense — does it do what I intended?

Press `q` to exit the diff view.

**In an office:**
- Senior engineers always do `git diff` before staging
- It catches mistakes before they become commits

---

### Step G5 — Stage your files

```bash
git add src/generate_data.py   # stage only this file
git add src/ingest.py          # stage only this file
git add src/ingest_from_api.py # stage only this file
```

**What staging means:**
- You are selecting which changes go into the next commit
- Git has a two-step save: stage first, then commit
- This lets you commit only specific files even if you changed many

**Why not `git add .`?**
- Using `.` adds every changed file including things you may not want — temporary files, `.env` files with passwords, large data files
- Always add by name or pattern

---

### Step G6 — Verify what is staged

```bash
git diff --staged  # show changes that ARE staged (about to be committed)
```
**What this shows:**
- The same line-by-line diff as before, but ONLY for files you just staged
- This is your final review before the commit is permanent

**The difference between `git diff` and `git diff --staged`:**
- `git diff` → shows unstaged changes (what you changed but have NOT added yet)
- `git diff --staged` → shows staged changes (what you HAVE added, about to commit)

Press `q` to exit.

---

### Step G7 — Commit

```bash
git commit -m "Guide 02: data generator with 50k records, SQLite ingestion, API pattern"  # -m = commit message
```
**What a commit is:**
- A permanent snapshot saved in Git's history
- Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`)
- You can always return to this exact state

**What makes a good commit message:**
- Good: `"Guide 02: data generator with 50k records, SQLite ingestion, API pattern"`
- Bad: `"done"`, `"update"`, `"changes"`

Rule: your future self reading this 3 months later should know exactly what changed without looking at the code.

---

### Step G8 — Check your commit was saved

```bash
git log --oneline  # show one line per commit; most recent at top
```
**What this shows:**
- All commits on this branch, one line each
- The most recent is at the top
- You should see your new commit at the top of the list

**What `--oneline` means:**
- Show one line per commit instead of the full multi-line format
- Makes it easy to scan history quickly

Example output:
```
a3f9c2b Guide 02: data generator with 50k records, SQLite ingestion, API pattern
e7d1a4f Guide 01: environment setup, requirements.txt, folder structure
9b2c3d1 Initial commit: project guides and README
```

**In an office:**
- `git log --oneline` is one of the most used commands
- It gives you the full history of the branch at a glance

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-02-data  # -u = link local branch to GitHub branch
```
**What `git push` does:**
- Uploads your local commits to GitHub
- Until you push, your commit only exists on your laptop

**What `-u` means:**
- Sets the upstream — links your local branch to a branch of the same name on GitHub
- You only need `-u` the first time you push a new branch
- After that, just `git push` is enough

**What `origin` means:**
- The name of your GitHub remote
- When you ran `git remote add origin ...` in Guide 00B, you named it `origin`
- That name sticks

- After pushing, go to your GitHub repository in the browser
- You will see a yellow banner: **"feature/guide-02-data had recent pushes"**

---

### Step G10 — Raise a Pull Request on GitHub

- A Pull Request (PR) is a formal request to merge your branch into another branch
- You are asking: "I finished this work, please review it and bring it into develop"

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-02-data` ← what you are merging in
3. Title: `Guide 02: data generation and ingestion`
4. Description: `Added synthetic data generator (50k delivery records), SQLite ingestion from CSV, and API ingestion pattern using JSONPlaceholder.`
5. Click **Create pull request**
6. Click **Merge pull request** → **Confirm merge**

**In an office:**
- A colleague would review your PR before approving
- They would read your diff, leave comments, and you would discuss
- Here you review and merge yourself — but the process is identical

**Why not push directly to develop?**
- In real teams, direct pushes to develop and main are blocked
- Every change must go through a PR
- This ensures someone always reviews code before it merges
- You are building that exact habit

---

### Step G11 — Pull the merged changes back locally

```bash
git checkout develop  # switch back to develop branch
```
- Switches you back to develop
- No `-b` here — `develop` already exists, you are just switching to it

```bash
git pull origin develop  # download the merged PR into local develop
```
- Downloads the merged PR from GitHub into your local develop
- Your local develop now has everything from the feature branch you just merged

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub
- `pull` — download + merge in one step (it runs `git fetch` then `git merge` automatically)

```bash
git log --oneline  # confirm Guide 02 commit appears in develop history
```
- You should now see your Guide 02 commit in develop's history
- Confirm it is there

**What `--oneline` means:** Show one line per commit instead of the full multi-line format.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-02-data  # -d = delete local branch (safe: fails if unmerged)
```
**What `-d` means:**
- Delete the branch locally
- Git will refuse to delete if the branch has unmerged commits — a safety guard
- Since you just merged the PR, `-d` works

```bash
git push origin --delete feature/guide-02-data  # delete the branch on GitHub too
```
Deletes the branch on GitHub too.

**What each part means:**
- `origin` — push this action to GitHub (not just locally)
- `--delete` — delete the named branch on GitHub

**Why delete?**
- Merged branches are dead branches
- Keeping them clutters the repository
- In real teams, merged branches are always deleted
- A clean repo = a professional habit

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-03-sql  # -b = create new branch and switch to it
```

**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 02 commit is in the history
- **Branches** → feature/guide-02-data is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_03_SQL.md](GUIDE_03_SQL.md) — Write analytical SQL to uncover patterns
