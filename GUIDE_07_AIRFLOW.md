# Guide 07 — Pipeline Orchestration with Apache Airflow

**Goal:** Use Apache Airflow to schedule and monitor the full pipeline: generate data → ingest → transform → test data quality → export. Airflow is the most widely used orchestration tool in data engineering.

---

## Why Airflow?

- A data pipeline that only runs when you manually type a command is not a production pipeline
- Airflow schedules pipelines to run automatically, handles failures, retries failed steps, sends alerts, and gives you a visual map of every pipeline run
- It is on almost every data engineering job description
- Understanding DAGs (Directed Acyclic Graphs) is essential

---

## What is a DAG?

**What a DAG is in plain terms:**
- A DAG (Directed Acyclic Graph) is simply a pipeline where each step is a "task," tasks run in a defined order (directed), and there are no loops — it always moves forward (acyclic)
- In Airflow, the whole pipeline is defined as a DAG: a Python file that lists tasks and says which one must finish before the next one starts

**What a task is vs a DAG:**
- A DAG is the whole pipeline
- A task is one individual step inside that pipeline — for example "run the data generation script" is one task, "run transformations" is another
- Each task is a discrete, named, retryable unit of work

A DAG is a pipeline definition. It has:
- **Tasks**: individual steps (run a script, run SQL, call an API)
- **Dependencies**: which task must finish before the next one starts
- **Schedule**: when to run (daily, hourly, on demand)
- **No cycles**: tasks flow in one direction only — no loops

Your pipeline DAG looks like:

```
generate_data_py → ingest_py → dbt_run_transformations → dbt_test_data_quality → export_mart_py
```

---

## Git — Before You Start This Guide

Every guide begins the same way in a real office: you make sure you are on the right branch and it is up to date before touching any files.

### Step G1 — Make sure you are on develop and it is current

```bash
git checkout develop
```
**What this does:**
- Switches you to the develop branch
- You always create feature branches FROM develop, never from main and never from another feature branch
- No `-b` here — this switches to an existing branch

```bash
git pull origin develop
```
**What this does:**
- Downloads any changes from GitHub that you do not have locally
- `pull` = download + merge in one command
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub

