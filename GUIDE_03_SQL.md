# Guide 03 — Analytical SQL

**Goal:** Write SQL queries to answer real business questions about delivery performance. SQL is the most important skill for a data engineer — every pipeline, every transformation, every metric starts here.

---

## Why SQL?

**What SQL is:** SQL (Structured Query Language) is the standard language for asking questions of a database. Instead of loading all 50,000 rows into Python and filtering them yourself, you write a sentence in SQL and the database does the work for you — returning only the rows and columns you need.

SQL is how data engineers communicate with databases. You already have 50,000 rows in your database. SQL lets you ask it questions without loading everything into Python. It's fast, readable, and the universal language of data.

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
git checkout -b feature/guide-03-sql
```
**What `-b` means:** Create a new branch AND switch to it. Without `-b`, checkout only switches to an existing branch.

**Why a new branch for every guide:** Each branch is one unit of work. If something breaks, you can delete the branch and start fresh without affecting develop or main. In an office, each feature or fix lives on its own branch for the same reason.

Confirm you are on the right branch:
```bash
git branch
```
You will see a `*` next to your current branch. That `*` means "you are here".

---

## Step 3.1 — Create `sql/analytics_queries.sql`

**Core SQL keywords — what each one does:**
- **`SELECT`** — choose which columns to return (like choosing which spreadsheet columns to show)
- **`FROM`** — which table to read from
- **`WHERE`** — filter rows to only those matching a condition (like a search filter)
- **`GROUP BY`** — collapse many rows into one row per group (e.g. one row per city)
- **`ORDER BY`** — sort the results, `ASC` = smallest first, `DESC` = largest first

**Aggregate functions — what they do:**
- **`COUNT(*)`** — count the number of rows in the group
- **`SUM(column)`** — add up all values in that column
- **`AVG(column)`** — calculate the mean (average) of that column
- **`ROUND(value, 2)`** — round a number to 2 decimal places

Create the file `sql/analytics_queries.sql`:

**How to create this file:**
```bash
notepad sql/analytics_queries.sql
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```sql
-- ============================================================
-- QUERY 1: Overall FADR (the headline metric)
-- Business question: What % of deliveries succeed on first attempt?
-- ============================================================
SELECT
    COUNT(*)                                      AS total_attempts,
    SUM(is_successful)                            AS successful,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent,
    SUM(1 - is_successful)                        AS failed,
    ROUND(AVG(1 - is_successful) * 100, 2)        AS failure_rate_percent
FROM deliveries;


-- ============================================================
-- QUERY 2: FADR by delivery window
-- Business question: When do deliveries fail most?
-- Insight: Morning slots have lowest FADR because people are at work.
-- ============================================================
SELECT
    delivery_window,
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY delivery_window
ORDER BY fadr_percent ASC;


-- ============================================================
-- QUERY 3: FADR by address type
-- Business question: Which address types are hardest to deliver to?
-- Insight: Apartments/PGs fail more — access restrictions, no one home.
-- ============================================================
SELECT
    address_type,
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY address_type
ORDER BY fadr_percent ASC;


-- ============================================================
-- QUERY 4: Impact of delivery preferences
-- Business question: Does having a saved preference improve success?
-- This validates Feature 4 from the LinkedIn post.
-- ============================================================
SELECT
    has_delivery_preference,
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY has_delivery_preference;


-- ============================================================
-- QUERY 5: Impact of proximity alerts
-- Business question: Does a 15-minute early alert improve success?
-- This validates Feature 5 from the LinkedIn post.
-- ============================================================
SELECT
    proximity_alert_sent,
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY proximity_alert_sent;


-- ============================================================
-- QUERY 6: Top failure reasons
-- Business question: Why are deliveries failing?
-- ============================================================

-- What a subquery is: (SELECT COUNT(*) FROM deliveries WHERE is_successful = 0) is a
-- "subquery" — a query inside a query. It runs first and returns one number (the total
-- failed count), which the outer query then divides by to calculate a percentage.

SELECT
    failure_reason,
    COUNT(*)                                      AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM deliveries WHERE is_successful = 0), 2) AS pct_of_failures
FROM deliveries
WHERE is_successful = 0
GROUP BY failure_reason
ORDER BY count DESC;


-- ============================================================
-- QUERY 7: Cost of failure (estimated)
-- Business question: What is the operational cost of failed deliveries?
-- Assumptions: avg repeat attempt costs Rs 45 in fuel + time
-- ============================================================
SELECT
    city,
    SUM(1 - is_successful)                        AS failed_deliveries,
    SUM(1 - is_successful) * 45                   AS estimated_cost_inr,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY city
ORDER BY estimated_cost_inr DESC;


-- ============================================================
-- QUERY 8: Worst combination (cross-segment analysis)
-- Business question: What is the single worst address+window combination?
-- ============================================================

-- What HAVING does: HAVING filters groups after aggregation — WHERE filters
-- individual rows before grouping. You cannot use WHERE here because
-- total_attempts does not exist until after GROUP BY creates it.
-- Think of it as: WHERE filters rows, HAVING filters groups.

SELECT
    address_type,
    delivery_window,
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY address_type, delivery_window
HAVING total_attempts > 200
ORDER BY fadr_percent ASC
LIMIT 10;


-- ============================================================
-- QUERY 9: Repeat attempt analysis
-- Business question: How many parcels needed 2 or 3 attempts?
-- ============================================================
SELECT
    attempt_number,
    COUNT(*)                                      AS deliveries,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM deliveries), 2) AS pct_of_total
FROM deliveries
GROUP BY attempt_number
ORDER BY attempt_number;


-- ============================================================
-- QUERY 10: Impact of high order value on failure
-- Business question: Do expensive orders fail more (hand-over only)?
-- ============================================================

-- What CASE WHEN does: it is SQL's version of an if/else statement.
-- It reads each row and assigns a label based on the value in a column.
-- WHEN condition THEN 'label' — the first matching condition wins.
-- ELSE covers anything that did not match any earlier WHEN.

SELECT
    CASE
        WHEN order_value < 500  THEN 'Under Rs 500'
        WHEN order_value < 1500 THEN 'Rs 500-1500'
        WHEN order_value < 3000 THEN 'Rs 1500-3000'
        ELSE 'Above Rs 3000'
    END                                           AS value_bucket,
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY value_bucket
ORDER BY fadr_percent ASC;
```

