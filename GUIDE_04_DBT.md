# Guide 04 — Data Transformation with dbt

**Goal:** Use dbt (data build tool) to turn raw data into clean, documented, testable analytical models. dbt is the industry-standard tool for the transformation layer.

---

## Why dbt?

**What dbt is:** dbt (data build tool) is a transformation tool — it is not a database. It takes SQL (Structured Query Language) files you write and runs them against whatever database you are connected to (SQLite locally, BigQuery in production). Think of it as a way to organise, version-control, and test all your SQL transformations in one place, with automatic dependency ordering.

**What YAML is:** YAML is a plain-text format for writing configuration — it uses indentation (spaces) to show structure instead of brackets or braces. dbt uses YAML files to define tests, descriptions, and settings. Every line of YAML you will write follows the same simple pattern: `key: value`.

Raw data is messy. dbt lets you:
- Write SQL transformations as `.sql` files (version controlled, reviewable)
- Add tests to guarantee data quality (e.g. "FADR (First Attempt Delivery Rate) must be between 0 and 1")
- Auto-generate documentation for every table and column
- Build a dependency graph of all your data models

Every modern data team uses dbt. It appears on almost every data engineering job description.

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
git checkout -b feature/guide-04-dbt
```
**What `-b` means:** Create a new branch AND switch to it. Without `-b`, checkout only switches to an existing branch.

**Why a new branch for every guide:** Each branch is one unit of work. If something breaks, you can delete the branch and start fresh without affecting develop or main. In an office, each feature or fix lives on its own branch for the same reason.

Confirm you are on the right branch:
```bash
git branch
```
You will see a `*` next to your current branch. That `*` means "you are here".

---

## Step 4.1 — Initialise a dbt project

```bash
dbt init delivery_dbt
```

When prompted:
- Enter project name: `delivery_dbt`
- Select database: `sqlite` (option will appear if dbt-sqlite is installed)

Then move into the project:
```bash
cd delivery_dbt
```

---

## Step 4.2 — Configure `profiles.yml`

**What `profiles.yml` is:** This file stores the connection details dbt needs to reach your database — the file path, the database type, and any credentials. It lives in your home directory (`~/.dbt/`) rather than inside the project folder so that sensitive connection details (passwords, API (Application Programming Interface) keys) are never accidentally committed to Git and shared publicly.

dbt needs to know where your database is. Edit the file that was created at `~/.dbt/profiles.yml` (in your home directory, NOT the project directory):

**Note on `~` (tilde):** The `~` symbol means your home directory — on Windows this is `C:/Users/YourName/`. So `~/.dbt/profiles.yml` means `C:/Users/YourName/.dbt/profiles.yml`.

**How to create this file:**
```bash
notepad %USERPROFILE%\.dbt\profiles.yml
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```yaml
delivery_dbt:
  target: dev
  outputs:
    dev:
      type: sqlite
      threads: 1
      database: "../data/delivery_db.sqlite"
      schema: main
      schemas_and_paths:
        main: "../data/delivery_db.sqlite"
      schema_directory: "../data"
```

**Why:** dbt separates connection details (profiles.yml) from your project code. This means you can use the same models with different databases — dev vs production — just by switching the profile. Never commit profiles.yml to git (it can contain passwords).

---

## Step 4.3 — Create dbt models

Inside the `delivery_dbt/models/` folder, create these files:

**File: `delivery_dbt/models/staging/stg_deliveries.sql`**

**How to create this file:**
```bash
notepad delivery_dbt/models/staging/stg_deliveries.sql
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```sql
-- Staging model: clean and type-cast raw deliveries
-- This is the first layer — we standardise columns but don't add business logic yet
SELECT
    delivery_id,
    customer_id,
    city,
    address_type,
    delivery_window,
    CAST(order_value AS REAL)           AS order_value,
    CAST(is_successful AS INTEGER)      AS is_successful,
    failure_reason,
    CAST(attempt_number AS INTEGER)     AS attempt_number,
    DATE(attempt_date)                  AS attempt_date,
    CAST(attempt_hour AS INTEGER)       AS attempt_hour,
    CAST(has_delivery_preference AS INTEGER) AS has_delivery_preference,
    CAST(proximity_alert_sent AS INTEGER)    AS proximity_alert_sent
FROM {{ source('main', 'deliveries') }}
WHERE delivery_id IS NOT NULL
-- What {{ source() }} means: this is dbt's way of referencing a raw table that already
-- exists in the database (the one you loaded from CSV in Guide 02). It tells dbt
-- "this table is an external source, not one I built." dbt tracks it in the lineage graph.
```

**File: `delivery_dbt/models/marts/mart_fadr_by_segment.sql`**

**How to create this file:**
```bash
notepad delivery_dbt/models/marts/mart_fadr_by_segment.sql
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```sql
-- Mart model: FADR aggregated by city and address type
-- This is what the dashboard and ML model will read from
SELECT
    city,
    address_type,
    COUNT(*)                                  AS total_attempts,
    SUM(is_successful)                        AS successful_deliveries,
    ROUND(AVG(is_successful), 4)              AS fadr,
    ROUND(AVG(1 - is_successful), 4)          AS failure_rate,
    AVG(order_value)                          AS avg_order_value
-- What {{ ref() }} means: this is dbt's way of referencing another model you built
-- (rather than a raw source table). dbt uses this to build a dependency graph —
-- it knows stg_deliveries must run before mart_fadr_by_segment.
FROM {{ ref('stg_deliveries') }}
GROUP BY city, address_type
```

