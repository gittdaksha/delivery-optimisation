# Guide 03 — Analytical SQL

**Goal:** Write SQL queries to answer real business questions about delivery performance. SQL is the most important skill for a data engineer — every pipeline, every transformation, every metric starts here.

---

## Why SQL?

**What SQL is:**
- SQL (Structured Query Language) is the standard language for asking questions of a database
- Instead of loading all 50,000 rows into Python and filtering them yourself, you write a sentence in SQL and the database does the work for you — returning only the rows and columns you need

- SQL is how data engineers communicate with databases
- You already have 50,000 rows in your database — SQL lets you ask it questions without loading everything into Python
- It's fast, readable, and the universal language of data

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
- No `-b` here — this switches to an existing branch. You do not use `-b` when the branch already exists

```bash
git pull origin develop  # download + merge changes from GitHub
```
**What this does:**
- Downloads any changes from GitHub that you do not have locally
- In an office, a colleague may have merged something since you last worked
- `pull` = download + merge in one command

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub

```bash
git status  # show current state of all files
```
**What this does:**
- Shows the current state
- You should see `On branch develop, nothing to commit, working tree clean`
- If you see modified files here, deal with them before moving forward — do not carry unrelated changes into a new branch
- No flags here — `git status` always shows full current state

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-03-sql  # -b = create new branch and switch to it
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
git branch  # list branches; * shows which one you are on
```
- You will see a `*` next to your current branch
- That `*` means "you are here"

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
notepad sql/analytics_queries.sql  # opens Notepad; click Yes to create the file
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

**What `analytics_queries.sql` does and why it exists:**
- **What it does:** A collection of 10 SQL queries that each answer one specific business question about delivery performance — from overall FADR to cost of failure to worst address-window combinations
- **Why separate:** Keeping SQL in `.sql` files (not buried inside Python strings) means any analyst, data scientist, or manager can open and read them without knowing Python. It also means each query is version-controlled independently — if Query 7's cost assumption changes, you update one block without touching Python code.
- **Input:** `data/delivery_db.sqlite` (the SQLite database loaded by `ingest.py`, specifically the `deliveries` table with 50,000 rows)
- **Output:** Query results printed to the terminal (tabular rows showing FADR percentages, failure counts, cost estimates — no file is written)
- **Pipeline position:** `data/delivery_db.sqlite` (loaded by `ingest.py`) → **these queries** → business insights that power the dashboard (Guide 10) and the ML features (Guide 09)

```sql
-- ============================================================
-- QUERY 1: Overall FADR (the headline metric)
-- Business question: What % of deliveries succeed on first attempt?
-- ============================================================
-- COUNT(*): counts every row regardless of value
-- → 50 000 rows in table → total_attempts = 50000

-- SUM(is_successful): is_successful is 0 or 1; summing 1s = counting successes
-- → values: 1,0,1,1,0 → SUM = 3 → successful = 3

-- AVG(is_successful) * 100: AVG of a 0/1 column = the proportion that are 1
-- → AVG(1,0,1,1,0) = 3/5 = 0.60  → × 100 = 60.0  → ROUND(..., 2) = 60.00
-- → fadr_percent = 60.00 means "60% first-attempt success rate"

-- SUM(1 - is_successful): flips 1→0 and 0→1, then sums — counts the 0s (failures)
-- → row is_successful=1 → 1-1=0 (not counted)
-- → row is_successful=0 → 1-0=1 (counted as failure)
-- → failed = total rows where is_successful was 0
SELECT
    COUNT(*)                                      AS total_attempts,     -- count every row
    SUM(is_successful)                            AS successful,         -- sum 1s = count successes
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent,       -- avg of 0/1 = rate; *100 = percent
    SUM(1 - is_successful)                        AS failed,             -- 1-1=0, 1-0=1 flips the flag
    ROUND(AVG(1 - is_successful) * 100, 2)        AS failure_rate_percent -- same trick for failures
FROM deliveries;                                                         -- the raw data table


-- ============================================================
-- QUERY 2: FADR by delivery window
-- Business question: When do deliveries fail most?
-- Insight: Morning slots have lowest FADR because people are at work.
-- ============================================================
-- GROUP BY delivery_window: collapses all rows with the same window into one output row
-- example rows in table: Morning,1 / Morning,0 / Afternoon,1 / Morning,1
-- → after GROUP BY:  Morning group   (3 rows) → COUNT=3, AVG=0.67 → fadr=66.67
--                    Afternoon group (1 row)  → COUNT=1, AVG=1.00 → fadr=100.00

