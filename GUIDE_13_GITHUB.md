# Guide 13 — Publish to GitHub & Write Your CV Entry

**Goal:** Make the project look professional on GitHub and write a CV entry that communicates real impact.

---

## Git — Before You Start This Guide

- Every guide begins the same way in a real office: make sure you are on the right branch and it is up to date before touching any files

### Step G1 — Make sure you are on main and it is current

```bash
git checkout main  # switch to main (must already exist)
```
**What this does:**
- Switches you to the main branch
- You always create feature branches FROM main
- No `-b` here — this switches to an existing branch; you do not use `-b` when the branch already exists

```bash
git pull origin main  # download + merge latest from GitHub
```
**What this does:**
- Downloads any changes from GitHub that you do not have locally
- In an office, a colleague may have merged something since you last worked
- `pull` = download + merge in one command

**What each part means:**
- `origin` — download from GitHub (the remote)
- `main` — specifically from the main branch on GitHub

```bash
git status  # show current state; should be clean
```
**What this does:**
- Shows the current state
- You should see `On branch main, nothing to commit, working tree clean`
- If you see modified files here, deal with them before moving forward — do not carry unrelated changes into a new branch
- No flags here — `git status` always shows full current state

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-13-github  # -b = create new branch and switch to it
```
**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

**Why a new branch for every guide:**
- Each branch is one unit of work
- If something breaks, you can delete the branch and start fresh without affecting main
- In an office, each feature or fix lives on its own branch for the same reason

Confirm you are on the right branch:
```bash
git branch  # list all branches; * = current
```
- You will see a `*` next to your current branch
- That `*` means "you are here"

---

## Step 13.1 — Review the README

- The README already exists at the root of the project
- It describes the problem, the full pipeline, and the reasoning behind each tool choice
- Open it and read through it — this is what a recruiter or hiring manager sees when they open your GitHub repo

```bash
cat README.md  # print README to the terminal so you can read it
```
**What this does:**
- Prints the full README content to the terminal
- Confirm it covers: the problem, the pipeline layers, the tools, and the project structure

**What makes a good README for a portfolio project:**
- Describes a real problem (not "this project uses X, Y, Z")
- Shows the architecture and why each tool was chosen
- Explains what the data will show — quantified results
- Has a clear project structure diagram
- Does NOT need screenshots or badges to be professional — clear writing is enough

---

## Step 13.2 — Your CV Entry

**How to use this section:**
- The text below is a ready-to-paste CV entry
- Copy the version that matches how far you got — the first version covers Guides 02–10, the second covers the full project
- Each bullet point describes one concrete thing you built, not a vague claim — this is what makes it credible to a technical recruiter or hiring manager

**Version 1 — Core pipeline (Guides 02–10):**

---

**Delivery Optimisation — Data Engineering Pipeline**
`Python` `SQL` `dbt` `Apache Airflow` `scikit-learn` `Streamlit` `SQLite` `Git`

- Built an end-to-end data pipeline to analyse First Attempt Delivery Rate (FADR) across 50,000 simulated delivery records
- Designed synthetic data generation with realistic business logic using Python and Faker
- Engineered transformation layer with dbt (Data Build Tool) (3 SQL (Structured Query Language) models, automated data quality tests)
- Orchestrated daily pipeline with Apache Airflow DAG (Directed Acyclic Graph) (5 tasks, automatic retry logic)
- Trained a Random Forest model (83% accuracy, ROC-AUC (Receiver Operating Characteristic — Area Under Curve) 0.88) predicting delivery success from address type, time window, and customer preferences
- Quantified that delivery preferences + optimised windows improve success probability by 25+ percentage points for high-risk addresses
- Built an interactive Streamlit dashboard with a business impact calculator showing ₹1.6Cr+ annual savings at 100K daily volume

GitHub: `github.com/gittdaksha/delivery-optimisation`

---

## Step 13.3 — LinkedIn post version

**Why post on LinkedIn:**
- LinkedIn posts with project links get significantly more recruiter engagement than a CV alone
- The post shows you can communicate technical work to a non-technical audience — a skill data engineers need daily
- Keep the post concise: problem → what you built → one quantified result → link

After completing the project, post this on LinkedIn:

- "I turned this problem into a data engineering project — built the full pipeline from synthetic data generation → SQL analysis → dbt transformations → Airflow orchestration → ML prediction → Streamlit dashboard"
- "The model confirms: apartments + morning windows fail ~35% more often"
- "Preferences + alerts improve success probability by 25 percentage points"
- "Full project on GitHub: github.com/gittdaksha/delivery-optimisation"

---

## Summary: What You Built

| Layer | Tool | What it does |
|---|---|---|
| Data Generation | Python + Faker | Creates 50,000 realistic delivery records |
| Storage | SQLite + SQLAlchemy | Structured database for all data |
| Transformation | SQL + dbt | Clean, tested, documented data models |
| Orchestration | Apache Airflow | Schedules the full pipeline daily |
| Big Data Processing | PySpark | DataFrame API, window functions, Parquet output |
| Real-Time Streaming | Apache Kafka | Event streaming with producer/consumer |
| Containerisation | Docker + Docker Compose | Full stack running with one command |
| Cloud Data Warehouse | BigQuery (GCP) | Date-partitioned, city-clustered production table |
| Cloud Streaming | Google Pub/Sub | Managed event streaming on GCP |
| Machine Learning | scikit-learn | Predicts delivery success with 83% accuracy |
| Visualisation | Streamlit | Interactive dashboard for stakeholders |
| CI/CD | GitHub Actions | Runs tests + linting on every push |
| Version Control | Git + GitHub | Full project history, shareable portfolio |

---

## Step 13.4 — Full-stack CV Entry (all 13 guides)

**Use this version if you completed all 13 guides.**
- It lists every major tool
- Interviewers at data-heavy companies (logistics, e-commerce, fintech) will recognise the full stack and know you can discuss each tool in depth

**Delivery Optimisation — End-to-End Data Engineering Pipeline**
`Python` `PySpark` `Apache Kafka` `Apache Airflow` `dbt` `Docker` `BigQuery` `SQLite` `scikit-learn` `Streamlit` `GitHub Actions` `Git`

- Built a full data engineering pipeline to improve First Attempt Delivery Rate (FADR) across 50,000 delivery records
- Processed data at scale with PySpark: window functions, feature engineering, Parquet output with partition pruning
- Streamed real-time delivery status events with Apache Kafka (producer → topic → consumer, 3 partitions, consumer groups)
- Orchestrated daily batch pipeline with Apache Airflow DAG (5 tasks, retry logic, PostgreSQL metadata backend)
- Transformed raw data with dbt (3 SQL models, automated data quality tests, lineage documentation)
- Containerised the entire stack (Kafka + Postgres + Airflow) with Docker Compose — starts with `docker-compose up`
- Loaded 50,000 rows to BigQuery (GCP) with date-partitioned, city-clustered table; mirrored events to Pub/Sub
- Automated CI/CD with GitHub Actions: 7 pytest unit tests + flake8 linting run on every push to main
- Trained Random Forest classifier (83% accuracy, ROC-AUC 0.88) proving delivery preferences improve success by 25+ pp
- Built Streamlit dashboard with business impact calculator showing ₹1.6Cr+ annual savings at 100K daily volume

GitHub: `github.com/gittdaksha/delivery-optimisation`

---

## What to mention in interviews

**How to use this section:**
- Read the sample answer below out loud a few times before your interview
- It sounds natural because it follows the pattern: what problem → what tools → what result
- Every sentence names a tool and connects it to a business outcome — this is exactly what technical interviewers are listening for
- You do not need to memorise it word for word; knowing what you built means you can answer this naturally

**"Tell me about a data engineering project you've built"**

- "I built a delivery optimisation pipeline end-to-end"
- "The batch side uses Python for data generation, dbt for SQL transformations with automated tests, and an Airflow DAG that orchestrates the full flow daily"
- "The real-time side uses Apache Kafka — a producer publishes delivery status events to a topic with 3 partitions, and a consumer reads them and logs them to a database"
- "For large-scale processing I used PySpark — DataFrames, window functions to rank delivery performance by city, and Parquet output with city partitioning"
- "The entire stack — Kafka, PostgreSQL, and Airflow — runs with `docker-compose up`"
- "I also loaded the same data to BigQuery on GCP, created a date-partitioned and city-clustered table for query performance, and mirrored real-time events to Google Pub/Sub"
- "CI/CD is automated with GitHub Actions — 7 pytest unit tests and flake8 linting run on every push so broken code can never reach main silently"
- "On top of that I trained a Random Forest model with 83% accuracy: apartments + morning windows fail 35% more often, and preferences + alerts improve success by 25 percentage points"
- "A Streamlit dashboard shows the business impact — at 100K daily deliveries, improving FADR by just 1% saves ₹16 lakh per day"

- This single answer covers: Kafka, Spark, Airflow, dbt, Docker, BigQuery, Pub/Sub, CI/CD, ML, SQL, dashboarding, and business impact — the full senior DE (Data Engineer) stack

---

---

## Git Checkpoint — End of Guide 13

- This is the full Git workflow you do at the end of every guide
- In a real office this is called "raising a PR (Pull Request)"
- You have now done this 13 times — it is automatic

**PR title and message for this guide:**
- Title: `Guide 13: project complete — README, CV entry, GitHub published`
- Description: `Guide 13 adds the final CV entry, LinkedIn post template, and interview Q&A. Project is now fully published on GitHub with 13 closed PRs showing professional contribution history.`

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
git add GUIDE_13_GITHUB.md  # stage the updated guide file
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
git commit -m "Guide 13: project complete — README, CV entry, GitHub published"  # save final snapshot
```
**What a commit is:**
- A permanent snapshot saved in Git's history
- Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`)
- You can always return to this exact state

**What makes a good commit message:**
- Good: `"Guide 13: project complete — README, CV entry, GitHub published"`
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
l8j5e6k Guide 13: project complete — README, CV entry, GitHub published
96b2986 Add logs/, .claude/, 4/ to .gitignore
9781c83 Merge pull request #10 from gittdaksha/feature/guide-12-cicd
```

