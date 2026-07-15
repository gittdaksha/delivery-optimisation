# Guide 09 — Large-Scale Processing with PySpark

**Goal:** Re-process the delivery data using Apache Spark instead of Pandas. Spark is the industry standard for processing data at scale — it runs on clusters of hundreds of machines and handles datasets of billions of rows.

---

## Why PySpark on your CV?

PySpark appears on **80%+ of data engineering job descriptions**. It is the #1 technical differentiator between a junior DE (Data Engineer) and a mid/senior DE. Companies like Flipkart, Swiggy, Zomato, Amazon, and every data platform team use Spark daily.

The skill is: knowing how to express data transformations in Spark's distributed API (Application Programming Interface) (DataFrames, SQL (Structured Query Language), Window functions). The same logic you wrote in Pandas in Guide 02-03 — now done at "big data" scale.

---

## What is Spark?

Pandas loads your entire dataset into one machine's RAM and processes it there. Spark splits data across many machines and processes it in parallel. A 50,000-row CSV (Comma-Separated Values) is trivially small — in production this would be 500 million rows. The code you write is the same either way. That's Spark's value.

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
git checkout -b feature/guide-05-pyspark
```
**What `-b` means:** Create a new branch AND switch to it. Without `-b`, checkout only switches to an existing branch.

**Why a new branch for every guide:** Each branch is one unit of work. If something breaks, you can delete the branch and start fresh without affecting develop or main. In an office, each feature or fix lives on its own branch for the same reason.

Confirm you are on the right branch:
```bash
git branch
```
You will see a `*` next to your current branch. That `*` means "you are here".

---

## Step 9.1 — Install PySpark

```bash
pip install pyspark==3.5.1
```

**Why:** PySpark is the Python API for Apache Spark. It bundles a local Spark engine so you can run Spark on a single laptop for development and testing.

Verify installation:
```bash
python -c "import pyspark; print(pyspark.__version__)"
```

---

## Step 9.2 — Create `src/spark_analysis.py`

Create the file `src/spark_analysis.py`:

**How to create this file:**
```bash
notepad src/spark_analysis.py
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import DoubleType, IntegerType
import os

# ── 1. Create SparkSession ───────────────────────────────────────────────────
# SparkSession is the entry point to everything Spark.
# In production this would point to a cluster (YARN, Kubernetes, Databricks).
# Locally it creates a mini-cluster on your machine.
spark = (
    SparkSession.builder
    .appName("DeliveryOptimisation")
    .master("local[*]")          # use all CPU cores locally
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
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")  # suppress verbose INFO logs
print(f"Spark version: {spark.version}")

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
df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv("data/raw/deliveries.csv")
)

print(f"Schema:")
df.printSchema()
print(f"Total records: {df.count():,}")

# ── 3. Overall FADR ─────────────────────────────────────────────────────────
print("\n--- Overall FADR ---")
df.select(
    F.count("*").alias("total"),
    F.sum("is_successful").alias("successful"),
    F.round(F.avg("is_successful") * 100, 2).alias("fadr_pct")
).show()

# ── 4. FADR by address type and window (GROUP BY in Spark) ─────────────────
print("--- FADR by Address Type × Delivery Window ---")
(
    df.groupBy("address_type", "delivery_window")
    .agg(
        F.count("*").alias("attempts"),
        F.round(F.avg("is_successful") * 100, 2).alias("fadr_pct"),
    )
    .orderBy("fadr_pct")
    .show(20, truncate=False)
)

# ── 5. Window function: rank each city by FADR ──────────────────────────────
# Window functions are a core Spark skill tested in DE interviews.
# This ranks address types within each city by their FADR.
print("--- Rank of Address Types Within Each City (Window Function) ---")
window_spec = Window.partitionBy("city").orderBy(F.asc("fadr_pct"))

city_fadr = (
    df.groupBy("city", "address_type")
    .agg(F.round(F.avg("is_successful") * 100, 2).alias("fadr_pct"))
)

ranked = (
    city_fadr
    .withColumn("rank_in_city", F.rank().over(window_spec))
    .filter(F.col("rank_in_city") == 1)   # worst-performing address type per city
    .orderBy("fadr_pct")
)
ranked.show(truncate=False)