```bash
git status
```
**What this does:**
- Shows the current state
- You should see `On branch develop, nothing to commit, working tree clean`

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-07-airflow
```
**What `-b` means:**
- Create a new branch AND switch to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

Confirm you are on the right branch:
```bash
git branch
```
- You will see a `*` next to your current branch

---

## Why Docker instead of local install

- Airflow does not run on Windows natively — it requires Linux
- WSL2 (Windows Subsystem for Linux) would normally solve this, but company laptops at Air India do not have admin rights to install WSL2
- Docker packages Airflow and all its dependencies into containers — isolated Linux environments that run inside Docker Desktop
- **GitHub Codespaces** is a cloud Linux machine you get free with GitHub — it runs Docker natively and solves the admin rights problem completely
- All Airflow work in this guide runs in Codespaces, not on your local machine

---

## Step 7.0 — Open your project in GitHub Codespaces

- Go to your GitHub repository in the browser
- Click the green **Code** button → **Codespaces** tab → **Create codespace on develop**
- A VS Code window opens in the browser — this is a full Linux machine with Docker already installed
- Your entire project folder is available inside it

---

## Step 7.1 — Create `docker-compose.yml`

**What `docker-compose.yml` is:**
- A configuration file that defines all the services (containers) your project needs
- One file launches Zookeeper, Kafka, Postgres, Airflow Init, Airflow Webserver, and Airflow Scheduler all at once with `docker compose up`
- Without it you would have to run 6+ separate `docker run` commands with many flags — impossible to remember

**What `docker-compose.yml` does and why it exists:**
- **What it does:** Defines 7 services, the network they share, and how they connect to each other
- **Why separate:** Each service (Kafka, Airflow, Postgres) needs different environment variables, ports, and startup commands — keeping them in one file makes the whole stack reproducible on any machine
- **Input:** Your local `dags/`, `src/`, `data/`, and `delivery_dbt/` folders (mounted into containers as volumes)
- **Output:** Running containers accessible from your browser (Airflow on port 8080, Kafka on port 9092)

Create the file `docker-compose.yml` in your project root:

```yaml
services:

  # ── Zookeeper ─────────────────────────────────────────────────────────────
  # → Kafka needs Zookeeper to coordinate its brokers (leader election, config)
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: zookeeper
    networks: [delivery-net]
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181   # port Kafka uses to talk to Zookeeper
      ZOOKEEPER_TICK_TIME: 2000     # heartbeat interval in milliseconds

  # ── Kafka ─────────────────────────────────────────────────────────────────
  # → the message broker: producers write to it, consumers read from it
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: kafka
    networks: [delivery-net]
    depends_on: [zookeeper]         # Kafka cannot start without Zookeeper
    ports:
      - "9092:9092"                 # external port so your Python scripts can connect
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181              # where to find Zookeeper
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092   # hostname other containers use
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1            # 1 broker = 1 replica is enough

  # ── Kafka Setup ───────────────────────────────────────────────────────────
  # → one-shot container that creates the Kafka topic then exits
  kafka-setup:
    image: confluentinc/cp-kafka:7.5.0
    container_name: kafka-setup
    networks: [delivery-net]
    depends_on: [kafka]
    entrypoint: /bin/bash
    command: >-
      -c "echo 'Waiting for Kafka...' &&
      cub kafka-ready -b kafka:9092 1 30 &&
      kafka-topics --create --if-not-exists --bootstrap-server kafka:9092 --topic delivery-events --partitions 3 --replication-factor 1 &&
      echo 'Topic created.'"

  # ── Postgres ──────────────────────────────────────────────────────────────
  # → Airflow stores its metadata (DAG runs, task states) in this database
  postgres:
    image: postgres:15
    container_name: airflow-postgres
    networks: [delivery-net]
    environment:
      POSTGRES_USER: airflow       # database username
      POSTGRES_PASSWORD: airflow   # database password
      POSTGRES_DB: airflow         # database name
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]  # check Postgres is accepting connections
      interval: 5s
      retries: 5

  # ── Airflow Init ──────────────────────────────────────────────────────────
  # → one-shot container: initialises the Airflow database and creates admin user
  # → runs once then exits — webserver waits for it to finish before starting
  airflow-init:
    image: apache/airflow:2.9.2
    container_name: airflow-init
    networks: [delivery-net]
    depends_on:
      postgres:
        condition: service_healthy  # wait until Postgres passes its healthcheck
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    volumes:
      - ./dags:/opt/airflow/dags  # mount your DAG files into the container
    entrypoint: /bin/bash
    command: -c "airflow db init && airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com"

  # ── Airflow Webserver ─────────────────────────────────────────────────────
  airflow-webserver:
    image: apache/airflow:2.9.2
    container_name: airflow-webserver
    networks: [delivery-net]
    depends_on: [airflow-init]
    ports:
      - "8080:8080"               # Airflow UI available at localhost:8080
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__WEBSERVER__SECRET_KEY: delivery-opt-secret
      # → installs these Python packages inside the container on every startup
      # → needed because the base Airflow image does not include faker, pandas, numpy
      _PIP_ADDITIONAL_REQUIREMENTS: "faker pandas numpy dbt-core==1.8.0 dbt-sqlite==1.8.1"
    volumes:
      - ./dags:/opt/airflow/dags          # your DAG files
      - ./src:/opt/airflow/src            # your Python scripts
      - ./data:/opt/airflow/data          # your data files
      - ./delivery_dbt:/opt/airflow/delivery_dbt  # dbt project folder
    command: webserver
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      retries: 5

  # ── Airflow Scheduler ─────────────────────────────────────────────────────
  # → reads DAG files, decides when tasks are due, sends them to the executor
  airflow-scheduler:
    image: apache/airflow:2.9.2
    container_name: airflow-scheduler
    networks: [delivery-net]
    depends_on: [airflow-webserver]
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      # → same packages needed here — the scheduler is the process that actually runs tasks
      _PIP_ADDITIONAL_REQUIREMENTS: "faker pandas numpy dbt-core==1.8.0 dbt-sqlite==1.8.1"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./src:/opt/airflow/src
      - ./data:/opt/airflow/data
      - ./delivery_dbt:/opt/airflow/delivery_dbt  # dbt project folder
    command: scheduler

# ── Shared network ────────────────────────────────────────────────────────
# → all containers join this network so they can reach each other by container_name
networks:
  delivery-net:
    driver: bridge
