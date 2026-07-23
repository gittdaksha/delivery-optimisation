# Guide 14 — Interview Preparation

- This guide collects every question an interviewer is likely to ask about this project — by tool, by concept, and about you personally
- Each answer is written the way you should actually say it, not the way a textbook would write it

**How to use this:**
- Read it after you finish building each guide, not before
- The answers will only stick if you have already run the code and seen the output yourself

---

## The one question that opens every interview

**"Tell me about a data engineering project you have built."**

- "I built a delivery optimisation pipeline — the problem came from a real experience where I missed calls from a delivery partner during a meeting and the parcel got rescheduled"
- "I wanted to quantify how often that happens and whether data could predict it before the delivery attempt is made"
- "The pipeline has two sides — the batch side generates delivery data, lands it in GCS, loads into BigQuery, and dbt transforms it into clean analytical tables — all orchestrated by an Airflow DAG that runs daily"
- "The real-time side uses Kafka, where a producer streams delivery status events and a consumer reads them and computes a live FADR"
- "The whole stack runs with docker-compose up"
- "On the analytics side, a Random Forest model predicts delivery success with 83% accuracy — apartments in morning windows fail 35% more than the average, and customers who set a delivery preference succeed 25 percentage points higher"
- "The project is on GitHub with 13 step-by-step guides, CI/CD running automated tests on every push, and a Streamlit dashboard with a business impact calculator"

- This answer is 60–90 seconds
- It covers the problem, the architecture, the tools, and the insight
- It gives the interviewer 5 different threads to pull on

---

## Python

**"How comfortable are you with Python for data engineering?"**
- "Comfortable with the data engineering use cases — reading and writing files, calling APIs with requests, loading data into databases with SQLAlchemy, data manipulation with Pandas, and writing modular scripts that Airflow can call as tasks"
- "I also wrote unit tests with pytest"
- "I am not a software engineer writing production web apps in Python, but for pipeline work I am confident"

**"What is a virtual environment and why do you use one?"**
- "A virtual environment isolates a project's Python dependencies from the rest of the system"
- "If project A needs pandas 1.5 and project B needs pandas 2.2, they each have their own venv and never conflict"
- "Every project I work on starts with python -m venv and a requirements.txt — it is the first thing, not an afterthought"

---

## SQL (Structured Query Language)

**"How strong is your SQL?"**
- "Strong for analytical work — comfortable with GROUP BY, aggregations, window functions like RANK and ROW_NUMBER, CTEs, subqueries, and joins"
- "In this project I wrote 10 analytical queries answering real business questions — FADR by address type, cost of failure by city, worst-performing address and window combinations"
- "I also wrote the dbt transformation layer which is pure SQL organised into staged models"

**"What is a window function? Give an example."**
- "A window function calculates a value for each row in relation to a group of rows — called a partition — without collapsing the rows the way GROUP BY does"
- "In this project I used RANK() to rank address types by FADR within each city"
- "So Mumbai shows Apartment ranked 1 as the worst, Delhi shows PG/Hostel ranked 1 — each city has its own ranking without losing the individual rows"

**"What is the difference between WHERE and HAVING?"**
- "WHERE filters rows before aggregation happens; HAVING filters after"
- "So WHERE city = 'Mumbai' reduces which rows go into the GROUP BY"
- "HAVING total_attempts > 200 removes groups whose count is too small to be meaningful — you cannot do that with WHERE because the count does not exist until after the GROUP BY runs"

---

## dbt

**"What is dbt and why did you use it instead of just writing SQL files?"**
- "dbt is a transformation framework that sits on top of SQL — you write .sql files, dbt runs them in the right order against your database"
- "It adds three things plain SQL files cannot: automated data quality tests on every build, auto-generated documentation for every table and column, and a dependency graph so you always know which models depend on which"
- "In a team, broken transformations get caught before they reach the dashboard, and a new team member can understand the whole data model without asking anyone"

**"What are staging and mart models in dbt?"**
- "Staging models are the first layer — they take raw source data and clean it: cast types, rename columns, remove obvious nulls — no business logic yet"
- "Mart models are the second layer — they apply business logic and aggregations on top of the staging layer"
- "This separation is from Kimball's data modelling methodology — if the source schema changes, you only update the staging model and everything downstream is unaffected"

