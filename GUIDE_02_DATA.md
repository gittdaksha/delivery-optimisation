# Guide 02 — Generate & Store Raw Data

**Goal:** Create realistic synthetic delivery data using Python, then store it in a database using SQL (Structured Query Language). This is the "ingestion" layer of the pipeline.

---

## Why synthetic data?

Real delivery data is private. Companies don't share it. But you need data to work with. `Faker` is a Python library that generates realistic-looking fake data — names, addresses, timestamps. This is a standard practice for building portfolio projects and for testing pipelines in development environments.

---

## Git — Before You Start This Guide

Every guide begins the same way in a real office: you make sure you are on the right branch and it is up to date before touching any files.

### Step G1 — Make sure you are on develop and it is current

```bash
git checkout develop
```
**What this does:** Switches you to the develop branch. You always create feature branches FROM develop, never from main and never from another feature branch.

```bash
git pull origin develop
```
**What this does:** Downloads any changes from GitHub that you do not have locally. In an office, a colleague may have merged something since you last worked. `pull` = download + merge in one command.

```bash
git status
```
**What this does:** Shows the current state. You should see `On branch develop, nothing to commit, working tree clean`. If you see modified files here, deal with them before moving forward — do not carry unrelated changes into a new branch.

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-02-data
```
**What `-b` means:** Create a new branch AND switch to it. Without `-b`, checkout only switches to an existing branch.

**Why a new branch for every guide:** Each branch is one unit of work. If something breaks, you can delete the branch and start fresh without affecting develop or main. In an office, each feature or fix lives on its own branch for the same reason.

Confirm you are on the right branch:
```bash
git branch
```
You will see a `*` next to your current branch. That `*` means "you are here".

---

## Step 2.1 — Create the project directories

```bash
mkdir src
mkdir sql
mkdir data
mkdir data\raw
mkdir data\processed
mkdir models
mkdir notebooks
```

---

## Step 2.2 — Create `src/generate_data.py`

Create the file `src/generate_data.py` with this content:

**How to create this file:**
```bash
notepad src/generate_data.py
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```python
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

fake = Faker('en_IN')  # Indian locale for realistic addresses
np.random.seed(42)
random.seed(42)

ADDRESS_TYPES = ['Apartment', 'PG/Hostel', 'House', 'Office', 'Gated Community']
DELIVERY_WINDOWS = ['Morning (9-12)', 'Afternoon (12-15)', 'Evening (15-19)', 'Night (19-22)']
FAILURE_REASONS = ['Customer Unavailable', 'Wrong Address', 'Refused Delivery', 'Building Access Denied', None]
CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Pune', 'Chennai']

def generate_delivery_data(n_records=50000):
    records = []

    for _ in range(n_records):
        city = random.choice(CITIES)
        address_type = random.choice(ADDRESS_TYPES)
        window = random.choice(DELIVERY_WINDOWS)
        order_value = round(random.uniform(150, 8000), 2)

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

        success_prob = max(0.10, min(0.97, success_prob))
        is_successful = random.random() < success_prob

        failure_reason = None
        if not is_successful:
            failure_reason = random.choice(FAILURE_REASONS[:-1])  # exclude None

        attempt_date = datetime.now() - timedelta(days=random.randint(1, 365))

        records.append({
            'delivery_id': fake.uuid4(),
            'customer_id': fake.uuid4()[:8],
            'city': city,
            'address_type': address_type,
            'delivery_window': window,
            'order_value': order_value,
            'is_successful': int(is_successful),
            'failure_reason': failure_reason,
            'attempt_number': random.choices([1, 2, 3], weights=[70, 22, 8])[0],
            'attempt_date': attempt_date.strftime('%Y-%m-%d'),
            'attempt_hour': int(window.split('(')[1].split('-')[0]),
            'has_delivery_preference': random.choices([0, 1], weights=[60, 40])[0],
            'proximity_alert_sent': random.choices([0, 1], weights=[55, 45])[0],
        })

    return pd.DataFrame(records)


if __name__ == '__main__':
    print("Generating 50,000 delivery records...")
    df = generate_delivery_data(50000)

    os.makedirs('data/raw', exist_ok=True)
    output_path = 'data/raw/deliveries.csv'
    df.to_csv(output_path, index=False)

    print(f"Saved to {output_path}")
    print(f"Shape: {df.shape}")
    print(f"\nOverall FADR: {df['is_successful'].mean():.2%}")
    print(f"\nFADR by address type:")
    print(df.groupby('address_type')['is_successful'].mean().sort_values())
    print(f"\nFADR by delivery window:")
    print(df.groupby('delivery_window')['is_successful'].mean().sort_values())
```

