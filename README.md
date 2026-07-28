# Delivery Optimisation — End-to-End Data Engineering Pipeline

A production-style data pipeline that predicts last-mile delivery success before a delivery attempt is made — reducing failed deliveries, repeat trips, and operational cost.

---

## The Problem

At scale, even a 1% improvement in first-attempt delivery success eliminates thousands of repeat trips per day. This project asks: **can data tell you, before the delivery happens, whether it will succeed?**

Key finding from the data:
- Worst case (Apartment + Morning + no preferences): ~52% success rate
- Best case (Office + Evening + preferences set): ~90% success rate
- Changing delivery conditions improves success probability by **~25–30 percentage points**

---

## Architecture

```
Raw Events (REST API / Faker)
        ↓
   SQLite / CSV
        ↓
   dbt (SQL Transforms)     ←— staging → facts → marts (Kimball pattern)
        ↓
   Apache Airflow            ←— scheduled batch pipeline with retries
        ↓
   Apache Kafka              ←— real-time delivery status stream
        ↓
   scikit-learn ML Model     ←— predicts delivery success probability
        ↓
   Streamlit Dashboard       ←— visualises results for non-technical users
        ↓
   BigQuery + GCP            ←— same pipeline on cloud infrastructure
```

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Data Generation | Python, Faker, REST API (`requests`) |
| Storage | SQLite, CSV, Parquet, Google Cloud Storage |
| Transformation | dbt (staging → facts → marts) |
| Scale Processing | PySpark (window functions, partitioning) |
| Orchestration | Apache Airflow (DAGs, scheduling, retries) |
| Streaming | Apache Kafka (producer/consumer) |
| ML | scikit-learn (classification, feature engineering) |
| Dashboard | Streamlit |
| Cloud | BigQuery, GCS, Pub/Sub (GCP) |
| Containerisation | Docker, Docker Compose |
| CI/CD | GitHub Actions (pytest, flake8) |

---

## Project Structure

```
delivery-optimisation/
├── src/                    ← Python source code
│   ├── ingest/             ← Data ingestion scripts
│   ├── transform/          ← PySpark transformation logic
│   ├── ml/                 ← Model training and prediction
│   └── dashboard/          ← Streamlit app
├── dags/                   ← Airflow DAG definitions
├── delivery_dbt/           ← dbt models (staging, facts, marts)
│   └── models/
│       ├── staging/
│       ├── facts/
│       └── marts/
├── sql/                    ← Raw SQL analysis queries
├── tests/                  ← pytest unit tests
├── data/
│   ├── raw/                ← Generated CSV files
│   └── processed/          ← Cleaned outputs and Parquet files
├── models/                 ← Saved ML model files
├── notebooks/              ← Jupyter exploration
├── docker-compose.yml      ← Full stack in one command
├── Dockerfile
├── requirements.txt
└── .github/workflows/      ← CI/CD pipeline (GitHub Actions)
```

---

## Getting Started

**Prerequisites:** Python 3.9+, Docker Desktop, Git

```bash
# Clone the repo
git clone https://github.com/gittdaksha/delivery-optimisation.git
cd delivery-optimisation

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Run the full stack with Docker:**
```bash
docker-compose up
```

**Run tests:**
```bash
pytest tests/
```

---

## Key Insights From the Data

| Condition | Delivery Success Rate |
|-----------|----------------------|
| Office + Evening + preferences set | ~90% |
| Any location + Evening | ~72% |
| Apartment + Morning + no preferences | ~52% |

Morning deliveries fail ~35% more than evening ones. Customers who set a delivery preference fail ~8–10% less. A 15-minute proximity alert reduces missed-door failures by ~6–8%.

---

## CI/CD

Every push to `main` triggers automated checks via GitHub Actions:
- `pytest` — 7 unit tests across pipeline components
- `flake8` — code style linting

---

## Author

**Daksha Kurhade** — Data Analyst, Air India | IIT Delhi  
[GitHub](https://github.com/gittdaksha) · [LinkedIn](https://linkedin.com/in/dakshakurhade)
