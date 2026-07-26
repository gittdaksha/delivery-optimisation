# Guide 12 — CI/CD (Continuous Integration/Continuous Deployment) with GitHub Actions

**Goal:** Set up a CI/CD pipeline that runs automatically on every `git push`. It runs your Python unit tests, dbt (Data Build Tool) data quality tests, and linting. If any check fails, the push is flagged before broken code reaches the main branch.

**Why this guide exists:** Right now you run tests manually — or forget to run them. CI/CD means every time you push code to GitHub, tests run automatically. If something breaks, GitHub blocks the merge and tells you exactly what failed. This is standard practice in every professional engineering team.

---

## Why CI/CD and why it belongs here

- Every JD you shared lists Git and CI/CD — they list them together because they go together
- Git tracks changes; CI/CD acts on those changes — automatically, consistently, without you having to remember to run tests manually
- In a real data team, you do not merge code to the main branch unless the pipeline passes
- CI/CD enforces that automatically — if your dbt model has a SQL (Structured Query Language) error, if a Python function breaks, if data quality degrades, the pipeline catches it before it reaches production
- This is the difference between a project that runs locally on your machine and a project that a team could actually rely on

**What GitHub Actions is:**
- An automation service built into GitHub
- You define workflows as YAML (YAML Ain't Markup Language) files in `.github/workflows/`
- Whenever a trigger event happens (like a push or pull request), GitHub spins up a clean machine, runs your workflow, and reports pass/fail on the commit
- Completely free for public repositories
- No separate account, no extra cost for public repos; every push triggers workflows automatically

---

## Git — Before You Start This Guide

- Every guide begins the same way in a real office: make sure you are on the right branch and it is up to date before touching any files

### Step G1 — Make sure you are on develop and it is current

```bash
git checkout develop  # switch to develop branch (must already exist)
```
**What this does:**
- Switches you to the develop branch
- You always create feature branches FROM develop, never from main and never from another feature branch
- No `-b` here — this switches to an existing branch; you do not use `-b` when the branch already exists

```bash
git pull origin develop  # download + merge latest changes from GitHub
```
**What this does:**
- Downloads any changes from GitHub that you do not have locally
- In an office, a colleague may have merged something since you last worked
- `pull` = download + merge in one command

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub

```bash
git status  # show current state; should be clean before creating a branch
```
**What this does:**
- Shows the current state
- You should see `On branch develop, nothing to commit, working tree clean`
- If you see modified files here, deal with them before moving forward — do not carry unrelated changes into a new branch
- No flags here — `git status` always shows full current state

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-12-cicd  # -b = create new branch and switch to it
```
**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

**Why a new branch for every guide:**
- Each branch is one unit of work
- If something breaks, you can delete the branch and start fresh without affecting develop or main
- In an office, each feature or fix lives on its own branch for the same reason

Confirm you are on the right branch:
```bash
git branch  # list all branches; * marks your current one
```
- You will see a `*` next to your current branch
- That `*` means "you are here"

---

## What you are automating

```
git push
    ↓
GitHub Actions triggered
    ↓
[Job 1: Test]
    ├── Install Python dependencies
    ├── Run pytest (unit tests on data generation + ingestion)
    └── Run dbt test (data quality checks on SQL models)
    ↓
[Job 2: Lint]
    └── flake8 (checks Python code style)
    ↓
Pass → green checkmark on your commit
Fail → red X, email notification, merge blocked
```

---

## Step 13.1 — Create the GitHub Actions workflow directory

```bash
mkdir -p .github/workflows  # -p = create parent folders too if they don't exist
```

**Why `.github/workflows`:**
- This is the folder GitHub looks in
- Every `.yml` file here is a workflow
- The folder name is not configurable — it must be exactly this

---

## Step 13.2 — Create `tests/test_pipeline.py`

Before writing the CI pipeline, you need tests to run. Create `tests/test_pipeline.py`:

**How to create this file:**
```bash
mkdir tests  # create the tests/ folder to hold all test files
notepad tests/test_pipeline.py  # open/create the test file in Notepad
```
**What `mkdir tests` does:**
- Creates the `tests/` folder
- Notepad will open (or ask to create the file — click Yes)
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad

**What `tests/test_pipeline.py` does and why it exists:**
- **What it does:** Contains 7 automated tests that verify the pipeline's core business rules — correct row count, no null IDs, binary success flags, valid address types, and positive order values
- **Why separate:** Tests must live outside the source code they test so they can be run independently by CI/CD without importing or running the full pipeline; pytest discovers and runs everything in the `tests/` folder automatically
- **Input:** `data/raw/deliveries.csv` + `data/deliveries.sqlite` (generated fresh before each test run)
- **Output:** Pass/fail results printed to terminal for all 7 tests, with error details on any failure
- **Pipeline position:** `src/generate_data.py` (the function under test) → **this file** → pytest pass/fail results → `.github/workflows/pipeline.yml` runs these tests on every push

```python
import pandas as pd  # needed to work with DataFrames in tests
import sys  # used to modify the Python import path
import os  # used to build the path to the src folder

# sys.path = the list of folders Python searches when you write "import something"
# sys.path.insert(0, ...) = add a new folder at position 0 (first in the search list)
# this is needed because test files live in tests/ but the code lives in src/
# without this, "from generate_data import ..." would fail with ModuleNotFoundError
#
# os.path.dirname(__file__) = the absolute path of the current test file's folder
#   e.g. "C:/Users/Daksha/project/tests"
# os.path.join(..., '..', 'src') = go up one level (..) then into src/
#   e.g. "C:/Users/Daksha/project/tests/../src" which resolves to "C:/Users/Daksha/project/src"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generate_data import generate_delivery_data  # import the function to test


def test_generated_data_shape():  # test: function creates correct number of rows/cols
    df = generate_delivery_data(n_records=100)
    # assert <condition>, "message" = if condition is False, the test FAILS with that message
    # assert True → test passes silently
    # assert False → test fails and pytest prints "Should generate exactly 100 records"
    # df.shape returns (rows, columns) as a tuple; [0] = rows, [1] = columns
    assert df.shape[0] == 100, "Should generate exactly 100 records"  # check row count
    assert df.shape[1] == 13,  "Should have 13 columns"  # check column count


def test_no_null_delivery_ids():  # test: every row has a delivery_id
    df = generate_delivery_data(n_records=100)
    assert df['delivery_id'].isnull().sum() == 0, "delivery_id must never be null"  # 0 nulls expected


def test_is_successful_is_binary():  # test: column must only contain 0 or 1
    df = generate_delivery_data(n_records=500)
    # .unique() = returns array of distinct values found in the column, e.g. [0, 1]
    # set(...) = convert to a Python set so we can use .issubset()
    values = set(df['is_successful'].unique())  # get all unique values in the column
    # .issubset({0, 1}) = True if 'values' contains only elements from {0, 1}
    # if values = {0, 1, 2} then issubset returns False → test fails
    assert values.issubset({0, 1}), f"is_successful must be 0 or 1, got: {values}"


def test_fadr_is_reasonable():  # test: overall success rate is in expected range
    df = generate_delivery_data(n_records=5000)
    fadr = df['is_successful'].mean()  # average of 0/1 column = success rate
    # 0.5 < fadr < 0.95 = Python chained comparison: fadr must be between 0.5 and 0.95
    # f"{fadr:.2%}" = format as percentage with 2 decimals → e.g. 0.753 → "75.30%"
    assert 0.5 < fadr < 0.95, f"FADR {fadr:.2%} is outside expected range 50-95%"


def test_failure_reason_null_when_successful():  # test: no failure reason on successes
    df = generate_delivery_data(n_records=500)
    # Successful deliveries should not have a failure reason
    # (df['is_successful'] == 1) = True/False column: True where delivery succeeded
    # (df['failure_reason'].notnull()) = True/False column: True where reason is NOT null
    # & = element-wise AND: both conditions must be True in the same row
    # df[...] = keep only rows where both are True (successful BUT has a failure reason = bug)
    bad_rows = df[(df['is_successful'] == 1) & (df['failure_reason'].notnull())]  # filter bad rows
    assert len(bad_rows) == 0, "Successful deliveries must not have a failure_reason"


def test_address_types_are_valid():  # test: no unexpected address categories
    df = generate_delivery_data(n_records=500)
    valid = {'Apartment', 'PG/Hostel', 'House', 'Office', 'Gated Community'}  # allowed values
    actual = set(df['address_type'].unique())  # values actually in the data
    # actual - valid = set difference: elements in 'actual' that are NOT in 'valid'
    # e.g. if actual = {'Apartment', 'Villa'}, then actual - valid = {'Villa'}
    # this tells you exactly which unexpected values appeared
    assert actual.issubset(valid), f"Unexpected address types: {actual - valid}"  # - = set difference


def test_order_value_positive():  # test: no zero or negative order values
    df = generate_delivery_data(n_records=500)
    # (df['order_value'] > 0) = True/False column: True for each row where value > 0
    # .all() = returns a single True only if every value in the column is True
    # if even one row has order_value <= 0, .all() returns False → test fails
    assert (df['order_value'] > 0).all(), "All order values must be positive"  # .all() = must be true for every row
```

Run locally first:

```bash
pytest tests/ -v  # -v = verbose; shows each test name and pass/fail
```

All 7 tests should pass. If one fails, fix the issue in `generate_data.py` before continuing.

**Why these tests:**
- Each test checks a business rule that, if broken, would silently corrupt the pipeline
- `is_successful` being something other than 0 or 1 would break the ML (Machine Learning) model
- A null `delivery_id` would break joins
- You test the rules that matter, not every line of code

---

## Step 13.3 — Create `.github/workflows/pipeline.yml`

Create the file `.github/workflows/pipeline.yml`:

**How to create this file:**
```bash
mkdir -p .github/workflows  # -p = create .github/ and workflows/ in one command
notepad .github/workflows/pipeline.yml  # open/create the workflow file in Notepad
```
**What `mkdir -p` means:**
- Creates the folder and any parent folders needed
- `-p` means "parents" — if `.github/` does not exist yet, it creates both `.github/` and `.github/workflows/` in one command
- Without `-p`, mkdir would fail if the parent folder does not exist
- Notepad will open (or ask to create the file — click Yes); paste the content below into it, then press **Ctrl+S** to save and close Notepad

**What `.github/workflows/pipeline.yml` does and why it exists:**
- **What it does:** A GitHub Actions workflow definition that automatically installs dependencies, runs pytest, generates test data, ingests it to SQLite, and runs flake8 linting every time you push to `main` or `develop`
- **Why separate:** The workflow is infrastructure configuration for GitHub's servers — it cannot live inside `tests/` or `src/` because GitHub only reads workflows from `.github/workflows/`; keeping it there also makes it immediately visible to any engineer reviewing the repository
- **Input:** `git push` event to `main` or `develop` (triggers GitHub Actions automatically)
- **Output:** Automated test run results + flake8 lint report shown as a green tick or red X on the commit in GitHub
- **Pipeline position:** `git push` to `main` or `develop` → GitHub detects **this file** → spins up a clean Ubuntu VM → runs `tests/test_pipeline.py` + flake8 on `src/` → reports green tick or red X on the commit

```yaml
name: Delivery Pipeline CI  # display name shown in GitHub Actions tab

# What on: push: means: this section defines the trigger — what event causes
# this workflow to run. Here it runs on any push to the 'main' or 'develop'
# branches, and also when a pull request targets 'main'. Every git push
# automatically fires this pipeline without you having to do anything manually.
on:
  push:
    branches: [main, develop]  # run on push to these branches
  pull_request:
    branches: [main]  # also run when a PR targets main

jobs:

  test:
    name: Run Tests  # label shown in GitHub UI
    # What runs-on: ubuntu-latest means: GitHub provides a fresh virtual machine
    # running the latest Ubuntu Linux to execute this job. A clean machine means
    # no leftover state from previous runs — every run starts identical.
    # This is what "it runs anywhere" means in practice.
    runs-on: ubuntu-latest  # use GitHub's free Ubuntu VM

    steps:
      - name: Checkout code
        # What uses: actions/checkout@v4 does: clones your GitHub repository into
        # the virtual machine so the workflow can access your code files. Without
        # this step, the machine has no knowledge of your project.
        uses: actions/checkout@v4  # pre-built action: clone the repo onto the VM

      - name: Set up Python 3.11
        uses: actions/setup-python@v5  # pre-built action: install Python
        with:
          python-version: "3.11"  # pin exact version for reproducibility

      - name: Cache pip dependencies
        # What cache: does: saves the pip download cache folder between workflow runs.
        # The first run downloads all packages (~2-3 minutes). On subsequent runs,
        # if requirements.txt has not changed (same hash), GitHub restores the cache
        # and pip installs from local copies — cutting install time to ~15 seconds.
        uses: actions/cache@v4  # pre-built action: save/restore a folder between runs
        with:
          path: ~/.cache/pip  # folder to cache (pip's download cache)
          # ${{ ... }} = GitHub Actions expression syntax — evaluated at runtime
          # runner.os = the OS of the current runner (e.g. "Linux")
          # hashFiles('requirements.txt') = a hash of the file's contents
          # if requirements.txt hasn't changed, the hash is the same → cache is reused
          # if you add a new package, the hash changes → cache is rebuilt
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}  # cache key: OS + file hash
          # restore-keys = fallback: if exact key not found, use any cache starting with this prefix
          # allows partial cache reuse even when requirements.txt changed slightly
          restore-keys: ${{ runner.os }}-pip-  # fallback key if exact match not found

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip  # upgrade pip itself first
          pip install pandas numpy faker scikit-learn pytest flake8  # install project deps

      - name: Run unit tests
        # pytest tests/ = run all test files found in the tests/ folder
        # -v = verbose: print each test function name and PASSED/FAILED next to it
        # --tb=short = when a test fails, show a compact traceback (not the full multi-line one)
        run: pytest tests/ -v --tb=short  # -v = verbose output; --tb=short = shorter tracebacks

      - name: Generate test data (needed for dbt)
        run: python src/generate_data.py  # create deliveries.csv in data/raw/

      - name: Ingest to SQLite
        run: python src/ingest.py  # load CSV into SQLite DB

  lint:
    name: Code Quality  # separate job that runs in parallel with test job
    runs-on: ubuntu-latest  # fresh Ubuntu VM

    steps:
      - name: Checkout code
        uses: actions/checkout@v4  # clone repo onto this VM too

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install flake8
        # What flake8 is: a Python linting tool that reads your code and reports
        # problems — syntax errors, undefined variable names, unused imports,
        # lines that are too long. It catches mistakes that would crash the
        # pipeline at runtime, before the code is ever run.
        run: pip install flake8  # install only flake8 (lint job doesn't need all deps)

      - name: Lint with flake8
        run: |
          # Stop on syntax errors or undefined names (these break the pipeline)
          # What --select=E9,F63 means: only report errors in these specific categories.
          # E9 = syntax errors (code Python cannot even parse). F63 = invalid assert
          # or print statements. F7 = syntax errors in expressions. F82 = undefined names.
          # These are the errors that will immediately crash your pipeline — style
          # warnings like line length (E501) are excluded here so they don't block CI.
          # --count = print total error count at end  |  --show-source = show the bad line
          # --statistics = group errors by type and show a summary count per category
          flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
          # Warn on style issues but don't fail (line length, unused imports)
          # --max-line-length=110 = allow lines up to 110 chars (default is 79)
          # --exit-zero = always exit with code 0 (success) even if style issues found
          # this means style warnings are shown in the log but do NOT fail the CI job
          flake8 src/ --count --max-line-length=110 --exit-zero --statistics  # --exit-zero = never fail on style
