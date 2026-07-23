# Guide 05 — Large-Scale Processing with PySpark

**Goal:** Re-process the delivery data using Apache Spark instead of Pandas. Spark is the industry standard for processing data at scale — it runs on clusters of hundreds of machines and handles datasets of billions of rows.

---

## Why PySpark on your CV?

- PySpark appears on **80%+ of data engineering job descriptions**
- It is the #1 technical differentiator between a junior DE (Data Engineer) and a mid/senior DE
- Companies like Flipkart, Swiggy, Zomato, Amazon, and every data platform team use Spark daily
- The skill is: knowing how to express data transformations in Spark's distributed API (Application Programming Interface) (DataFrames, SQL (Structured Query Language), Window functions)
- The same logic you wrote in Pandas in Guide 02-03 — now done at "big data" scale

---

## What is Spark?

- Pandas loads your entire dataset into one machine's RAM and processes it there
- Spark splits data across many machines and processes it in parallel
- A 50,000-row CSV (Comma-Separated Values) is trivially small — in production this would be 500 million rows
- The code you write is the same either way — that's Spark's value

---

## Git — Before You Start This Guide

Every guide begins the same way in a real office: you make sure you are on the right branch and it is up to date before touching any files.

### One-time cleanup — Commit guide numbering fixes

During Guide 04 the heading numbers in 6 guide files were corrected. Those changes are sitting uncommitted on develop. Run these now to clean them up before starting:

```bash
git add GUIDE_05_PYSPARK.md GUIDE_06_AIRFLOW.md GUIDE_08_DOCKER.md GUIDE_09_ML.md GUIDE_10_DASHBOARD.md GUIDE_13_GITHUB.md
```
- Stages the 6 guide files that had their heading numbers fixed

```bash
git commit -m "Fix guide numbering in headings to match file names"
```
- Commits the heading fixes as a clean snapshot on develop

```bash
git push origin develop
```
- Pushes the commit to GitHub so develop on GitHub matches your local develop

After this, run `git status` — you should see `nothing to commit, working tree clean` before proceeding to G1.

---

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
git checkout -b feature/guide-05-pyspark  # -b = create new branch and switch to it
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

## Step 9.1 — Install PySpark

```bash
pip install pyspark==3.5.1  # install exact version for reproducibility
```

**Why:**
- PySpark is the Python API for Apache Spark
- It bundles a local Spark engine so you can run Spark on a single laptop for development and testing

Verify installation:
```bash
python -c "import pyspark; print(pyspark.__version__)"  # print installed version
```

---

## Step 9.2 — Create `src/spark_analysis.py`

Create the file `src/spark_analysis.py`:

**How to create this file:**
```bash
notepad src/spark_analysis.py  # open/create the PySpark script
```
- Notepad will open (or ask to create the file — click Yes)
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad

**What `src/spark_analysis.py` does and why it exists:**
- **What it does:** Loads the raw delivery CSV into Spark, replicates the FADR analysis from Guide 03 using the distributed DataFrame API, adds new feature columns, writes the enriched dataset to Parquet partitioned by city, and runs a cost-of-failure query using Spark SQL
- **Why separate:** The Pandas scripts in Guide 02-03 run on a single machine and would grind to a halt on hundreds of millions of rows; this script does the same analysis using Spark's distributed engine — the logic is identical but the execution scales to any cluster size; keeping it separate from the dbt models means the heavy distributed processing step is clearly distinct from the SQL transformation layer
- **Input:** `data/raw/deliveries.csv` (50,000-row CSV produced by `generate_data.py` in Guide 02)
- **Output:** `data/processed/deliveries.parquet/` (partitioned Parquet folder, one subfolder per city, containing all 50,000 rows enriched with `order_value_bucket` and `is_high_risk` feature columns)
- **Pipeline position:** `data/raw/deliveries.csv` (Guide 02) → **this script** → writes `data/processed/deliveries.parquet` (partitioned by city), which the ML model (Guide 09) reads as its training input

