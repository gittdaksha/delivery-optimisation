from datetime import datetime, timedelta  # datetime for start_date; timedelta for delays
from airflow import DAG  # DAG class: defines the whole pipeline
from airflow.operators.python import PythonOperator  # runs a Python function as a task
from airflow.operators.bash import BashOperator  # runs a shell command as a task

default_args = {  # default settings applied to every task in this DAG
    'owner': 'daksha',  # who owns this pipeline (shown in Airflow UI)
    'retries': 2,  # retry a failed task up to 2 times before marking it failed
    # timedelta(minutes=5) = a duration object representing exactly 5 minutes
    # → e.g. timedelta(hours=1) = 1 hour wait; timedelta(days=1) = 24-hour wait
    # → used here to say "wait 5 minutes before trying the failed task again"
    'retry_delay': timedelta(minutes=5),  # wait 5 minutes between retries
    'email_on_failure': False,  # don't send email alerts (no email configured)
}

def run_generate():  # Python function Airflow calls for the data generation task
    import subprocess  # lets Python run other programs/scripts
    # subprocess.run(['python', 'src/generate_data.py'], ...) = runs that command in a shell
    # → same as typing: python src/generate_data.py  in your terminal
    # → capture_output=True = capture what the script prints (stdout) and any errors (stderr)
    # → text=True = return stdout/stderr as a Python string, not raw bytes
    result = subprocess.run(['python', 'src/generate_data.py'], capture_output=True, text=True)  # run script; capture stdout+stderr
    print(result.stdout)  # show the script's printed output in Airflow logs
    # result.returncode = the exit code the script returned when it finished
    # → 0 means success (universal convention in all operating systems)
    # → anything else (1, 2, -1 ...) means the script crashed or reported an error
    if result.returncode != 0:  # non-zero code = script crashed
        raise Exception(f"Data generation failed: {result.stderr}")  # fail the task with error detail

def run_ingest():  # Python function Airflow calls for the ingest task
    import subprocess  # lets Python run other programs/scripts
    # Same pattern as run_generate above:
    # → runs 'python src/ingest.py' as a subprocess; captures its printed output and errors
    result = subprocess.run(['python', 'src/ingest.py'], capture_output=True, text=True)  # run ingest script; capture output
    print(result.stdout)  # show the script's printed output in Airflow logs
    if result.returncode != 0:  # non-zero code = script crashed
        raise Exception(f"Ingestion failed: {result.stderr}")  # fail the task with error detail

def run_export():  # Python function Airflow calls for the CSV export task
    import sqlite3  # built-in Python library for SQLite databases
    import pandas as pd  # pandas for reading SQL results into a dataframe
    conn = sqlite3.connect('data/delivery_db.sqlite')  # open the project database
    # pd.read_sql(sql, conn) = runs the SQL query and returns the results as a pandas DataFrame
    # → a DataFrame is a table of rows and columns you can work with in Python
    df = pd.read_sql("SELECT * FROM fadr_by_segment", conn)  # load the mart table into a dataframe
    # df.to_csv('path', index=False) = write the DataFrame to a CSV file
    # → index=False = do NOT write the row numbers (0, 1, 2...) as an extra column in the file
    # → without index=False the CSV gets an unwanted first column: 0, 1, 2, 3 ...
    df.to_csv('data/processed/fadr_mart.csv', index=False)  # save as CSV; index=False skips row numbers
    conn.close()  # always close DB connections to free resources
    print(f"Exported {len(df)} rows to data/processed/fadr_mart.csv")  # log the export count

