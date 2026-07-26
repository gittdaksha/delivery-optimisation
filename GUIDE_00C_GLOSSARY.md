# Guide 00C — Full Forms and Glossary

**Why this guide exists:** The guides use many abbreviations (FADR, dbt, DAG, CSV, ML, CI/CD). Instead of explaining each one every time it appears, they are all collected here. When you see a term you do not recognise, check this file first.

- Every abbreviation, acronym, and technical term used across all guides — with its full form and a one-line plain-English meaning.

- Bookmark this file.
- When you encounter a term you do not recognise, check here first.

---

## Project-Specific Terms

| Short Form | Full Form | What it means |
|---|---|---|
| FADR | First Attempt Delivery Rate | The percentage of deliveries that succeed on the very first try — the core metric of this project |
| DE | Data Engineer | The job role this project is built for — someone who designs, builds, and maintains data pipelines |
| JD | Job Description | The requirements list a company posts when hiring |
| pp | Percentage Points | A direct difference between two percentages. "Up 25pp" means the number increased by 25 percentage points |
| CV | Curriculum Vitae | Another word for resume — a document listing your education, skills, and work experience |

---

## General Computing

| Short Form | Full Form | What it means |
|---|---|---|
| OS | Operating System | The software that runs your computer — Windows, macOS, Linux |
| CPU | Central Processing Unit | The main processor chip in your computer — does all the calculations |
| RAM | Random Access Memory | Short-term memory your computer uses while programs are running |
| CLI | Command Line Interface | A text-based interface where you type commands — your terminal/bash window |
| GUI | Graphical User Interface | A visual interface with buttons and windows — what you normally use |
| IDE | Integrated Development Environment | A code editor with extra tools — VS Code is one |
| VM | Virtual Machine | A software-based computer running inside your real computer |
| URL | Uniform Resource Locator | A web address — e.g. `https://github.com/your-repo` |
| SDK | Software Development Kit | A set of tools and libraries provided by a service to help you build on it — e.g. GCP SDK |

---

## Terminal / Command Line

| Short Form / Term | Full Form | What it means |
|---|---|---|
| `cd` | Change Directory | Moves your terminal's location into a different folder |
| `pwd` | Print Working Directory | Shows the full path of the folder your terminal is currently in |
| `mkdir` | Make Directory | Creates a new folder |
| `ls` | List | Lists all files and folders in the current directory (Linux/Mac) |
| `dir` | Directory | Same as `ls` but for Windows Command Prompt |
| `touch` | — | Creates an empty file (Linux/Mac/Git Bash) |
| bash | Bourne Again SHell | The most common Unix shell — the language your terminal commands are written in |
| flag | — | An option added to a command, always starting with `-` or `--`. Example: `-v` means "verbose" (show more detail) |
| PATH | — | A system variable listing folders where your OS looks for executable programs. "Adding Python to PATH" means your OS can find `python` when you type it |

---

## Python

| Short Form / Term | Full Form | What it means |
|---|---|---|
| pip | Pip Installs Packages | Python's package manager — used to install libraries |
| venv | Virtual Environment | An isolated folder holding a project's private Python and libraries |
| `import` | — | Loads a library into your Python script so you can use its functions |
| `def` | Define | Declares a function in Python |
| `__init__.py` | — | A file that marks a folder as a Python package — allows importing from it |
| `__name__` | — | A special Python variable. When you run a file directly, `__name__` equals `'__main__'`. When imported by another file, it equals the filename |
| `if __name__ == '__main__':` | — | Code under this line only runs when you execute the file directly, not when another file imports it |
| `-m` | Module | Tells Python to run a built-in module. `python -m venv` runs the venv module |
| `-c` | Command | Tells Python to run a string as code directly in the terminal |

---

## Data Formats and Storage

| Short Form / Term | Full Form | What it means |
|---|---|---|
| CSV | Comma-Separated Values | A plain text file where each row is a line and each column is separated by a comma. Opens in Excel |
| JSON | JavaScript Object Notation | A text format for structured data using curly braces and key-value pairs. Common for APIs |
| YAML | YAML Ain't Markup Language | A human-readable format for configuration files — uses indentation instead of brackets. Used in dbt, Airflow, Docker |
| Parquet | — | A columnar binary file format. Much faster and smaller than CSV for analytical queries. Standard in data lakes |
| SQLite | — | A file-based database — the entire database is stored in a single `.sqlite` file. No server required |
| DB | Database | An organised collection of structured data |
| UUID | Universally Unique Identifier | A 128-bit randomly generated ID that is practically guaranteed to be unique across all systems — looks like `3f2504e0-4f89-11d3-9a0c-0305e82c3301` |
| `.pkl` | Pickle | A Python binary file format for saving Python objects (like ML models) to disk |
| `.env` | Environment | A file that stores secret configuration values like API keys and passwords — never committed to Git |