```

---

## Step 13.4 — Create `tests/__init__.py`

```bash
touch tests/__init__.py  # create empty file; makes tests/ a Python package for pytest
```

- This makes `tests/` a proper Python package so pytest can discover it

---

## Step 13.5 — Push to GitHub and watch it run

```bash
git add .github/ tests/  # stage the workflow file and test files
git commit -m "Add CI/CD: GitHub Actions runs pytest and flake8 on every push"  # save snapshot
git push origin main  # upload; Actions tab will show the pipeline running
```

- Go to your GitHub repo → click the **Actions** tab
- You will see the workflow running
- Green checkmark = all tests passed
- Every future commit shows the same

---

## Step 13.6 — What you see in the Actions tab

- Each commit on GitHub now shows a small icon:
  - ✅ green — all tests passed, code is safe to merge
  - ❌ red — something broke, click to see which step and why
- Click any run to see the full log: which test passed, which failed, the exact error message and line number

---

## Step 13.7 — Key CI/CD concepts for interviews

| Concept | What it is | Why interviewers ask |
|---|---|---|
| Trigger | `on: push` — what starts the workflow | Automated, not manual — that's the point |
| Job | A group of steps that run on one machine | Jobs run in parallel by default |
| Step | One action within a job | Sequential within a job |
| Runner | The machine that runs the job (`ubuntu-latest`) | GitHub provides free runners for public repos |
| Cache | Saves pip dependencies between runs | Cuts pipeline time from 3 min to 30 sec |
| `--select=E9,F63,F7,F82` | Only fail on syntax errors, not style | You want to block broken code, not enforce tabs vs spaces |

---

## Common interview questions

**"What is CI/CD and how did you use it?"**

- "CI is Continuous Integration — every code change is automatically tested before it can be merged"
- "CD is Continuous Deployment — passing changes are automatically deployed"
- "In this project I used GitHub Actions: on every push, it installs dependencies, runs 7 pytest unit tests on the data generation logic, and runs flake8 to catch syntax errors"
- "If any test fails, the commit is flagged and I get a notification"
- "This means broken pipeline code never silently reaches the main branch"

**"Why do you test data generation code?"**

- "Because data quality bugs are silent"
- "If `is_successful` starts producing values other than 0 and 1, the ML model trains on garbage and gives confident but wrong predictions"
- "You would not know until downstream results stopped making sense"
- "A test that runs in 2 seconds on every push catches this immediately"



---

## Step 13.8 — Kimball data modelling (explicit naming)

- This belongs in Guide 04 context but is worth naming here for interview preparation
- The dbt structure you built in Guide 04 is Kimball's dimensional modelling pattern:

| dbt layer | Kimball term | What it contains |
|---|---|---|
| `stg_deliveries` | Staging / Operational Data Store | Raw data cleaned and typed, no business logic |
| `mart_fadr_by_segment` | Fact table | Measurable business events (delivery attempts, FADR (First Attempt Delivery Rate)) at grain: city + address type |
| `mart_window_analysis` | Dimension-enriched fact | Facts joined with dimension attributes (window, preference flags) |

- When an interviewer asks "are you familiar with Kimball methodology?" — yes, and the structure you built follows it
- Staging → Facts → Dimension-enriched marts is exactly the Kimball warehouse lifecycle

---

## Commit

```bash
git add tests/ .github/  # stage test files and workflow config
git commit -m "Add 7 unit tests covering data generation business rules"  # save snapshot
git push origin main  # upload to GitHub; triggers the CI pipeline
```

---

## Checkpoint

You now have:
- 7 automated tests that run on every push
- GitHub Actions CI/CD pipeline
- Understanding of Kimball data modelling (which you already built in Guide 04)

- Your project now does what a real production project does: test automatically, fail fast, never let broken code reach main silently

---

## Git Checkpoint — End of Guide 12

- This is the full Git workflow you do at the end of every guide
- In a real office this is called "raising a PR (Pull Request)"
- You will do this 13 times — by the third time it feels automatic

---

### Step G3 — Check what changed

```bash
git status  # show modified and untracked files
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
git diff  # show exact lines changed before staging
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
git add .github/workflows/pipeline.yml  # stage the CI workflow file
git add tests/test_pipeline.py  # stage the unit test file
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
git diff --staged  # show diff of only staged files
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
git commit -m "Guide 12: GitHub Actions CI/CD with 7 pytest unit tests and flake8 linting"  # save snapshot
```
**What a commit is:**
- A permanent snapshot saved in Git's history
- Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`)
- You can always return to this exact state

