# Guide 10 — Interactive Dashboard with Streamlit

**Goal:** Build a web dashboard that lets anyone explore the FADR (First Attempt Delivery Rate) data, run predictions, and see the business impact of the proposed solutions — without needing to code.

---

## Why Streamlit?

- Streamlit turns a Python script into a web app
- No HTML, no JavaScript, no deployment configuration
- You write Python and get an interactive UI
- Used by data teams at Uber, Airbnb, and hundreds of other companies for internal analytics tools

---

## Git — Before You Start This Guide

- Every guide begins the same way in a real office: make sure you are on the right branch and it is up to date before touching any files

### Step G1 — Make sure you are on develop and it is current

```bash
git checkout develop  # switch to the develop branch (must exist already)
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
git status  # show current branch state and any modified files
```
**What this does:**
- Shows the current state
- You should see `On branch develop, nothing to commit, working tree clean`
- If you see modified files here, deal with them before moving forward — do not carry unrelated changes into a new branch
- No flags here — `git status` always shows full current state

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-10-dashboard  # -b = create new branch and switch to it
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
git branch  # list all branches; * marks your current branch
```
- You will see a `*` next to your current branch
- That `*` means "you are here"

---

## Step 7.1 — Create `src/dashboard.py`

Create the file `src/dashboard.py`:

**How to create this file:**
```bash
notepad src/dashboard.py  # open/create file in Windows Notepad
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

**What `src/dashboard.py` does and why it exists:**
- **What it does:** A Streamlit web app that reads the SQLite database and the saved ML model, then renders live FADR metrics, charts, a business impact calculator, and city-level heatmaps in a browser
- **Why separate:** The dashboard is a presentation layer — it consumes the outputs that the pipeline already produced; merging it into any earlier script would couple UI code with data-processing logic, making both harder to maintain
- **Input:** `data/delivery_db.sqlite` (live SQL queries against 50,000 delivery records) + `models/fadr_predictor.pkl` (trained model for predictions)
- **Output:** Streamlit web app at `localhost:8501` (interactive browser dashboard with charts, KPIs, and business impact calculator)
- **Pipeline position:** `data/delivery_db.sqlite` (from `ingest.py`) + `models/fadr_predictor.pkl` (from `predict.py`) → **this script** → interactive web dashboard at `localhost:8501`