---

## SQL

| Short Form / Term | Full Form | What it means |
|---|---|---|
| SQL | Structured Query Language | The language used to talk to databases — SELECT, INSERT, UPDATE, DELETE |
| `SELECT` | — | Chooses which columns to return |
| `FROM` | — | Specifies which table to read from |
| `WHERE` | — | Filters rows before any grouping |
| `GROUP BY` | — | Groups rows that share a value in a column so you can aggregate them |
| `HAVING` | — | Filters groups after GROUP BY — like WHERE but for aggregated results |
| `ORDER BY` | — | Sorts the result rows |
| `JOIN` | — | Combines rows from two tables based on a matching column |
| `AVG` | Average | Calculates the mean of a column |
| `COUNT` | — | Counts the number of rows |
| `SUM` | — | Adds up all values in a column |
| `ROUND` | — | Rounds a number to a specified number of decimal places |
| `CASE WHEN` | — | Conditional logic in SQL — like an if/else statement |
| CTE | Common Table Expression | A temporary named result set defined with `WITH name AS (...)` — makes complex queries readable |
| PK | Primary Key | A column (or set of columns) that uniquely identifies each row in a table |
| FK | Foreign Key | A column that references the primary key of another table — creates a relationship between tables |
| `IF NOT EXISTS` | — | Only runs the statement if the named thing does not already exist — prevents errors on re-runs |
| `WRITE_TRUNCATE` | — | A BigQuery option that deletes all existing rows before loading new ones |
| DDL | Data Definition Language | SQL commands that define structure — CREATE TABLE, ALTER TABLE, DROP TABLE |
| DML | Data Manipulation Language | SQL commands that modify data — INSERT, UPDATE, DELETE |

---

## dbt

| Short Form / Term | Full Form | What it means |
|---|---|---|
| dbt | Data Build Tool | A transformation framework — you write SQL, dbt runs it in the right order with tests and documentation |
| `{{ ref() }}` | Reference | dbt's way of referring to another model — `{{ ref('stg_deliveries') }}` means "use the output of the stg_deliveries model" |
| `{{ source() }}` | Source | dbt's way of referring to a raw source table — `{{ source('main', 'deliveries') }}` means "use the deliveries table from the main schema" |
| `profiles.yml` | — | dbt's connection configuration file — tells dbt which database to connect to |
| stg | Staging | The first transformation layer — cleans and casts raw data, no business logic |
| mart | — | The final transformation layer — business logic applied, ready for analysis |

---

## Apache Airflow

| Short Form / Term | Full Form | What it means |
|---|---|---|
| DAG | Directed Acyclic Graph | A pipeline definition where tasks flow in one direction with no loops — the core concept in Airflow |
| task | — | A single unit of work inside a DAG — run a script, execute SQL, call an API |
| `@daily` | — | A schedule shortcut meaning "run once per day at midnight" |
| `catchup=False` | — | Tells Airflow not to run all missed schedule intervals since the start date — only run the current one |
| `>>` | — | The dependency operator in Airflow — `task_a >> task_b` means task_b only starts after task_a finishes |
| LocalExecutor | — | Runs tasks as processes on the same machine as the Airflow scheduler |
| CeleryExecutor | — | Distributes tasks across multiple worker machines |

---

## Apache Spark / PySpark

| Short Form / Term | Full Form | What it means |
|---|---|---|
| Spark | — | Apache Spark — a distributed computing framework for processing large datasets |
| PySpark | Python for Spark | The Python API for Apache Spark |
| SparkSession | — | The entry point to Spark — you create one at the start of every Spark job |
| `local[*]` | — | Runs Spark on your local machine using all available CPU cores. `*` means "all cores" |
| DataFrame | — | A distributed table in Spark — like a pandas DataFrame but split across many machines |
| lazy evaluation | — | Spark does not execute until you call an action. Transformations (filter, groupBy) build a plan. Actions (count, show, write) execute it |
| action | — | A Spark operation that triggers execution — `.count()`, `.show()`, `.write()` |
| transformation | — | A Spark operation that builds the execution plan but does not run yet — `.filter()`, `.groupBy()`, `.withColumn()` |
| partition | — | A chunk of data. Spark splits data into partitions and processes them in parallel across workers |
| partition pruning | — | When Spark skips entire partitions that do not match a filter — reads less data, runs faster |

---

## Apache Kafka