# 'with DAG(...) as dag:' is a Python context manager
# → everything indented inside this block is part of this pipeline definition
# → 'as dag' assigns the created DAG object to the variable name 'dag'
with DAG(  # 'with DAG() as dag:' creates the pipeline definition object
    dag_id='delivery_optimisation_pipeline',  # unique pipeline name shown in Airflow UI
    # default_args = the dict you defined above; Airflow applies every key in it to all tasks
    # → so every task in this DAG automatically gets retries=2, retry_delay=5min, etc.
    # → you can still override these on individual tasks if needed
    default_args=default_args,  # apply the defaults dict defined above
    description='End-to-end delivery FADR pipeline',  # description shown in Airflow UI
    schedule_interval='@daily',          # runs every day at midnight
    # What @daily means: a shorthand schedule meaning "run once every day at
    # midnight." Airflow also supports cron expressions like '0 6 * * *' (6am daily)
    # for more precise scheduling.
    # datetime(2024, 1, 1) = creates a date object for January 1st 2024
    # → datetime(year, month, day): the pipeline will not schedule any run before this date
    start_date=datetime(2024, 1, 1),  # pipeline will not run before this date
    catchup=False,  # don't backfill missed runs from start_date to today
    # What catchup=False means: if a DAG has a start_date in the past, Airflow
    # would normally "catch up" by running a separate job for every missed day.
    # catchup=False tells Airflow to skip the historical backfill and only run
    # from now forward — which is what you want for a new pipeline.
    tags=['delivery', 'fadr', 'logistics'],  # labels for filtering in Airflow UI
) as dag:  # 'as dag' assigns the pipeline object to the variable 'dag'

    # What PythonOperator is: a task that runs a Python function you define.
    # You pass python_callable=your_function and Airflow calls it when the task executes.
    t1_generate = PythonOperator(  # task 1: generate raw delivery data
        task_id='generate_data_py',  # matches src/generate_data.py
        python_callable=run_generate,  # the function to call when this task runs
    )

    t2_ingest = PythonOperator(  # task 2: ingest data to SQLite database
        task_id='ingest_py',  # matches src/ingest.py
        python_callable=run_ingest,  # the function to call when this task runs
    )

    # What BashOperator is: a task that runs a shell command (a bash command).
    # Use it when you want to run a CLI tool like dbt that doesn't have a Python API.
    t3_dbt = BashOperator(  # task 3: run dbt transformation models
        task_id='dbt_run_transformations',  # dbt has no single script file; name reflects the dbt command
        # 'cd delivery_dbt && dbt run ...' = two shell commands joined by &&
    # → cd delivery_dbt  = move into the delivery_dbt folder first
    # → &&              = only run the second command IF the first succeeded (exit code 0)
    # → dbt run         = run all dbt transformation models
    # → --profiles-dir ~/.dbt = tell dbt where to find database credentials
    bash_command='cd delivery_dbt && dbt run --profiles-dir ~/.dbt',  # cd to dbt dir, then run models
    )

    t4_test = BashOperator(  # task 4: run dbt data quality tests
        task_id='dbt_test_data_quality',  # dbt has no single script file; name reflects the dbt command
        # Same && pattern as above: cd first, then only run 'dbt test' if cd succeeded
        # → dbt test = runs all tests defined in your dbt schema.yml files
        bash_command='cd delivery_dbt && dbt test --profiles-dir ~/.dbt',  # cd to dbt dir, then test data quality
    )

    t5_export = PythonOperator(  # task 5: export the mart table to CSV
        task_id='export_mart_py',  # matches src/export_mart.py (runs inline export function)
        python_callable=run_export,  # the function to call when this task runs
    )

    # What >> means: the "bit shift right" operator in Airflow sets dependencies.
    # t1 >> t2 means "t2 must not start until t1 finishes successfully."
    # This chain means each task waits for the previous one to complete.
    # → t1_generate >> t2_ingest = t2 waits for t1 to succeed
    # → t2_ingest >> t3_dbt      = t3 waits for t2 to succeed
    # → you can chain as many as you like: A >> B >> C >> D >> E
    # → if t2 fails, t3, t4, and t5 are all skipped automatically
    # Define the dependency chain
    t1_generate >> t2_ingest >> t3_dbt >> t4_test >> t5_export  # run tasks in this exact order