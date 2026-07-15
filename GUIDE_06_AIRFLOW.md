# Guide 05 — Pipeline Orchestration with Apache Airflow

**Goal:** Use Apache Airflow to schedule and monitor the full pipeline: generate data → ingest → transform → export. Airflow is the most widely used orchestration tool in data engineering.

---

## Why Airflow?

A data pipeline that only runs when you manually type a command is not a production pipeline. Airflow schedules pipelines to run automatically, handles failures, retries failed steps, sends alerts, and gives you a visual map of every pipeline run.

It is on almost every data engineering job description. Understanding DAGs (Directed Acyclic Graphs) is essential.

---

## What is a DAG?

**What a DAG is in plain terms:** A DAG (Directed Acyclic Graph) is simply a pipeline where each step is a "task," tasks run in a defined order (directed), and there are no loops — it always moves forward (acyclic). In Airflow, the whole pipeline is defined as a DAG: a Python file that lists tasks and says which one must finish before the next one starts.

**What a task is vs a DAG:** A DAG is the whole pipeline. A task is one individual step inside that pipeline — for example "run the data generation script" is one task, "run dbt (Data Build Tool)" is another. Each task is a discrete, named, retryable unit of work.

A DAG is a pipeline definition. It has:
- **Tasks**: individual steps (run a script, run SQL (Structured Query Language), call an API (Application Programming Interface))
- **Dependencies**: which task must finish before the next one starts
- **Schedule**: when to run (daily, hourly, on demand)
- **No cycles**: tasks flow in one direction only — no loops

Your pipeline DAG looks like:

```
generate_data → ingest_to_db → run_dbt_models → export_mart
                                                      ↓
                                              notify_complete
```

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
git checkout -b feature/guide-06-airflow
```
**What `-b` means:** Create a new branch AND switch to it. Without `-b`, checkout only switches to an existing branch.

**Why a new branch for every guide:** Each branch is one unit of work. If something breaks, you can delete the branch and start fresh without affecting develop or main. In an office, each feature or fix lives on its own branch for the same reason.

Confirm you are on the right branch:
```bash
git branch
```
You will see a `*` next to your current branch. That `*` means "you are here".

---

## Step 5.1 — Initialise Airflow

```bash
export AIRFLOW_HOME=$(pwd)/airflow_home
airflow db init
```

**Why:** Airflow needs its own database to track task runs, logs, and state. `airflow db init` creates it. `AIRFLOW_HOME` tells Airflow where to store everything.

On Windows (Command Prompt, NOT Git Bash):
```cmd
set AIRFLOW_HOME=%CD%\airflow_home
airflow db init
```

---

## Step 5.2 — Create `dags/delivery_pipeline.py`

Create the `dags/` folder first:
```bash
mkdir dags
```

Create the file `dags/delivery_pipeline.py`:

**How to create this file:**
```bash
notepad dags/delivery_pipeline.py
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'daksha',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

