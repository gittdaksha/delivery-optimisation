# Guide 07 — Pipeline Orchestration with Apache Airflow

**Goal:** Use Apache Airflow to schedule and monitor the full pipeline: generate data → ingest → transform → export. Airflow is the most widely used orchestration tool in data engineering.

---

## Why Airflow?

- A data pipeline that only runs when you manually type a command is not a production pipeline
- Airflow schedules pipelines to run automatically, handles failures, retries failed steps, sends alerts, and gives you a visual map of every pipeline run
- It is on almost every data engineering job description
- Understanding DAGs (Directed Acyclic Graphs) is essential

---

## What is a DAG?

**What a DAG is in plain terms:**
- A DAG (Directed Acyclic Graph) is simply a pipeline where each step is a "task," tasks run in a defined order (directed), and there are no loops — it always moves forward (acyclic)
- In Airflow, the whole pipeline is defined as a DAG: a Python file that lists tasks and says which one must finish before the next one starts

**What a task is vs a DAG:**
- A DAG is the whole pipeline
- A task is one individual step inside that pipeline — for example "run the data generation script" is one task, "run dbt (Data Build Tool)" is another
- Each task is a discrete, named, retryable unit of work

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
git checkout develop  # switch to the develop branch
```
**What this does:**
- Switches you to the develop branch
- You always create feature branches FROM develop, never from main and never from another feature branch

- No `-b` here — this switches to an existing branch
- You do not use `-b` when the branch already exists

```bash
git pull origin develop  # download + merge remote changes locally
```
**What this does:**
- Downloads any changes from GitHub that you do not have locally
- In an office, a colleague may have merged something since you last worked
- `pull` = download + merge in one command

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub

```bash
git status  # show current working tree state
```
**What this does:**
- Shows the current state
- You should see `On branch develop, nothing to commit, working tree clean`
- If you see modified files here, deal with them before moving forward — do not carry unrelated changes into a new branch

No flags here — `git status` always shows full current state.

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-07-airflow  # -b = create new branch and switch to it
```
**What `-b` means:**
- Create a new branch AND switch to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

**Why a new branch for every guide:**
- Each branch is one unit of work
- If something breaks, you can delete the branch and start fresh without affecting develop or main
- In an office, each feature or fix lives on its own branch for the same reason

Confirm you are on the right branch:
```bash
git branch  # list all branches; * marks current branch
```
- You will see a `*` next to your current branch
- That `*` means "you are here"

---

## Step 5.0 — Windows only: Install WSL2 before running Airflow

- Airflow does not run on Windows natively — it requires a Linux environment
- WSL2 (Windows Subsystem for Linux 2) gives you a real Linux terminal inside Windows — free and built into Windows 11
- You only need to do this once

**Step 1 — Open PowerShell as Administrator**
- Press the Windows key
- Type `PowerShell`
- Right-click it and select "Run as administrator"

**Step 2 — Install WSL2**
```powershell
wsl --install
```
- This installs WSL2 and Ubuntu (a Linux distribution) automatically
- It will ask you to restart your computer — do it

**Step 3 — After restart, Ubuntu opens automatically**
- It will ask you to create a Linux username and password
- Use a simple username (e.g. `daksha`) and a password you will remember
- This is separate from your Windows login

**Step 4 — Open Ubuntu from the Start menu from now on**
- Search "Ubuntu" in the Start menu and open it
- You now have a Linux terminal on your Windows machine

**Step 5 — Inside Ubuntu, navigate to your project**
```bash
cd "/mnt/c/Users/DakshaKurhade/OneDrive - AIR INDIA LIMITED/Desktop/Delivery Optimisation"
```
- WSL2 mounts your Windows drives under `/mnt/c/`
- Your project folder is accessible from inside Linux via this path

**Step 6 — Create and activate a virtual environment inside WSL2**
```bash
python3 -m venv venv
source venv/bin/activate
pip install apache-airflow
```

**Step 7 — Continue all Airflow steps below from inside the Ubuntu terminal**

---

## Step 5.1 — Initialise Airflow

```bash
export AIRFLOW_HOME=$(pwd)/airflow_home  # tell Airflow where to store all its files
airflow db init  # create Airflow's tracking database and default config
```

**Why:**
- Airflow needs its own database to track task runs, logs, and state
- `airflow db init` creates it
- `AIRFLOW_HOME` tells Airflow where to store everything

On Windows (Command Prompt, NOT Git Bash):
```cmd
set AIRFLOW_HOME=%CD%\airflow_home  # Windows version: set Airflow folder path
airflow db init  # create Airflow's tracking database and default config
```

---

## Step 5.2 — Create `dags/delivery_pipeline.py`

Create the `dags/` folder first:
```bash
mkdir dags  # create the folder where Airflow looks for DAG files
```

Create the file `dags/delivery_pipeline.py`:

**How to create this file:**
```bash
notepad dags/delivery_pipeline.py  # open Notepad to create this new file
```
- Notepad will open (or ask to create the file — click Yes)
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad

**What `dags/delivery_pipeline.py` does and why it exists:**
- **What it does:** Defines the entire pipeline as an Airflow DAG — telling Airflow which scripts to run, in what order, on what schedule, and what to do if a step fails
- **Why separate:** Without this file, the pipeline only runs when you manually type commands in a terminal. This file is what makes it automated — Airflow reads it, registers the schedule, and takes over running everything for you. If it did not exist, you would have to remember to run every script yourself, in the right order, every single day.
- **Input:** Schedule trigger (Airflow fires this DAG daily at midnight via `schedule_interval='@daily'`, or manually from the Airflow UI — no data file is read directly by the DAG file itself)
- **Output:** Runs all five pipeline scripts in order (`generate_data.py` → `ingest.py` → `dbt run` → `dbt test` → export mart to `data/processed/fadr_mart.csv`), with task status logged in the Airflow database
- **Pipeline position:** Individual scripts (`generate_data.py`, `ingest.py`, dbt models) already exist → **this DAG file** → Airflow runs them automatically every day in the correct sequence, retrying any step that fails, and showing you the result in a visual dashboard

```python
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
        task_id='generate_raw_data',  # unique name for this task in Airflow UI
        python_callable=run_generate,  # the function to call when this task runs
    )

    t2_ingest = PythonOperator(  # task 2: ingest data to SQLite database
        task_id='ingest_to_database',  # unique name for this task in Airflow UI
        python_callable=run_ingest,  # the function to call when this task runs
    )

    # What BashOperator is: a task that runs a shell command (a bash command).
    # Use it when you want to run a CLI tool like dbt that doesn't have a Python API.
    t3_dbt = BashOperator(  # task 3: run dbt transformation models
        task_id='run_dbt_transformations',  # unique name for this task in Airflow UI
        # 'cd delivery_dbt && dbt run ...' = two shell commands joined by &&
    # → cd delivery_dbt  = move into the delivery_dbt folder first
    # → &&              = only run the second command IF the first succeeded (exit code 0)
    # → dbt run         = run all dbt transformation models
    # → --profiles-dir ~/.dbt = tell dbt where to find database credentials
    bash_command='cd delivery_dbt && dbt run --profiles-dir ~/.dbt',  # cd to dbt dir, then run models
    )

    t4_test = BashOperator(  # task 4: run dbt data quality tests
        task_id='run_dbt_tests',  # unique name for this task in Airflow UI
        # Same && pattern as above: cd first, then only run 'dbt test' if cd succeeded
        # → dbt test = runs all tests defined in your dbt schema.yml files
        bash_command='cd delivery_dbt && dbt test --profiles-dir ~/.dbt',  # cd to dbt dir, then test data quality
    )

    t5_export = PythonOperator(  # task 5: export the mart table to CSV
        task_id='export_mart_to_csv',  # unique name for this task in Airflow UI
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
```

---

## Step 5.3 — Copy the DAG to Airflow's DAGs folder

```bash
mkdir -p airflow_home/dags
cp dags/delivery_pipeline.py airflow_home/dags/
```

---

## Step 5.4 — Start the Airflow web server

Open two separate terminal windows.

**Terminal 1:**
```bash
export AIRFLOW_HOME=$(pwd)/airflow_home  # tell Airflow where its files are
airflow webserver --port 8080  # start the Airflow UI on port 8080
```

**Terminal 2:**
```bash
export AIRFLOW_HOME=$(pwd)/airflow_home  # tell Airflow where its files are
airflow scheduler  # start the process that triggers and monitors DAG runs
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

**Why this matters:**
- Being able to show a running Airflow DAG in a portfolio interview is extremely powerful
- It demonstrates you understand production-grade orchestration, not just scripts

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
git add dags/  # stage the entire dags folder
git commit -m "Add Airflow DAG for end-to-end delivery pipeline orchestration"  # save snapshot
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

- This is the full Git workflow you do at the end of every guide
- In a real office this is called "raising a PR (Pull Request)"
- You will do this 13 times — by the third time it feels automatic

---

### Step G3 — Check what changed

```bash
git status  # show what files changed since last commit
```
**What to look for:**
- Files listed in red under "Changes not staged for commit" — these are files you modified
- Files in red under "Untracked files" — these are new files Git has never seen before
- Nothing should be green yet — you have not staged anything

**In an office:**
- Before staging anything, always read `git status` first
- It shows you exactly what you are about to commit
- Committing blindly is how secrets (passwords, API keys) accidentally get pushed to GitHub

---

### Step G4 — Review your changes line by line

```bash
git diff  # show exact lines changed (+ added, - removed)
```
**What this shows:**
- The exact lines you added (in green with `+`) and deleted (in red with `-`) in every modified file
- This is your chance to review your own work before anyone else sees it

**What to check:**
- Did I accidentally leave a `print("test123")` debugging line?
- Did I hardcode a password anywhere?
- Does the change make sense — does it do what I intended?

Press `q` to exit the diff view.

**In an office:**
- Senior engineers always do `git diff` before staging
- It catches mistakes before they become commits

---

### Step G5 — Stage your files

```bash
git add dags/delivery_pipeline.py  # stage this specific file for commit
```

**What staging means:**
- You are selecting which changes go into the next commit
- Git has a two-step save: stage first, then commit
- This lets you commit only specific files even if you changed many

**Why not `git add .`?**
- Using `.` adds every changed file including things you may not want — temporary files, `.env` files with passwords, large data files
- Always add by name or pattern

---

### Step G6 — Verify what is staged

```bash
git diff --staged  # show staged changes (what will be in the next commit)
```
**What this shows:**
- The same line-by-line diff as before, but ONLY for files you just staged
- This is your final review before the commit is permanent

**The difference between `git diff` and `git diff --staged`:**
- `git diff` → shows unstaged changes (what you changed but have NOT added yet)
- `git diff --staged` → shows staged changes (what you HAVE added, about to commit)

Press `q` to exit.

---

### Step G7 — Commit

```bash
git commit -m "Guide 06: Airflow DAG orchestrating 5-task delivery pipeline with daily schedule"  # save permanent snapshot
```
**What a commit is:**
- A permanent snapshot saved in Git's history
- Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`)
- You can always return to this exact state

