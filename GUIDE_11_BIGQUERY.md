# Guide 11 — Move from SQLite to BigQuery (GCP)

**Goal:** Run the same pipeline — the same SQL (Structured Query Language), the same dbt (Data Build Tool) models — against Google BigQuery instead of SQLite. This is not a new pipeline. It is the same pipeline on production infrastructure.

**Why this guide exists:** SQLite is a local file on your laptop — no company uses it in production. BigQuery is Google's cloud data warehouse used by thousands of companies. This guide proves you can take what you built locally and run it on real cloud infrastructure — the most important step for getting a job.

---

## Why this matters

- Every query you wrote in Guide 03 runs on BigQuery without changes
- Every dbt model in Guide 04 runs on BigQuery by changing one line in `profiles.yml`
- That is the point — the skills transfer directly
- The JDs you saw ask for BigQuery specifically because that is what GCP-based companies use as their data warehouse
- SQLite is fine for local development
- BigQuery is what you use when the data is too large for a single machine, the queries need to run in seconds on billions of rows, and multiple teams need to access the same data simultaneously
- This guide connects what you already built to GCP — which is what those JDs are actually asking for

---

## Git — Before You Start This Guide

- Every guide begins the same way in a real office: make sure you are on the right branch and it is up to date before touching any files

### Step G1 — Make sure you are on develop and it is current

```bash
git checkout develop  # switch to develop branch (must already exist)
```
**What this does:**
- Switches you to the develop branch
- You always create feature branches FROM develop, never from main and never from another feature branch
- No `-b` here — this switches to an existing branch; you do not use `-b` when the branch already exists

```bash
git pull origin develop  # download + merge latest changes from GitHub
```
**What this does:**
- Downloads any changes from GitHub that you do not have locally
- In an office, a colleague may have merged something since you last worked
- `pull` = download + merge in one command

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub

```bash
git status  # show current state; should be clean before creating a branch
```
**What this does:**
- Shows the current state
- You should see `On branch develop, nothing to commit, working tree clean`
- If you see modified files here, deal with them before moving forward — do not carry unrelated changes into a new branch
- No flags here — `git status` always shows full current state

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-11-bigquery  # -b = create new branch and switch to it
```
**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

**Why a new branch for every guide:**
- Each branch is one unit of work
- If something breaks, you can delete the branch and start fresh without affecting develop or main
- In an office, each feature or fix lives on its own branch for the same reason

Confirm you are on the right branch:
```bash
git branch  # list all branches; * marks your current one
```
- You will see a `*` next to your current branch
- That `*` means "you are here"

---

## What BigQuery is

- BigQuery is Google's fully managed, serverless data warehouse
- You do not provision servers, manage storage, or tune indexes
- You upload data and run SQL; it scales automatically
- You pay per query (or per storage, on flat-rate pricing)
- In the delivery optimisation context: in production, every delivery event from every city lands in BigQuery
- Analysts, data scientists, and the ML (Machine Learning) pipeline all query from there
- The dbt models transform raw events into clean mart tables that the dashboard reads

---

## Step 11.1 — Create a GCP account and project

**What a GCP project is:**
- A GCP (Google Cloud Platform) project is a container that groups all the cloud resources you create — databases, storage buckets, compute jobs — under one billing account and permission set
- Every BigQuery dataset, every GCS (Google Cloud Storage) bucket, every API (Application Programming Interface) call is associated with a specific project
- The Project ID is a unique string (like `delivery-optimisation-abc123`) that you use in all API calls to say "this belongs to my project"

1. Go to console.cloud.google.com
2. Sign in with a Google account
3. Click **Select a project → New Project**
4. Name it: `delivery-optimisation`
5. Note your **Project ID** — you will need it throughout

- GCP gives you a free tier with $300 credit for 90 days
- BigQuery has a permanent free tier: 10GB storage + 1TB queries per month
- This project will use a fraction of that

---

## Step 11.2 — Enable the BigQuery API

In the GCP console:
1. Go to **APIs & Services → Library**
2. Search for **BigQuery API**
3. Click **Enable**

---

## Step 11.3 — Install the GCP SDK (Software Development Kit) and Python client

**Step 1 — Install Python libraries:**
```bash
pip install google-cloud-bigquery==3.23.0 google-cloud-storage==2.16.0 db-dtypes==1.2.0
```

**Step 2 — Install the GCP CLI (`gcloud`) in Codespaces:**
```bash
curl https://sdk.cloud.google.com | bash -s -- --disable-prompts
source /root/.bashrc
```
**What this does:**
- Downloads and installs the `gcloud` CLI into Codespaces
- `source /root/.bashrc` reloads the shell so `gcloud` is available immediately
- On your local Windows machine, download the installer from `https://cloud.google.com/sdk/docs/install` instead

