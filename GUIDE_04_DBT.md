# Guide 04 — Data Transformation with dbt

**Goal:** Use dbt (data build tool) to turn raw data into clean, documented, testable analytical models. dbt is the industry-standard tool for the transformation layer.

---

## Why dbt?

**What dbt is:**
- dbt (data build tool) is a transformation tool — it is not a database
- It takes SQL (Structured Query Language) files you write and runs them against whatever database you are connected to (SQLite locally, BigQuery in production)
- Think of it as a way to organise, version-control, and test all your SQL transformations in one place, with automatic dependency ordering

**What YAML is:**
- YAML is a plain-text format for writing configuration — it uses indentation (spaces) to show structure instead of brackets or braces
- dbt uses YAML files to define tests, descriptions, and settings
- Every line of YAML you will write follows the same simple pattern: `key: value`

Raw data is messy. dbt lets you:
- Write SQL transformations as `.sql` files (version controlled, reviewable)
- Add tests to guarantee data quality (e.g. "FADR (First Attempt Delivery Rate) must be between 0 and 1")
- Auto-generate documentation for every table and column
- Build a dependency graph of all your data models

- Every modern data team uses dbt
- It appears on almost every data engineering job description

---

## Git — Before You Start This Guide

Every guide begins the same way in a real office: you make sure you are on the right branch and it is up to date before touching any files.

### Step G1 — Make sure you are on develop and it is current

```bash
git checkout develop  # switch to develop (no -b, branch already exists)
```
**What this does:**
- Switches you to the develop branch
- You always create feature branches FROM develop, never from main and never from another feature branch

- No `-b` here — this switches to an existing branch
- You do not use `-b` when the branch already exists

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
git status  # show all changed, new, and staged files
```
**What this does:**
- Shows the current state
- You should see `On branch develop, nothing to commit, working tree clean`
- If you see modified files here, deal with them before moving forward — do not carry unrelated changes into a new branch

No flags here — `git status` always shows full current state.

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-04-dbt  # -b = create new branch and switch to it
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
git branch  # list all branches; * marks your current branch
```
- You will see a `*` next to your current branch
- That `*` means "you are here"

---

## Step 4.1 — Initialise a dbt project

```python
python -c "
import os
from dbt.cli.main import dbtRunner
dbtRunner().invoke(['init', 'delivery_dbt'])
"
```

**Note:**
- `dbt.exe` is blocked by IT policy on this machine
- `dbt.main` no longer exists in dbt 1.5+; the new API is `dbt.cli.main.dbtRunner`
- This command runs dbt directly through Python and works identically

When prompted:
- Enter project name: `delivery_dbt`
- Select database: `sqlite` (option will appear if dbt-sqlite is installed)

Then move into the project:
```bash
cd delivery_dbt  # move into the newly created project folder
```

---

## Step 4.2 — Configure `profiles.yml`