-- ORDER BY fadr_percent ASC: ASC = ascending = smallest number first
-- → worst-performing window appears at the top of results (easiest to spot problems)
SELECT
    delivery_window,                              -- group label (Morning / Afternoon etc)
    COUNT(*)                                      AS total_attempts,     -- rows in each group
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent        -- success rate per window
FROM deliveries
GROUP BY delivery_window                          -- one result row per time window
ORDER BY fadr_percent ASC;                        -- ASC = worst (lowest) first


-- ============================================================
-- QUERY 3: FADR by address type
-- Business question: Which address types are hardest to deliver to?
-- Insight: Apartments/PGs fail more — access restrictions, no one home.
-- ============================================================
-- GROUP BY address_type: same mechanics as Query 2 — one output row per distinct address_type value
-- → Apartment group → its own COUNT and AVG
-- → Office group    → its own COUNT and AVG
-- ORDER BY fadr_percent ASC: lowest success rate (worst) appears first
SELECT
    address_type,                                 -- group label (Apartment / Office etc)
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY address_type                             -- one result row per address type
ORDER BY fadr_percent ASC;                        -- worst performer at top


-- ============================================================
-- QUERY 4: Impact of delivery preferences
-- Business question: Does having a saved preference improve success?
-- This validates Feature 4 from the LinkedIn post.
-- ============================================================
-- GROUP BY has_delivery_preference: only two distinct values (0 and 1) so result is exactly 2 rows
-- → group 0: all rows with no preference → their own COUNT, AVG → fadr_percent
-- → group 1: all rows with a preference  → their own COUNT, AVG → fadr_percent
-- reading the two rows side by side shows the impact of having a preference
SELECT
    has_delivery_preference,                      -- 0 = no preference, 1 = has preference
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY has_delivery_preference;                 -- compare 0 vs 1 side by side


-- ============================================================
-- QUERY 5: Impact of proximity alerts
-- Business question: Does a 15-minute early alert improve success?
-- This validates Feature 5 from the LinkedIn post.
-- ============================================================
-- GROUP BY proximity_alert_sent: same 2-row pattern as Query 4
-- → group 0: deliveries where no alert was sent → COUNT and AVG → fadr_percent
-- → group 1: deliveries where alert was sent    → COUNT and AVG → fadr_percent
-- difference between the two fadr_percent values = measurable impact of the alert feature
SELECT
    proximity_alert_sent,                         -- 0 = no alert, 1 = alert sent
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY proximity_alert_sent;                    -- compare 0 vs 1 side by side


-- ============================================================
-- QUERY 6: Top failure reasons
-- Business question: Why are deliveries failing?
-- ============================================================

-- What a subquery is: (SELECT COUNT(*) FROM deliveries WHERE is_successful = 0) is a
-- "subquery" — a query inside a query. It runs first and returns one number (the total
-- failed count), which the outer query then divides by to calculate a percentage.

-- WHERE is_successful = 0: filters BEFORE grouping — only failed rows enter GROUP BY
-- → rows with is_successful=1 are discarded entirely from this query

-- subquery (SELECT COUNT(*) FROM deliveries WHERE is_successful = 0):
-- → runs once, returns a single number, e.g. 12 000 (total failed deliveries)
-- → the outer query divides each group's count by that number

-- COUNT(*) * 100.0 / subquery: step-by-step for one group
-- → failure_reason = 'Wrong Address', COUNT(*) = 3600
-- → 3600 * 100.0 = 360000.0   (the .0 forces decimal division, not integer division)
-- → 360000.0 / 12000 = 30.0   → ROUND(..., 2) = 30.00
-- → pct_of_failures = 30.00 means "Wrong Address is 30% of all failures"

-- ORDER BY count DESC: DESC = descending = largest number first → most common reason at top
SELECT
    failure_reason,                               -- text label for why it failed
    COUNT(*)                                      AS count,              -- how many times this reason occurred
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM deliveries WHERE is_successful = 0), 2) AS pct_of_failures  -- share of all failures
FROM deliveries
WHERE is_successful = 0                           -- only look at failed deliveries
GROUP BY failure_reason                           -- one row per failure reason
ORDER BY count DESC;                              -- most common reason first


-- ============================================================
-- QUERY 7: Cost of failure (estimated)
-- Business question: What is the operational cost of failed deliveries?
-- Assumptions: avg repeat attempt costs Rs 45 in fuel + time
-- ============================================================
-- SUM(1 - is_successful): flip-and-sum trick from Query 1 — counts failures per city group
-- → city='Mumbai': rows 1,0,0,1,0 → 1-values: 0,1,1,0,1 → SUM = 3 → failed_deliveries = 3