**Step 3 — Log in and set your project:**
```bash
gcloud init
```
- Choose your Google account
- Select your `delivery-optimisation` project

```bash
gcloud auth application-default login
```
**What `application-default login` does:**
- Opens a browser window where you log in with your Google account
- Saves credentials to a file (`~/.config/gcloud/`)
- Any GCP SDK call — from Python, dbt, or the CLI — automatically reads these credentials to prove you are authorised
- You are not embedding passwords into code; the credential file handles it transparently

---

## Step 11.4 — Create a BigQuery dataset

A BigQuery **dataset** is equivalent to a database schema — it is a container for tables.

**What `bq mk` does:**
- `bq` is the BigQuery command-line tool
- `mk` stands for "make" — it creates a new resource
- `--dataset` specifies you are creating a dataset (BigQuery's equivalent of a schema or folder for tables)
- The `--location` flag sets which Google data centre stores your data

```bash
bq mk --dataset --location=asia-south1 YOUR_PROJECT_ID:delivery_raw  # create raw data dataset in Mumbai region
bq mk --dataset --location=asia-south1 YOUR_PROJECT_ID:delivery_marts  # create transformed data dataset
```

Replace `YOUR_PROJECT_ID` with your actual project ID.

**Why `asia-south1`:**
- Mumbai region
- Data residency matters — keeping data in India is relevant for Indian logistics companies
- Lower latency for local queries

---

## Step 11.5 — Create `src/load_to_bigquery.py`

**What `src/load_to_bigquery.py` does and why it exists:**
- **What it does:** Reads the local CSV file and uploads it to a BigQuery table in your GCP project, replacing any previously loaded data on each run
- **Why separate:** Cloud ingestion is a distinct concern from local data generation or SQLite loading — the credentials, SDK calls, and error handling are all GCP-specific; keeping it separate means the rest of the pipeline continues to work locally even when cloud access is unavailable
- **Input:** `data/raw/deliveries.csv` (50,000 delivery records, ~8MB local CSV file)
- **Output:** BigQuery table `project.delivery_raw.deliveries` (50,000 rows loaded into GCP, queryable with SQL)
- **Pipeline position:** `data/raw/deliveries.csv` (from `generate_data.py`) → **this script** → `delivery_raw.deliveries` table in BigQuery → dbt `--target bigquery` for cloud transformations

Run this command in Codespaces to create the file:

```bash
cat > src/load_to_bigquery.py << 'ENDOFFILE'
from google.cloud import bigquery  # GCP BigQuery Python client library
import pandas as pd  # needed to read the CSV into a DataFrame first
import os  # read environment variables (like GCP_PROJECT_ID)

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")   # read project ID from environment variable
DATASET    = "delivery_raw"  # BigQuery dataset (like a schema) to load into
TABLE      = "deliveries"  # BigQuery table name to create or overwrite

def load_csv_to_bigquery():  # function that does the actual load
    client = bigquery.Client(project=PROJECT_ID)  # create authenticated BQ client

    df = pd.read_csv("data/raw/deliveries.csv")  # read local CSV into a DataFrame
    print(f"Loaded {len(df):,} rows from CSV")  # confirm row count before upload

    # f-string builds the full 3-part BigQuery table address
    # → e.g. "my-project-123.delivery_raw.deliveries"
    # BigQuery always needs: project_id.dataset_name.table_name
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"  # full BQ table path: project.dataset.table

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # overwrite on reload
        # What write_disposition WRITE_TRUNCATE means: before loading new data,
        # delete all existing rows in the destination table and replace them with
        # the new data. This is like mode("overwrite") in PySpark. Use it for a
        # full reload. The alternative WRITE_APPEND adds new rows without deleting
        # existing ones.
        autodetect=True,
        # What autodetect=True does: instead of you manually defining the schema
        # (column names and types), BigQuery inspects the first few rows of your data
        # and infers the types automatically. Useful for getting started quickly,
        # but in production you typically define the schema explicitly to avoid
        # surprises if the source data format changes.
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)  # start async load job
    # load_table_from_dataframe() returns immediately — the upload runs in the background
    # job.result() blocks Python here and waits until BigQuery confirms the job finished
    # without this line the script would exit before the data is fully loaded
    job.result()   # block here until the load job finishes

    table = client.get_table(table_id)  # fetch table metadata to confirm load
    print(f"Loaded {table.num_rows:,} rows into {table_id}")  # print actual row count in BQ
    # table.schema = list of SchemaField objects; f.name extracts just the column name string
    # [f.name for f in table.schema] = list comprehension → ['delivery_id', 'city', ...]
    print(f"Schema: {[f.name for f in table.schema]}")  # print column names BQ detected

if __name__ == "__main__":  # only run when called directly, not when imported
    load_csv_to_bigquery()  # execute the load function
ENDOFFILE
```

---

## Step 11.6 — Set your project ID and run

```bash
export GCP_PROJECT_ID=your-actual-project-id  # set env var so the script can read it
python src/load_to_bigquery.py  # run the load script
```

---

## Step 11.7 — Use GCS as the landing zone (the real ELT (Extract, Load, Transform) pattern)

In production, data does not go CSV → BigQuery directly. It goes:

```
Source system → Cloud Storage (GCS) → BigQuery
```

- GCS is the raw data landing zone — like an S3 bucket, cheap object storage
- The delivery CSV lands here first, BigQuery then loads from it
- This matters because:
  - Multiple systems can read from GCS independently (Spark, BigQuery, Dataflow)
  - You have a permanent audit trail of raw files before transformation
  - BigQuery loads from GCS are faster and cheaper than streaming row inserts

Install the GCS client:
```bash
pip install google-cloud-storage==2.16.0  # GCS Python library (may already be installed)
```

Add this to `src/load_to_bigquery.py` (before the BigQuery load):

```python
from google.cloud import storage  # GCS Python client library

# local_path: str  — the ": str" after the parameter name is a type hint
# it tells Python (and any reader) that this parameter must be a string
# Python does not enforce this at runtime but it documents what the function expects
def upload_to_gcs(local_path: str, bucket_name: str, gcs_path: str):  # type hints: str = text input
    """Upload a local file to Google Cloud Storage."""
    client = storage.Client(project=PROJECT_ID)  # create authenticated GCS client

    # Create bucket if it doesn't exist
    try:
        bucket = client.get_bucket(bucket_name)  # try to fetch existing bucket
    except Exception:  # bucket not found — create a new one
        bucket = client.create_bucket(bucket_name, location="asia-south1")  # Mumbai region
        print(f"  Created bucket gs://{bucket_name}")

    blob = bucket.blob(gcs_path)  # blob = a file inside the bucket at this path
    blob.upload_from_filename(local_path)  # read local file and upload to GCS
    print(f"  Uploaded {local_path} → gs://{bucket_name}/{gcs_path}")
    # builds a GCS URI string like: "gs://my-project-delivery-raw/deliveries/2024/deliveries.csv"
    # this URI is what load_table_from_uri() needs to know where to read the file from
    return f"gs://{bucket_name}/{gcs_path}"  # return the GCS URI for the next step

def load_from_gcs_to_bigquery(gcs_uri: str, table_id: str):
    """Load data from GCS into BigQuery — the production ELT pattern."""
    client = bigquery.Client(project=PROJECT_ID)  # create authenticated BQ client

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,  # tell BQ the file is a CSV
        skip_leading_rows=1,      # header row — skip first row (column names)
        autodetect=True,  # let BQ detect column types automatically
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # overwrite existing data
    )

    job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)  # start async load job
    # same pattern as before: job starts in the background, .result() waits for it to finish
    # if the job fails, .result() raises an exception with the error details from BigQuery
    job.result()  # block until job completes before printing status
    print(f"  Loaded from GCS into {table_id}")
```

Usage (replace the direct DataFrame load):
```python
# Step 1: land raw file in GCS
gcs_uri = upload_to_gcs(
    local_path="data/raw/deliveries.csv",  # local source file to upload
    bucket_name=f"{PROJECT_ID}-delivery-raw",  # GCS bucket name (globally unique)
    gcs_path="deliveries/2024/deliveries.csv"  # path/filename inside the bucket
)

# Step 2: load from GCS into BigQuery
load_from_gcs_to_bigquery(gcs_uri, f"{PROJECT_ID}.delivery_raw.deliveries")  # project.dataset.table
```

**Why this order matters:**
- The GCS file is your raw layer — unchanged source data, permanently stored
- BigQuery is your processed layer
- If a transformation runs wrong and corrupts BigQuery, you reload from GCS
- Without GCS you have no safety net

---

## Step 11.8 — Optimise the BigQuery table

- The JD specifically asks for BigQuery optimisation
- This means partitioning and clustering — the two most important levers for query performance and cost control in BigQuery

Run this in the BigQuery SQL workspace:

**What PARTITION BY does in BigQuery:**
- Divides the table into separate storage segments by a date column
- When a query filters by that date column, BigQuery only reads the relevant segment and skips all others
- Dramatically reduces the data scanned and the cost of the query

**What CLUSTER BY does in BigQuery:**
- Within each partition, sorts and groups the data by the specified columns
- When a query filters by a clustered column (e.g. `WHERE city = 'Mumbai'`), BigQuery skips blocks that don't contain that value
- Clustering and partitioning work together — partition first (by date), cluster second (by city/address)

```sql
-- Create an optimised version of the deliveries table
-- Partition by date: queries filtering on attempt_date only scan that day's data
-- Cluster by city, address_type: queries filtering by these columns skip irrelevant blocks

CREATE OR REPLACE TABLE `your-project-id.delivery_raw.deliveries_optimised`  -- backticks wrap project.dataset.table
-- PARTITION BY DATE(...) = physically divide the table into separate storage segments, one per day
-- DATE(attempt_date) = convert the timestamp to a date — BigQuery partitions by DATE not TIMESTAMP
-- effect: a query with WHERE attempt_date = '2024-03-15' only reads that day's segment
PARTITION BY DATE(attempt_date)  -- split table storage by date; filter by date = skip other dates
-- CLUSTER BY = within each partition, sort and group rows by these columns
-- queries filtering WHERE city = 'Mumbai' skip storage blocks that don't contain Mumbai
-- list most-filtered-by column first; city is more selective than address_type here
CLUSTER BY city, address_type  -- sort within each partition by city then address_type
AS
SELECT
    delivery_id,  -- unique ID for each delivery event
    customer_id,  -- which customer placed the order
    city,  -- city where delivery happened (used for clustering)
    address_type,  -- type of address (used for clustering)
    delivery_window,  -- morning/afternoon/evening/night slot
    order_value,  -- order value in rupees
    is_successful,  -- 1 = delivered, 0 = failed
    failure_reason,  -- reason if failed, NULL if succeeded
    attempt_number,  -- 1 = first try, 2+ = re-attempt
    -- CAST(x AS DATE) = convert the value to a DATE type
    -- needed because the source column may be stored as a string or TIMESTAMP
    -- PARTITION BY DATE(...) requires a DATE type, not a string like "2024-03-15"
    CAST(attempt_date AS DATE)    AS attempt_date,  -- convert to DATE type for partitioning
    attempt_hour,  -- hour of day (0-23)
    has_delivery_preference,  -- 1 if customer set delivery preferences
    proximity_alert_sent  -- 1 if driver sent proximity notification
FROM `your-project-id.delivery_raw.deliveries`;  -- source = the unoptimised table
```

Now compare a query before and after optimisation. BigQuery shows bytes processed in the bottom right of the query editor:

```sql
-- On the UNOPTIMISED table — scans the full table
SELECT city, ROUND(AVG(is_successful)*100,2) AS fadr  -- AVG(0/1 column) = success rate
FROM `your-project-id.delivery_raw.deliveries`
WHERE attempt_date >= '2024-01-01'  -- filter by date, but BQ still scans everything
GROUP BY city;  -- one row per city

-- On the OPTIMISED table — skips all partitions outside 2024
-- AND skips data blocks where city doesn't match
SELECT city, ROUND(AVG(is_successful)*100,2) AS fadr
FROM `your-project-id.delivery_raw.deliveries_optimised`
WHERE attempt_date >= '2024-01-01'  -- partition pruning: only 2024 partitions read
GROUP BY city;  -- clustering helps skip blocks for each city
```

**What you will observe:**
- The optimised query processes less data
- On 50,000 rows the difference is small
- At 500 million rows — what a real delivery platform has — partitioning can reduce query cost by 90%

**Interview answer: "How do you optimise a slow BigQuery query?"**
- "First I check if the table is partitioned — if not, every query scans the full table regardless of filters"
- "I'd partition by the date column most filters use"
- "Then I check clustering — if queries consistently filter by city or address type, clustering on those columns reduces the blocks BigQuery reads within each partition"
- "I also check whether the query is selecting `SELECT *` when it only needs 3 columns — BigQuery is columnar, so selecting fewer columns reduces bytes read directly"

---

## Step 11.9 — Pub/Sub: the GCP version of Kafka

- You already built the Kafka producer/consumer in Guide 07
- Pub/Sub is Google's managed equivalent — the same concept, no servers to manage

The mapping is direct:

| Kafka | Pub/Sub |
|---|---|
| Topic | Topic |
| Producer (publish) | Publisher |
| Consumer (subscribe) | Subscriber / Subscription |
| Consumer group | Subscription (each subscription gets all messages independently) |
| Partition | Pub/Sub handles distribution automatically |

Install:
```bash
pip install google-cloud-pubsub==2.21.0  # Pub/Sub Python client library
```

Create `src/pubsub_producer.py`:

**What `src/pubsub_producer.py` does and why it exists:**
- **What it does:** Publishes simulated delivery status events as JSON messages to a Google Cloud Pub/Sub topic in real time
- **Why separate:** The producer only *publishes* events — it has no knowledge of who reads them or what they do with them; this decoupling is the whole point of a message queue, and it mirrors the same producer/consumer separation you built with Kafka in Guide 07
- **Input:** Generated delivery events (simulated in a Python loop — delivery_id, city, status, timestamp)
- **Output:** 20 JSON messages published to the `delivery-events` Google Pub/Sub topic
- **Pipeline position:** Live delivery events (simulated in a loop) → **this script** → `delivery-events` Pub/Sub topic → `src/pubsub_consumer.py` reads and processes them

Run this command in Codespaces to create the file:

```bash
cat > src/pubsub_producer.py << 'ENDOFFILE'
from google.cloud import pubsub_v1  # Pub/Sub client library
import json  # convert Python dict to JSON string
import os  # read environment variables
from datetime import datetime  # get current timestamp
import random  # pick random city and status

PROJECT_ID = os.environ["GCP_PROJECT_ID"]  # read project ID (set with export command)
TOPIC_ID   = "delivery-events"  # name of the Pub/Sub topic to publish to

publisher  = pubsub_v1.PublisherClient()  # create an authenticated publisher client
# topic_path() is a helper method that builds the full resource path string
# → result: "projects/my-project-123/topics/delivery-events"
# GCP APIs require this full path format; you cannot just pass "delivery-events"
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)  # build full topic resource path

# Create topic if it doesn't exist
try:
    publisher.create_topic(request={"name": topic_path})  # try to create the topic
    print(f"Created topic: {topic_path}")
except Exception:  # topic already exists — that's fine, continue
    print(f"Topic already exists: {topic_path}")

CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Pune']  # list to pick from randomly

for i in range(20):  # publish 20 test events
    event = {
        # f"D{i:04d}" = f-string with :04d format spec
        # :04d = integer, minimum 4 digits, zero-padded on the left
        # → i=1 gives "D0001", i=42 gives "D0042", i=1000 gives "D1000"
        "delivery_id": f"D{i:04d}",  # e.g. D0001, D0002 — zero-padded 4 digits
        "city":        random.choice(CITIES),  # random city from the list
        "status":      random.choice(["DELIVERED", "FAILED", "IN_TRANSIT"]),  # random status
        # datetime.now().isoformat() = current time as a standardised string
        # → e.g. "2024-03-15T14:23:07.123456"  (ISO 8601 format)
        "timestamp":   datetime.now().isoformat(),  # current time as ISO string
    }

    # Pub/Sub requires bytes — encode the JSON
    # json.dumps(event) = Python dict → JSON string: '{"delivery_id": "D0001", ...}'
    # .encode("utf-8") = JSON string → bytes: b'{"delivery_id": "D0001", ...}'
    data = json.dumps(event).encode("utf-8")  # dict → JSON string → bytes

    # publish() is non-blocking — returns a Future
    future = publisher.publish(topic_path, data=data)  # send message to Pub/Sub
    # future.result() blocks until Pub/Sub confirms receipt and returns the message ID
    print(f"  Published message id: {future.result()}")  # .result() waits and returns message ID

print("Done publishing.")
ENDOFFILE
```

Create `src/pubsub_consumer.py`:

**What `src/pubsub_consumer.py` does and why it exists:**
- **What it does:** Subscribes to the Pub/Sub topic, receives each delivery event message, decodes it, processes it, and acknowledges it so Pub/Sub knows not to re-deliver it
- **Why separate:** The consumer only *reads* — it is completely independent of how or when events were published; a separate file means you can run multiple consumers (for analytics, alerts, storage) against the same topic without touching the producer
- **Input:** `delivery-events` Google Pub/Sub topic (JSON messages published by `pubsub_producer.py`)
- **Output:** Decoded delivery events printed to terminal; in production, each event would be inserted as a row into a BigQuery table in real time
- **Pipeline position:** `delivery-events` Pub/Sub topic (fed by `src/pubsub_producer.py`) → **this script** → processed event output (printed, or written to BigQuery in a production version)

Run this command in Codespaces to create the file:

```bash
cat > src/pubsub_consumer.py << 'ENDOFFILE'
from google.cloud import pubsub_v1  # Pub/Sub client library
import json  # parse JSON bytes back to a Python dict
import os  # read environment variables

PROJECT_ID       = os.environ["GCP_PROJECT_ID"]  # read project ID from environment
TOPIC_ID         = "delivery-events"  # topic name to subscribe to
SUBSCRIPTION_ID  = "delivery-analytics-sub"  # subscription name (each subscriber has its own)

subscriber       = pubsub_v1.SubscriberClient()  # create authenticated subscriber client
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)  # full resource path

# Create subscription if needed
try:
    topic_path = f"projects/{PROJECT_ID}/topics/{TOPIC_ID}"  # full topic path string
    subscriber.create_subscription(
        request={"name": subscription_path, "topic": topic_path}  # link subscription to topic
    )
    print(f"Created subscription: {subscription_path}")
except Exception:  # subscription already exists — continue
    print(f"Subscription already exists: {subscription_path}")

# callback is a function passed as an argument to subscriber.subscribe()
# Pub/Sub calls this function automatically whenever a new message arrives
# you do not call callback() yourself — the subscriber library calls it for you
def callback(message):  # called automatically for each message received
    # message.data is bytes; .decode("utf-8") converts bytes → string
    # json.loads() converts the JSON string → Python dict so you can use ['city'] etc.
    event = json.loads(message.data.decode("utf-8"))  # bytes → string → Python dict
    print(f"  Received: {event['city']} | {event['status']} | {event['timestamp']}")
    # message.ack() = "I have processed this message successfully"
    # without ack(), Pub/Sub re-delivers the message after a timeout (it assumes failure)
    message.ack()   # acknowledge — tells Pub/Sub this message was processed

print("Listening for messages...")
# subscriber.subscribe() starts a background thread that listens for messages
# callback=callback passes your function so the library knows what to call per message
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)  # start listening

try:
    # .result(timeout=30) = wait here for up to 30 seconds
    # if no messages arrive within 30s, a TimeoutError is raised → caught by except below
    streaming_pull_future.result(timeout=30)  # listen for up to 30 seconds then stop
except Exception:
    # .cancel() tells the background thread to stop pulling messages and clean up
    streaming_pull_future.cancel()  # cleanly stop the streaming pull
    print("Done.")
ENDOFFILE
```

Run producer then consumer in two terminals:
```bash
python src/pubsub_producer.py  # publish 20 events to Pub/Sub
python src/pubsub_consumer.py  # receive and print those events
```

**Why this is the same concept as Kafka:**
- You publish events; subscribers consume them independently
- `message.ack()` is the equivalent of Kafka's offset commit — it tells the system you have processed the message
- The core pattern is identical
- The difference is operational: Kafka you manage yourself (or use Confluent Cloud), Pub/Sub is fully managed by Google with zero infrastructure to maintain

---

## Step 11.10 — Run the same SQL in BigQuery

Go to console.cloud.google.com → BigQuery → SQL workspace.

Paste this — it is identical to Guide 03's Query 2:

```sql
SELECT
    delivery_window,  -- group by morning/afternoon/evening/night
    COUNT(*)                                      AS total_attempts,  -- total rows per window
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_pct  -- avg of 0/1 = success rate %
FROM `your-project-id.delivery_raw.deliveries`  -- backtick syntax = project.dataset.table in BQ
GROUP BY delivery_window  -- one row per delivery window
ORDER BY fadr_pct ASC;  -- lowest FADR first (worst performing windows at top)
```

**This is the same SQL you already wrote.**
- The only change is the table name includes the project and dataset
- Every analytical skill from Guide 03 transfers here directly

---

## Step 11.11 — Point dbt at BigQuery

Install the BigQuery adapter for dbt:

```bash
pip install dbt-bigquery==1.8.0  # BigQuery adapter plugin for dbt
```

Edit `~/.dbt/profiles.yml` — add a BigQuery target:

**Note on `~` (tilde):**
- The `~` symbol means your home directory — on Windows this is `C:/Users/YourName/`
- So `~/.dbt/profiles.yml` means `C:/Users/YourName/.dbt/profiles.yml`

Add the BigQuery target to `~/.dbt/profiles.yml`. Open it with:
```bash
cat ~/.dbt/profiles.yml  # view current contents first
```
Then append the bigquery section using:
```bash
cat >> ~/.dbt/profiles.yml << 'ENDOFFILE'
ENDOFFILE
```
Or edit directly — add the following under the existing `outputs:` block:

```yaml
delivery_dbt:  # project name — must match name in dbt_project.yml
  target: dev  # default target when you run dbt without --target flag
  outputs:
    dev:
      type: sqlite          # keep local dev pointing to SQLite
      ...
    bigquery:  # new target — use with: dbt run --target bigquery
      type: bigquery  # tells dbt to use the BigQuery adapter
      method: oauth         # uses the gcloud credentials you set up in Step 12.3
      project: your-project-id  # your GCP project ID
      dataset: delivery_marts  # BigQuery dataset where dbt creates tables
      location: asia-south1  # Mumbai region — data stored here
      threads: 4  # run up to 4 dbt models in parallel
```

Run dbt against BigQuery:

```bash
cd delivery_dbt  # move into the dbt project folder
python -c "import sys; sys.argv=['dbt','run','--target','bigquery']; import dbt.main; dbt.main.main()"
python -c "import sys; sys.argv=['dbt','test','--target','bigquery']; import dbt.main; dbt.main.main()"
```

**What just happened:**
- The exact same SQL models from Guide 04 — `stg_deliveries`, `mart_fadr_by_segment`, `mart_window_analysis` — now ran inside BigQuery
- They created tables in the `delivery_marts` dataset
- dbt handled the translation
- You changed one flag, not the models

---

## Step 11.12 — Key BigQuery concepts for interviews

| Concept | What it is | Why it comes up |
|---|---|---|
| Serverless warehouse | No servers to manage — BigQuery handles all infrastructure | Explains why companies choose it over self-managed Postgres |
| Columnar storage | Data stored by column, not row — queries that read 2 columns out of 50 only scan those 2 | Why BigQuery is fast on analytical queries |
| Partitioning | Like Parquet partitioning in Guide 05 — divide a table by date or a column so queries skip irrelevant partitions | "How do you optimise a slow BigQuery query?" |
| Clustering | Sort data within a partition by a column — further reduces scan size | Goes alongside partitioning in optimisation questions |
| Slots | Unit of compute BigQuery allocates to a query | Relevant for cost control at scale |
| Dataset | Container for tables — like a schema in Postgres | First thing you create before loading any data |

---

## Common interview question

**"How would you migrate this pipeline from SQLite to BigQuery?"**

- "The SQL doesn't change — BigQuery is ANSI SQL compliant"
- "The dbt models don't change either — you change one line in profiles.yml to point to the BigQuery adapter"
- "The ingestion layer changes: instead of `df.to_sql()` with SQLAlchemy, you use the BigQuery Python client's `load_table_from_dataframe`"
- "The Airflow DAG gets a `BigQueryOperator` replacing the `BashOperator` for dbt"
- "For performance, I'd partition the deliveries table by `attempt_date` and cluster by `city` — that way queries filtering by city or date range skip most of the table"

---

## Step 11.13 — Other GCP services this project touches

- You do not need to implement all of these, but knowing where they fit is interview-relevant

| GCP Service | Where it fits in this project |
|---|---|
| **Cloud Storage (GCS)** | Landing zone for raw CSV files before loading to BigQuery — replaces `data/raw/` folder |
| **Dataflow** | Managed Apache Beam service — the GCP-native alternative to running PySpark yourself |
| **Dataproc** | Managed Spark/Hadoop clusters — run your Guide 05 PySpark code without managing servers |
| **Pub/Sub** | GCP's managed Kafka equivalent — the Guide 07 Kafka producer/consumer maps directly to Pub/Sub |
| **Cloud Composer** | Managed Airflow — the Guide 06 DAG (Directed Acyclic Graph) runs here instead of your local machine |

- Every tool in Guides 05–07 has a GCP managed equivalent
- The concepts transfer; the managed service removes the operational burden

---

## Step 11.14 — Commit

```bash
git add src/load_to_bigquery.py src/pubsub_producer.py src/pubsub_consumer.py  # stage the 3 new files
git commit -m "Add GCS landing zone, BigQuery optimisation, Pub/Sub streaming on GCP"  # save snapshot
```

---

## Checkpoint

You now have:
- Data loaded into BigQuery from Python
- The same SQL queries running on GCP infrastructure
- dbt models deployed to BigQuery with one flag change
- Understanding of the full GCP data stack and where each service fits

---

## Git Checkpoint — End of Guide 11

- This is the full Git workflow you do at the end of every guide
- In a real office this is called "raising a PR (Pull Request)"
- You will do this 13 times — by the third time it feels automatic

---

### Step G3 — Check what changed

```bash
git status  # show modified and untracked files before staging
```
**What to look for:**
- Files listed in red under "Changes not staged for commit" — these are files you modified
- Files in red under "Untracked files" — these are new files Git has never seen before
- Nothing should be green yet — you have not staged anything

**In an office:**
- Before staging anything, always read `git status` first
- It shows you exactly what you are about to commit
- Committing blindly is how secrets (passwords, API keys) accidentally get pushed to GitHub

---

### Step G4 — Review your changes line by line

```bash
git diff  # show exact lines added/removed before staging
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
git add src/load_to_bigquery.py  # stage the BigQuery loader script
git add src/upload_to_gcs.py  # stage the GCS uploader script
git add src/pubsub_producer.py  # stage the Pub/Sub publisher script
git add src/pubsub_consumer.py  # stage the Pub/Sub subscriber script
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
git diff --staged  # show diff of only staged files (what will be committed)
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
git commit -m "Guide 11: BigQuery ingestion, GCS landing zone, BQ partitioning, Pub/Sub streaming"  # save snapshot
```
**What a commit is:**
- A permanent snapshot saved in Git's history
- Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`)
- You can always return to this exact state

**What makes a good commit message:**
- Good: `"Guide 11: BigQuery ingestion, GCS landing zone, BQ partitioning, Pub/Sub streaming"`
- Bad: `"done"`, `"update"`, `"changes"`
- Rule: your future self reading this 3 months later should know exactly what changed without looking at the code

---

### Step G8 — Check your commit was saved

```bash
git log --oneline  # list all commits one line each; newest at top
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
j6h3c4i Guide 11: BigQuery ingestion, GCS landing zone, BQ partitioning, Pub/Sub streaming
i5g2b3h Guide 10: Streamlit dashboard with FADR analysis, heatmap, and business impact calculator
9b2c3d1 Initial commit: project guides and README
```

**In an office:**
- `git log --oneline` is one of the most used commands
- It gives you the full history of the branch at a glance

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-11-bigquery  # upload commits; -u links branch to GitHub
```
**What `git push` does:**
- Uploads your local commits to GitHub
- Until you push, your commit only exists on your laptop

**What `-u` means:**
- Sets the upstream — links your local branch to a branch of the same name on GitHub
- You only need `-u` the first time you push a new branch; after that, just `git push` is enough

**What `origin` means:**
- The name of your GitHub remote
- When you ran `git remote add origin ...` in Guide 00B, you named it `origin`; that name sticks

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-11-bigquery had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-11-bigquery` ← what you are merging in
3. Title: `Guide 11: GCP stack - BigQuery, GCS, Pub/Sub`
4. Description: 1-2 lines about what this guide added
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
git checkout develop  # switch back to develop (no -b, it already exists)
```
- Switches you back to develop
- No `-b` here — `develop` already exists, you are just switching to it

```bash
git pull origin develop  # download merged changes from GitHub into local develop
```
- Downloads the merged PR from GitHub into your local develop
- Your local develop now has everything from the feature branch you just merged

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub
- `pull` — download + merge in one step (it runs `git fetch` then `git merge` automatically)

```bash
git log --oneline  # confirm Guide 11 commit now appears in develop history
```
- You should now see your Guide 11 commit in develop's history
- Confirm it is there

**What `--oneline` means:** Show one line per commit instead of the full multi-line format.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-11-bigquery  # -d = delete local branch safely (refuses if unmerged)
```
**What `-d` means:**
- Delete the branch locally
- Git will refuse to delete if the branch has unmerged commits — a safety guard
- Since you just merged the PR, `-d` works
- Use `-D` (capital D) only if you want to force-delete without merging

```bash
git push origin --delete feature/guide-11-bigquery  # delete the branch on GitHub too
```
- Deletes the branch on GitHub too

**What each part means:**
- `origin` — push this action to GitHub (not just locally)
- `--delete` — delete the named branch on GitHub

**Why delete?**
- Merged branches are dead branches
- Keeping them clutters the repository
- In real teams, merged branches are always deleted
- A clean repo = a professional habit

**Note — good point to promote to main:** The full local pipeline is now complete. Merge to main as a milestone:
```bash
git checkout main  # switch to main branch
git merge develop  # bring all develop commits into main
git push origin main  # upload updated main to GitHub
git checkout develop  # switch back to develop for next guide
```

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-12-cicd  # -b = create new branch and switch to it
```

**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

- You are now on a fresh branch, ready for the next guide

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 11 commit is in the history
- **Branches** → feature/guide-11-bigquery is gone (deleted)

- This is exactly what a professional Git history looks like

**Next:** [GUIDE_12_CICD.md](GUIDE_12_CICD.md) — Automate testing and deployment with GitHub Actions