**"What is a dbt test?"**
- "A dbt test is a data quality check that runs automatically when you run dbt test"
- "The built-in ones are: unique, not_null, accepted_values, and relationships"
- "In this project I tested that delivery_id is unique and not null, and that is_successful only contains 0 or 1"
- "If any test fails, dbt reports it as an error before that data reaches the dashboard or ML model"

---

## Apache Airflow

**"What is Airflow and what problem does it solve?"**
- "Airflow is a pipeline orchestration tool — it solves the problem of running multi-step pipelines reliably on a schedule"
- "Without Airflow, you would manually run scripts in sequence and hope nothing failed"
- "With Airflow, you define tasks and their dependencies as a DAG in Python, set a schedule, and Airflow handles running them, retrying on failure, alerting you if something breaks, and keeping a full history of every run"

**"What is a DAG?"**
- "Directed Acyclic Graph — Directed means tasks flow in one direction (task A triggers task B), Acyclic means no loops (a task cannot eventually trigger itself)"
- "In Airflow, your pipeline is a DAG: generate data → ingest → transform → test → export"
- "Each arrow is a dependency — Airflow uses the graph to know what can run in parallel and what must wait"

**"What happens when an Airflow task fails?"**
- "Airflow marks that task as failed and stops the downstream tasks that depend on it"
- "Depending on the retry configuration — I set retries: 2 with a 5-minute delay — it will retry before giving up"
- "If it exhausts retries, it sends an alert"
- "The upstream tasks that already succeeded are not re-run — when you fix the issue and clear the failed task, Airflow re-runs only from that point forward"

**"What is the difference between LocalExecutor and CeleryExecutor?"**
- "LocalExecutor runs tasks as subprocesses on the same machine as the Airflow scheduler — works for development and moderate workloads"
- "CeleryExecutor distributes tasks across multiple worker machines — each worker picks tasks from a queue"
- "You use CeleryExecutor when your pipeline has too many tasks for one machine, or when you need horizontal scaling"
- "In this project I used LocalExecutor because it runs in Docker on a single machine, which is sufficient"

---

## Apache Spark / PySpark

**"Why did you use PySpark instead of Pandas?"**
- "Honest answer — the dataset I generated has 50,000 rows, which Pandas handles easily"
- "I used PySpark specifically to learn the API and understand how the same transformations work at cluster scale"
- "In production, a delivery platform has hundreds of millions of rows — that is where Spark is the right tool"
- "I used it here to build the skill, not because the dataset required it"

**"What is lazy evaluation in Spark?"**
- "When you call a Spark transformation like filter() or groupBy(), Spark does not execute it immediately — it builds an execution plan (a DAG of operations)"
- "Execution only happens when you call an action like count(), show(), or write()"
- "This matters because Spark can optimise the full plan before running anything — for example, pushing a filter earlier in the chain to reduce data volume before a join"

**"What is a window function in Spark? Give an example."**
- "Same concept as SQL window functions — a calculation over a partition of rows without collapsing them"
- "In this project I used Window.partitionBy('city').orderBy('fadr') with rank() to find the worst-performing address type within each city"
- "Every city gets its own ranked list and I can filter for rank == 1 to find the single worst segment per city"

**"What is Parquet and why use it instead of CSV?"**
- "Parquet is a columnar file format — CSV stores data row by row, Parquet stores it column by column"
- "For analytical queries that only read 3 columns out of 50, Parquet only reads those 3 columns and physically skips the rest"
- "It is also compressed by default, typically 3–5x smaller than CSV"
- "In this project I wrote the processed data as Parquet partitioned by city — a query filtering for Mumbai only reads the Mumbai partition (partition pruning)"

**"What is partition pruning?"**
- "When you write Parquet data with partitionBy('city'), Spark creates separate folders per city: city=Mumbai/, city=Delhi/, etc."
- "When you later query with WHERE city = 'Mumbai', Spark skips all other folders entirely — it only opens the Mumbai folder"
- "At large scale this can reduce data read from 500GB to 5GB for a city-specific query"

---

## Apache Kafka

**"What is Kafka and why is it different from Airflow?"**
- "They solve different problems — Airflow runs batch jobs on a schedule, Kafka handles events that happen right now"
- "A delivery partner marks a parcel delivered at 2:37pm — that event needs to be available to 5 different systems immediately: the tracking app, the analytics pipeline, the notification service, billing"
- "Kafka is a real-time message bus; Airflow is a batch scheduler"
- "In this project I use both — Airflow for the nightly batch pipeline, Kafka for the real-time delivery status stream"