```

**Key concepts in this file:**

**What `_PIP_ADDITIONAL_REQUIREMENTS` does:**
- The base `apache/airflow:2.9.2` Docker image does not include `faker`, `pandas`, or `numpy`
- This environment variable tells the Airflow container to `pip install` those packages automatically on every startup
- It is set on BOTH `airflow-webserver` and `airflow-scheduler` because the scheduler is the process that actually runs your task code — if packages are only on the webserver the tasks still fail
- This is why the containers take a few minutes to become healthy on first start — they are installing packages

**What `volumes` does:**
- A volume mount shares a folder from your Codespace into the container
- `./dags:/opt/airflow/dags` means: your local `dags/` folder appears inside the container at `/opt/airflow/dags/`
- The Airflow container reads DAG files from `/opt/airflow/dags/` — the volume mount makes your file available there without copying
- Changes you make locally are immediately visible inside the container

**What `depends_on` does:**
- Controls startup order
- `airflow-webserver: depends_on: [airflow-init]` means the webserver will not start until airflow-init has finished creating the database
- Without this, the webserver would crash on startup because the database does not exist yet

**What `healthcheck` does:**
- Defines a command Docker runs periodically to check if the service is ready
- `pg_isready -U airflow` — Postgres is ready when it can accept connections
- Other services wait for `condition: service_healthy` before starting

---

## Step 7.2 — Fix folder permissions in Codespaces

- The Airflow container runs as a non-root user
- When it tries to write files to your mounted `data/` folder, it gets "Permission denied"
- `chmod 777` gives read/write/execute permission to all users — including the container user

Run these in the Codespaces terminal:

```bash
sudo chmod -R 777 data
```
**What each part means:**
- `sudo` — run as superuser (administrator) — needed to change permissions
- `chmod` — change file permissions
- `-R` — recursive: applies to the folder AND everything inside it
- `777` — gives full read/write/execute to owner, group, and everyone else
- `data` — the folder to apply this to

```bash
mkdir -p data/processed
```
**What each part means:**
- `mkdir` — make directory
- `-p` — create parent folders too if they do not exist; no error if folder already exists
- `data/processed` — the folder path to create
- This folder is where `export_mart_py` saves the output CSV

```bash
sudo chmod -R 777 data
```
Run chmod again after creating the new folder so the container can write into `data/processed/` too.

---

## Step 7.3 — Create `dags/delivery_pipeline.py`

**What `dags/delivery_pipeline.py` does and why it exists:**
- **What it does:** Defines the entire pipeline as an Airflow DAG — telling Airflow which scripts to run, in what order, on what schedule, and what to do if a step fails
- **Why separate:** Without this file, the pipeline only runs when you manually type commands in a terminal. This file is what makes it automated — Airflow reads it, registers the schedule, and takes over running everything for you
- **Input:** Schedule trigger (Airflow fires this DAG daily at midnight via `schedule_interval='@daily'`, or manually from the Airflow UI)
- **Output:** Runs all five pipeline steps in order with task status logged in the Airflow database
- **Pipeline position:** `generate_data.py` → `ingest.py` → SQL transformations → data quality tests → export to `data/processed/fadr_mart.csv`

**Why sqlite3 instead of dbt CLI for transformations:**
- `dbt-sqlite` (the SQLite adapter for dbt) has a known incompatibility with `dbt-core` 1.9 — a macro called `core_overrides.sql` inside dbt-sqlite passes `Undefined` instead of a string to `ref()`, crashing every `dbt run`
- Multiple version combinations were attempted (1.5, 1.7, 1.8, 1.9) — none resolved the macro issue in the Docker container
- The fix: write the same SQL transformations directly in Python using `sqlite3`, Python's built-in database library
- The output is identical — the same tables are created, the same SQL logic runs — but with zero dependency on dbt version compatibility
- This is also realistic: in production, many pipelines run SQL directly via Python rather than through dbt

**Task ID naming convention:**
- Task IDs match the script filenames for easy identification in the Airflow UI
- `generate_data_py` → runs `src/generate_data.py`
- `ingest_py` → runs `src/ingest.py`
- `dbt_run_transformations` → runs the same SQL as `delivery_dbt/models/`
- `dbt_test_data_quality` → runs the same checks as `delivery_dbt/tests/`
- `export_mart_py` → exports mart table to CSV

Create the file `dags/delivery_pipeline.py`:

```python
from datetime import datetime, timedelta  # datetime for start_date; timedelta for delays
from airflow import DAG  # DAG class: defines the whole pipeline
from airflow.operators.python import PythonOperator  # runs a Python function as a task