# ── 6. Feature engineering in Spark ─────────────────────────────────────────
# Add derived columns — same logic as Pandas, Spark API
print("--- Feature Engineering ---")
df_featured = (
    df
    .withColumn("order_value_bucket",
        F.when(F.col("order_value") < 500,  "Under 500")
        .when(F.col("order_value") < 1500, "500-1500")
        .when(F.col("order_value") < 3000, "1500-3000")
        .otherwise("Above 3000")
    )
    .withColumn("is_high_risk",
        (
            (F.col("address_type").isin("Apartment", "PG/Hostel")) &
            (F.col("delivery_window") == "Morning (9-12)") &
            (F.col("has_delivery_preference") == 0)
        ).cast(IntegerType())
    )
)

print("High-risk deliveries (Apartment/PG + Morning + No preference):")
df_featured.groupBy("is_high_risk").agg(
    F.count("*").alias("count"),
    F.round(F.avg("is_successful") * 100, 2).alias("fadr_pct")
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
output_path = "data/processed/deliveries.parquet"
(
    df_featured
    .write
    .mode("overwrite")
    .partitionBy("city")          # partitioning is a core DE concept
    .parquet(output_path)
)
print(f"\nWrote Parquet to {output_path}")
print("Partitioned by city — queries filtering by city skip all other partitions (partition pruning)")

# ── 8. Read back from Parquet to verify ─────────────────────────────────────
df_parquet = spark.read.parquet(output_path)
print(f"Read back {df_parquet.count():,} rows from Parquet")

# ── 9. Run SQL on Spark (Spark SQL) ─────────────────────────────────────────
# Spark has a built-in SQL engine — same SQL you wrote in Guide 03, now
# running distributed across a cluster.
df_featured.createOrReplaceTempView("deliveries")

print("\n--- Spark SQL: Cost of failure by city ---")
spark.sql("""
    SELECT
        city,
        SUM(1 - is_successful)                    AS failed_deliveries,
        SUM(1 - is_successful) * 45               AS estimated_cost_inr,
        ROUND(AVG(is_successful) * 100, 2)        AS fadr_pct
    FROM deliveries
    GROUP BY city
    ORDER BY estimated_cost_inr DESC
""").show()

spark.stop()
print("\nSparkSession stopped. Done.")
```

---

## Step 9.3 — Run PySpark analysis

```bash
python src/spark_analysis.py
```

The first run takes 20–30 seconds as Spark initialises the local engine. Subsequent runs are faster.

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
git add src/spark_analysis.py
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
git add src/spark_analysis.py
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
git commit -m "Guide 05: PySpark analysis with window functions, feature engineering, Parquet output"
```
**What a commit is:** A permanent snapshot saved in Git's history. Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`). You can always return to this exact state.

**What makes a good commit message:**
- Good: `"Guide 05: PySpark analysis with window functions, feature engineering, Parquet output"`
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
d9a3b1f Guide 05: PySpark analysis with window functions, feature engineering, Parquet output
c7f4d2e Guide 04: dbt project with staging, mart models and data quality tests
9b2c3d1 Initial commit: project guides and README
```

**In an office:** `git log --oneline` is one of the most used commands. It gives you the full history of the branch at a glance.

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-05-pyspark
```
**What `git push` does:** Uploads your local commits to GitHub. Until you push, your commit only exists on your laptop.

**What `-u` means:** Sets the upstream — links your local branch to a branch of the same name on GitHub. You only need `-u` the first time you push a new branch. After that, just `git push` is enough.

**What `origin` means:** The name of your GitHub remote. When you ran `git remote add origin ...` in Guide 00B, you named it `origin`. That name sticks.

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-05-pyspark had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-05-pyspark` ← what you are merging in
3. Title: `Guide 05: PySpark large-scale processing`
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
You should now see your Guide 05 commit in develop's history. Confirm it is there.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-05-pyspark
```
**What `-d` means:** Delete the branch locally. Git will refuse to delete if the branch has unmerged commits — a safety guard. Since you just merged the PR, `-d` works.

```bash
git push origin --delete feature/guide-05-pyspark
```
Deletes the branch on GitHub too.

**Why delete?** Merged branches are dead branches. Keeping them clutters the repository. In real teams, merged branches are always deleted. A clean repo = a professional habit.

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-06-airflow
```

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 05 commit is in the history
- **Branches** → feature/guide-05-pyspark is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_06_AIRFLOW.md](GUIDE_06_AIRFLOW.md) — Automate the pipeline with Apache Airflow