| Short Form / Term | Full Form | What it means |
|---|---|---|
| Kafka | — | Apache Kafka — a distributed real-time message streaming platform |
| topic | — | A named channel in Kafka — like a table but for events. Producers write to it, consumers read from it |
| partition | — | A topic is split into partitions for parallelism — more partitions = more consumers reading simultaneously |
| offset | — | The position of a message within a partition — Kafka tracks this per consumer group |
| producer | — | A program that writes (publishes) messages to a Kafka topic |
| consumer | — | A program that reads (subscribes to) messages from a Kafka topic |
| consumer group | — | A set of consumers sharing the work of reading a topic — each partition goes to one consumer in the group |
| `bootstrap_servers` | — | The address(es) of the Kafka broker(s) your producer or consumer should connect to |
| `ack()` | Acknowledge | Tells Kafka "I have successfully processed this message" — Kafka will not re-deliver it |
| broker | — | A Kafka server that stores and serves messages |
| Zookeeper | — | A coordination service Kafka depends on for cluster management (being replaced in newer Kafka versions) |

---

## Docker

| Short Form / Term | Full Form | What it means |
|---|---|---|
| Docker | — | A platform for running applications in containers |
| container | — | A lightweight, isolated process that packages code + dependencies + OS layer together |
| image | — | A static blueprint for a container — like a class. A container is a running instance of an image |
| Docker Compose | — | A tool that manages multiple containers together using a single YAML file |
| `-d` | Detached | Runs containers in the background — your terminal is free to use while they run |
| `ports:` | — | Maps a port on your laptop to a port inside the container. `"8080:8080"` means your laptop's port 8080 connects to the container's port 8080 |
| `volumes:` | — | Mounts a folder from your laptop into the container so data persists after the container stops |
| `depends_on:` | — | Tells Docker Compose to start this service only after the named service has started |
| `healthcheck:` | — | A command Docker runs inside the container to verify it is truly ready — not just started |
| `environment:` | — | Sets environment variables inside the container — like system-level configuration |

---

## Machine Learning

| Short Form / Term | Full Form | What it means |
|---|---|---|
| ML | Machine Learning | Teaching a computer to find patterns in data without explicitly programming the rules |
| Random Forest | — | An ML algorithm that builds many decision trees and combines their answers — robust and accurate |
| train/test split | — | Dividing data into training data (model learns from this) and test data (model is evaluated on this — it never saw it during training) |
| `stratify=y` | — | Ensures the train and test sets have the same proportion of 0s and 1s as the full dataset |
| `n_jobs=-1` | — | Use all available CPU cores for training — speeds up the process |
| `predict()` | — | Returns the predicted class label (0 or 1) |
| `predict_proba()` | — | Returns the probability of each class (e.g. 78% chance of success) |
| ROC-AUC | Receiver Operating Characteristic — Area Under Curve | A measure of model quality from 0 to 1. 0.5 = random guessing. 1.0 = perfect. Above 0.8 is generally considered good |
| feature importance | — | How much each input variable contributed to the model's predictions — tells you which features matter most |
| overfitting | — | When a model memorises training data but fails on new data — why we use a test set |
| pickle | — | Python's built-in serialisation format — saves a Python object (like a trained model) as a binary file on disk |

---

## GCP — Google Cloud Platform

| Short Form / Term | Full Form | What it means |
|---|---|---|
| GCP | Google Cloud Platform | Google's suite of cloud computing services |
| GCS | Google Cloud Storage | GCP's object storage service — like a cloud hard drive for files |
| BigQuery | — | GCP's serverless data warehouse — runs SQL on massive datasets without managing servers |
| Pub/Sub | Publish/Subscribe | GCP's managed real-time messaging service — the GCP equivalent of Kafka |
| Cloud Composer | — | GCP's managed Airflow service — runs your Airflow DAGs without you managing the infrastructure |
| Dataflow | — | GCP's managed data processing service — runs Apache Beam pipelines |
| Dataproc | — | GCP's managed Spark and Hadoop service |
| Cloud Run | — | GCP's serverless container execution service — runs a Docker container without managing servers |
| `bq` | BigQuery CLI | The BigQuery command-line tool installed with the GCP SDK |
| `bq mk` | BigQuery Make | Creates a new dataset or table in BigQuery |
| `gcloud` | — | The main GCP command-line tool for managing GCP resources |
| `application-default login` | — | Saves your Google account credentials locally so Python scripts can authenticate to GCP automatically |
| `asia-south1` | — | GCP's Mumbai data centre region — keeps data in India |

---

## APIs