default_args = {  # default settings applied to every task in this DAG
    'owner': 'daksha',  # who owns this pipeline (shown in Airflow UI)
    'retries': 2,  # retry a failed task up to 2 times before marking it failed
    # timedelta(minutes=5) = a duration object representing exactly 5 minutes
    # → e.g. timedelta(hours=1) = 1 hour wait; timedelta(days=1) = 24-hour wait
    # → used here to say "wait 5 minutes before trying the failed task again"
    'retry_delay': timedelta(minutes=5),  # wait 5 minutes between retries
    'email_on_failure': False,  # don't send email alerts (no email configured)
}

def run_generate():  # Python function Airflow calls for the data generation task
    import subprocess  # lets Python run other programs/scripts
    # subprocess.run(['python', 'src/generate_data.py'], ...) = runs that command in a shell
    # → same as typing: python src/generate_data.py  in your terminal
    # → capture_output=True = capture what the script prints (stdout) and any errors (stderr)
    # → text=True = return stdout/stderr as a Python string, not raw bytes
    result = subprocess.run(['python', 'src/generate_data.py'], capture_output=True, text=True)  # run script; capture stdout+stderr
    print(result.stdout)  # show the script's printed output in Airflow logs
    # result.returncode = the exit code the script returned when it finished
    # → 0 means success (universal convention in all operating systems)
    # → anything else (1, 2, -1 ...) means the script crashed or reported an error
    if result.returncode != 0:  # non-zero code = script crashed
        raise Exception(f"Data generation failed: {result.stderr}")  # fail the task with error detail

def run_ingest():  # Python function Airflow calls for the ingest task
    import subprocess  # lets Python run other programs/scripts
    # Same pattern as run_generate above:
    # → runs 'python src/ingest.py' as a subprocess; captures its printed output and errors
    result = subprocess.run(['python', 'src/ingest.py'], capture_output=True, text=True)  # run ingest script; capture output
    print(result.stdout)  # show the script's printed output in Airflow logs
    if result.returncode != 0:  # non-zero code = script crashed
        raise Exception(f"Ingestion failed: {result.stderr}")  # fail the task with error detail

def run_dbt_transformations():
    import sqlite3
    conn = sqlite3.connect('/opt/airflow/data/delivery_db.sqlite')
    cur = conn.cursor()

    # stg_deliveries_cleaned — staging model: cleans and casts columns from raw deliveries table
    cur.execute("DROP VIEW IF EXISTS stg_deliveries_cleaned")
    cur.execute("""
        CREATE VIEW stg_deliveries_cleaned AS
        SELECT
            delivery_id, customer_id, city, address_type, delivery_window,
            CAST(order_value AS REAL) AS order_value,
            CAST(is_successful AS INTEGER) AS is_successful,
            failure_reason,
            CAST(attempt_number AS INTEGER) AS attempt_number,
            DATE(attempt_date) AS attempt_date,
            CAST(attempt_hour AS INTEGER) AS attempt_hour,
            CAST(has_delivery_preference AS INTEGER) AS has_delivery_preference,
            CAST(proximity_alert_sent AS INTEGER) AS proximity_alert_sent
        FROM deliveries
        WHERE delivery_id IS NOT NULL
    """)

    # mart_fadr_by_city_and_address — FADR (First Attempt Delivery Rate) breakdown by city and address type
    cur.execute("DROP TABLE IF EXISTS mart_fadr_by_city_and_address")
    cur.execute("""
        CREATE TABLE mart_fadr_by_city_and_address AS
        SELECT
            city, address_type,
            COUNT(*) AS total_attempts,
            SUM(is_successful) AS successful_deliveries,
            ROUND(AVG(is_successful), 4) AS fadr,
            ROUND(AVG(1 - is_successful), 4) AS failure_rate,
            AVG(order_value) AS avg_order_value
        FROM stg_deliveries_cleaned
        GROUP BY city, address_type
    """)

    # mart_fadr_by_window_and_alerts — FADR by delivery window and alert settings
    cur.execute("DROP TABLE IF EXISTS mart_fadr_by_window_and_alerts")
    cur.execute("""
        CREATE TABLE mart_fadr_by_window_and_alerts AS
        SELECT
            delivery_window, address_type, has_delivery_preference, proximity_alert_sent,
            COUNT(*) AS total_attempts,
            ROUND(AVG(is_successful), 4) AS fadr
        FROM stg_deliveries_cleaned
        GROUP BY delivery_window, address_type, has_delivery_preference, proximity_alert_sent
        HAVING total_attempts > 50
    """)

    conn.commit()
    conn.close()
    print("dbt transformations completed: stg_deliveries_cleaned, mart_fadr_by_city_and_address, mart_fadr_by_window_and_alerts")