```python
import streamlit as st  # web app framework, turns script into a web page
import pandas as pd  # data tables (DataFrames)
import sqlite3  # built-in Python library for reading SQLite databases
import pickle  # load saved ML model from a .pkl file
import matplotlib.pyplot as plt  # draw charts and graphs
import seaborn as sns  # heatmap and statistical charts

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(  # configure browser tab appearance
    page_title="Delivery Optimisation Dashboard",  # text shown in browser tab
    page_icon="📦",  # icon shown in browser tab
    layout="wide"  # use full screen width instead of narrow default
)

# ── Load data ───────────────────────────────────────────────────────────────
# What @st.cache_data does: this decorator tells Streamlit to run this function
# once, cache the result (the DataFrame) in memory, and return the cached copy
# on every subsequent call — without re-reading from the database. This makes
# the dashboard fast: 50,000 rows are loaded once, not on every user interaction.
# Use @st.cache_data for data (DataFrames, lists, dicts).
@st.cache_data  # cache result; avoid re-querying DB on every interaction
def load_data():  # function to read all deliveries from SQLite
    conn = sqlite3.connect('data/delivery_db.sqlite')  # open the database file
    df = pd.read_sql("SELECT * FROM deliveries", conn)  # run SQL query → DataFrame
    conn.close()  # always close DB connection when done
    return df  # send the DataFrame back to the caller

# What @st.cache_resource does: similar to @st.cache_data but for shared resources
# like database connections, ML models, or API clients that should not be
# recreated for every user interaction. The loaded model is kept in memory and
# reused — loading a pickle file repeatedly would slow the dashboard significantly.
@st.cache_resource  # cache model object in memory, not reloaded on each click
def load_model():  # function to load the saved Random Forest model
    with open('models/fadr_predictor.pkl', 'rb') as f:  # rb = read binary mode
        return pickle.load(f)  # deserialise the .pkl file back to a Python object

df = load_data()  # call the function once; cached result reused after that

# ── Header ──────────────────────────────────────────────────────────────────
st.title("📦 Delivery Optimisation — FADR Analytics")  # large H1 heading at top
# next line: italic subheading shown below the title
st.markdown("*First Attempt Delivery Rate dashboard — identifying where and why deliveries fail*")

# ── KPI Row ─────────────────────────────────────────────────────────────────
# What st.columns() does: divides the page horizontally into N equal columns.
# Each column is an independent layout container. You write content into each
# one using a with block or by calling methods on the column object (col1.metric()).
col1, col2, col3, col4 = st.columns(4)  # split page into 4 equal side-by-side columns

total     = len(df)  # count total delivery attempts
success   = df['is_successful'].sum()  # count rows where delivery succeeded
failed    = total - success  # count rows where delivery failed
# → success = 37,650  |  total = 50,000  |  37,650 / 50,000 * 100 = 75.3
fadr      = success / total * 100  # FADR as a percentage (e.g. 75.3)
# df[df['attempt_number'] > 1] = keep only rows where attempt_number is 2 or higher
# .shape returns a tuple (rows, columns); .shape[0] = just the row count
repeat    = df[df['attempt_number'] > 1].shape[0]  # count rows needing re-delivery

# What st.metric() is: a Streamlit widget that displays a bold headline number
# with an optional delta value shown in green (positive) or red (negative) below it.
# It is designed for KPI (Key Performance Indicator) tiles — the headline numbers
# at the top of a dashboard.
# f"{total:,}" = f-string with :, format spec → adds thousand-separator commas
# e.g. total=50000 → "50,000"
col1.metric("Total Attempts",         f"{total:,}")  # KPI tile 1; :, adds comma separator
# f"{fadr:.1f}%" = :.1f means 1 decimal place → fadr=75.34 → "75.3%"
col2.metric("Overall FADR",           f"{fadr:.1f}%")  # KPI tile 2; :.1f = 1 decimal place
# delta= shows a secondary number below the headline; delta_color="inverse" makes it red
# because for a bad metric (failures), a negative delta is highlighted red not green
# f"-{failed/total*100:.1f}%" builds the string: "-" + failure% rounded to 1 decimal
col3.metric("Failed Deliveries",      f"{failed:,}",  delta=f"-{failed/total*100:.1f}%", delta_color="inverse")
# shows repeat attempts as % of total; red because it indicates wasted cost
col4.metric("Repeat Attempt Required",f"{repeat:,}",  delta=f"{repeat/total*100:.1f}% of total", delta_color="inverse")

# What st.divider() does: draws a horizontal line across the full width of the
# page, visually separating sections of the dashboard so users can distinguish
# different topics at a glance.
st.divider()  # horizontal line to separate sections visually

# ── Two-column analysis ─────────────────────────────────────────────────────
col_a, col_b = st.columns(2)  # split page into 2 side-by-side panels

with col_a:  # everything indented here appears in the left panel
    st.subheader("FADR by Delivery Window")  # bold H3 section heading
    # .groupby('delivery_window') = group rows by each window value (morning, afternoon, etc.)
    # ['is_successful'].mean() = average of 0/1 column = fraction that succeeded
    # .sort_values() = sort ascending so worst window appears at the bottom of the chart
    # * 100 = convert 0.75 fraction to 75.0 percent
    window_fadr = df.groupby('delivery_window')['is_successful'].mean().sort_values() * 100
    fig, ax = plt.subplots(figsize=(7, 4))  # create a 7x4 inch figure
    # barh = horizontal bar chart; colours go red→orange→green→blue
    bars = ax.barh(window_fadr.index, window_fadr.values, color=['#d62728','#ff7f0e','#2ca02c','#1f77b4'])
    ax.set_xlabel("FADR (%)")  # label the x-axis
    # draw a vertical dashed line at the overall average for reference
    ax.axvline(fadr, color='black', linestyle='--', linewidth=1, label=f'Overall avg: {fadr:.1f}%')
    ax.legend()  # show the legend label for the average line
    # zip(bars, window_fadr.values) pairs each bar object with its numeric value
    # so in each iteration: bar = the rectangle shape, val = the % number
    for bar, val in zip(bars, window_fadr.values):  # loop over bars + values together
        # bar.get_y() = bottom edge of bar  |  bar.get_height()/2 = half the bar height
        # together they calculate the vertical midpoint of each bar
        # val + 0.3 = nudge the label 0.3 units to the right of the bar tip
        ax.text(val + 0.3, bar.get_y() + bar.get_height()/2, f'{val:.1f}%', va='center')
    # What plt.tight_layout() does: automatically adjusts the spacing between
    # chart elements (title, axis labels, tick marks) so nothing overlaps or gets
    # cut off. Always call it before saving or displaying a matplotlib chart.
    plt.tight_layout()  # auto-fix spacing so labels don't get cut off
    st.pyplot(fig)  # render the matplotlib figure in Streamlit

with col_b:  # everything indented here appears in the right panel
    st.subheader("FADR by Address Type")  # bold H3 section heading
    # same pattern as col_a: groupby → mean → sort → scale
    addr_fadr = df.groupby('address_type')['is_successful'].mean().sort_values() * 100
    fig2, ax2 = plt.subplots(figsize=(7, 4))  # new 7x4 inch figure
    bars2 = ax2.barh(addr_fadr.index, addr_fadr.values, color='steelblue')  # horizontal bars
    ax2.set_xlabel("FADR (%)")  # label the x-axis
    ax2.axvline(fadr, color='black', linestyle='--', linewidth=1)  # overall average line
    for bar, val in zip(bars2, addr_fadr.values):  # loop to add value labels
        # bar.get_y() + bar.get_height()/2 = vertical midpoint of the bar
        ax2.text(val + 0.3, bar.get_y() + bar.get_height()/2, f'{val:.1f}%', va='center')
    plt.tight_layout()  # prevent labels from being clipped
    st.pyplot(fig2)  # render chart in Streamlit

st.divider()  # horizontal line separator

# ── Preference & Alert Impact ───────────────────────────────────────────────
st.subheader("Impact of Data-Driven Features")  # section heading
col_c, col_d = st.columns(2)  # two side-by-side panels

with col_c:  # left panel: preference impact chart
    pref_data = df.groupby('has_delivery_preference')['is_successful'].mean() * 100  # FADR by preference flag
    labels = ['No Preference Set', 'Preference Set']  # x-axis bar labels
    fig3, ax3 = plt.subplots(figsize=(5, 3))  # smaller figure for side panel
    ax3.bar(labels, pref_data.values, color=['#ff7f0e', '#2ca02c'])  # orange=no pref, green=pref set
    ax3.set_ylabel("FADR (%)")  # y-axis label
    ax3.set_title("Delivery Preference Profile Impact")  # chart title
    for i, v in enumerate(pref_data.values):  # loop to add labels above each bar
        ax3.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold')  # label above bar
    st.pyplot(fig3)  # render chart

with col_d:  # right panel: proximity alert impact chart
    alert_data = df.groupby('proximity_alert_sent')['is_successful'].mean() * 100  # FADR by alert flag
    labels2 = ['No Alert Sent', 'Alert Sent']  # x-axis bar labels
    fig4, ax4 = plt.subplots(figsize=(5, 3))  # figure for alert impact chart
    ax4.bar(labels2, alert_data.values, color=['#ff7f0e', '#2ca02c'])  # orange=no alert, green=alert sent
    ax4.set_ylabel("FADR (%)")  # y-axis label
    ax4.set_title("Proximity Alert Impact")  # chart title
    for i, v in enumerate(alert_data.values):  # loop to add labels above each bar
        ax4.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold')  # label above bar
    st.pyplot(fig4)  # render chart

st.divider()  # section separator

# ── Cost Calculator ─────────────────────────────────────────────────────────
st.subheader("Business Impact Calculator")  # section heading
st.markdown("Estimate the operational cost of failed deliveries and the savings from improving FADR.")  # description text

col_e, col_f = st.columns(2)  # inputs on left, calculated outputs on right

with col_e:  # left panel: user input controls
    # number_input: text box with up/down arrows; value=default shown, step=increment
    daily_vol     = st.number_input("Daily delivery volume", value=100000, step=10000)
    # cost of each failed delivery in rupees (default ₹45)
    cost_per_fail = st.number_input("Cost per failed attempt (₹)", value=45, step=5)
    # st.slider(label, min, max, default, step)
    # float(f"{fadr:.1f}") converts the calculated fadr float to exactly 1 decimal place
    # so the slider default matches the data (e.g. 75.3) not a long float like 75.3142...
    current_fadr  = st.slider("Current FADR (%)", 60.0, 95.0, float(f"{fadr:.1f}"), step=0.1)
    # min(current_fadr + 5.0, 99.0) = add 5% to current, but cap at 99.0 so slider stays valid
    # if current_fadr is 96.0, then 96.0+5=101.0 which is above max=99.0, so min() gives 99.0
    target_fadr   = st.slider("Target FADR (%) after improvement", current_fadr, 99.0, min(current_fadr + 5.0, 99.0), step=0.1)

with col_f:  # right panel: calculated results update automatically
    # (1 - current_fadr / 100) = failure rate as a decimal
    # e.g. FADR=75% → failure rate = 1 - 0.75 = 0.25 → 100,000 * 0.25 = 25,000 failures/day
    current_failures = daily_vol * (1 - current_fadr / 100)  # failures per day at current FADR
    target_failures  = daily_vol * (1 - target_fadr / 100)  # failures per day at target FADR
    # difference in failures × cost per fail = money saved per day
    daily_savings    = (current_failures - target_failures) * cost_per_fail  # rupees saved per day
    annual_savings   = daily_savings * 365  # rupees saved per year

    st.metric("Current daily failures",    f"{int(current_failures):,}")  # KPI tile
    st.metric("Target daily failures",     f"{int(target_failures):,}")  # KPI tile
    st.metric("Daily cost saving",         f"₹{daily_savings:,.0f}")  # KPI tile
    st.metric("Annual cost saving",        f"₹{annual_savings:,.0f}", delta="per year")  # KPI tile

st.divider()  # section separator

# ── Failure Reason Breakdown ────────────────────────────────────────────────
st.subheader("Why Deliveries Fail")  # section heading
fail_df = df[df['is_successful'] == 0]['failure_reason'].value_counts()  # count each failure reason
fig5, ax5 = plt.subplots(figsize=(8, 3))  # wide, short figure
fail_df.plot(kind='barh', ax=ax5, color='crimson')  # horizontal bar chart in red
ax5.set_xlabel("Number of failures")  # x-axis label
ax5.set_title("Top Failure Reasons")  # chart title
st.pyplot(fig5)  # render chart

st.divider()  # section separator

# ── City Filter ─────────────────────────────────────────────────────────────
st.subheader("Explore by City")  # section heading
# sorted(df['city'].unique()) = get all unique city values, then sort alphabetically
# this ensures the dropdown always shows cities in A→Z order
city = st.selectbox("Select city", sorted(df['city'].unique()))  # dropdown of all unique cities
# df['city'] == city creates a True/False column; df[...] keeps only True rows
city_df = df[df['city'] == city]  # filter rows for the selected city only
city_fadr = city_df['is_successful'].mean() * 100  # FADR % for this city
# f"**text**" = bold in Markdown; {len(city_df):,} adds comma separator to the count
st.markdown(f"**{city} FADR: {city_fadr:.1f}%** across {len(city_df):,} attempts")  # bold summary

# .groupby(['address_type', 'delivery_window']) = group by two columns simultaneously
# .mean() = FADR fraction for each combination
# .unstack() = pivot the inner groupby level (delivery_window) from rows into columns
# result: a 2D table where rows = address_type, columns = delivery_window, values = FADR
# * 100 = convert fractions to percentages
city_segment = city_df.groupby(['address_type', 'delivery_window'])['is_successful'].mean().unstack() * 100
fig6, ax6 = plt.subplots(figsize=(10, 4))  # wide figure for the heatmap
# annot=True = show the number in each cell
# fmt='.0f' = format numbers as integers (no decimals) inside cells
# cmap='RdYlGn' = Red (low FADR) → Yellow (mid) → Green (high FADR) colour scale
# vmin/vmax = pin the colour scale so 50% is always red and 95% is always green
sns.heatmap(city_segment, annot=True, fmt='.0f', cmap='RdYlGn', ax=ax6,
            vmin=50, vmax=95, linewidths=0.5)
ax6.set_title(f"{city}: FADR Heatmap by Address Type × Delivery Window")  # chart title
st.pyplot(fig6)  # render heatmap

st.caption("Built by Daksha Kurhade | Delivery Optimisation Data Engineering Project")  # small footer text
```