**"What is a Kafka topic, partition, and offset?"**
- "A topic is a named channel — like a table but for events; delivery-events is the topic in this project"
- "A partition is how a topic is split for parallelism — I used 3 partitions, so 3 consumers can read in parallel"
- "An offset is the position of a message within a partition — Kafka tracks where each consumer group has read to"
- "If a consumer crashes and restarts, it picks up from the last committed offset so no message is lost or processed twice"

**"What is a consumer group?"**
- "A consumer group is a set of consumers that share the work of reading a topic — each partition is assigned to exactly one consumer in the group"
- "Multiple consumer groups can read the same topic independently, each maintaining their own offset"
- "In this project the analytics consumer group reads all events to compute FADR; a separate notification group could read the same events to send customer alerts — both groups get every message"

**"What happens if a consumer crashes?"**
- "Kafka retains messages for a configurable period — default 7 days"
- "The consumer's offset is stored in Kafka itself — when the consumer restarts, it reads its last committed offset and continues from there"
- "No messages are lost — this is fundamentally different from a queue like RabbitMQ where a consumed message is deleted"
- "Kafka's retention is what makes it possible to replay history, reprocess events, or add a new consumer group that reads from the beginning"

---

## Docker

**"What is Docker and why did you use it?"**
- "Docker packages an application and all its dependencies into a container — a self-contained unit that runs identically on any machine"
- "My pipeline depends on Kafka, PostgreSQL, and Airflow all running together with specific versions — without Docker, anyone who wants to run this has to install and configure each service manually"
- "With docker-compose up, everything starts with one command — works on my laptop, a colleague's machine, or a cloud VM"

**"What is the difference between an image and a container?"**
- "An image is the static blueprint — it defines the operating system, dependencies, and code"
- "A container is a running instance of an image — the same image can run as 10 containers simultaneously"
- "Think of an image as a class and a container as an object instance of that class"

**"What is Docker Compose?"**
- "Docker Compose lets you define multiple containers and their relationships in a single YAML file and manage them together"
- "In this project, docker-compose.yml defines Zookeeper, Kafka, PostgreSQL, Airflow webserver, and Airflow scheduler — their ports, environment variables, volumes, startup order, and health checks"
- "One file, one command to start, one command to stop"

---

## BigQuery and GCP (Google Cloud Platform)

**"What is BigQuery and when would you choose it over PostgreSQL?"**
- "BigQuery is Google's serverless data warehouse — no servers to provision, no indexes to manage; you load data and run SQL"
- "BigQuery is columnar storage designed for analytical queries on massive datasets; PostgreSQL is row storage designed for transactional workloads"
- "For frequent writes and reads of individual rows (orders, users, sessions) — use PostgreSQL"
- "For aggregations across hundreds of millions of rows (how many deliveries failed per city per week) — BigQuery is faster and cheaper"

**"How do you optimise a slow BigQuery query?"**
- "First, check if the table is partitioned — if not, every query scans the full table regardless of filters; partition by the date column most queries filter on"
- "Second, check clustering — if queries consistently filter by city or address_type, clustering on those columns reduces blocks read within each partition"
- "Third, check the SELECT — BigQuery is columnar, so SELECT * reads all columns even if you only need 3; select only what you need"
- "In this project I created a partitioned and clustered version of the deliveries table and the query cost dropped significantly"

**"What is the ELT pattern and how does it differ from ETL?"**
- "ETL (Extract, Transform, Load) — transforms data before loading it into the warehouse"
- "ELT (Extract, Load, Transform) — loads raw data into the warehouse first, then transforms it there using SQL"
- "Modern cloud warehouses like BigQuery are powerful enough that transforming inside the warehouse is faster and cheaper than transforming externally"
- "In this project I follow ELT: raw CSV lands in GCS, loads into BigQuery as-is, then dbt transforms it into clean mart tables inside BigQuery"

**"What is GCS and why does data land there before BigQuery?"**
- "GCS is Google Cloud Storage — object storage like a file system in the cloud"
- "Data lands in GCS first because it is the raw, unchanged source of truth — if a dbt transformation corrupts the BigQuery tables, I reload from GCS"
- "Multiple systems can also read from GCS independently — Spark, Dataflow, and BigQuery can all read the same raw file for different purposes"
- "GCS is the raw layer; BigQuery is the processed layer"

---

## CI/CD and Testing