def run_dbt_tests():
    import sqlite3
    conn = sqlite3.connect('/opt/airflow/data/delivery_db.sqlite')
    cur = conn.cursor()

    # Test 1: no NULL delivery_ids in staging
    cur.execute("SELECT COUNT(*) FROM stg_deliveries_cleaned WHERE delivery_id IS NULL")
    nulls = cur.fetchone()[0]
    assert nulls == 0, f"Test failed: {nulls} NULL delivery_ids in stg_deliveries_cleaned"

    # Test 2: is_successful only contains 0 or 1
    cur.execute("SELECT COUNT(*) FROM stg_deliveries_cleaned WHERE is_successful NOT IN (0, 1)")
    bad = cur.fetchone()[0]
    assert bad == 0, f"Test failed: {bad} invalid is_successful values"

    # Test 3: mart tables exist and have rows
    cur.execute("SELECT COUNT(*) FROM mart_fadr_by_city_and_address")
    rows = cur.fetchone()[0]
    assert rows > 0, "Test failed: mart_fadr_by_city_and_address is empty"

    conn.close()
    print("All dbt tests passed")


def run_export():  # Python function Airflow calls for the CSV export task
    import sqlite3  # built-in Python library for SQLite databases
    import pandas as pd  # pandas for reading SQL results into a dataframe
    conn = sqlite3.connect('/opt/airflow/data/delivery_db.sqlite')  # open the project database
    # pd.read_sql(sql, conn) = runs the SQL query and returns the results as a pandas DataFrame
    # → a DataFrame is a table of rows and columns you can work with in Python
    df = pd.read_sql("SELECT * FROM mart_fadr_by_city_and_address", conn)  # load the mart table into a dataframe
    # df.to_csv('path', index=False) = write the DataFrame to a CSV file
    # → index=False = do NOT write the row numbers (0, 1, 2...) as an extra column in the file
    # → without index=False the CSV gets an unwanted first column: 0, 1, 2, 3 ...
    df.to_csv('/opt/airflow/data/processed/fadr_mart.csv', index=False)  # save as CSV; index=False skips row numbers
    conn.close()  # always close DB connections to free resources
    print(f"Exported {len(df)} rows to data/processed/fadr_mart.csv")  # log the export count