---

## Step 3.2 — Run all queries

```bash
python -c "
import sqlite3

conn = sqlite3.connect('data/delivery_db.sqlite')
cur = conn.cursor()

queries = {
    'Overall FADR': 'SELECT ROUND(AVG(is_successful)*100,2) as fadr FROM deliveries',
    'FADR by Window': 'SELECT delivery_window, ROUND(AVG(is_successful)*100,2) as fadr FROM deliveries GROUP BY delivery_window ORDER BY fadr',
    'FADR by Address': 'SELECT address_type, ROUND(AVG(is_successful)*100,2) as fadr FROM deliveries GROUP BY address_type ORDER BY fadr',
    'Preference Impact': 'SELECT has_delivery_preference, ROUND(AVG(is_successful)*100,2) as fadr FROM deliveries GROUP BY has_delivery_preference',
}

for name, query in queries.items():
    print(f'\n--- {name} ---')
    cur.execute(query)
    for row in cur.fetchall():
        print(row)

conn.close()
"
```

---

## Step 3.3 — What you will observe

| Insight | What It Means |
|---|---|
| Morning FADR (First Attempt Delivery Rate) ~63% | Most people are at work 9–12am |
| Apartment FADR ~65% | Access restrictions, intercoms, locked lobbies |
| Preference saves ~8–10% FADR | Customers who set a preference fail less |
| Alert saves ~6–8% FADR | 15-min warning reduces "missed knock" failures |
| Repeat attempts: 22% need 2nd try | That's 11,000 extra trips on your dataset |

---

## Step 3.4 — Commit your work

```bash
git add sql/
git commit -m "Add analytical SQL queries for delivery FADR analysis"
```

---

## Checkpoint

You now have:
- 10 business-relevant SQL queries
- Quantified the impact of preferences and alerts
- Identified the worst-performing address+window combinations

---

## Git Checkpoint — End of Guide 03

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
git add sql/analytics_queries.sql
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
git commit -m "Guide 03: 10 analytical SQL queries for FADR analysis by window, address, city"
```
**What a commit is:** A permanent snapshot saved in Git's history. Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`). You can always return to this exact state.

**What makes a good commit message:**
- Good: `"Guide 03: 10 analytical SQL queries for FADR analysis by window, address, city"`
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
b5e2f1a Guide 03: 10 analytical SQL queries for FADR analysis by window, address, city
a3f9c2b Guide 02: data generator with 50k records, SQLite ingestion, API pattern
9b2c3d1 Initial commit: project guides and README
```

**In an office:** `git log --oneline` is one of the most used commands. It gives you the full history of the branch at a glance.

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-03-sql
```
**What `git push` does:** Uploads your local commits to GitHub. Until you push, your commit only exists on your laptop.

**What `-u` means:** Sets the upstream — links your local branch to a branch of the same name on GitHub. You only need `-u` the first time you push a new branch. After that, just `git push` is enough.

**What `origin` means:** The name of your GitHub remote. When you ran `git remote add origin ...` in Guide 00B, you named it `origin`. That name sticks.

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-03-sql had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-03-sql` ← what you are merging in
3. Title: `Guide 03: analytical SQL queries`
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
You should now see your Guide 03 commit in develop's history. Confirm it is there.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-03-sql
```
**What `-d` means:** Delete the branch locally. Git will refuse to delete if the branch has unmerged commits — a safety guard. Since you just merged the PR, `-d` works.

```bash
git push origin --delete feature/guide-03-sql
```
Deletes the branch on GitHub too.

**Why delete?** Merged branches are dead branches. Keeping them clutters the repository. In real teams, merged branches are always deleted. A clean repo = a professional habit.

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-04-dbt
```

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 03 commit is in the history
- **Branches** → feature/guide-03-sql is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_04_DBT.md](GUIDE_04_DBT.md) — Transform data with dbt (Data Build Tool) (the industry standard for SQL transformations)