**Key concepts in this code:**

**What `random.seed(42)` means:** Setting a seed makes random number generation reproducible — every time you run this script you get the exact same 50,000 records in the same order. The number 42 is arbitrary; any integer works. Without a seed, each run produces different data, making debugging and comparing results harder.

**What `fake.uuid4()` is:** A UUID (Universally Unique Identifier) is a randomly generated string like `f47ac10b-58cc-4372-a567-0e02b2c3d479`. It is statistically guaranteed to be unique — no two deliveries share the same ID. This is how real systems identify records without using sequential numbers that could clash.

**What `pd.DataFrame(records)` is:** A DataFrame is a table held in memory — rows and columns, just like a spreadsheet. `pd.DataFrame(records)` converts your list of Python dictionaries into this table, where each row is one delivery and each column is one field (city, address_type, etc.).

**What `if __name__ == '__main__':` means:** This Python pattern means "only run this code if this file is executed directly — not when it is imported by another script." It lets `generate_delivery_data` be reused as a function in other scripts without automatically triggering the full 50,000-record generation.

---

## Step 2.3 — Run the data generator

**What a CSV file is:** A CSV (Comma-Separated Values) file is a plain text file where each line is one row of data and values are separated by commas. It is the simplest universal format for tabular data — any spreadsheet, database, or data tool can open it.

**What this does:** Runs the data generation script and saves 50,000 synthetic delivery records to `data/raw/deliveries.csv`.

```bash
python src/generate_data.py
```

**Why:** This creates `data/raw/deliveries.csv` with 50,000 synthetic delivery records. You will see the overall FADR and how it breaks down by address type and delivery window — this is your first insight.

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

**What SQLite is:** SQLite is a database that lives entirely in a single file on your computer — no separate database server to install or run. It is perfect for learning and for development because it is simple to set up. In production, companies use server-based databases like PostgreSQL, MySQL, or cloud warehouses like BigQuery, but the SQL you write is the same.

**What this does:** Creates a `.sql` file that defines the structure (schema) of your database tables — what columns each table has and what type of data each column holds.

Create `sql/create_tables.sql`:

**How to create this file:**
```bash
notepad sql/create_tables.sql
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

**What `IF NOT EXISTS` means:** This tells the database "create this table only if it does not already exist — otherwise do nothing." Without it, running the script a second time would throw an error because the table already exists.

**What `PRIMARY KEY` means:** The primary key uniquely identifies each row. No two rows can have the same value in this column, and it cannot be empty. Here `delivery_id` is the primary key — every delivery has exactly one unique ID.

```sql
-- Raw deliveries table: one row per delivery attempt
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id       TEXT PRIMARY KEY,
    customer_id       TEXT NOT NULL,
    city              TEXT NOT NULL,
    address_type      TEXT NOT NULL,
    delivery_window   TEXT NOT NULL,
    order_value       REAL NOT NULL,
    is_successful     INTEGER NOT NULL,   -- 1 = success, 0 = failed
    failure_reason    TEXT,               -- NULL if successful
    attempt_number    INTEGER NOT NULL,
    attempt_date      TEXT NOT NULL,
    attempt_hour      INTEGER NOT NULL,
    has_delivery_preference INTEGER NOT NULL,
    proximity_alert_sent    INTEGER NOT NULL
);