# 'with DAG(...) as dag:' is a Python context manager
# → everything indented inside this block is part of this pipeline definition
# → 'as dag' assigns the created DAG object to the variable name 'dag'
with DAG(  # 'with DAG() as dag:' creates the pipeline definition object
    dag_id='delivery_optimisation_pipeline',  # unique pipeline name shown in Airflow UI
    # default_args = the dict you defined above; Airflow applies every key in it to all tasks
    # → so every task in this DAG automatically gets retries=2, retry_delay=5min, etc.
    # → you can still override these on individual tasks if needed
    default_args=default_args,  # apply the defaults dict defined above
    description='End-to-end delivery FADR pipeline',  # description shown in Airflow UI
    schedule_interval='@daily',          # runs every day at midnight
    # What @daily means: a shorthand schedule meaning "run once every day at
    # midnight." Airflow also supports cron expressions like '0 6 * * *' (6am daily)
    # for more precise scheduling.
    # datetime(2024, 1, 1) = creates a date object for January 1st 2024
    # → datetime(year, month, day): the pipeline will not schedule any run before this date
    start_date=datetime(2024, 1, 1),  # pipeline will not run before this date
    catchup=False,  # don't backfill missed runs from start_date to today
    # What catchup=False means: if a DAG has a start_date in the past, Airflow
    # would normally "catch up" by running a separate job for every missed day.
    # catchup=False tells Airflow to skip the historical backfill and only run
    # from now forward — which is what you want for a new pipeline.
    tags=['delivery', 'fadr', 'logistics'],  # labels for filtering in Airflow UI
) as dag:  # 'as dag' assigns the pipeline object to the variable 'dag'

    # What PythonOperator is: a task that runs a Python function you define.
    # You pass python_callable=your_function and Airflow calls it when the task executes.
    t1_generate = PythonOperator(  # task 1: generate raw delivery data
        task_id='generate_data_py',  # matches src/generate_data.py
        python_callable=run_generate,  # the function to call when this task runs
    )

    t2_ingest = PythonOperator(  # task 2: ingest data to SQLite database
        task_id='ingest_py',  # matches src/ingest.py
        python_callable=run_ingest,  # the function to call when this task runs
    )

    # PythonOperator runs the SQL transformations directly in Python using sqlite3
    # — avoids dbt version compatibility issues in the Docker container
    t3_dbt = PythonOperator(  # task 3: run dbt-equivalent SQL transformations
        task_id='dbt_run_transformations',
        python_callable=run_dbt_transformations,
    )

    t4_test = PythonOperator(  # task 4: run data quality tests
        task_id='dbt_test_data_quality',
        python_callable=run_dbt_tests,
    )

    t5_export = PythonOperator(  # task 5: export the mart table to CSV
        task_id='export_mart_py',  # matches src/export_mart.py (runs inline export function)
        python_callable=run_export,  # the function to call when this task runs
    )

    # What >> means: the "bit shift right" operator in Airflow sets dependencies.
    # t1 >> t2 means "t2 must not start until t1 finishes successfully."
    # This chain means each task waits for the previous one to complete.
    # → t1_generate >> t2_ingest = t2 waits for t1 to succeed
    # → t2_ingest >> t3_dbt      = t3 waits for t2 to succeed
    # → you can chain as many as you like: A >> B >> C >> D >> E
    # → if t2 fails, t3, t4, and t5 are all skipped automatically
    t1_generate >> t2_ingest >> t3_dbt >> t4_test >> t5_export  # run tasks in this exact order