```python
from pyspark.sql import SparkSession          # entry point to all Spark operations
from pyspark.sql import functions as F        # built-in Spark functions (avg, sum, etc.)
from pyspark.sql.window import Window         # for window (ranking/running total) functions
from pyspark.sql.types import DoubleType, IntegerType  # column data type definitions
import os                                     # access OS environment variables if needed

# ── 1. Create SparkSession ───────────────────────────────────────────────────
# SparkSession is the entry point to everything Spark.
# In production this would point to a cluster (YARN, Kubernetes, Databricks).
# Locally it creates a mini-cluster on your machine.
# SparkSession.builder = start configuring a new Spark session (like a builder pattern)
# .appName("DeliveryOptimisation") = give this job a label that shows in the Spark Web UI
# .master("local[*]") = tell Spark where to run:
#   "local"    = run on this single machine (not a remote cluster)
#   [*]        = use ALL available CPU cores  →  4-core laptop creates 4 parallel threads
#   production = replace with "yarn" or a Databricks cluster URL
# .config("spark.sql.shuffle.partitions", "8") = set one config key:
#   shuffle partitions = how many parts Spark splits data into after a join or groupBy
#   default is 200 (for large clusters); 8 is right-sized for a small local dataset
# .getOrCreate() = if a SparkSession already exists in this process, reuse it; else create new
#   → prevents "session already exists" errors when re-running in Jupyter or a loop
spark = (
    SparkSession.builder              # start building a SparkSession config
    .appName("DeliveryOptimisation")  # name shown in Spark UI for this job
    .master("local[*]")               # local[*] = use all CPU cores on this machine
    # What SparkSession is: SparkSession is the entry point to Spark — every Spark
    # program starts by creating one. Think of it like a database connection object
    # but for Spark's distributed engine. You use it to read data, run SQL, and
    # configure how Spark behaves.
    #
    # What local[*] means: "local" means run Spark on this single machine (not a
    # cluster). The [*] means "use all available CPU cores." On a 4-core laptop this
    # creates 4 parallel processing threads. In production, you would replace this
    # with the address of a real cluster (e.g. yarn, or a Databricks cluster URL).
    .config("spark.sql.shuffle.partitions", "8")   # small for local dev
    .getOrCreate()  # create new session or reuse one that already exists
)
spark.sparkContext.setLogLevel("ERROR")  # suppress verbose INFO logs
print(f"Spark version: {spark.version}")  # confirm Spark started successfully

# ── 2. Load raw CSV ─────────────────────────────────────────────────────────
# What lazy evaluation means: Spark does not immediately execute transformations
# like .filter() or .groupBy() when you write them. Instead it builds a plan
# (a DAG of operations). Only when you call an action — .show(), .count(),
# or .write() — does Spark actually execute the plan. This lets Spark optimise
# the full chain of operations before touching the data, which is much faster
# than executing each step one at a time.
#
# What .show() vs .count() triggers: both are "actions" that force Spark to
# execute. .show() retrieves and prints the first 20 rows. .count() scans the
# full dataset to count rows. Either one triggers the full computation plan.
# Spark reads CSVs lazily — it doesn't actually read the file until you
# trigger an action (like .show() or .count())
# spark.read = start a DataFrameReader (lets you chain .option() and a format method)
# .option("header", "true") = treat first CSV row as column names, not data
#   → without this: columns would be named _c0, _c1, _c2 ...
# .option("inferSchema", "true") = Spark scans the file to guess each column's type
#   → "134.50" → DoubleType, "1" → IntegerType, "Mumbai" → StringType
#   → without this: every column is StringType (text) even if it contains numbers
# .csv("data/raw/deliveries.csv") = specify the file format AND path to read from
#   → this is a LAZY operation — Spark does not read the file here, just records the plan
df = (
    spark.read                         # start a file-reading operation
    .option("header", "true")          # first row is column names, not data
    .option("inferSchema", "true")     # auto-detect column types (int, float, etc.)
    .csv("data/raw/deliveries.csv")    # path to the CSV file to load
)

print(f"Schema:")
df.printSchema()                       # print column names and inferred types
# f"Total records: {df.count():,}" — f-string with format spec
# df.count()   = ACTION: triggers Spark to actually read the file and count rows → e.g. 50000
# :,           = format spec: add comma as thousands separator → 50000 → "50,000"
print(f"Total records: {df.count():,}")  # count rows; :, adds thousands separator

# ── 3. Overall FADR ─────────────────────────────────────────────────────────
print("\n--- Overall FADR ---")
# df.select(...) = choose which columns (or computed expressions) to include in the output
# F.count("*") = count every row (including rows with NULLs); equivalent to SQL COUNT(*)
# .alias("total") = rename the output column to "total" instead of "count(1)"
# F.sum("is_successful") = add up all values in is_successful; 0+1+1+0+1 → 3
# F.avg("is_successful") = mean of 0/1 column → e.g. 0.72 (72% success rate)
# * 100 = multiply to get a percentage → 0.72 * 100 = 72.0
# F.round(value, 2) = keep 2 decimal places → 72.0 → 72.0 (or 71.843... → 71.84)
# .alias("fadr_pct") = name the final column "fadr_pct"
# .show() = ACTION — forces Spark to execute the full plan and print the result table
df.select(
    F.count("*").alias("total"),                     # count all rows
    F.sum("is_successful").alias("successful"),      # sum of 1s = number of successes
    F.round(F.avg("is_successful") * 100, 2).alias("fadr_pct")  # success rate as %
).show()  # action: triggers execution and prints result table

# ── 4. FADR by address type and window (GROUP BY in Spark) ─────────────────
print("--- FADR by Address Type × Delivery Window ---")
# .groupBy("address_type", "delivery_window") = split rows into groups by unique combinations
#   → like SQL: GROUP BY address_type, delivery_window
#   → e.g. all "Apartment" + "Morning (9-12)" rows form one group
# .agg(...) = apply aggregate functions to each group (must follow .groupBy())
#   agg takes one or more F.function().alias() expressions
# F.round(F.avg("is_successful") * 100, 2):
#   step 1 — F.avg("is_successful") → e.g. 0.6842
#   step 2 — * 100                  → 68.42
#   step 3 — F.round(..., 2)        → 68.42 (already 2 dp; would round 68.427 → 68.43)
# .orderBy("fadr_pct") = sort output rows by fadr_pct ascending (lowest = worst FADR first)
# .show(20, truncate=False):
#   20           = print up to 20 rows (default is also 20, but explicit is clearer)
#   truncate=False = don't shorten long strings; shows full city/window names uncut
(
    df.groupBy("address_type", "delivery_window")  # group rows by these two columns
    .agg(
        F.count("*").alias("attempts"),                         # rows per group
        F.round(F.avg("is_successful") * 100, 2).alias("fadr_pct"),  # success % per group
    )
    .orderBy("fadr_pct")              # sort by FADR ascending (worst first)
    .show(20, truncate=False)         # show 20 rows; False = don't cut off long text
)

# ── 5. Window function: rank each city by FADR ──────────────────────────────
# Window functions are a core Spark skill tested in DE interviews.
# This ranks address types within each city by their FADR.
print("--- Rank of Address Types Within Each City (Window Function) ---")
# Window.partitionBy("city") = divide all rows into groups by city value
#   → like GROUP BY in SQL, but window functions keep ALL original rows (no collapsing)
#   → e.g. all Mumbai rows form one partition; all Delhi rows form another
# .orderBy(F.asc("fadr_pct")) = within each city partition, sort rows by fadr_pct ascending
#   F.asc("fadr_pct") = ascending order (lowest value first = worst FADR ranked 1st)
# rank() will later assign 1 to the lowest fadr_pct row in each city partition
window_spec = Window.partitionBy("city").orderBy(F.asc("fadr_pct"))
# partitionBy = reset rank counter for each city (like GROUP BY in SQL)
# orderBy + asc = rank from lowest FADR (worst) to highest within each city

city_fadr = (
    df.groupBy("city", "address_type")  # one row per city + address type
    .agg(F.round(F.avg("is_successful") * 100, 2).alias("fadr_pct"))  # FADR per group
)

# .withColumn("rank_in_city", F.rank().over(window_spec)):
#   withColumn(name, expr) = add a NEW column called "rank_in_city" to every row
#   F.rank()               = assign an integer rank within each window partition
#     → within Mumbai: Apartment=68.4 gets rank 1, House=71.2 gets rank 2, etc.
#     → ties get the same rank and the next rank skips (1,1,3) — use dense_rank for (1,1,2)
#   .over(window_spec)     = apply rank() using the partition+order rules we defined above
# .filter(F.col("rank_in_city") == 1):
#   F.col("rank_in_city") = reference the column we just created
#   == 1                  = keep only the row ranked 1st in each city (worst FADR)
#   → result: one row per city, showing the address_type with the lowest FADR
# .orderBy("fadr_pct") = sort the final result so worst-performing cities appear first
ranked = (
    city_fadr
    .withColumn("rank_in_city", F.rank().over(window_spec))  # add rank column
    .filter(F.col("rank_in_city") == 1)   # worst-performing address type per city
    .orderBy("fadr_pct")                  # sort by FADR ascending across all cities
)
ranked.show(truncate=False)  # print full text, don't truncate city names

# ── 6. Feature engineering in Spark ─────────────────────────────────────────
# Add derived columns — same logic as Pandas, Spark API
print("--- Feature Engineering ---")
# .withColumn(name, expr) = add a brand-new column to each row (does not modify original df)
# F.when(condition, value) = start an if/elif/else chain (like SQL CASE WHEN):
#   F.when(F.col("order_value") < 500,  "Under 500")  → if value < 500 assign "Under 500"
#   .when(F.col("order_value") < 1500, "500-1500")    → elif value < 1500 assign "500-1500"
#   .when(F.col("order_value") < 3000, "1500-3000")   → elif value < 3000 assign "1500-3000"
#   .otherwise("Above 3000")                          → else (≥3000) assign "Above 3000"
# Spark evaluates conditions top-to-bottom and stops at the first match (like elif)
# F.col("address_type").isin("Apartment", "PG/Hostel"):
#   F.col("address_type") = reference the address_type column
#   .isin(...)            = True if value equals ANY item in the list; False otherwise
#   → like SQL: address_type IN ('Apartment', 'PG/Hostel')
# & = AND operator for Spark boolean columns (use & not 'and'; wrap each condition in ())
# .cast(IntegerType()) = convert the resulting True/False boolean column to 1/0 integer
#   → True → 1, False → 0 (needed for arithmetic like SUM and AVG later)
df_featured = (
    df
    .withColumn("order_value_bucket",          # add a new column with value bands
        F.when(F.col("order_value") < 500,  "Under 500")    # if < 500 → label
        .when(F.col("order_value") < 1500, "500-1500")      # elif < 1500 → label
        .when(F.col("order_value") < 3000, "1500-3000")     # elif < 3000 → label
        .otherwise("Above 3000")                            # all remaining rows
    )
    .withColumn("is_high_risk",                # add 1/0 flag for risky deliveries
        (
            (F.col("address_type").isin("Apartment", "PG/Hostel")) &  # these address types
            (F.col("delivery_window") == "Morning (9-12)") &          # AND morning slot
            (F.col("has_delivery_preference") == 0)                   # AND no preference set
        ).cast(IntegerType())  # convert True/False boolean to 1/0 integer
    )
)

print("High-risk deliveries (Apartment/PG + Morning + No preference):")
# .groupBy("is_high_risk") = split rows into two groups: is_high_risk=0 and is_high_risk=1
# .agg(...).show() = compute aggregates and print; .show() is the action that triggers execution
df_featured.groupBy("is_high_risk").agg(  # group by the flag we just created
    F.count("*").alias("count"),                                    # count per group
    F.round(F.avg("is_successful") * 100, 2).alias("fadr_pct")     # FADR per group
).show()

# ── 7. Write output as Parquet ───────────────────────────────────────────────
# Parquet is the standard columnar format for data lakes (S3, GCS, ADLS).
# It's 3-5x smaller than CSV and 10x faster to query on column-based reads.
# Every DE job uses Parquet. Knowing CSV alone is not enough.
#
# What a partition is in Parquet context: partitioning splits a large dataset
# into separate subfolders, one per unique value of a column. Here .partitionBy("city")
# creates a separate subfolder for Mumbai, Delhi, Bangalore, etc. When a query
# later filters WHERE city = 'Mumbai', Spark only reads that one subfolder and
# skips all others — this is called "partition pruning" and dramatically reduces
# the data read from disk.
#
# What mode("overwrite") means: if the output folder already exists from a
# previous run, delete it and write fresh. Without this, Spark would error out
# rather than overwrite existing files. The alternative is mode("append") which
# adds new files to the existing folder.
output_path = "data/processed/deliveries.parquet"  # destination folder path
# .write = start a DataFrameWriter (lets you chain .mode(), .partitionBy(), and a format method)
# .mode("overwrite"):
#   "overwrite" = if the folder already exists, delete it completely and write fresh files
#   "append"    = add new files alongside existing files in the folder
#   "error"     = (default) raise an error if the folder already exists — safe but inconvenient
# .partitionBy("city"):
#   splits the data into subfolders, one per unique city value
#   → data/processed/deliveries.parquet/city=Mumbai/part-0000.parquet
#   → data/processed/deliveries.parquet/city=Delhi/part-0000.parquet
#   later queries filtering WHERE city='Mumbai' only open that one subfolder (partition pruning)
# .parquet(output_path) = write in Parquet columnar format to the given path
#   → ACTION: triggers Spark to execute all prior transformations and write the files
(
    df_featured
    .write
    .mode("overwrite")       # delete existing output folder before writing
    .partitionBy("city")     # create one subfolder per city value
    .parquet(output_path)    # write in Parquet columnar format (not CSV)
)
print(f"\nWrote Parquet to {output_path}")
print("Partitioned by city — queries filtering by city skip all other partitions (partition pruning)")

# ── 8. Read back from Parquet to verify ─────────────────────────────────────
# spark.read.parquet(path) = read ALL partition subfolders under the path into one DataFrame
#   Spark automatically discovers all city=* subfolders and combines them
df_parquet = spark.read.parquet(output_path)  # read all partitions back in
# {df_parquet.count():,} — same :, format spec as earlier: adds thousands separators to count
print(f"Read back {df_parquet.count():,} rows from Parquet")  # should match original count

# ── 9. Run SQL on Spark (Spark SQL) ─────────────────────────────────────────
# Spark has a built-in SQL engine — same SQL you wrote in Guide 03, now
# running distributed across a cluster.
# .createOrReplaceTempView("deliveries"):
#   registers this DataFrame as a temporary SQL table named "deliveries"
#   "Temp" = only exists for this SparkSession; gone when spark.stop() is called
#   "OrReplace" = if a view called "deliveries" already exists, overwrite it (no error)
#   → now you can write SQL: SELECT * FROM deliveries (Spark translates it to DataFrame ops)
df_featured.createOrReplaceTempView("deliveries")  # register df as a SQL table name

print("\n--- Spark SQL: Cost of failure by city ---")
spark.sql("""
    SELECT
        city,
        -- SUM(1 - is_successful): flip each row's value, then sum
        -- is_successful=1 → (1-1)=0, is_successful=0 → (1-0)=1
        -- → summing those 1s counts the failures (equivalent to COUNT WHERE is_successful=0)
        SUM(1 - is_successful)                    AS failed_deliveries,  -- count of 0s
        -- SUM(1 - is_successful) * 45: total failures × cost per failure
        -- → 320 failed deliveries × 45 INR = 14,400 INR estimated cost for that city
        SUM(1 - is_successful) * 45               AS estimated_cost_inr, -- 45 INR per failure
        -- AVG(is_successful) * 100: fraction → percentage  (0.72 → 72.0)
        -- ROUND(..., 2): keep 2 decimal places → 72.0 (or 71.843 → 71.84)
        ROUND(AVG(is_successful) * 100, 2)        AS fadr_pct            -- success rate %
    FROM deliveries
    GROUP BY city
    -- ORDER BY estimated_cost_inr DESC: sort with LARGEST value first
    -- DESC = descending (biggest first); default is ASC (smallest first)
    ORDER BY estimated_cost_inr DESC  -- worst city (most costly) at top
""").show()

spark.stop()  # release all Spark resources and shut down the local engine
print("\nSparkSession stopped. Done.")
```