| Short Form / Term | Full Form | What it means |
|---|---|---|
| API | Application Programming Interface | A defined way for two programs to communicate — you send a request, it sends back data |
| REST | Representational State Transfer | A style of API design using HTTP methods — the most common type of API |
| HTTP | HyperText Transfer Protocol | The communication protocol the web runs on |
| GET | — | An HTTP method for fetching/reading data from an API |
| POST | — | An HTTP method for sending/creating data to an API |
| `status_code` | — | A number the API returns indicating success (200) or failure (404, 500) |
| `raise_for_status()` | — | A requests method that throws an error if the status code is 4xx or 5xx |
| JSON | JavaScript Object Notation | The data format most APIs use for sending and receiving data |
| endpoint | — | A specific URL on an API that performs a specific action — e.g. `/v1/orders` |
| authentication | — | Proving your identity to an API — usually via an API key or token in the request headers |

---

## CI/CD and Git

| Short Form / Term | Full Form | What it means |
|---|---|---|
| CI | Continuous Integration | Automatically running tests on every code change to catch problems early |
| CD | Continuous Deployment | Automatically deploying code that passes tests to a live environment |
| CI/CD | Continuous Integration / Continuous Deployment | The combined practice of automated testing and deployment |
| PR | Pull Request | A formal request to merge one branch into another — reviewed before merging |
| MR | Merge Request | Same as PR — GitLab uses this term, GitHub uses PR |
| `origin` | — | The conventional name for the remote repository on GitHub |
| `upstream` | — | The branch on GitHub that your local branch tracks — set with `-u` flag |
| commit | — | A saved snapshot of staged changes with a message |
| staging | — | The step before committing — you `git add` files to stage them |
| hash | — | The unique ID of a commit — a long string like `3a4f9c1` |
| `HEAD` | — | A pointer to your current position in Git history — usually the latest commit on your current branch |
| flake8 | — | A Python code linting tool — checks for syntax errors, undefined names, style issues |
| lint | — | The process of automatically checking code for errors and style problems |
| `--select=E9,F63` | — | Tells flake8 to only report specific error codes: E9 = syntax errors, F63/F7/F82 = undefined names |
| `runner` | — | The machine GitHub provides to run a workflow — `ubuntu-latest` is a Linux machine |
| workflow | — | A GitHub Actions automation script — defines what to run and when |
| `.github/workflows/` | — | The folder GitHub looks in for workflow YAML files |

---

## Streamlit / Dashboard

| Short Form / Term | Full Form | What it means |
|---|---|---|
| `@st.cache_data` | — | A decorator that saves the function's return value — if the function is called again with the same inputs, it returns the saved result instead of re-running |
| `@st.cache_resource` | — | Like `cache_data` but for shared resources like database connections and ML models — loaded once and reused |
| `st.columns()` | — | Divides the page into side-by-side sections |
| `st.metric()` | — | Displays a KPI tile — a large number with a label and optional delta (change indicator) |
| `st.divider()` | — | Draws a horizontal line to separate sections |
| KPI | Key Performance Indicator | A measurable value that shows how well something is performing — FADR is a KPI |

---

## Data Engineering Concepts

| Short Form / Term | Full Form | What it means |
|---|---|---|
| ETL | Extract, Transform, Load | Extract data from a source, transform it, load it into a destination |
| ELT | Extract, Load, Transform | Load raw data into the warehouse first, then transform it there — modern approach |
| ORM | Object-Relational Mapper | A library that lets you talk to a database using Python objects instead of raw SQL — SQLAlchemy is one |
| BI | Business Intelligence | Tools and processes for analysing data and presenting it to decision-makers — Power BI, Tableau |
| data warehouse | — | A central repository for structured, transformed data used for analysis — BigQuery, Snowflake |
| data lake | — | A storage system for raw, unprocessed data in any format — GCS, S3, ADLS |
| data lakehouse | — | A hybrid of data lake and warehouse — raw storage with warehouse-like query capability |
| Kimball | — | A data modelling methodology by Ralph Kimball — staging → facts → dimensions. The structure this project follows |
| fact table | — | A table that stores measurable business events at a defined grain — deliveries, transactions |
| dimension table | — | A table that provides context about facts — addresses, customers, time periods |
| grain | — | The level of detail one row in a fact table represents — e.g. "one row per delivery attempt" |
| partition | — | Dividing a large table or file into smaller pieces based on a column value — improves query performance |
| clustering | — | Sorting data within a partition by a column — further reduces data read in BigQuery |
| columnar storage | — | Storing data by column rather than by row — faster for queries that only read a few columns |
| schema | — | The structure definition of a table — its column names, data types, and constraints |
| lineage | — | A record of where data came from and how it was transformed — dbt generates this automatically |
| idempotent | — | A pipeline that produces the same result no matter how many times you run it — a quality all pipelines should have |