**File: `delivery_dbt/models/marts/mart_window_analysis.sql`**

**How to create this file:**
```bash
notepad delivery_dbt/models/marts/mart_window_analysis.sql
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```sql
-- Mart model: FADR by delivery window and address type combined
SELECT
    delivery_window,
    address_type,
    has_delivery_preference,
    proximity_alert_sent,
    COUNT(*)                                  AS total_attempts,
    ROUND(AVG(is_successful), 4)              AS fadr
FROM {{ ref('stg_deliveries') }}
GROUP BY delivery_window, address_type, has_delivery_preference, proximity_alert_sent
HAVING total_attempts > 50
```

---

## Step 4.4 — Create dbt source definition

**File: `delivery_dbt/models/staging/sources.yml`**

**How to create this file:**
```bash
notepad delivery_dbt/models/staging/sources.yml
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```yaml
version: 2

sources:
  - name: main
    description: Raw delivery data loaded from CSV
    tables:
      - name: deliveries
        description: One row per delivery attempt
        columns:
          - name: delivery_id
            description: Unique identifier for each delivery attempt
            tests:
              - unique
              - not_null
          - name: is_successful
            description: 1 if delivered, 0 if failed
            tests:
              - not_null
              - accepted_values:
                  values: [0, 1]
```

---

## Step 4.5 — Add model tests

**What `schema.yml` is:** This YAML file is where you describe your dbt models and add data quality tests. dbt reads it and automatically generates test queries — for example, checking that a column is never NULL or always within an expected value range. It also feeds the auto-generated documentation with descriptions for each column.

**File: `delivery_dbt/models/marts/schema.yml`**

**How to create this file:**
```bash
notepad delivery_dbt/models/marts/schema.yml
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```yaml
version: 2

models:
  - name: mart_fadr_by_segment
    description: FADR aggregated by city and address type segment
    columns:
      - name: fadr
        description: First Attempt Delivery Rate (0 to 1)
        tests:
          - not_null
      - name: total_attempts
        description: Number of delivery attempts in this segment
        tests:
          - not_null
```

---

## Step 4.6 — Run dbt

```bash
dbt run
```

**Why:** This executes all your `.sql` models against the database and creates the output tables. Think of it as running all your SQL transformations in the right order automatically.

---

## Step 4.7 — Run dbt tests

```bash
dbt test
```

**Why:** This runs all the tests you defined in the `schema.yml` files. If any test fails — e.g. a NULL in `is_successful` — you know the data is broken before it reaches the dashboard or ML (Machine Learning) model. Data quality testing is a professional standard that separates senior engineers from juniors.

---

## Step 4.8 — Generate documentation

```bash
dbt docs generate
dbt docs serve
```

**Why:** This creates a full website documenting every table, column, and dependency in your pipeline. Open `http://localhost:8080` in your browser. You can show this to an interviewer as proof of professional data engineering practice.

---

## Checkpoint

You now have:
- A dbt project with 3 SQL models
- Data quality tests
- Auto-generated documentation
- Clean, tested tables ready for ML and dashboards

---

## Git Checkpoint — End of Guide 04

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
git add models/staging/stg_deliveries.sql
git add models/marts/mart_fadr_by_segment.sql
git add models/marts/mart_window_analysis.sql
git add dbt_project.yml
git add profiles.yml
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
git commit -m "Guide 04: dbt project with staging, mart models and data quality tests"
```
**What a commit is:** A permanent snapshot saved in Git's history. Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`). You can always return to this exact state.

**What makes a good commit message:**
- Good: `"Guide 04: dbt project with staging, mart models and data quality tests"`
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
c7f4d2e Guide 04: dbt project with staging, mart models and data quality tests
b5e2f1a Guide 03: 10 analytical SQL queries for FADR analysis
9b2c3d1 Initial commit: project guides and README
```

**In an office:** `git log --oneline` is one of the most used commands. It gives you the full history of the branch at a glance.

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-04-dbt
```
**What `git push` does:** Uploads your local commits to GitHub. Until you push, your commit only exists on your laptop.

**What `-u` means:** Sets the upstream — links your local branch to a branch of the same name on GitHub. You only need `-u` the first time you push a new branch. After that, just `git push` is enough.

**What `origin` means:** The name of your GitHub remote. When you ran `git remote add origin ...` in Guide 00B, you named it `origin`. That name sticks.

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-04-dbt had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-04-dbt` ← what you are merging in
3. Title: `Guide 04: dbt transformation models`
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
You should now see your Guide 04 commit in develop's history. Confirm it is there.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-04-dbt
```
**What `-d` means:** Delete the branch locally. Git will refuse to delete if the branch has unmerged commits — a safety guard. Since you just merged the PR, `-d` works.

```bash
git push origin --delete feature/guide-04-dbt
```
Deletes the branch on GitHub too.

**Why delete?** Merged branches are dead branches. Keeping them clutters the repository. In real teams, merged branches are always deleted. A clean repo = a professional habit.

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-05-pyspark
```

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 04 commit is in the history
- **Branches** → feature/guide-04-dbt is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_05_PYSPARK.md](GUIDE_05_PYSPARK.md) — Process the same data at scale with PySpark