**What makes a good commit message:**
- Good: `"Guide 06: Airflow DAG orchestrating 5-task delivery pipeline with daily schedule"`
- Bad: `"done"`, `"update"`, `"changes"`

Rule: your future self reading this 3 months later should know exactly what changed without looking at the code.

---

### Step G8 — Check your commit was saved

```bash
git log --oneline  # show commit history, one line per commit
```
**What this shows:**
- All commits on this branch, one line each
- The most recent is at the top
- You should see your new commit at the top of the list

**What `--oneline` means:**
- Show one line per commit instead of the full multi-line format
- Makes it easy to scan history quickly

Example output:
```
e2c5a9b Guide 06: Airflow DAG orchestrating 5-task delivery pipeline with daily schedule
d9a3b1f Guide 05: PySpark analysis with window functions, feature engineering, Parquet output
9b2c3d1 Initial commit: project guides and README
```

**In an office:**
- `git log --oneline` is one of the most used commands
- It gives you the full history of the branch at a glance

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-07-airflow  # -u = set upstream; push branch to GitHub
```
**What `git push` does:**
- Uploads your local commits to GitHub
- Until you push, your commit only exists on your laptop

**What `-u` means:**
- Sets the upstream — links your local branch to a branch of the same name on GitHub
- You only need `-u` the first time you push a new branch
- After that, just `git push` is enough

**What `origin` means:**
- The name of your GitHub remote
- When you ran `git remote add origin ...` in Guide 00B, you named it `origin`
- That name sticks

- After pushing, go to your GitHub repository in the browser
- You will see a yellow banner: **"feature/guide-07-airflow had recent pushes"**

---

### Step G10 — Raise a Pull Request on GitHub

- A Pull Request (PR) is a formal request to merge your branch into another branch
- You are asking: "I finished this work, please review it and bring it into develop"

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-07-airflow` ← what you are merging in
3. Title: `Guide 06: Airflow pipeline orchestration`
4. Description: 1-2 lines about what this guide added
5. Click **Create pull request**
6. Click **Merge pull request** → **Confirm merge**

**In an office:**
- A colleague would review your PR before approving
- They would read your diff, leave comments, and you would discuss
- Here you review and merge yourself — but the process is identical

**Why not push directly to develop?**
- In real teams, direct pushes to develop and main are blocked
- Every change must go through a PR
- This ensures someone always reviews code before it merges
- You are building that exact habit

---

### Step G11 — Pull the merged changes back locally

```bash
git checkout develop  # switch back to develop branch
```
- Switches you back to develop
- No `-b` here — `develop` already exists, you are just switching to it

```bash
git pull origin develop  # bring merged PR changes down to your local machine
```
- Downloads the merged PR from GitHub into your local develop
- Your local develop now has everything from the feature branch you just merged

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub
- `pull` — download + merge in one step (it runs `git fetch` then `git merge` automatically)

```bash
git log --oneline  # confirm Guide 06 commit appears in develop history
```
- You should now see your Guide 06 commit in develop's history
- Confirm it is there

**What `--oneline` means:** Show one line per commit instead of the full multi-line format.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-07-airflow  # -d = delete locally (safe: refuses if unmerged)
```
**What `-d` means:**
- Delete the branch locally
- Git will refuse to delete if the branch has unmerged commits — a safety guard
- Since you just merged the PR, `-d` works

```bash
git push origin --delete feature/guide-07-airflow  # delete the branch on GitHub too
```
Deletes the branch on GitHub too.

**What each part means:**
- `origin` — push this action to GitHub (not just locally)
- `--delete` — delete the named branch on GitHub

**Why delete?**
- Merged branches are dead branches
- Keeping them clutters the repository
- In real teams, merged branches are always deleted
- A clean repo = a professional habit

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-08-kafka  # -b = create new branch and switch to it
```

**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 06 commit is in the history
- **Branches** → feature/guide-07-airflow is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_07_KAFKA.md](GUIDE_07_KAFKA.md) — Handle real-time delivery events with Apache Kafka