-- SUM(1 - is_successful) * 45: multiply the failure count by cost assumption
-- → failed_deliveries = 3 → 3 * 45 = 135 → estimated_cost_inr = 135

-- ORDER BY estimated_cost_inr DESC: DESC = largest first → most expensive city at the top
SELECT
    city,                                         -- group by city
    SUM(1 - is_successful)                        AS failed_deliveries,  -- count failures per city
    SUM(1 - is_successful) * 45                   AS estimated_cost_inr, -- failures * Rs 45 per attempt
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY city
ORDER BY estimated_cost_inr DESC;                 -- most expensive city at top


-- ============================================================
-- QUERY 8: Worst combination (cross-segment analysis)
-- Business question: What is the single worst address+window combination?
-- ============================================================

-- What HAVING does: HAVING filters groups after aggregation — WHERE filters
-- individual rows before grouping. You cannot use WHERE here because
-- total_attempts does not exist until after GROUP BY creates it.
-- Think of it as: WHERE filters rows, HAVING filters groups.

-- GROUP BY address_type, delivery_window: creates one row per PAIR of values
-- → ('Apartment', 'Morning') → one row
-- → ('Apartment', 'Afternoon') → separate row
-- → ('Office', 'Morning') → separate row
-- total distinct combinations could be 3 address types × 4 windows = up to 12 rows

-- HAVING total_attempts > 200: filters the GROUPS produced by GROUP BY
-- execution order:  1) GROUP BY runs → creates groups
--                   2) COUNT(*) is calculated for each group → total_attempts exists now
--                   3) HAVING filters out groups where total_attempts <= 200
-- → you cannot use WHERE here because total_attempts does not exist until after step 1

-- LIMIT 10: after ORDER BY sorts all remaining rows, LIMIT cuts the output to 10 rows
-- → only the 10 worst address+window combinations are returned
SELECT
    address_type,
    delivery_window,
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY address_type, delivery_window            -- one row per address+window pair
HAVING total_attempts > 200                       -- HAVING = filter groups (not rows)
ORDER BY fadr_percent ASC                         -- worst combo first
LIMIT 10;                                         -- show only top 10 worst results


-- ============================================================
-- QUERY 9: Repeat attempt analysis
-- Business question: How many parcels needed 2 or 3 attempts?
-- ============================================================
-- subquery (SELECT COUNT(*) FROM deliveries): returns total row count, e.g. 50 000
-- COUNT(*) * 100.0 / 50000: step-by-step for attempt_number = 2
-- → COUNT(*) for group 2 = 11 000
-- → 11000 * 100.0 = 1100000.0   (100.0 not 100 → forces decimal division)
-- → 1100000.0 / 50000 = 22.0    → ROUND(..., 2) = 22.00
-- → pct_of_total = 22.00 means "22% of all deliveries needed a 2nd attempt"

-- ORDER BY attempt_number: no ASC/DESC specified → defaults to ASC → 1, 2, 3 in order
SELECT
    attempt_number,                               -- 1, 2, or 3
    COUNT(*)                                      AS deliveries,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM deliveries), 2) AS pct_of_total  -- share of all deliveries
FROM deliveries
GROUP BY attempt_number                           -- one row per attempt number
ORDER BY attempt_number;                          -- show 1, 2, 3 in order


-- ============================================================
-- QUERY 10: Impact of high order value on failure
-- Business question: Do expensive orders fail more (hand-over only)?
-- ============================================================

-- What CASE WHEN does: it is SQL's version of an if/else statement.
-- It reads each row and assigns a label based on the value in a column.
-- WHEN condition THEN 'label' — the first matching condition wins.
-- ELSE covers anything that did not match any earlier WHEN.