---

## Step 9.3 — Run PySpark analysis

```bash
python src/spark_analysis.py  # run the Spark script with the local Python interpreter
```

- The first run takes 20–30 seconds as Spark initialises the local engine
- Subsequent runs are faster

---

## Step 9.4 — Key concepts to understand

| Concept | What it is | Why interviewers ask about it |
|---|---|---|
| SparkSession | Entry point, like a database connection | First line in every Spark job |
| Lazy evaluation | Spark builds a plan but doesn't execute until an action (`.show()`, `.count()`) | Core to how Spark optimises execution |
| DataFrame | Distributed table, like Pandas but across a cluster | The primary Spark API |
| Window function | `RANK()`, `ROW_NUMBER()`, `LAG()` across partitions | Tested in almost every DE interview |
| Parquet | Columnar file format, compressed, partitioned | Replaces CSV in all production pipelines |
| Partition pruning | Spark skips folders that don't match a filter | Key performance concept — "why do we partition?" |
| Spark SQL | Run SQL on Spark DataFrames | Same SQL knowledge, now distributed |

---

## Step 9.5 — Common interview questions this prepares you for

- *"What is the difference between a transformation and an action in Spark?"*
  Answer: Transformations (`.filter()`, `.groupBy()`) are lazy — they build a DAG (Directed Acyclic Graph). Actions (`.count()`, `.show()`, `.write()`) trigger execution.