**What makes a good commit message:**
- Good: `"Guide 12: GitHub Actions CI/CD with 7 pytest unit tests and flake8 linting"`
- Bad: `"done"`, `"update"`, `"changes"`
- Rule: your future self reading this 3 months later should know exactly what changed without looking at the code

---

### Step G8 — Check your commit was saved

```bash
git log --oneline  # list all commits, newest first
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
k7i4d5j Guide 12: GitHub Actions CI/CD with 7 pytest unit tests and flake8 linting
j6h3c4i Guide 11: BigQuery ingestion, GCS landing zone, BQ partitioning, Pub/Sub streaming
9b2c3d1 Initial commit: project guides and README
```

**In an office:**
- `git log --oneline` is one of the most used commands
- It gives you the full history of the branch at a glance

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-12-cicd  # upload; -u links branch to GitHub
```
**What `git push` does:**
- Uploads your local commits to GitHub
- Until you push, your commit only exists on your laptop

**What `-u` means:**
- Sets the upstream — links your local branch to a branch of the same name on GitHub
- You only need `-u` the first time you push a new branch; after that, just `git push` is enough

**What `origin` means:**
- The name of your GitHub remote
- When you ran `git remote add origin ...` in Guide 00B, you named it `origin`; that name sticks

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-12-cicd had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-12-cicd` ← what you are merging in
3. Title: `Guide 12: CI/CD pipeline with automated tests`
4. Description: 1-2 lines about what this guide added
5. Click **Create pull request**
6. Click **Merge pull request** → **Confirm merge**
7. Go to the **Actions** tab — you will see the workflow run automatically on merge. Wait for the green tick.

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
git pull origin develop  # download merged PR from GitHub
```
- Downloads the merged PR from GitHub into your local develop
- Your local develop now has everything from the feature branch you just merged

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub
- `pull` — download + merge in one step (it runs `git fetch` then `git merge` automatically)

```bash
git log --oneline  # verify Guide 12 commit appears
```
- You should now see your Guide 12 commit in develop's history
- Confirm it is there

**What `--oneline` means:** Show one line per commit instead of the full multi-line format.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-12-cicd  # -d = delete local merged branch
```
**What `-d` means:**
- Delete the branch locally
- Git will refuse to delete if the branch has unmerged commits — a safety guard
- Since you just merged the PR, `-d` works
- Use `-D` (capital D) only if you want to force-delete without merging

```bash
git push origin --delete feature/guide-12-cicd  # delete branch on GitHub too
```
- Deletes the branch on GitHub too

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
git checkout -b feature/guide-13-github  # -b = create new branch and switch to it
```

**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

- You are now on a fresh branch, ready for the next guide

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 12 commit is in the history
- **Branches** → feature/guide-12-cicd is gone (deleted)

- This is exactly what a professional Git history looks like

**Next:** [GUIDE_13_GITHUB.md](GUIDE_13_GITHUB.md) — Push the final project and write your CV entry
