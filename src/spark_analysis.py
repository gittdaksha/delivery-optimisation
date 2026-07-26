import os                                     # access OS environment variables if needed
from pyspark.sql import SparkSession          # entry point to all Spark operations
from pyspark.sql import functions as F        # built-in Spark functions (avg, sum, etc.)
from pyspark.sql.window import Window         # for window (ranking/running total) functions
from pyspark.sql.types import DoubleType, IntegerType  # column data type definitions
import pyarrow as pa                          # columnar in-memory format
import pyarrow.parquet as pq                  # read/write Parquet files
import shutil                                 # delete output folder before overwrite

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
# into separate subfolders, one per unique value of a column. Here partition_by=["city"]
# creates a separate subfolder for Mumbai, Delhi, Bangalore, etc. When a query
# later filters WHERE city = 'Mumbai', only that subfolder is read (partition pruning).
#
# Why pyarrow instead of spark.write.parquet() here:
#   On Windows, Spark's file writer requires winutils.exe (a Hadoop binary) which is
#   not installed by default. pyarrow writes identical partitioned Parquet files without
#   any Hadoop dependency — the output format is exactly the same as Spark would produce.
#   In production (Linux cluster / Databricks) you would use spark.write.parquet() directly.
output_path = "data/processed/deliveries.parquet"  # destination folder path

# Convert Spark DataFrame → pandas → pyarrow Table, then write partitioned Parquet
# .toPandas() = collect all Spark partitions back to the driver as a pandas DataFrame
#   → only safe on small datasets; on 500M rows you would keep it in Spark
# pa.Table.from_pandas(pdf) = convert pandas DataFrame to a pyarrow Table
#   → pyarrow is the in-memory columnar format Parquet is built on
# pq.write_to_dataset(..., partition_cols=["city"]):
#   → creates data/processed/deliveries.parquet/city=Mumbai/part-0.parquet etc.
#   → identical folder structure to spark.write.partitionBy("city").parquet()
if os.path.exists(output_path):
    shutil.rmtree(output_path)          # delete previous output (same as mode="overwrite")

pdf = df_featured.toPandas()            # Spark DataFrame → pandas (driver collects all rows)
table = pa.Table.from_pandas(pdf)       # pandas → pyarrow Table (columnar in-memory)
pq.write_to_dataset(
    table,
    root_path=output_path,              # top-level output folder
    partition_cols=["city"],            # one subfolder per city (partition pruning)
)
print(f"\nWrote Parquet to {output_path}")
print("Partitioned by city — queries filtering by city skip all other partitions (partition pruning)")

# ── 8. Read back from Parquet to verify ─────────────────────────────────────
# pq.read_table(path) = read ALL partition subfolders under the path into one pyarrow Table
#   pyarrow automatically discovers all city=* subfolders and combines them
table_back = pq.read_table(output_path)         # read all partitions back in
print(f"Read back {len(table_back):,} rows from Parquet")  # should match original count

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