---

## Step 7.2 — Run the dashboard

```bash
streamlit run src/dashboard.py  # start web server; auto-opens browser at localhost:8501
```

**Why:**
- Streamlit automatically opens your browser to `http://localhost:8501`
- You will see the full interactive dashboard

---

## Step 7.3 — What the dashboard shows

| Section | What it answers |
|---|---|
| KPI Row | Headline numbers — FADR, failures, repeat trips |
| FADR by Window | Visually confirms morning hours are the worst |
| FADR by Address | Visually confirms apartments/PGs fail more |
| Preference Impact | Quantifies Feature 4 from the LinkedIn post |
| Alert Impact | Quantifies Feature 5 from the LinkedIn post |
| Business Impact Calculator | Lets stakeholders input their own scale to see savings |
| City heatmap | Cross-segment analysis — worst combinations by city |

---

## Step 7.4 — Screenshot for your CV/portfolio

- Once the dashboard runs, take a screenshot of it
- This is a visual proof point you can add to your portfolio, resume, or LinkedIn

---

## Step 7.5 — Commit

```bash
git add src/dashboard.py  # stage only this file, not any unrelated changes
git commit -m "Add Streamlit FADR dashboard with business impact calculator"  # save snapshot
```

---

## Checkpoint

You now have:
- A fully interactive web dashboard
- Business impact calculator (stakeholder-ready)
- City-level heatmap analysis