-- CASE WHEN evaluates conditions top-to-bottom; the FIRST matching WHEN wins
-- example row: order_value = 350
-- → WHEN 350 < 500  → TRUE  → result = 'Under Rs 500'  (stops here, skips rest)
-- example row: order_value = 800
-- → WHEN 800 < 500  → FALSE → try next
-- → WHEN 800 < 1500 → TRUE  → result = 'Rs 500-1500'   (stops here)
-- example row: order_value = 4500
-- → WHEN 4500 < 500  → FALSE
-- → WHEN 4500 < 1500 → FALSE
-- → WHEN 4500 < 3000 → FALSE
-- → ELSE             → result = 'Above Rs 3000'         (catch-all for remaining rows)
-- END AS value_bucket: closes the CASE expression and names the resulting column
SELECT
    CASE
        WHEN order_value < 500  THEN 'Under Rs 500'   -- first matching WHEN wins
        WHEN order_value < 1500 THEN 'Rs 500-1500'
        WHEN order_value < 3000 THEN 'Rs 1500-3000'
        ELSE 'Above Rs 3000'                           -- ELSE = catch-all for remaining rows
    END                                           AS value_bucket,       -- label for this bucket
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY value_bucket                             -- one row per price bucket
ORDER BY fadr_percent ASC;                        -- cheapest bucket vs most expensive
```

---

## Step 3.2 — Run all queries

**What this query runner does and why it exists:**
- **What it does:** Opens the SQLite database, loops through each named SQL query, executes it, and prints the results to the terminal so you can see the numbers immediately
- **Why separate:** The SQL file (`analytics_queries.sql`) only defines the queries — it cannot run itself. You need Python to open the database connection, send the SQL to SQLite, and format the output you can read. Keeping the runner separate from the queries means you can swap queries without touching the runner, and vice versa.
- **Input:** `data/delivery_db.sqlite` (SQLite database) and `sql/analytics_queries.sql` (the four named query definitions)
- **Output:** Query results printed to the terminal (4 labelled sections: Overall FADR, FADR by Window, FADR by Address, Preference Impact — no file written)
- **Pipeline position:** `data/delivery_db.sqlite` + `sql/analytics_queries.sql` (the query definitions) → **this runner** → printed results in your terminal (and later, inputs for the ML model and dashboard)

```bash
python -c "
import sqlite3

conn = sqlite3.connect('data/delivery_db.sqlite')  # open the database file
cur = conn.cursor()                                # cursor = tool to run SQL

queries = {
    'Overall FADR': 'SELECT ROUND(AVG(is_successful)*100,2) as fadr FROM deliveries',
    'FADR by Window': 'SELECT delivery_window, ROUND(AVG(is_successful)*100,2) as fadr FROM deliveries GROUP BY delivery_window ORDER BY fadr',
    'FADR by Address': 'SELECT address_type, ROUND(AVG(is_successful)*100,2) as fadr FROM deliveries GROUP BY address_type ORDER BY fadr',
    'Preference Impact': 'SELECT has_delivery_preference, ROUND(AVG(is_successful)*100,2) as fadr FROM deliveries GROUP BY has_delivery_preference',
}

# queries.items() returns each (key, value) pair as a tuple: ('Overall FADR', 'SELECT ...')
# → name = 'Overall FADR'   query = 'SELECT ROUND(...) ...'
# → name = 'FADR by Window' query = 'SELECT delivery_window, ...'
for name, query in queries.items():               # loop over each query by name
    print(f'\n--- {name} ---')
    cur.execute(query)                            # run the SQL query
    # fetchall() returns a list of tuples — one tuple per result row
    # → e.g. [(72.45,)] for Overall FADR  or  [('Morning', 63.1), ('Afternoon', 78.2)] for Window
    for row in cur.fetchall():                    # fetchall = get all result rows
        print(row)

conn.close()                                      # close connection when done
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
git add sql/                                      # stage all files inside the sql/ folder
git commit -m "Add analytical SQL queries for delivery FADR analysis"  # -m = commit message
```

---

## Checkpoint

You now have:
- 10 business-relevant SQL queries
- Quantified the impact of preferences and alerts
- Identified the worst-performing address+window combinations

---

## Git Checkpoint — End of Guide 03

- This is the full Git workflow you do at the end of every guide
- In a real office this is called "raising a PR (Pull Request)"
- You will do this 13 times — by the third time it feels automatic

---

### Step G3 — Check what changed

```bash
git status  # show which files changed since last commit
```
**What to look for:** Files listed in red under "Changes not staged for commit" — these are files you modified. Files in red under "Untracked files" — these are new files Git has never seen before. Nothing should be green yet — you have not staged anything.

**In an office:**
- Before staging anything, always read `git status` first
- It shows you exactly what you are about to commit
- Committing blindly is how secrets (passwords, API keys) accidentally get pushed to GitHub

---

### Step G4 — Review your changes line by line

```bash
git diff  # show exact line-by-line changes not yet staged
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
git add sql/analytics_queries.sql  # stage only this file
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
# --staged: shifts the comparison point
# without --staged:  working directory  vs  staging area   (what you changed but NOT yet added)
# with    --staged:  staging area        vs  last commit   (what you HAVE added, about to commit)
# → green lines (+) = new lines you added    → red lines (-) = lines you removed
git diff --staged  # show changes that ARE staged (about to be committed)
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
git commit -m "Guide 03: 10 analytical SQL queries for FADR analysis by window, address, city"  # -m = commit message
```
**What a commit is:**
- A permanent snapshot saved in Git's history
- Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`)
- You can always return to this exact state