- *"Why do we partition data in Parquet?"*
  Answer: Queries that filter on the partition column (e.g. `WHERE city = 'Mumbai'`) skip all other partitions — this is called partition pruning. It dramatically reduces the data Spark needs to read.

- *"What is a Window function? Give an example."*
  Answer: A window function calculates a value for each row relative to a group (partition) of rows — e.g. ranking address types by FADR (First Attempt Delivery Rate) within each city without collapsing the rows like GROUP BY would.

---

## Step 9.6 — Commit

```bash
git add src/spark_analysis.py  # stage only this file (not temp files or data)
# -m = write the commit message inline, no text editor opens
git commit -m "Add PySpark analysis: FADR at scale, window functions, Parquet output"
```

---

## Checkpoint

You now know:
- How to create a SparkSession
- DataFrame API (groupBy, agg, withColumn, filter)
- Window functions (rank, partition)
- Writing and reading Parquet with partitioning
- Running Spark SQL

---

## Git Checkpoint — End of Guide 05

- This is the full Git workflow you do at the end of every guide
- In a real office this is called "raising a PR (Pull Request)"
- You will do this 13 times — by the third time it feels automatic

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

```bash
git add src/spark_analysis.py  # stage only the PySpark script
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
git commit -m "Guide 05: PySpark analysis with window functions, feature engineering, Parquet output"
```
**What a commit is:**
- A permanent snapshot saved in Git's history
- Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`)
- You can always return to this exact state

**What makes a good commit message:**
- Good: `"Guide 05: PySpark analysis with window functions, feature engineering, Parquet output"`
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
d9a3b1f Guide 05: PySpark analysis with window functions, feature engineering, Parquet output
c7f4d2e Guide 04: dbt project with staging, mart models and data quality tests
9b2c3d1 Initial commit: project guides and README
```