-- Summary table: FADR by city and address type
CREATE TABLE IF NOT EXISTS fadr_by_segment (
    city            TEXT,
    address_type    TEXT,
    total_attempts  INTEGER,
    successful      INTEGER,
    fadr            REAL,
    PRIMARY KEY (city, address_type)
);
```

---

## Step 2.5 — Create `src/ingest.py`

**What this does:** Reads the CSV file and loads it into the SQLite database so you can query it with SQL.

Create `src/ingest.py`:

**How to create this file:**
```bash
notepad src/ingest.py
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```python
import pandas as pd
import sqlite3
import os

DB_PATH = 'data/delivery_db.sqlite'
CSV_PATH = 'data/raw/deliveries.csv'

def load_to_db():
    print(f"Loading {CSV_PATH} into SQLite database...")

    df = pd.read_csv(CSV_PATH)
    conn = sqlite3.connect(DB_PATH)

    # Load raw data
    df.to_sql('deliveries', conn, if_exists='replace', index=False)
    print(f"  Loaded {len(df):,} rows into 'deliveries' table")

    # Pre-compute FADR summary
    fadr = (
        df.groupby(['city', 'address_type'])
        .agg(
            total_attempts=('is_successful', 'count'),
            successful=('is_successful', 'sum')
        )
        .reset_index()
    )
    fadr['fadr'] = fadr['successful'] / fadr['total_attempts']
    fadr.to_sql('fadr_by_segment', conn, if_exists='replace', index=False)
    print(f"  Computed FADR for {len(fadr)} city/address-type segments")

    conn.close()
    print(f"\nDatabase saved to {DB_PATH}")

if __name__ == '__main__':
    load_to_db()
```

---

## Step 2.6 — Run ingestion

**What this does:** Executes the ingestion script, which reads the CSV and writes it into the SQLite database file.

```bash
python src/ingest.py
```

**Why:** This loads the CSV into a SQLite database. SQLite is a file-based database — no server needed. Perfect for learning. In production this would be PostgreSQL, BigQuery, or Snowflake.

---

## Step 2.7 — Verify the data in the database

**What this does:** Opens the database directly from the command line and runs two quick SQL checks — one to count the rows, one to show FADR grouped by address type. The `-c` flag tells Python to run a short script written inline instead of from a file.

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/delivery_db.sqlite')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM deliveries')
print('Rows in deliveries:', cur.fetchone()[0])
cur.execute('SELECT address_type, ROUND(AVG(is_successful)*100,1) as fadr FROM deliveries GROUP BY address_type ORDER BY fadr')
for row in cur.fetchall():
    print(row)