**What `profiles.yml` is and why it exists:**
- Tells dbt how to connect to your database (database type, file path, which environment to use)
- Lives in `~/.dbt/` (your home directory, `C:\Users\YourName\.dbt\`) — NOT inside the project folder
- Kept outside the project so passwords and API keys are never accidentally committed to Git
- dbt reads it on every `dbt run` or `dbt test` to know where to execute your SQL models
- `~` (tilde) means home directory on all platforms — `~/.dbt/profiles.yml` = `C:\Users\YourName\.dbt\profiles.yml`

**Note on `~` (tilde):** The `~` symbol means your home directory — on Windows this is `C:/Users/YourName/`.

**How to create this file:**
**In PowerShell (VS Code terminal):**
```powershell
mkdir "$HOME\.dbt" -ErrorAction SilentlyContinue
notepad "$HOME\.dbt\profiles.yml"
```

**In Git Bash:**
```bash
mkdir -p "$HOME/.dbt"
notepad "$HOME/.dbt/profiles.yml"
```

**What this does:**
- Creates the `.dbt` folder in `C:\Users\YourName\.dbt` if it does not exist, then opens `profiles.yml` in Notepad
- `-ErrorAction SilentlyContinue` (PowerShell) and `-p` (Git Bash) both mean "don't error if the folder already exists"

- Notepad will open and ask "Do you want to create a new file?" — click **Yes**
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad

```yaml
delivery_dbt:            # project name — must match dbt_project.yml
  target: dev            # default environment to run dbt against
  outputs:               # define one or more connection environments here
    dev:                 # name of this environment
      type: sqlite       # database engine to connect to
      threads: 1         # parallel threads; 1 = safe for local dev
      database: "../data/delivery_db.sqlite"  # path to SQLite DB file
      schema: main       # schema name to use inside the database
      schemas_and_paths:
        main: "../data/delivery_db.sqlite"  # maps schema "main" to DB file
      schema_directory: "../data"  # folder dbt uses for schema resolution
```

---

## Step 4.3 — Create dbt models

Inside the `delivery_dbt/models/` folder, create these files:

**File: `delivery_dbt/models/staging/stg_deliveries_cleaned.sql`**

**How to create this file:**
```bash
mkdir -p delivery_dbt/models/staging
notepad delivery_dbt/models/staging/stg_deliveries_cleaned.sql
```
- Notepad will open (or ask to create the file — click Yes)
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad

**What `stg_deliveries_cleaned.sql` does and why it exists:**
- **What it does:** Cleans the raw deliveries table — fixes data types (text → numbers), strips timestamps to dates, drops rows with a missing `delivery_id`
- **Why separate:** Raw data can have "NULL" stored as a string, or order_value stored as text. If you run business logic on dirty data, one bad row silently corrupts every metric downstream. The staging layer fixes this once so every model after it can trust what it receives
- **Input:** Raw `deliveries` table in `data/delivery_db.sqlite` (50,000 rows loaded by `ingest.py` in Guide 02)
- **Output:** `stg_deliveries_cleaned` table — same 50,000 rows but with correct data types and missing `delivery_id` rows removed
- **Pipeline position:** raw `deliveries` → **this model** → `mart_fadr_by_city_and_address.sql` and `mart_fadr_by_window_and_alerts.sql`

```sql
-- Staging model: clean and type-cast raw deliveries
-- This is the first layer — we standardise columns but don't add business logic yet
SELECT
    delivery_id,                -- pass through the unique delivery ID unchanged
    customer_id,                -- pass through the customer identifier unchanged
    city,                       -- city of the delivery address
    address_type,               -- Apartment, House, Office, etc.
    delivery_window,            -- time slot: Morning, Afternoon, Evening
    -- CAST(expr AS type): converts a column's data type; CSVs load all columns as text by default
    -- CAST(order_value AS REAL): "134" (text string) → 134.0 (decimal number usable in math)
    CAST(order_value AS REAL)           AS order_value,      -- convert to decimal number
    -- CAST(is_successful AS INTEGER): "1" (text) → 1 (integer; guarantees 0 or 1, not "0"/"1")
    CAST(is_successful AS INTEGER)      AS is_successful,    -- ensure stored as 0 or 1
    failure_reason,             -- why delivery failed (NULL if successful)
    -- CAST(attempt_number AS INTEGER): "2" (text) → 2 (integer; needed for ORDER BY and arithmetic)
    CAST(attempt_number AS INTEGER)     AS attempt_number,   -- which attempt: 1, 2, 3
    -- DATE(attempt_date): strips the time portion from a datetime value
    -- → "2024-01-15 08:32:11" → "2024-01-15" (date string only, no time)
    DATE(attempt_date)                  AS attempt_date,     -- extract date only, drop time
    CAST(attempt_hour AS INTEGER)       AS attempt_hour,     -- hour 0-23 as integer
    CAST(has_delivery_preference AS INTEGER) AS has_delivery_preference, -- 0 or 1
    CAST(proximity_alert_sent AS INTEGER)    AS proximity_alert_sent     -- 0 or 1
FROM {{ source('main', 'deliveries') }} -- raw table defined in raw_deliveries_source_and_tests.yml
-- WHERE filters individual rows BEFORE any grouping or aggregation
-- IS NOT NULL: true if the column has a value; false if the cell is empty/missing (NULL)
WHERE delivery_id IS NOT NULL           -- drop rows that have no delivery ID
-- What {{ source() }} means: this is dbt's way of referencing a raw table that already
-- exists in the database (the one you loaded from CSV in Guide 02). It tells dbt
-- "this table is an external source, not one I built." dbt tracks it in the lineage graph.
```

**File: `delivery_dbt/models/marts/mart_fadr_by_city_and_address.sql`**

**How to create this file:**
```bash
mkdir -p delivery_dbt/models/marts
notepad delivery_dbt/models/marts/mart_fadr_by_city_and_address.sql
```
- Notepad will open (or ask to create the file — click Yes)
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad

**What `mart_fadr_by_city_and_address.sql` does and why it exists:**
- **What it does:** Aggregates cleaned delivery data to calculate FADR, failure rate, and average order value — grouped by city and address type
- **Why separate:** Staging only cleans, it never calculates. Business metrics live in mart models so when the FADR formula changes, there is one place to update it — not dozens of scripts
- **Input:** `stg_deliveries_cleaned` table (cleaned rows from `stg_deliveries_cleaned.sql`)
- **Output:** `mart_fadr_by_city_and_address` table — one row per city + address type combination, with FADR, failure rate, and average order value
- **Pipeline position:** `stg_deliveries_cleaned` → **this model** → Streamlit dashboard (Guide 10) and ML model (Guide 09)

```sql
-- Mart model: FADR aggregated by city and address type
-- This is what the dashboard and ML model will read from
SELECT
    city,                                             -- group output by city
    address_type,                                     -- group output by address type
    -- COUNT(*): counts every row in the group regardless of NULL values
    COUNT(*)                                  AS total_attempts,         -- rows per group
    -- SUM(is_successful): adds up all values; since is_successful is 0 or 1, sum = count of successes
    -- → rows [1, 0, 1, 1, 0] → SUM = 3 (three successful deliveries)
    SUM(is_successful)                        AS successful_deliveries,  -- count of 1s = successes
    -- AVG(is_successful): mean of a 0/1 column = fraction of 1s = success rate
    -- → rows [1, 0, 1, 1, 0] → AVG = 0.6 (60% success rate)
    -- ROUND(value, 4): keep 4 decimal places  → 0.600000 → 0.6000
    ROUND(AVG(is_successful), 4)              AS fadr,         -- avg of 0/1 = success rate
    -- AVG(1 - is_successful): flip 0→1 and 1→0, then average = failure fraction
    -- → rows [1, 0, 1, 1, 0] → (1-is_successful) = [0,1,0,0,1] → AVG = 0.4
    ROUND(AVG(1 - is_successful), 4)          AS failure_rate, -- 1 - fadr = failure rate
    AVG(order_value)                          AS avg_order_value -- mean order value per group
-- What {{ ref() }} means: this is dbt's way of referencing another model you built
-- (rather than a raw source table). dbt uses this to build a dependency graph —
-- it knows stg_deliveries must run before mart_fadr_by_segment.
FROM {{ ref('stg_deliveries_cleaned') }}        -- use the staging model as input
-- GROUP BY collapses all rows with the same combination of values into ONE output row
-- GROUP BY city, address_type: e.g. all "Mumbai" + "Apartment" rows become one aggregated row
GROUP BY city, address_type             -- one output row per city + address type combo
```

**File: `delivery_dbt/models/marts/mart_fadr_by_window_and_alerts.sql`**

**How to create this file:**
```bash
notepad delivery_dbt/models/marts/mart_fadr_by_window_and_alerts.sql
```
- Notepad will open (or ask to create the file — click Yes)
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad

**What `mart_fadr_by_window_and_alerts.sql` does and why it exists:**
- **What it does:** Calculates FADR grouped by delivery time window, address type, whether the customer set a preference, and whether a proximity alert was sent — filtering out groups too small to be statistically meaningful
- **Why separate:** Answers a different business question than `mart_fadr_by_city_and_address` (time-window patterns vs city/address-type patterns); keeping them separate means each can be queried, tested, and updated independently without breaking the other
- **Input:** `stg_deliveries_cleaned` table in `data/delivery_db.sqlite` (cleaned rows produced by `stg_deliveries_cleaned.sql`)
- **Output:** `mart_fadr_by_window_and_alerts` table — one row per delivery window + address type + preference + alert combination, groups with fewer than 50 attempts excluded
- **Pipeline position:** `stg_deliveries_cleaned` → **this model** → Streamlit dashboard (Guide 10) reads this to show which time windows perform best

```sql
-- Mart model: FADR by delivery window and address type combined
SELECT
    delivery_window,          -- Morning, Afternoon, Evening time slot
    address_type,             -- type of delivery location
    has_delivery_preference,  -- 1 = customer set a preferred delivery time
    proximity_alert_sent,     -- 1 = SMS alert sent when courier was nearby
    COUNT(*)                                  AS total_attempts, -- total rows in this group
    ROUND(AVG(is_successful), 4)              AS fadr            -- success rate 0 to 1
FROM {{ ref('stg_deliveries_cleaned') }}  -- use the staging model as input
-- GROUP BY with 4 columns: one output row for every unique combination of all four values
-- e.g. "Morning" + "Apartment" + 1 + 0 becomes its own aggregated row
GROUP BY delivery_window, address_type, has_delivery_preference, proximity_alert_sent
-- HAVING filters OUTPUT ROWS after GROUP BY (WHERE filters input rows before grouping)
-- HAVING total_attempts > 50: discard any group that produced fewer than 50 rows
-- → a group with 3 rows would give an unreliable FADR of 0.33 or 1.00 — not meaningful
HAVING total_attempts > 50  -- only show groups with enough data to be meaningful
```

---

## Step 4.4 — Create dbt source definition

**File: `delivery_dbt/models/staging/raw_deliveries_source_and_tests.yml`**

**How to create this file:**
```bash
notepad delivery_dbt/models/staging/raw_deliveries_source_and_tests.yml
```
- Notepad will open (or ask to create the file — click Yes)
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad

**What `raw_deliveries_source_and_tests.yml` does and why it exists:**
- **What it does:** Formally declares the raw `deliveries` table (loaded from CSV in Guide 02) as an official dbt source, and adds basic data quality tests on the raw table before any transformation runs
- **Why separate:** Without this file dbt has no knowledge the raw table exists — it cannot track it in the lineage graph, cannot run tests on it, and `{{ source('main', 'deliveries') }}` in `stg_deliveries_cleaned.sql` would fail; it also lets dbt warn you if the raw table has not been refreshed recently
- **Input:** None — this is a config file you write by hand to declare an already-existing raw table
- **Output:** None — dbt reads this file at runtime, it produces no output table itself
- **Pipeline position:** raw SQLite `deliveries` table (Guide 02) → **this file registers it** → `stg_deliveries_cleaned.sql` references it via `{{ source() }}`, and `dbt test` runs its quality checks before transformation begins

```yaml
version: 2  # dbt config format version (always 2 for modern dbt)

sources:
  - name: main  # schema name — must match profiles.yml schema: main
    description: Raw delivery data loaded from CSV
    tables:
      - name: deliveries  # raw table name in the database
        description: One row per delivery attempt
        columns:
          - name: delivery_id
            description: Unique identifier for each delivery attempt
            tests:
              - unique      # test: no two rows share the same delivery_id
              - not_null    # test: delivery_id must never be NULL
          - name: is_successful
            description: 1 if delivered, 0 if failed
            tests:
              - not_null    # test: every row must have a value here
              - accepted_values:
                  values: [0, 1]  # test: only 0 or 1 allowed, nothing else
```

---

## Step 4.5 — Add model tests

**What `mart_models_column_tests.yml` is:**
- This YAML file is where you describe your dbt models and add data quality tests
- dbt reads it and automatically generates test queries — for example, checking that a column is never NULL or always within an expected value range
- It also feeds the auto-generated documentation with descriptions for each column

**File: `delivery_dbt/models/marts/mart_models_column_tests.yml`**

**How to create this file:**
```bash
notepad delivery_dbt/models/marts/mart_models_column_tests.yml
```
- Notepad will open (or ask to create the file — click Yes)
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad

**What `mart_models_column_tests.yml` does and why it exists:**
- **What it does:** Describes the mart models (column names, what each means) and wires up automated data quality tests that dbt runs with `dbt test` — for example, checking that `fadr` is never NULL
- **Why separate:** dbt cannot know what your models are supposed to look like just from the SQL; this file is where you state your guarantees — "this column must never be NULL" — so if a future code change breaks them, `dbt test` catches it before the dashboard shows wrong numbers
- **Input:** None — this is a config file you write by hand to describe mart models that already exist
- **Output:** None — dbt reads this file at runtime, it produces no output table itself
- **Pipeline position:** `mart_fadr_by_city_and_address.sql` and `mart_fadr_by_window_and_alerts.sql` produce tables → **this file defines tests on those tables** → `dbt test` auto-generates SQL checks; `dbt docs generate` reads it to build the documentation website

```yaml
version: 2  # dbt config format version (always 2 for modern dbt)

models:
  - name: mart_fadr_by_city_and_address  # must exactly match the .sql file name
    description: FADR aggregated by city and address type segment
    columns:
      - name: fadr
        description: First Attempt Delivery Rate (0 to 1)
        tests:
          - not_null  # test: fadr column must never be NULL
      - name: total_attempts
        description: Number of delivery attempts in this segment
        tests:
          - not_null  # test: total_attempts must never be NULL
```

---

## Step 4.6 — Run dbt

Make sure you are inside the `delivery_dbt` folder first:

```bash
cd "c:\Users\DakshaKurhade\OneDrive - AIR INDIA LIMITED\Desktop\Delivery Optimisation\delivery_dbt"
```

Then run:

```python
python -c "
import os
from dbt.cli.main import dbtRunner
home = os.path.expanduser('~')
dbtRunner().invoke(['run', '--project-dir', '.', '--profiles-dir', home + '/.dbt'])
"
```

**Expected output:**
```
3 of 3 OK created sql view model main.mart_fadr_by_window_and_alerts
PASS=3 WARN=0 ERROR=0 SKIP=0 TOTAL=3
```

**Why run this:**
- This executes all your `.sql` models against the database and creates the output views
- dbt automatically determines the correct order — staging runs first, then marts (because mart models depend on the staging model being ready)
- Without running this, no output tables exist — the mart models are just SQL files, not actual database tables yet
- `dbt.main` no longer exists in dbt 1.5+; the new API is `dbt.cli.main.dbtRunner` — this is why we call it through Python

**What each part means:**
- `python -c "..."` — runs Python code inline from the command line without creating a separate script file
- `import os` — loads Python's built-in module for reading file paths and environment variables
- `os.path.expanduser('~')` — converts `~` into the full home path on your machine (e.g. `C:\Users\DakshaKurhade`)
- `dbtRunner()` — creates a dbt runner using the new dbt 1.5+ programmatic API
- `.invoke(['run', ...])` — tells dbt to execute the `run` command (build all models) with the flags listed
- `--project-dir '.'` — tells dbt the current folder is the project root; dbt looks here for `dbt_project.yml`
- `--profiles-dir home + '/.dbt'` — tells dbt exactly where `profiles.yml` lives; dbt cannot connect to the database without this

---

## Step 4.7 — Run dbt tests

```python
python -c "
import os
from dbt.cli.main import dbtRunner
home = os.path.expanduser('~')
dbtRunner().invoke(['test', '--project-dir', '.', '--profiles-dir', home + '/.dbt'])
"
```

**Expected output:**
```
PASS=6 WARN=0 ERROR=0 SKIP=0 TOTAL=6
```

**Why run this:**
- This runs all the tests you defined in `raw_deliveries_source_and_tests.yml` and `mart_models_column_tests.yml`
- If any test fails — e.g. a NULL in `is_successful` or a duplicate `delivery_id` — you know the data is broken before it reaches the dashboard or ML model
- Running tests after every `dbt run` is a professional standard — it proves your data is trustworthy, not just that the SQL executed without crashing
- Data quality testing is what separates a data pipeline that occasionally produces wrong numbers from one that can be trusted

**What each part means:**
- `dbtRunner().invoke(['test', ...])` — tells dbt to run the `test` command instead of `run`; dbt auto-generates SQL queries from your YAML test definitions and executes them
- `--project-dir '.'` — same as in Step 4.6; tells dbt this folder is the project root
- `--profiles-dir home + '/.dbt'` — same as in Step 4.6; tells dbt where to find the database connection details

---

## Step 4.8 — Generate documentation

```python
python -c "
import os
from dbt.cli.main import dbtRunner
home = os.path.expanduser('~')
dbtRunner().invoke(['docs', 'generate', '--project-dir', '.', '--profiles-dir', home + '/.dbt'])
"
```

Then serve it:

```python
python -c "
import os
from dbt.cli.main import dbtRunner
home = os.path.expanduser('~')
dbtRunner().invoke(['docs', 'serve', '--project-dir', '.', '--profiles-dir', home + '/.dbt'])
"
```

**Why run `docs generate`:**
- dbt reads all your `.sql` files and `.yml` description files and compiles them into a static documentation site
- Without this step there is no website to view — it must be generated first before it can be served
- The output is a set of HTML/JSON files saved inside `delivery_dbt/target/`

**What each part means (`docs generate`):**
- `['docs', 'generate', ...]` — tells dbt to compile documentation from your models, sources, and YAML description files into the `target/` folder
- `--project-dir '.'` — tells dbt where to find your project files
- `--profiles-dir home + '/.dbt'` — tells dbt where to find the database connection; needed because `docs generate` also queries the database to capture actual column types

**Why run `docs serve`:**
- This starts a local web server so you can open the generated documentation in a browser
- Open `http://localhost:8080` to see a full interactive site showing every table, column, dependency graph, and test result
- You can show this to an interviewer as proof of professional data engineering practice — almost no junior engineers produce this

**What each part means (`docs serve`):**
- `['docs', 'serve', ...]` — tells dbt to start a local HTTP server pointing at the generated docs in `target/`
- `--project-dir '.'` — same as above; tells dbt where the project lives
- `--profiles-dir home + '/.dbt'` — same as above; needed for the serve command to resolve paths correctly

**How to open the docs in your browser:**
- Make sure the terminal is still running (the `docs serve` command must stay running — do not close it)
- Open your browser (Chrome, Edge, etc.)
- Type exactly this in the address bar and press Enter: `http://127.0.0.1:8080`
- If that does not load, try: `http://localhost:8080`
- The terminal will appear frozen/stuck — that is correct, it is the web server running
- To stop the server when you are done: press `Ctrl + C` in the terminal

---

## Checkpoint

You now have:
- A dbt project with 3 SQL models
- Data quality tests
- Auto-generated documentation
- Clean, tested tables ready for ML and dashboards

---

## Git Checkpoint — End of Guide 04

- This is the full Git workflow you do at the end of every guide
- In a real office this is called "raising a PR (Pull Request)"
- You will do this 13 times — by the third time it feels automatic

**First — navigate back to the root folder:**
```bash
cd "c:\Users\DakshaKurhade\OneDrive - AIR INDIA LIMITED\Desktop\Delivery Optimisation"
```
- The dbt steps ran from inside `delivery_dbt/` — you need to go back up before any Git command
- All Git commands in every guide are always run from this root folder
- You can confirm you are in the right place by checking your terminal prompt — it should end with `Delivery Optimisation`

---

### Step G3 — Check what changed

```bash
git status  # show changed/new/staged files before staging anything
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
git diff  # show line-by-line changes not yet staged
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

**Make sure you are in the root folder before staging — if you ran dbt steps earlier, you may still be inside `delivery_dbt/`:**
```bash
cd "c:\Users\DakshaKurhade\OneDrive - AIR INDIA LIMITED\Desktop\Delivery Optimisation"
```

```bash
git add delivery_dbt/models/staging/stg_deliveries_cleaned.sql      # stage the staging SQL model
git add delivery_dbt/models/marts/mart_fadr_by_city_and_address.sql  # stage the FADR mart model
git add delivery_dbt/models/marts/mart_fadr_by_window_and_alerts.sql # stage the window analysis model
git add delivery_dbt/dbt_project.yml                                 # stage the dbt project config
git add GUIDE_04_DBT.md                                              # stage the guide file
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
git diff --staged  # show diff of staged files only (what you're about to commit)
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
# -m = write the commit message inline, no text editor opens
git commit -m "Guide 04: dbt project with staging, mart models and data quality tests"
```
**What a commit is:**
- A permanent snapshot saved in Git's history
- Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`)
- You can always return to this exact state

