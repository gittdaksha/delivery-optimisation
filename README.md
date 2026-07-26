# Delivery Optimisation — Data Engineering Project

## The Problem

A delivery partner called 5 times. The customer was in a meeting. The parcel got rescheduled.

The partner's route got delayed. Fuel was wasted. It cost the platform money. The customer was frustrated. Nobody won.

This isn't a technology failure. The system is working exactly as designed — it's optimised for routing efficiency, not for whether the customer is actually home. At millions of deliveries per day, even a 1% improvement in first-attempt success eliminates thousands of repeat trips daily.

**The question this project asks: can data tell you, before the delivery happens, whether it will succeed?**

---

## What This Project Does

This project builds a realistic data pipeline for that question. It is not a toy script. It follows the same architecture that logistics companies like Delhivery, Amazon, and Zomato actually use:

- Raw events land from an operational system
- A batch pipeline cleans, transforms, and stores them for analysis
- A real-time stream handles events as they happen
- An ML model learns patterns from historical data to predict future outcomes
- A dashboard makes the findings visible to people who don't write code

Each layer uses the tool that is genuinely the right fit for that job. Nothing is added just to make the CV look longer.

---

## The Sequence — and Why It Is This Order

The order mirrors how a real data platform is built. Each step has a reason.

```
Raw Data
   ↓
[01] Setup           — environment before anything else
   ↓
[02] Generate Data   — you need data before you can do anything with it
   ↓
[03] SQL Analysis    — understand the data before transforming it
   ↓
[04] dbt             — formalise transformations once you understand the data
   ↓
[05] PySpark         — process that same data at scale, the production way
   ↓
[06] Docker          — package all services so they run anywhere with one command
   ↓
[07] Airflow         — once the pipeline works, automate and schedule it
   ↓
[08] Kafka           — real-time events are a separate concern, separate tool
   ↓
[09] ML Model        — with clean reliable data, build the predictive layer
   ↓
[10] Dashboard       — with results, make them visible to non-technical people
   ↓
[11] BigQuery        — run the same SQL and dbt models on GCP production infra
   ↓
[12] CI/CD           — automate testing so broken code never reaches main branch
   ↓
[13] GitHub          — project is complete, now publish it
```

**Why BigQuery comes after the local pipeline, not before:** You learn the concepts locally first — SQLite has no setup friction, no billing, no accounts. Once you know what the pipeline does, BigQuery is a target swap. The SQL is identical. The dbt models are identical. You only change the connection config. Learning it in that order means you understand what BigQuery is replacing, not just how to click buttons in a console.

**Why CI/CD comes after BigQuery:** You need a complete, tested pipeline before you automate quality checks on it. CI/CD enforces "the pipeline must pass before merging" — that only makes sense once there is a pipeline worth protecting.

**Why GitHub is last:** Committing as you go is covered in each guide. Publishing the final project to a public repo is the last step because you are publishing something complete, not a work-in-progress.

---

## What You Will Learn and Why Each Tool Is Here