conn.close()
"
```

**Why:** Always verify data loaded correctly. Never trust a pipeline without checking the output. This is a habit that separates reliable data engineers from unreliable ones.

---

---

## Step 2.8 — API (Application Programming Interface) ingestion (how it works in production)

In production, delivery data does not come from a CSV. It comes from an API — the order management system exposes endpoints that your pipeline calls to pull new records.

This step shows you how to write an API-based ingestion function. You will use a real public API (JSONPlaceholder — a free fake REST (Representational State Transfer) API used for exactly this kind of learning) to understand the GET/POST pattern, then map it to what a real logistics API would look like.

Install the requests library:
```bash
pip install requests==2.32.3
```

Create `src/ingest_from_api.py`:

**How to create this file:**
```bash
notepad src/ingest_from_api.py
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```python
import requests
import pandas as pd
import sqlite3
import json

# ── What a real delivery API call looks like ────────────────────────────────
# In production this would be:
#   GET https://api.deliveryplatform.com/v1/orders?status=failed&date=2024-01-15
#   Headers: {"Authorization": "Bearer YOUR_API_KEY"}
#
# Here we use JSONPlaceholder — a free public API that returns fake structured
# data so you can learn the pattern without needing real credentials.

BASE_URL = "https://jsonplaceholder.typicode.com"

def fetch_from_api(endpoint: str, params: dict = None) -> list:
    """
    Make a GET request to an API endpoint and return the JSON response.
    This is the same pattern used to call BigQuery REST API, GCS API,
    Kafka REST proxy, or any logistics platform API.
    """
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params)

    # Always check the status code — never assume an API call succeeded
    response.raise_for_status()   # raises an exception if status is 4xx or 5xx

    return response.json()

def post_to_api(endpoint: str, payload: dict) -> dict:
    """
    Make a POST request — used to send data back: update a delivery status,
    trigger a re-attempt, or write to a webhook.
    """
    response = requests.post(
        f"{BASE_URL}/{endpoint}",
        json=payload,                              # serialises dict to JSON (JavaScript Object Notation) body
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # ── GET: pull records ───────────────────────────────────────────────────
    print("GET /posts (simulates pulling delivery records from an API)...")
    records = fetch_from_api("posts")
    print(f"  Fetched {len(records)} records")
    print(f"  First record: {json.dumps(records[0], indent=2)}")

    # ── GET with query params ────────────────────────────────────────────────
    print("\nGET /posts?userId=1 (simulates filtering by delivery partner ID)...")
    partner_records = fetch_from_api("posts", params={"userId": 1})
    print(f"  Fetched {len(partner_records)} records for userId=1")

    # ── POST: send data back ─────────────────────────────────────────────────
    print("\nPOST /posts (simulates writing a delivery status update)...")
    status_update = {
        "delivery_id": "abc-123",
        "status": "FAILED",
        "reason": "Customer unavailable",
        "attempt": 1,
        "partner_id": "P001"
    }
    result = post_to_api("posts", status_update)
    print(f"  API acknowledged with id: {result.get('id')}")

    # ── Load API response to SQLite (same pattern as load_to_bigquery.py) ───
    df = pd.DataFrame(records)
    conn = sqlite3.connect("data/delivery_db.sqlite")
    df.to_sql("api_ingested_records", conn, if_exists="replace", index=False)
    conn.close()
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
python src/ingest_from_api.py
```

**What this teaches:** GET fetches data into your pipeline. POST sends updates back (triggering a re-delivery, marking a status). Every data engineer writes this pattern constantly — pulling from CRM APIs, ERP APIs, payment APIs. The requests library and the response-to-DataFrame flow is the same regardless of which API you call.

---

## Checkpoint

You now have:
- `data/raw/deliveries.csv` — 50,000 synthetic records (local dev source)
- `data/delivery_db.sqlite` — structured database with 2 tables
- `src/ingest_from_api.py` — GET/POST pattern for real API-based ingestion
- First insight: **FADR is lowest for apartments and morning windows**

---

## Git Checkpoint — End of Guide 02

This is the full Git workflow you do at the end of every guide. In a real office this is called "raising a PR (Pull Request)". You will do this 13 times — by the third time it feels automatic.

---

### Step G3 — Check what changed

```bash
git status
```
**What to look for:** Files listed in red under "Changes not staged for commit" — these are files you modified. Files in red under "Untracked files" — these are new files Git has never seen before. Nothing should be green yet — you have not staged anything.

**In an office:** Before staging anything, always read `git status` first. It shows you exactly what you are about to commit. Committing blindly is how secrets (passwords, API keys) accidentally get pushed to GitHub.

---

### Step G4 — Review your changes line by line

```bash
git diff
```
**What this shows:** The exact lines you added (in green with `+`) and deleted (in red with `-`) in every modified file. This is your chance to review your own work before anyone else sees it.

**What to check:**
- Did I accidentally leave a `print("test123")` debugging line?
- Did I hardcode a password anywhere?
- Does the change make sense — does it do what I intended?

Press `q` to exit the diff view.