**What makes a good commit message:**
- Good: `"Guide 03: 10 analytical SQL queries for FADR analysis by window, address, city"`
- Bad: `"done"`, `"update"`, `"changes"`

Rule: your future self reading this 3 months later should know exactly what changed without looking at the code.

---

### Step G8 — Check your commit was saved

```bash
# --oneline: compresses each commit from 6 lines to 1 line
# without --oneline → full format:
#   commit b5e2f1a...
#   Author: Daksha Kurhade <...>
#   Date:   Wed Jul 16 ...
#
#       Guide 03: 10 analytical SQL queries...
# with --oneline →  b5e2f1a Guide 03: 10 analytical SQL queries...
git log --oneline  # show one line per commit; most recent at top
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
b5e2f1a Guide 03: 10 analytical SQL queries for FADR analysis by window, address, city
a3f9c2b Guide 02: data generator with 50k records, SQLite ingestion, API pattern
9b2c3d1 Initial commit: project guides and README
```

**In an office:**
- `git log --oneline` is one of the most used commands
- It gives you the full history of the branch at a glance

---

### Step G9 — Push to GitHub

```bash
# -u = --set-upstream: permanently records the link between local and GitHub branch
# first push (need -u):   git push -u origin feature/guide-03-sql
#                         → LOCAL: saves "upstream = origin/feature/guide-03-sql" in .git/config
#                         → GITHUB: creates branch feature/guide-03-sql and uploads commits
# all later pushes:       git push
#                         → Git reads the saved upstream, knows where to send commits
git push -u origin feature/guide-03-sql  # -u = link local branch to GitHub branch
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
- You will see a yellow banner: **"feature/guide-03-sql had recent pushes"**

---

### Step G10 — Raise a Pull Request on GitHub

- A Pull Request (PR) is a formal request to merge your branch into another branch
- You are asking: "I finished this work, please review it and bring it into develop"

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-03-sql` ← what you are merging in
3. Title: `Guide 03: analytical SQL queries`
4. Description: `Added 10 analytical SQL queries covering FADR by window, address type, city, failure reasons, cost estimation, and repeat attempt analysis.`
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
git pull origin develop  # download the merged PR into local develop
```
- Downloads the merged PR from GitHub into your local develop
- Your local develop now has everything from the feature branch you just merged

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub
- `pull` — download + merge in one step (it runs `git fetch` then `git merge` automatically)

```bash
# --oneline: same as Step G8 — one short line per commit
# confirms the Guide 03 commit hash appears in develop's history after the merge
git log --oneline  # confirm Guide 03 commit appears in develop history
```
- You should now see your Guide 03 commit in develop's history
- Confirm it is there

**What `--oneline` means:** Show one line per commit instead of the full multi-line format.

---

### Step G12 — Delete the feature branch

```bash
# -d = --delete (safe mode): only deletes if the branch is fully merged
# → if branch has unmerged commits: "error: the branch is not fully merged"
# → use -D (capital) only to force-delete without the safety check
# LOCAL effect:  removes branch pointer from your machine
# GITHUB effect: none — branch still exists on GitHub until the push --delete below
git branch -d feature/guide-03-sql  # -d = delete local branch (safe: fails if unmerged)
```
**What `-d` means:**
- Delete the branch locally
- Git will refuse to delete if the branch has unmerged commits — a safety guard
- Since you just merged the PR, `-d` works

```bash
# --delete: tells GitHub to remove the named branch reference from its server
# syntax: git push <remote> --delete <branch-name>
# LOCAL effect:  none — your local branch is already deleted above
# GITHUB effect: feature/guide-03-sql disappears from GitHub's branch list immediately
git push origin --delete feature/guide-03-sql  # delete the branch on GitHub too
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
git checkout -b feature/guide-04-dbt  # -b = create new branch and switch to it
```

**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 03 commit is in the history
- **Branches** → feature/guide-03-sql is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_04_DBT.md](GUIDE_04_DBT.md) — Transform data with dbt (Data Build Tool) (the industry standard for SQL transformations)

---

## PR Record

- This section is added at the end of every guide to log exactly what PR title and description was used when merging into develop
- This way you always know which message was used for which guide

| Field | Value |
|---|---|
| **Branch merged** | `feature/guide-03-sql` → `develop` |
| **PR Title** | `Guide 03: added 10 analytical SQL queries for FADR analysis` |
| **PR Description** | `Added 10 analytical SQL queries covering FADR by window, address type, city, failure reasons, cost estimation, and repeat attempt analysis.` |