| Guide | Tool | Why this tool specifically |
|---|---|---|
| 01 | Python, pip, venv, Git | Every data project starts with environment isolation and version control |
| 02 | Python, Faker, SQLite, REST API | You need realistic data. Faker generates it. SQLite stores it. Plus: API ingestion (GET/POST with `requests`) — because in production data comes from APIs, not CSVs |
| 03 | SQL | SQL is the primary language of data. Understand the data here before touching any pipeline tool |
| 04 | dbt | The standard way to manage SQL transformations in teams — version controlled, tested, documented. Sits on top of SQL, not instead of it. The structure you build is Kimball's staging → facts → marts pattern |
| 05 | PySpark | When data is too large for one machine, Spark distributes it. Same DataFrame logic, cluster scale. Window functions and Parquet are tested in nearly every DE interview |
| 06 | Docker | Multiple services (Airflow, Kafka, Postgres) need to start together consistently. Docker Compose does that with one command, identically on every machine |
| 07 | Airflow | The batch pipeline needs to run on a schedule with retries and monitoring. That is specifically Airflow's job — not a general scripting task |
| 08 | Kafka | Batch pipelines run hourly or daily. But delivery status changes happen right now — partner marks parcel delivered in the field. That continuous stream needs a different system. Kafka is that system |
| 09 | scikit-learn | With a clean, reliable data pipeline behind it, ML has something worth predicting on. The model answers: can we know before the delivery whether it will succeed? |
| 10 | Streamlit | The model output and SQL results sitting in files are invisible to anyone who does not write code. Streamlit turns them into a usable web app |
| 11 | BigQuery, GCS, Pub/Sub | BigQuery: same SQL and dbt models, now on GCP. GCS: the real ELT landing zone — CSV lands in Cloud Storage first, BigQuery loads from there. BigQuery optimisation: partitioning by date + clustering by city. Pub/Sub: the GCP-managed version of the Kafka producer/consumer you built in Guide 07 — same concept, no infrastructure to manage |
| 12 | GitHub Actions (CI/CD) | Every JD lists CI/CD alongside Git. This step automates running your tests on every push so broken code cannot reach the main branch silently |
| 13 | GitHub | Project is complete. You publish it so others can see it, run it, and evaluate it |

---

## What the Data Will Show You

Once you run the pipeline, these are the patterns you will find in your own data:

- Morning (9–12am) deliveries fail ~35% more than evening ones — most people are at work
- Apartments and PGs fail ~20% more than offices — access restrictions, intercoms
- Customers who set a delivery preference fail ~8–10% less
- A 15-minute proximity alert before arrival reduces missed-door failures by ~6–8%
- Worst combination: Apartment + Morning + no preferences ≈ 52% success rate
- Best combination: Office + Evening + preferences set ≈ 90% success rate

The ML model (Guide 09) quantifies the gap: changing from worst to best combination improves success probability by ~25–30 percentage points. That is the data proof of the problem your LinkedIn post described.

---

## Project Structure

```
Delivery Optimisation/
├── README.md
├── GUIDE_00_WHAT_YOU_WILL_BUILD.md  ← Read this first
├── GUIDE_00B_GIT_WORKFLOW.md        ← Read this second, before any commands
├── GUIDE_00C_GLOSSARY.md            ← Full forms of every term — bookmark this
├── GUIDE_01_SETUP.md
├── GUIDE_02_DATA.md
├── GUIDE_03_SQL.md
├── GUIDE_04_DBT.md
├── GUIDE_05_PYSPARK.md
├── GUIDE_06_DOCKER.md
├── GUIDE_07_AIRFLOW.md
├── GUIDE_08_KAFKA.md
├── GUIDE_09_ML.md
├── GUIDE_10_DASHBOARD.md
├── GUIDE_11_BIGQUERY.md
├── GUIDE_12_CICD.md
├── GUIDE_13_GITHUB.md
├── GUIDE_14_INTERVIEW_PREP.md       ← Read before any interview
│
├── src/                    ← Python source code
├── sql/                    ← Raw SQL and dbt models
├── dags/                   ← Airflow DAG definitions
├── data/raw/               ← Generated CSV files
├── data/processed/         ← Cleaned outputs and Parquet
├── models/                 ← Saved ML model files
├── notebooks/              ← Jupyter exploration
├── docker-compose.yml      ← Full stack in one file
└── Dockerfile              ← Python pipeline container
```

---

## Start Here

Before touching any code, read [GUIDE_00_WHAT_YOU_WILL_BUILD.md](GUIDE_00_WHAT_YOU_WILL_BUILD.md) — it shows exactly what you will see when the project is done and how each guide connects to a job description.

Then open [GUIDE_01_SETUP.md](GUIDE_01_SETUP.md).

Each guide gives you the exact command to run, explains why that command exists, and tells you what to expect as output. You run every command yourself — that is how you actually learn it.
