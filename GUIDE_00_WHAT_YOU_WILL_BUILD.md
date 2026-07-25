# Guide 00 — What You Will Build and Why

**Why this guide exists:** Read this before anything else. It gives you the full picture of what you are building, why each guide exists, and how they connect — so you never feel lost wondering "why am I doing this step."

Read this before you start anything. It answers three questions:
- What will I actually see when this is done?
- What do I learn from each part?
- How does this help me get a job?

---

## What you will see at the end

### 1. A live web dashboard (browser, localhost:8501)

Run `streamlit run src/dashboard.py` and open your browser. You will see:

- **Headline numbers** — overall FADR (First Attempt Delivery Rate) (e.g. 74.3%), total failed deliveries, how many needed a second attempt
- **Bar chart: FADR by delivery window** — morning slots fail 35% more than evening slots, visible immediately
- **Bar chart: FADR by address type** — apartments and PGs at the bottom, offices at the top
- **Impact comparison** — customers with a saved delivery preference succeed 8–10% more often
- **City heatmap** — Mumbai × Apartment × Morning = the worst combination, colour-coded
- **Business impact calculator** — you type any daily volume (e.g. 100,000) and it calculates: at current FADR, ₹11 lakh is wasted per day on repeat trips. Improve FADR by 5% and save ₹4 lakh/day

- This is not a static image.
- It is an interactive web app — you change inputs, the numbers update.

---

### 2. A real-time event stream (two terminals)

Run `python src/kafka_producer.py` in one terminal and `python src/kafka_consumer.py` in another.

Terminal 1 shows:
```
[0001] ✓ Mumbai       | Office             | DELIVERED
[0002] ✗ Delhi        | Apartment          | FAILED
[0003] → Bangalore    | PG/Hostel          | IN_TRANSIT
```

- Terminal 2 shows the consumer reading events as they arrive and printing a live FADR that updates every 10 messages.
- This simulates exactly what a delivery platform does in production — every status change from every delivery partner streams into a central system in real time.

---

### 3. A scheduled pipeline with a visual UI (browser, localhost:8080)

Run `docker-compose up` then open Airflow at `localhost:8080`. You will see:

- Your DAG (Directed Acyclic Graph) `delivery_optimisation_pipeline` listed
- Click it and see 5 tasks as boxes connected by arrows: `generate_raw_data → ingest_to_database → run_dbt_transformations → run_dbt_tests → export_mart_to_csv`
- Trigger it manually — watch each box turn green as it succeeds
- Click any task to see its full log output

- This is the same UI that data engineers at real companies use every day to monitor production pipelines.

---

### 4. A machine learning result

Run `python src/predict.py` and the terminal prints:

```
Accuracy : 83.4%
ROC-AUC (Receiver Operating Characteristic — Area Under Curve)  : 0.8821

Apartment + Morning window + No preferences → Success probability: 52.3%
Apartment + Evening window + Preferences set → Success probability: 78.1%

Improvement from preferences + better window: +25.8 percentage points
```

- This is the quantified answer to the original problem.
- The model learned from 40,000 historical deliveries that changing the window and adding preferences moves success probability by 25+ points for the hardest address type.

---

### 5. A GitHub repository

- At the end you push everything to GitHub.
- Anyone — a recruiter, a hiring manager, a fellow engineer — can go to your profile and see:

- 13 guide files explaining the full project
- Python code for every component
- SQL files and dbt models
- A Dockerfile and docker-compose.yml
- A GitHub Actions badge showing "tests passing" on every commit
- A clear README explaining what the project does and why

---

## What each guide teaches you and why it matters

| Guide | What you build | What you learn | Why it is on DE (Data Engineer) job descriptions |
|---|---|---|---|
| 01 | Python environment, Git | Virtual envs, pip (Pip Installs Packages), version control | Foundation — every project starts here |
| 02 | Synthetic data, API (Application Programming Interface) ingestion | Faker, SQLite, GET/POST with requests | Data comes from APIs in production, not CSV (Comma-Separated Values) files |
| 03 | 10 SQL (Structured Query Language) queries | Analytical SQL, GROUP BY, window functions | SQL is on 100% of DE job descriptions |
| 04 | dbt (Data Build Tool) models + tests | Staging → facts → marts (Kimball), data quality testing | dbt is the standard transformation tool in modern data teams |
| 05 | PySpark analysis | DataFrame API, window functions, Parquet, partition pruning | Spark is on 80%+ of DE job descriptions |
| 06 | Docker Compose stack | Containers, images, volumes, multi-service orchestration | Docker is on 85%+ of DE job descriptions |
| 07 | Airflow DAG | Scheduling, task dependencies, retries, monitoring | Airflow is on 75%+ of DE job descriptions |
| 08 | Kafka producer + consumer | Topics, partitions, offsets, consumer groups, real-time streams | Kafka is on 70%+ of DE job descriptions |
| 09 | Random Forest ML (Machine Learning) model | Feature engineering, train/test split, ROC-AUC, feature importance | Adds data science depth to the engineering story |
| 10 | Streamlit dashboard | Interactive web apps, visualisation, business impact framing | Makes results visible to non-technical stakeholders |
| 11 | BigQuery + GCS (Google Cloud Storage) + Pub/Sub | GCP (Google Cloud Platform) data warehouse, ELT (Extract, Load, Transform) pattern, BQ optimisation, managed streaming | GCP stack is on most cloud-native DE job descriptions |
| 12 | GitHub Actions CI/CD (Continuous Integration/Continuous Deployment) | Automated testing, lint checks, merge protection | CI/CD is on every senior DE job description |
| 13 | GitHub publish + CV entry | Portfolio presentation, interview language | The point of doing all of the above |

---

## How this helps you get a job

**What most candidates do:**
- List tools on a CV.
- Say "I know Spark" in an interview.
- Cannot answer "how does partition pruning work?" or "what is a consumer group?"

**What you will be able to do:**
- Point to running code.
- Explain why you chose each tool.
- Answer follow-up questions because you built it yourself and read the WHY for every step.

**The interview conversation this enables:**

*"Tell me about a data engineering project."*

- "I built a delivery optimisation pipeline end-to-end — the problem was that failed deliveries waste fuel and cost money, and I wanted to quantify how much and whether data could predict it"
- "The batch pipeline uses Airflow to schedule daily runs: Python generates data, it lands in GCS, loads into BigQuery, dbt transforms it into clean mart tables"
- "The real-time side uses Kafka — a producer streams delivery status events, a consumer reads them and computes a live FADR"
- "Everything runs with docker-compose up"
- "On top of that I trained a Random Forest model that predicts delivery success with 83% accuracy — the key finding is that apartments in morning windows fail 35% more, and customers who set delivery preferences succeed 25 points higher"
- "The whole thing is on GitHub with CI/CD running 7 automated tests on every push"

- That answer covers: pipeline architecture, GCP, dbt, Airflow, Kafka, Docker, ML, CI/CD, and business impact — in one minute, from one project.

---

## Realistic expectation

- This project, done properly and understood deeply, makes you competitive for **0–2 year data engineering roles**.
- It covers the core stack that most entry-level and junior JDs ask for.
- What it cannot replace is experience from a real production system — scale, on-call incidents, team collaboration, legacy code.
- But it closes the technical gap significantly and gives you something concrete to talk about in every interview.

- **Start with Guide 01. Do every command yourself. Read the WHY for each step. That is the whole point.**