**In an office:** Senior engineers always do `git diff` before staging. It catches mistakes before they become commits.

---

### Step G5 — Stage your files

```bash
git add src/generate_data.py
git add src/ingest.py
git add src/ingest_from_api.py
```

**What staging means:** You are selecting which changes go into the next commit. Git has a two-step save: stage first, then commit. This lets you commit only specific files even if you changed many.

**Why not `git add .`?** Using `.` adds every changed file including things you may not want — temporary files, `.env` files with passwords, large data files. Always add by name or pattern.

---

### Step G6 — Verify what is staged

```bash
git diff --staged
```
**What this shows:** The same line-by-line diff as before, but ONLY for files you just staged. This is your final review before the commit is permanent.

**The difference between `git diff` and `git diff --staged`:**
- `git diff` → shows unstaged changes (what you changed but have NOT added yet)
- `git diff --staged` → shows staged changes (what you HAVE added, about to commit)

Press `q` to exit.

---

### Step G7 — Commit

```bash
git commit -m "Guide 02: data generator with 50k records, SQLite ingestion, API pattern"
```
**What a commit is:** A permanent snapshot saved in Git's history. Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`). You can always return to this exact state.

**What makes a good commit message:**
- Good: `"Guide 02: data generator with 50k records, SQLite ingestion, API pattern"`
- Bad: `"done"`, `"update"`, `"changes"`

Rule: your future self reading this 3 months later should know exactly what changed without looking at the code.

---

### Step G8 — Check your commit was saved

```bash
git log --oneline
```
**What this shows:** All commits on this branch, one line each. The most recent is at the top. You should see your new commit at the top of the list.

Example output:
```
a3f9c2b Guide 02: data generator with 50k records, SQLite ingestion, API pattern
e7d1a4f Guide 01: environment setup, requirements.txt, folder structure
9b2c3d1 Initial commit: project guides and README
```

**In an office:** `git log --oneline` is one of the most used commands. It gives you the full history of the branch at a glance.

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-02-data
```
**What `git push` does:** Uploads your local commits to GitHub. Until you push, your commit only exists on your laptop.

**What `-u` means:** Sets the upstream — links your local branch to a branch of the same name on GitHub. You only need `-u` the first time you push a new branch. After that, just `git push` is enough.

**What `origin` means:** The name of your GitHub remote. When you ran `git remote add origin ...` in Guide 00B, you named it `origin`. That name sticks.

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-02-data had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-02-data` ← what you are merging in
3. Title: `Guide 02: data generation and ingestion`
4. Description: 1-2 lines about what this guide added
5. Click **Create pull request**
6. Click **Merge pull request** → **Confirm merge**

**In an office:** A colleague would review your PR before approving. They would read your diff, leave comments, and you would discuss. Here you review and merge yourself — but the process is identical.

**Why not push directly to develop?** In real teams, direct pushes to develop and main are blocked. Every change must go through a PR. This ensures someone always reviews code before it merges. You are building that exact habit.

---

### Step G11 — Pull the merged changes back locally

```bash
git checkout develop
```
Switches you back to develop.

```bash
git pull origin develop
```
Downloads the merged PR from GitHub into your local develop. Your local develop now has everything from the feature branch you just merged.

```bash
git log --oneline
```
You should now see your Guide 02 commit in develop's history. Confirm it is there.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-02-data
```
**What `-d` means:** Delete the branch locally. Git will refuse to delete if the branch has unmerged commits — a safety guard. Since you just merged the PR, `-d` works.

```bash
git push origin --delete feature/guide-02-data
```
Deletes the branch on GitHub too.

**Why delete?** Merged branches are dead branches. Keeping them clutters the repository. In real teams, merged branches are always deleted. A clean repo = a professional habit.

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-03-sql
```

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 02 commit is in the history
- **Branches** → feature/guide-02-data is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_03_SQL.md](GUIDE_03_SQL.md) — Write analytical SQL to uncover patterns
