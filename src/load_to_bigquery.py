from google.cloud import bigquery
import pandas as pd
import os

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
DATASET    = "delivery_raw"
TABLE      = "deliveries"

def load_csv_to_bigquery():
    client = bigquery.Client(project=PROJECT_ID)
    df = pd.read_csv("data/raw/deliveries.csv")
    print(f"Loaded {len(df):,} rows from CSV")
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    table = client.get_table(table_id)
    print(f"Loaded {table.num_rows:,} rows into {table_id}")
    print(f"Schema: {[f.name for f in table.schema]}")

if __name__ == "__main__":
    load_csv_to_bigquery()