```

---

## Step 7.4 — Start the containers in Codespaces

In the Codespaces terminal:

```bash
docker compose up -d
```
**What each part means:**
- `docker compose` — Docker Compose CLI tool, reads `docker-compose.yml`
- `up` — start all services defined in the file
- `-d` — detached mode: runs containers in the background, gives you the terminal back

Wait about 2 minutes for the containers to start and install pip packages. Check status:

```bash
docker ps
```
**What to look for:**
- All containers should show `(healthy)` or `Up` in the STATUS column
- `airflow-webserver` and `airflow-scheduler` will take longer — they are installing `faker`, `pandas`, `numpy` via `_PIP_ADDITIONAL_REQUIREMENTS`
- Do not open the UI until you see `(healthy)` next to `airflow-webserver`

---

## Step 7.5 — Open the Airflow UI in Codespaces

- Codespaces does not expose container ports the same way as `localhost`
- In the Codespaces terminal, click the **PORTS** tab at the bottom
- Find port `8080` in the list
- Right-click it → **Port Visibility** → **Public** (required for the browser to open it)
- Click the globe icon next to port `8080` to open the Airflow UI in your browser

Login credentials:
- Username: `admin`
- Password: `admin`

---

## Step 7.6 — Trigger a manual run

In the Airflow UI:
1. Find `delivery_optimisation_pipeline` in the DAG list
2. Click the **▶** (play) button on the right → **Trigger DAG**
3. Click the DAG name to open the Graph view
4. Watch each task turn dark green as it succeeds

**What the colours mean:**
- Light green / running = task is currently executing
- Dark green = task succeeded
- Red = task failed (click it → **Log** to see the error)
- Grey = task is waiting for an upstream task to finish

---

## Step 7.7 — Understanding what you built

| Concept | What you did |
|---|---|
| DAG | Defined the pipeline as code in Python |
| Task | Each step is a discrete, named, retryable unit |
| Dependencies | `>>` operator sets execution order |
| Schedule | `@daily` means this runs automatically every day |
| Retry logic | `retries: 2` means failed tasks retry twice before alerting |
| Docker | Containerised Airflow so it runs anywhere without admin rights |
| `_PIP_ADDITIONAL_REQUIREMENTS` | Installs missing Python packages inside the container on startup |
| Volume mounts | Shares your local code and data folders with the containers |
| sqlite3 instead of dbt CLI | Avoids dbt-sqlite version incompatibility in Docker |

---

## Step 7.8 — Commit

```bash
git add dags/delivery_pipeline.py docker-compose.yml delivery_dbt/profiles.yml
git add -u delivery_dbt/macros/
git commit -m "Guide 07: Airflow DAG with Docker, all 5 tasks passing via sqlite3"
```

---

## Checkpoint

You now have:
- A full scheduled pipeline that runs daily
- Visual monitoring of every task
- Automatic retries on failure
- Version-controlled pipeline code
- Docker stack that reproduces the entire environment with one command

---

## Git Checkpoint — End of Guide 07

- This is the full Git workflow you do at the end of every guide
- In a real office this is called "raising a PR (Pull Request)"

### Step G3 — Check what changed

```bash
git status
```
**What to look for:**
- Files listed in red under "Changes not staged for commit" — these are files you modified
- Files in red under "Untracked files" — these are new files Git has never seen before
- Nothing should be green yet — you have not staged anything

### Step G4 — Review your changes line by line

```bash
git diff
```
**What this shows:**
- The exact lines you added (in green with `+`) and deleted (in red with `-`) in every modified file
- This is your chance to review your own work before anyone else sees it

Press `q` to exit the diff view.

### Step G5 — Stage your files

```bash
git add dags/delivery_pipeline.py docker-compose.yml delivery_dbt/profiles.yml
git add -u delivery_dbt/macros/
```
**What `-u` means on git add:**
- `-u` stages modifications AND deletions of already-tracked files
- Needed here because `delivery_dbt/macros/core_overrides.sql` was deleted — plain `git add` only adds new or modified files

### Step G6 — Verify what is staged

```bash
git diff --staged
```
**The difference between `git diff` and `git diff --staged`:**
- `git diff` → shows unstaged changes (what you changed but have NOT added yet)
- `git diff --staged` → shows staged changes (what you HAVE added, about to commit)

Press `q` to exit.

### Step G7 — Commit

```bash
git commit -m "Guide 07: Airflow DAG with Docker, all 5 tasks passing via sqlite3"
```
**What makes a good commit message:**
- Good: `"Guide 07: Airflow DAG with Docker, all 5 tasks passing via sqlite3"`
- Bad: `"done"`, `"update"`, `"changes"`
- Rule: your future self reading this 3 months later should know exactly what changed

### Step G8 — Check your commit was saved

```bash
git log --oneline
```
**What this shows:**
- All commits on this branch, one line each
- The most recent is at the top

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-07-airflow
```
**What `-u` means:**
- Sets the upstream — links your local branch to a branch of the same name on GitHub
- You only need `-u` the first time you push a new branch

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-07-airflow had recent pushes"**

### Step G10 — Raise a Pull Request on GitHub

**PR title:** `Guide 07: Airflow pipeline orchestration with Docker`

**PR description:**
```
- Added docker-compose.yml with 7 services: Zookeeper, Kafka, Postgres, Airflow Init, Webserver, Scheduler, Kafka Setup
- Created dags/delivery_pipeline.py with 5 PythonOperator tasks
- Used sqlite3 instead of dbt CLI to avoid dbt-sqlite version incompatibility in Docker
- All 5 tasks passing in GitHub Codespaces: generate_data_py → ingest_py → dbt_run_transformations → dbt_test_data_quality → export_mart_py
```

Steps in GitHub:
1. Click **Compare & pull request** in the yellow banner
2. Check: **base:** `develop` ← **compare:** `feature/guide-07-airflow`
3. Paste the title and description above
4. Click **Create pull request**
5. Click **Merge pull request** → **Confirm merge**

### Step G11 — Pull the merged changes back locally

```bash
git checkout develop
```
```bash
git pull origin develop
```
```bash
git log --oneline
```
- You should now see your Guide 07 commit in develop's history

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-07-airflow
```
**What `-d` means:**
- Delete the branch locally
- Git will refuse to delete if the branch has unmerged commits — a safety guard

```bash
git push origin --delete feature/guide-07-airflow
```
- Deletes the branch on GitHub too
- Merged branches are dead branches — a clean repo is a professional habit

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-08-kafka
```

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR: `Guide 07: Airflow pipeline orchestration with Docker`
- **develop branch → commits** → your Guide 07 commit is in the history
- **Branches** → `feature/guide-07-airflow` is gone (deleted)

**Next:** [GUIDE_08_KAFKA.md](GUIDE_08_KAFKA.md) — Handle real-time delivery events with Apache Kafka