**"What is CI/CD?"**
- "CI is Continuous Integration — every code change is automatically tested before it can be merged"
- "CD is Continuous Deployment — passing changes are automatically deployed"
- "In this project I set up GitHub Actions: on every push, it installs dependencies, runs 7 pytest unit tests on the data generation logic, and runs flake8 to catch syntax errors"
- "If any test fails, the commit is flagged and I am notified — no broken code silently reaches the main branch"

**"Why do you test data generation code? Isn't it just fake data?"**
- "Because data quality bugs are silent and expensive"
- "If is_successful starts producing values other than 0 and 1, the ML model trains on bad data and gives confident but wrong predictions — you would not know until results stopped making sense downstream"
- "A test that catches this in 2 seconds on every push is far cheaper than debugging a corrupted model three days later"
- "I test the business rules that, if broken, cause silent failures: no null IDs, FADR within a realistic range, failure reason is null when a delivery succeeded"



---

## Data Modelling

**"Are you familiar with Kimball data modelling?"**
- "Yes — the dbt structure in this project follows it"
- "Kimball's approach has staging tables that clean raw data without business logic, fact tables that store measurable business events at a defined grain, and dimension tables that describe context"
- "In this project: stg_deliveries_cleaned is the staging layer, mart_fadr_by_city_and_address is the fact layer aggregated at city × address_type grain, and mart_fadr_by_window_and_alerts adds dimensional attributes like delivery_window and preference flags"
- "The staging → marts separation is the core of the Kimball warehouse lifecycle"

---

## Behavioural questions about the project

**"Why did you choose this problem to build a project around?"**
- "It came from a real experience — I missed 5 calls from a delivery partner during a meeting, the parcel got rescheduled, and I thought about the scale of that problem"
- "Millions of deliveries every day, each failed attempt costs fuel and time"
- "I wanted to quantify exactly how much and whether data could predict failures before they happen"
- "The problem felt genuine, not like a tutorial exercise"

**"What was the hardest part of building this?"**
- "Understanding when each tool belongs and when it does not"
- "It is easy to add tools just to list them on a CV — the harder discipline is being honest about why each one is there"
- "For example, PySpark on a 50,000-row dataset is not the natural choice — I used it to learn the scale API, and I know I need to be clear about that in an interview"
- "Getting that honest framing right took more thought than the code"

**"What would you do differently if you were building this for a real company?"**
- "The data is synthetic — in production I would need to handle real API authentication, pagination, and rate limits for ingestion"
- "The ML model would need a proper feature store and retraining pipeline, not a one-time script"
- "I would use Cloud Composer instead of local Airflow, and the BigQuery tables would have proper access controls and cost monitoring"
- "The architecture is the same — the operational maturity around it is what changes"

**"What is FADR and why does it matter?"**
- "First Attempt Delivery Rate — the percentage of deliveries that succeed on the first try"
- "Every failed attempt means a repeat trip: more fuel, more time for the delivery partner, more cost for the platform, more frustration for the customer"
- "At 100,000 daily deliveries with a 75% FADR, that is 25,000 repeat trips per day — at ₹45 per repeat trip, that is ₹11 lakh wasted daily"
- "A 1% improvement in FADR eliminates 1,000 of those trips and saves ₹16,000 per day — at scale, small percentages are large numbers"

---

## Questions to ask the interviewer

- These show you think like an engineer, not just a candidate:

- "What does your current data pipeline stack look like — batch, streaming, or both?"
- "How do you handle data quality failures in production — alerting, automatic reprocessing, or manual intervention?"
- "What is the approximate scale of data your pipelines process daily?"
- "How does the team currently manage dbt models — is there a review process for new transformations?"
- "What does the on-call rotation look like for pipeline failures?"

---

## The honest Spark answer (keep this ready)

- Every interviewer who sees PySpark on your CV will ask why you used it on a small dataset

- "The dataset I built has 50,000 rows — Pandas handles that easily"
- "I used PySpark to learn the distributed computing API: how DataFrames work across partitions, how window functions behave at scale, how Parquet partitioning affects query performance"
- "In production, a logistics platform has hundreds of millions of delivery records — the code is identical, the cluster handles the scale"
- "I used a small dataset locally so I could iterate fast while learning the right tool for that scale"

- Say this confidently and directly
- An interviewer who hears this respects it — it shows you understand appropriate tool selection, which is a senior engineering skill