---

## Git Checkpoint — End of Guide 10

- This is the full Git workflow you do at the end of every guide
- In a real office this is called "raising a PR (Pull Request)"
- You will do this 13 times — by the third time it feels automatic

---

### Step G3 — Check what changed

```bash
git status  # show modified and untracked files before staging
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
git diff  # show exact lines changed (+ added, - removed) before staging
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
git add src/dashboard.py  # stage this file to include in the next commit
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
git diff --staged  # show diff of only staged files (what will be committed)
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
git commit -m "Guide 10: Streamlit dashboard with FADR analysis, heatmap, and business impact calculator"  # save permanent snapshot
```
**What a commit is:**
- A permanent snapshot saved in Git's history
- Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`)
- You can always return to this exact state

**What makes a good commit message:**
- Good: `"Guide 10: Streamlit dashboard with FADR analysis, heatmap, and business impact calculator"`
- Bad: `"done"`, `"update"`, `"changes"`
- Rule: your future self reading this 3 months later should know exactly what changed without looking at the code

---

### Step G8 — Check your commit was saved

```bash
git log --oneline  # show one-line summary of every commit; newest at top
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
i5g2b3h Guide 10: Streamlit dashboard with FADR analysis, heatmap, and business impact calculator
h4f1a2c Guide 09: Random Forest model predicting delivery success at 83% accuracy
9b2c3d1 Initial commit: project guides and README
```

**In an office:**
- `git log --oneline` is one of the most used commands
- It gives you the full history of the branch at a glance

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-10-dashboard  # upload commits; -u links branch to GitHub
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

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-10-dashboard had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-10-dashboard` ← what you are merging in
3. Title: `Guide 10: Streamlit dashboard`
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
git checkout develop  # switch back to develop branch (no -b, it already exists)
```
- Switches you back to develop
- No `-b` here — `develop` already exists, you are just switching to it

```bash
git pull origin develop  # download merged PR changes from GitHub into local develop
```
- Downloads the merged PR from GitHub into your local develop
- Your local develop now has everything from the feature branch you just merged

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub
- `pull` — download + merge in one step (it runs `git fetch` then `git merge` automatically)

```bash
git log --oneline  # verify your Guide 10 commit now appears in develop history
```
- You should now see your Guide 10 commit in develop's history
- Confirm it is there

**What `--oneline` means:** Show one line per commit instead of the full multi-line format.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-10-dashboard  # -d = delete local branch (safe, refuses if unmerged)
```
**What `-d` means:**
- Delete the branch locally
- Git will refuse to delete if the branch has unmerged commits — a safety guard
- Since you just merged the PR, `-d` works
- Use `-D` (capital D) only if you want to force-delete without merging

```bash
git push origin --delete feature/guide-10-dashboard  # delete the branch on GitHub too
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
git checkout -b feature/guide-11-bigquery  # -b = create new branch and switch to it
```

**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

- You are now on a fresh branch, ready for the next guide

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 10 commit is in the history
- **Branches** → feature/guide-10-dashboard is gone (deleted)

- This is exactly what a professional Git history looks like

**Next:** [GUIDE_11_BIGQUERY.md](GUIDE_11_BIGQUERY.md) — Run the same pipeline on GCP (Google Cloud Platform) BigQuery