def run_generate():
    import subprocess
    result = subprocess.run(['python', 'src/generate_data.py'], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Data generation failed: {result.stderr}")

def run_ingest():
    import subprocess
    result = subprocess.run(['python', 'src/ingest.py'], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Ingestion failed: {result.stderr}")

def run_export():
    import sqlite3
    import pandas as pd
    conn = sqlite3.connect('data/delivery_db.sqlite')
    df = pd.read_sql("SELECT * FROM fadr_by_segment", conn)
    df.to_csv('data/processed/fadr_mart.csv', index=False)
    conn.close()
    print(f"Exported {len(df)} rows to data/processed/fadr_mart.csv")

with DAG(
    dag_id='delivery_optimisation_pipeline',
    default_args=default_args,
    description='End-to-end delivery FADR pipeline',
    schedule_interval='@daily',          # runs every day at midnight
    # What @daily means: a shorthand schedule meaning "run once every day at
    # midnight." Airflow also supports cron expressions like '0 6 * * *' (6am daily)
    # for more precise scheduling.
    start_date=datetime(2024, 1, 1),
    catchup=False,
    # What catchup=False means: if a DAG has a start_date in the past, Airflow
    # would normally "catch up" by running a separate job for every missed day.
    # catchup=False tells Airflow to skip the historical backfill and only run
    # from now forward — which is what you want for a new pipeline.
    tags=['delivery', 'fadr', 'logistics'],
) as dag:

    # What PythonOperator is: a task that runs a Python function you define.
    # You pass python_callable=your_function and Airflow calls it when the task executes.
    t1_generate = PythonOperator(
        task_id='generate_raw_data',
        python_callable=run_generate,
    )

    t2_ingest = PythonOperator(
        task_id='ingest_to_database',
        python_callable=run_ingest,
    )

    # What BashOperator is: a task that runs a shell command (a bash command).
    # Use it when you want to run a CLI tool like dbt that doesn't have a Python API.
    t3_dbt = BashOperator(
        task_id='run_dbt_transformations',
        bash_command='cd delivery_dbt && dbt run --profiles-dir ~/.dbt',
    )

    t4_test = BashOperator(
        task_id='run_dbt_tests',
        bash_command='cd delivery_dbt && dbt test --profiles-dir ~/.dbt',
    )

    t5_export = PythonOperator(
        task_id='export_mart_to_csv',
        python_callable=run_export,
    )

    # What >> means: the "bit shift right" operator in Airflow sets dependencies.
    # t1 >> t2 means "t2 must not start until t1 finishes successfully."
    # This chain means each task waits for the previous one to complete.
    # Define the dependency chain
    t1_generate >> t2_ingest >> t3_dbt >> t4_test >> t5_export
```

---

## Step 5.3 — Copy the DAG to Airflow's DAGs folder

```bash
cp dags/delivery_pipeline.py airflow_home/dags/
```

---

## Step 5.4 — Start the Airflow web server

Open two separate terminal windows.

**Terminal 1:**
```bash
export AIRFLOW_HOME=$(pwd)/airflow_home
airflow webserver --port 8080
```

**Terminal 2:**
```bash
export AIRFLOW_HOME=$(pwd)/airflow_home
airflow scheduler
```

---

## Step 5.5 — Open the Airflow UI

Go to `http://localhost:8080` in your browser.

Default credentials:
- Username: `admin`
- Password: (shown in terminal when you first ran `airflow db init`)

You will see your DAG `delivery_optimisation_pipeline` listed.

---

## Step 5.6 — Trigger a manual run

In the Airflow UI:
1. Find `delivery_optimisation_pipeline`
2. Click the play button (Trigger DAG)
3. Watch each task turn green as it succeeds

**Why this matters:** Being able to show a running Airflow DAG in a portfolio interview is extremely powerful. It demonstrates you understand production-grade orchestration, not just scripts.

---

## Step 5.7 — Understanding what you built

| Concept | What you did |
|---|---|
| DAG | Defined the pipeline as code in Python |
| Task | Each step is a discrete, named, retryable unit |
| Dependencies | `>>` operator sets execution order |
| Schedule | `@daily` means this runs automatically every day |
| Retry logic | `retries: 2` means failed tasks retry twice before alerting |

---

## Step 5.8 — Commit

```bash
git add dags/
git commit -m "Add Airflow DAG for end-to-end delivery pipeline orchestration"
```

---

## Checkpoint

You now have:
- A full scheduled pipeline that runs daily
- Visual monitoring of every task
- Automatic retries on failure
- Version-controlled pipeline code

---

## Git Checkpoint — End of Guide 06

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
git add dags/delivery_pipeline.py
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
git commit -m "Guide 06: Airflow DAG orchestrating 5-task delivery pipeline with daily schedule"
```
**What a commit is:** A permanent snapshot saved in Git's history. Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`). You can always return to this exact state.

**What makes a good commit message:**
- Good: `"Guide 06: Airflow DAG orchestrating 5-task delivery pipeline with daily schedule"`
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
e2c5a9b Guide 06: Airflow DAG orchestrating 5-task delivery pipeline with daily schedule
d9a3b1f Guide 05: PySpark analysis with window functions, feature engineering, Parquet output
9b2c3d1 Initial commit: project guides and README
```

**In an office:** `git log --oneline` is one of the most used commands. It gives you the full history of the branch at a glance.

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-06-airflow
```
**What `git push` does:** Uploads your local commits to GitHub. Until you push, your commit only exists on your laptop.

**What `-u` means:** Sets the upstream — links your local branch to a branch of the same name on GitHub. You only need `-u` the first time you push a new branch. After that, just `git push` is enough.

**What `origin` means:** The name of your GitHub remote. When you ran `git remote add origin ...` in Guide 00B, you named it `origin`. That name sticks.

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-06-airflow had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-06-airflow` ← what you are merging in
3. Title: `Guide 06: Airflow pipeline orchestration`
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
You should now see your Guide 06 commit in develop's history. Confirm it is there.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-06-airflow
```
**What `-d` means:** Delete the branch locally. Git will refuse to delete if the branch has unmerged commits — a safety guard. Since you just merged the PR, `-d` works.

```bash
git push origin --delete feature/guide-06-airflow
```
Deletes the branch on GitHub too.

**Why delete?** Merged branches are dead branches. Keeping them clutters the repository. In real teams, merged branches are always deleted. A clean repo = a professional habit.

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-07-kafka
```

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 06 commit is in the history
- **Branches** → feature/guide-06-airflow is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_07_KAFKA.md](GUIDE_07_KAFKA.md) — Handle real-time delivery events with Apache Kafka
