# Guide 07 — Interactive Dashboard with Streamlit

**Goal:** Build a web dashboard that lets anyone explore the FADR (First Attempt Delivery Rate) data, run predictions, and see the business impact of the proposed solutions — without needing to code.

---

## Why Streamlit?

Streamlit turns a Python script into a web app. No HTML, no JavaScript, no deployment configuration. You write Python and get an interactive UI. It's used by data teams at Uber, Airbnb, and hundreds of other companies for internal analytics tools.

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
git checkout -b feature/guide-10-dashboard
```
**What `-b` means:** Create a new branch AND switch to it. Without `-b`, checkout only switches to an existing branch.

**Why a new branch for every guide:** Each branch is one unit of work. If something breaks, you can delete the branch and start fresh without affecting develop or main. In an office, each feature or fix lives on its own branch for the same reason.

Confirm you are on the right branch:
```bash
git branch
```
You will see a `*` next to your current branch. That `*` means "you are here".

---

## Step 7.1 — Create `src/dashboard.py`

Create the file `src/dashboard.py`:

**How to create this file:**
```bash
notepad src/dashboard.py
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```python
import streamlit as st
import pandas as pd
import sqlite3
import pickle
import matplotlib.pyplot as plt
import seaborn as sns

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Delivery Optimisation Dashboard",
    page_icon="📦",
    layout="wide"
)

# ── Load data ───────────────────────────────────────────────────────────────
# What @st.cache_data does: this decorator tells Streamlit to run this function
# once, cache the result (the DataFrame) in memory, and return the cached copy
# on every subsequent call — without re-reading from the database. This makes
# the dashboard fast: 50,000 rows are loaded once, not on every user interaction.
# Use @st.cache_data for data (DataFrames, lists, dicts).
@st.cache_data
def load_data():
    conn = sqlite3.connect('data/delivery_db.sqlite')
    df = pd.read_sql("SELECT * FROM deliveries", conn)
    conn.close()
    return df

# What @st.cache_resource does: similar to @st.cache_data but for shared resources
# like database connections, ML models, or API clients that should not be
# recreated for every user interaction. The loaded model is kept in memory and
# reused — loading a pickle file repeatedly would slow the dashboard significantly.
@st.cache_resource
def load_model():
    with open('models/fadr_predictor.pkl', 'rb') as f:
        return pickle.load(f)

df = load_data()

# ── Header ──────────────────────────────────────────────────────────────────
st.title("📦 Delivery Optimisation — FADR Analytics")
st.markdown("*First Attempt Delivery Rate dashboard — identifying where and why deliveries fail*")

# ── KPI Row ─────────────────────────────────────────────────────────────────
# What st.columns() does: divides the page horizontally into N equal columns.
# Each column is an independent layout container. You write content into each
# one using a with block or by calling methods on the column object (col1.metric()).
col1, col2, col3, col4 = st.columns(4)

total     = len(df)
success   = df['is_successful'].sum()
failed    = total - success
fadr      = success / total * 100
repeat    = df[df['attempt_number'] > 1].shape[0]

# What st.metric() is: a Streamlit widget that displays a bold headline number
# with an optional delta value shown in green (positive) or red (negative) below it.
# It is designed for KPI (Key Performance Indicator) tiles — the headline numbers
# at the top of a dashboard.
col1.metric("Total Attempts",         f"{total:,}")
col2.metric("Overall FADR",           f"{fadr:.1f}%")
col3.metric("Failed Deliveries",      f"{failed:,}",  delta=f"-{failed/total*100:.1f}%", delta_color="inverse")
col4.metric("Repeat Attempt Required",f"{repeat:,}",  delta=f"{repeat/total*100:.1f}% of total", delta_color="inverse")

# What st.divider() does: draws a horizontal line across the full width of the
# page, visually separating sections of the dashboard so users can distinguish
# different topics at a glance.
st.divider()

# ── Two-column analysis ─────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("FADR by Delivery Window")
    window_fadr = df.groupby('delivery_window')['is_successful'].mean().sort_values() * 100
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(window_fadr.index, window_fadr.values, color=['#d62728','#ff7f0e','#2ca02c','#1f77b4'])
    ax.set_xlabel("FADR (%)")
    ax.axvline(fadr, color='black', linestyle='--', linewidth=1, label=f'Overall avg: {fadr:.1f}%')
    ax.legend()
    for bar, val in zip(bars, window_fadr.values):
        ax.text(val + 0.3, bar.get_y() + bar.get_height()/2, f'{val:.1f}%', va='center')
    # What plt.tight_layout() does: automatically adjusts the spacing between
    # chart elements (title, axis labels, tick marks) so nothing overlaps or gets
    # cut off. Always call it before saving or displaying a matplotlib chart.
    plt.tight_layout()
    st.pyplot(fig)

with col_b:
    st.subheader("FADR by Address Type")
    addr_fadr = df.groupby('address_type')['is_successful'].mean().sort_values() * 100
    fig2, ax2 = plt.subplots(figsize=(7, 4))
    bars2 = ax2.barh(addr_fadr.index, addr_fadr.values, color='steelblue')
    ax2.set_xlabel("FADR (%)")
    ax2.axvline(fadr, color='black', linestyle='--', linewidth=1)
    for bar, val in zip(bars2, addr_fadr.values):
        ax2.text(val + 0.3, bar.get_y() + bar.get_height()/2, f'{val:.1f}%', va='center')
    plt.tight_layout()
    st.pyplot(fig2)

st.divider()

# ── Preference & Alert Impact ───────────────────────────────────────────────
st.subheader("Impact of Data-Driven Features")
col_c, col_d = st.columns(2)

with col_c:
    pref_data = df.groupby('has_delivery_preference')['is_successful'].mean() * 100
    labels = ['No Preference Set', 'Preference Set']
    fig3, ax3 = plt.subplots(figsize=(5, 3))
    ax3.bar(labels, pref_data.values, color=['#ff7f0e', '#2ca02c'])
    ax3.set_ylabel("FADR (%)")
    ax3.set_title("Delivery Preference Profile Impact")
    for i, v in enumerate(pref_data.values):
        ax3.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold')
    st.pyplot(fig3)

with col_d:
    alert_data = df.groupby('proximity_alert_sent')['is_successful'].mean() * 100
    labels2 = ['No Alert Sent', 'Alert Sent']
    fig4, ax4 = plt.subplots(figsize=(5, 3))
    ax4.bar(labels2, alert_data.values, color=['#ff7f0e', '#2ca02c'])
    ax4.set_ylabel("FADR (%)")
    ax4.set_title("Proximity Alert Impact")
    for i, v in enumerate(alert_data.values):
        ax4.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold')
    st.pyplot(fig4)

st.divider()

# ── Cost Calculator ─────────────────────────────────────────────────────────
st.subheader("Business Impact Calculator")
st.markdown("Estimate the operational cost of failed deliveries and the savings from improving FADR.")

col_e, col_f = st.columns(2)

with col_e:
    daily_vol     = st.number_input("Daily delivery volume", value=100000, step=10000)
    cost_per_fail = st.number_input("Cost per failed attempt (₹)", value=45, step=5)
    current_fadr  = st.slider("Current FADR (%)", 60.0, 95.0, float(f"{fadr:.1f}"), step=0.1)
    target_fadr   = st.slider("Target FADR (%) after improvement", current_fadr, 99.0, min(current_fadr + 5.0, 99.0), step=0.1)

with col_f:
    current_failures = daily_vol * (1 - current_fadr / 100)
    target_failures  = daily_vol * (1 - target_fadr / 100)
    daily_savings    = (current_failures - target_failures) * cost_per_fail
    annual_savings   = daily_savings * 365

    st.metric("Current daily failures",    f"{int(current_failures):,}")
    st.metric("Target daily failures",     f"{int(target_failures):,}")
    st.metric("Daily cost saving",         f"₹{daily_savings:,.0f}")
    st.metric("Annual cost saving",        f"₹{annual_savings:,.0f}", delta="per year")

st.divider()

# ── Failure Reason Breakdown ────────────────────────────────────────────────
st.subheader("Why Deliveries Fail")
fail_df = df[df['is_successful'] == 0]['failure_reason'].value_counts()
fig5, ax5 = plt.subplots(figsize=(8, 3))
fail_df.plot(kind='barh', ax=ax5, color='crimson')
ax5.set_xlabel("Number of failures")
ax5.set_title("Top Failure Reasons")
st.pyplot(fig5)

st.divider()

# ── City Filter ─────────────────────────────────────────────────────────────
st.subheader("Explore by City")
city = st.selectbox("Select city", sorted(df['city'].unique()))
city_df = df[df['city'] == city]
city_fadr = city_df['is_successful'].mean() * 100
st.markdown(f"**{city} FADR: {city_fadr:.1f}%** across {len(city_df):,} attempts")

city_segment = city_df.groupby(['address_type', 'delivery_window'])['is_successful'].mean().unstack() * 100
fig6, ax6 = plt.subplots(figsize=(10, 4))
sns.heatmap(city_segment, annot=True, fmt='.0f', cmap='RdYlGn', ax=ax6,
            vmin=50, vmax=95, linewidths=0.5)
ax6.set_title(f"{city}: FADR Heatmap by Address Type × Delivery Window")
st.pyplot(fig6)

st.caption("Built by Daksha Kurhade | Delivery Optimisation Data Engineering Project")
```