**In an office:**
- `git log --oneline` is one of the most used commands
- It gives you the full history of the branch at a glance

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-13-github  # upload; -u links to GitHub
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

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-13-github had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into main."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `main` ← where the code will go
   - **compare:** `feature/guide-13-github` ← what you are merging in
3. Title: `Guide 13: project complete — README, CV entry, GitHub published`
4. Description: `Guide 13 adds the final CV entry, LinkedIn post template, and interview Q&A. Project is now fully published on GitHub with 13 closed PRs showing professional contribution history.`
5. Click **Create pull request**
6. Click **Merge pull request** → **Confirm merge**

**In an office:**
- A colleague would review your PR before approving
- They would read your diff, leave comments, and you would discuss
- Here you review and merge yourself — but the process is identical

**Why not push directly to main?**
- In real teams, direct pushes to main are blocked
- Every change must go through a PR
- This ensures someone always reviews code before it merges
- You are building that exact habit

---

### Step G11 — Pull the merged changes back locally

```bash
git checkout main  # switch back to main
```
- Switches you back to main
- No `-b` here — `main` already exists, you are just switching to it

```bash
git pull origin main  # download merged PR
```
- Downloads the merged PR from GitHub into your local main
- Your local main now has everything from the feature branch you just merged

**What each part means:**
- `origin` — download from GitHub (the remote)
- `main` — specifically from the main branch on GitHub
- `pull` — download + merge in one step (it runs `git fetch` then `git merge` automatically)

```bash
git log --oneline  # verify Guide 13 commit appears
```
- You should now see your Guide 13 commit in main's history
- Confirm it is there

**What `--oneline` means:** Show one line per commit instead of the full multi-line format.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-13-github  # -d = delete local merged branch
```
**What `-d` means:**
- Delete the branch locally
- Git will refuse to delete if the branch has unmerged commits — a safety guard
- Since you just merged the PR, `-d` works
- Use `-D` (capital D) only if you want to force-delete without merging

```bash
git push origin --delete feature/guide-13-github  # delete branch on GitHub too
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

### What your GitHub looks like after this

- **Pull Requests tab** → 13 closed PRs, one per guide — a professional contribution history
- **main branch → commits** → the complete project from Guide 01 through Guide 13
- **Branches** → only `main` remains — all feature branches were cleaned up

- This is exactly what a professional Git history looks like
- You built a full data engineering portfolio with proper version control habits from day one

**Next:** [GUIDE_14_INTERVIEW_PREP.md](GUIDE_14_INTERVIEW_PREP.md) — Full interview Q&A for every tool and concept in this project