**What makes a good commit message:**
- Good: `"Guide 04: dbt project with staging, mart models and data quality tests"`
- Bad: `"done"`, `"update"`, `"changes"`

Rule: your future self reading this 3 months later should know exactly what changed without looking at the code.

---

### Step G8 — Check your commit was saved

```bash
git log --oneline  # show commit history, one line per commit
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
c7f4d2e Guide 04: dbt project with staging, mart models and data quality tests
b5e2f1a Guide 03: 10 analytical SQL queries for FADR analysis
9b2c3d1 Initial commit: project guides and README
```

**In an office:**
- `git log --oneline` is one of the most used commands
- It gives you the full history of the branch at a glance

---

### Step G9 — Push to GitHub

```bash
# -u = link local branch to GitHub branch (only needed on first push)
git push -u origin feature/guide-04-dbt
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
- You will see a yellow banner: **"feature/guide-04-dbt had recent pushes"**

---

### Step G10 — Raise a Pull Request on GitHub

- A Pull Request (PR) is a formal request to merge your branch into another branch
- You are asking: "I finished this work, please review it and bring it into develop"

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-04-dbt` ← what you are merging in
3. Title: `Guide 04: dbt transformation models`
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
git pull origin develop  # download the merged PR from GitHub
```
- Downloads the merged PR from GitHub into your local develop
- Your local develop now has everything from the feature branch you just merged

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub
- `pull` — download + merge in one step (it runs `git fetch` then `git merge` automatically)

```bash
git log --oneline  # confirm Guide 04 commit now appears in develop's history
```
- You should now see your Guide 04 commit in develop's history
- Confirm it is there

**What `--oneline` means:** Show one line per commit instead of the full multi-line format.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-04-dbt  # -d = delete locally (safe, already merged)
```
**What `-d` means:**
- Delete the branch locally
- Git will refuse to delete if the branch has unmerged commits — a safety guard
- Since you just merged the PR, `-d` works

```bash
git push origin --delete feature/guide-04-dbt  # delete the branch on GitHub too
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
git checkout -b feature/guide-05-pyspark  # -b = create new branch and switch to it
```

**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 04 commit is in the history
- **Branches** → feature/guide-04-dbt is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_05_PYSPARK.md](GUIDE_05_PYSPARK.md) — Process the same data at scale with PySpark