---

## Step 7.2 — Run the dashboard

```bash
streamlit run src/dashboard.py
```

**Why:** Streamlit automatically opens your browser to `http://localhost:8501`. You will see the full interactive dashboard.

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

Once the dashboard runs, take a screenshot of it. This is a visual proof point you can add to your portfolio, resume, or LinkedIn.

---

## Step 7.5 — Commit

```bash
git add src/dashboard.py
git commit -m "Add Streamlit FADR dashboard with business impact calculator"
```

---

## Checkpoint

You now have:
- A fully interactive web dashboard
- Business impact calculator (stakeholder-ready)
- City-level heatmap analysis

---

## Git Checkpoint — End of Guide 10

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
git add src/dashboard.py
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
git commit -m "Guide 10: Streamlit dashboard with FADR analysis, heatmap, and business impact calculator"
```
**What a commit is:** A permanent snapshot saved in Git's history. Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`). You can always return to this exact state.

**What makes a good commit message:**
- Good: `"Guide 10: Streamlit dashboard with FADR analysis, heatmap, and business impact calculator"`
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
i5g2b3h Guide 10: Streamlit dashboard with FADR analysis, heatmap, and business impact calculator
h4f1a2c Guide 09: Random Forest model predicting delivery success at 83% accuracy
9b2c3d1 Initial commit: project guides and README
```

**In an office:** `git log --oneline` is one of the most used commands. It gives you the full history of the branch at a glance.

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-10-dashboard
```
**What `git push` does:** Uploads your local commits to GitHub. Until you push, your commit only exists on your laptop.

**What `-u` means:** Sets the upstream — links your local branch to a branch of the same name on GitHub. You only need `-u` the first time you push a new branch. After that, just `git push` is enough.

**What `origin` means:** The name of your GitHub remote. When you ran `git remote add origin ...` in Guide 00B, you named it `origin`. That name sticks.

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
You should now see your Guide 10 commit in develop's history. Confirm it is there.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-10-dashboard
```
**What `-d` means:** Delete the branch locally. Git will refuse to delete if the branch has unmerged commits — a safety guard. Since you just merged the PR, `-d` works.

```bash
git push origin --delete feature/guide-10-dashboard
```
Deletes the branch on GitHub too.

**Why delete?** Merged branches are dead branches. Keeping them clutters the repository. In real teams, merged branches are always deleted. A clean repo = a professional habit.

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-11-bigquery
```

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 10 commit is in the history
- **Branches** → feature/guide-10-dashboard is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_11_BIGQUERY.md](GUIDE_11_BIGQUERY.md) — Run the same pipeline on GCP (Google Cloud Platform) BigQuery