**In an office:**
- `git log --oneline` is one of the most used commands
- It gives you the full history of the branch at a glance

---

### Step G9 — Push to GitHub

```bash
# -u = link local branch to GitHub branch (only needed on first push)
git push -u origin feature/guide-05-pyspark
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
- You will see a yellow banner: **"feature/guide-05-pyspark had recent pushes"**

---

### Step G10 — Raise a Pull Request on GitHub

- A Pull Request (PR) is a formal request to merge your branch into another branch
- You are asking: "I finished this work, please review it and bring it into develop"

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-05-pyspark` ← what you are merging in
3. Title: `Guide 05: PySpark large-scale processing`
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
git log --oneline  # confirm Guide 05 commit now appears in develop's history
```
- You should now see your Guide 05 commit in develop's history
- Confirm it is there

**What `--oneline` means:** Show one line per commit instead of the full multi-line format.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-05-pyspark  # -d = delete locally (safe, already merged)
```
**What `-d` means:**
- Delete the branch locally
- Git will refuse to delete if the branch has unmerged commits — a safety guard
- Since you just merged the PR, `-d` works

```bash
git push origin --delete feature/guide-05-pyspark  # delete the branch on GitHub too
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
git checkout -b feature/guide-06-airflow  # -b = create new branch and switch to it
```

**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 05 commit is in the history
- **Branches** → feature/guide-05-pyspark is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_06_AIRFLOW.md](GUIDE_06_AIRFLOW.md) — Automate the pipeline with Apache Airflow
