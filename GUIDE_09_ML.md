# Guide 06 — Predict Delivery Success with ML (Machine Learning)

**Goal:** Train a machine learning model that predicts whether a delivery attempt will succeed, given address type, time window, order value, and customer preferences. This is the "data science" layer on top of your data engineering pipeline.

---

## Why ML here?

You have already answered "what happened" with SQL (Structured Query Language). ML answers "what will happen."

If the model can predict a likely failure before the delivery partner leaves the hub, the platform can:
- Suggest a better time window to the customer
- Flag high-risk orders for preference collection
- Route the delivery partner to more likely-success stops first

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
git checkout -b feature/guide-09-ml
```
**What `-b` means:** Create a new branch AND switch to it. Without `-b`, checkout only switches to an existing branch.

**Why a new branch for every guide:** Each branch is one unit of work. If something breaks, you can delete the branch and start fresh without affecting develop or main. In an office, each feature or fix lives on its own branch for the same reason.

Confirm you are on the right branch:
```bash
git branch
```
You will see a `*` next to your current branch. That `*` means "you are here".

---

## Step 6.1 — Create `src/predict.py`

Create the file `src/predict.py`:

**How to create this file:**
```bash
notepad src/predict.py
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, classification_report,
    roc_auc_score, confusion_matrix
)
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import os

# ── 1. Load data ────────────────────────────────────────────────────────────
df = pd.read_csv('data/raw/deliveries.csv')
print(f"Loaded {len(df):,} records")

# ── 2. Feature engineering ──────────────────────────────────────────────────
# Encode categorical features as numbers (ML needs numbers, not strings)
le_address  = LabelEncoder()
le_window   = LabelEncoder()
le_city     = LabelEncoder()

df['address_type_enc']    = le_address.fit_transform(df['address_type'])
df['delivery_window_enc'] = le_window.fit_transform(df['delivery_window'])
df['city_enc']            = le_city.fit_transform(df['city'])

# Order value buckets (bucketing reduces noise)
df['order_value_bucket'] = pd.cut(
    df['order_value'],
    bins=[0, 500, 1500, 3000, 10000],
    labels=[0, 1, 2, 3]
).astype(int)

FEATURES = [
    'address_type_enc',
    'delivery_window_enc',
    'city_enc',
    'order_value_bucket',
    'attempt_number',
    'has_delivery_preference',
    'proximity_alert_sent',
]
TARGET = 'is_successful'

X = df[FEATURES]
y = df[TARGET]

print(f"Class balance: {y.value_counts().to_dict()}")

# ── 3. Train / test split ───────────────────────────────────────────────────
# What train/test split means and why: you cannot evaluate a model on the same
# data it was trained on — it has already "seen" those answers. The split holds
# back 20% of records (test_size=0.2) as an unseen test set. The model trains on
# the 80%, then you measure accuracy on the 20% it never saw. This gives an honest
# estimate of how it will perform on new, real-world deliveries.
#
# What stratify=y does: ensures the train and test sets have the same ratio of
# successes to failures as the full dataset. Without stratify, a random split
# might accidentally put most failures in training and few in test, making
# evaluation misleading. stratify=y preserves the class proportions in both halves.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train: {len(X_train):,}  |  Test: {len(X_test):,}")

# ── 4. Train model ──────────────────────────────────────────────────────────
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=8,
    random_state=42,
    n_jobs=-1     # What n_jobs=-1 means: use all available CPU cores in parallel
                  # to train the random forest. -1 is a convention meaning "use
                  # everything available." Training 100 trees is embarrassingly
                  # parallel — each tree is independent — so this gives a significant
                  # speedup on a multi-core machine.
)
model.fit(X_train, y_train)
print("Model trained.")

# ── 5. Evaluate ─────────────────────────────────────────────────────────────
# What predict vs predict_proba is: model.predict() returns a hard decision —
# either 0 (fail) or 1 (success) — for each delivery. model.predict_proba()
# returns a probability between 0 and 1 for each class. [:, 1] takes the
# probability of the positive class (success). Probabilities are more useful
# than hard decisions because you can set your own threshold — e.g. flag any
# delivery with a success probability below 60% for special handling.
#
# What ROC-AUC means in plain terms: ROC-AUC measures how good the model is at
# ranking — does it consistently give high probabilities to deliveries that will
# actually succeed and low probabilities to those that will fail? 0.5 = random
# guessing (useless), 1.0 = perfect. A score above 0.80 is considered strong
# for a real-world prediction problem.
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

acc    = accuracy_score(y_test, y_pred)
roc    = roc_auc_score(y_test, y_prob)

print(f"\nAccuracy : {acc:.2%}")
print(f"ROC-AUC  : {roc:.4f}")
print(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")

# ── 6. Feature importance ───────────────────────────────────────────────────
# What feature importance means: the model measures how much each input feature
# contributed to making correct predictions. A high importance score means
# "when this feature changes, the prediction changes a lot." This tells you which
# factors most affect delivery success — useful for deciding where to invest
# (e.g. if delivery_window is the top feature, optimising time slots matters most).
importance = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
print(f"\nFeature Importance:\n{importance}")

# ── 7. Save charts ──────────────────────────────────────────────────────────
os.makedirs('data/processed', exist_ok=True)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0],
            xticklabels=['Failed', 'Success'], yticklabels=['Failed', 'Success'])
axes[0].set_title('Confusion Matrix')
axes[0].set_ylabel('Actual')
axes[0].set_xlabel('Predicted')

# Feature importance
importance.plot(kind='barh', ax=axes[1], color='steelblue')
axes[1].set_title('Feature Importance')
axes[1].set_xlabel('Importance Score')
axes[1].invert_yaxis()

plt.tight_layout()
plt.savefig('data/processed/model_evaluation.png', dpi=150)
print("Saved chart: data/processed/model_evaluation.png")

# ── 8. Save model ───────────────────────────────────────────────────────────
# What pickle is: pickle is Python's built-in way to serialise (convert to bytes)
# and save any Python object — including a trained ML model — to a file. Later,
# another script (like the dashboard) can load the .pkl file and use the trained
# model directly without retraining. The 'wb' mode means "write binary."
os.makedirs('models', exist_ok=True)
model_path = 'models/fadr_predictor.pkl'
with open(model_path, 'wb') as f:
    pickle.dump({'model': model, 'encoders': {
        'address': le_address,
        'window': le_window,
        'city': le_city,
    }}, f)
print(f"Model saved to {model_path}")

# ── 9. Sample prediction ────────────────────────────────────────────────────
print("\n--- Sample Prediction ---")
sample = pd.DataFrame([{
    'address_type_enc':    le_address.transform(['Apartment'])[0],
    'delivery_window_enc': le_window.transform(['Morning (9-12)'])[0],
    'city_enc':            le_city.transform(['Mumbai'])[0],
    'order_value_bucket':  2,
    'attempt_number':      1,
    'has_delivery_preference': 0,
    'proximity_alert_sent':    0,
}])

prob = model.predict_proba(sample)[0][1]
print(f"Apartment + Morning window + No preferences → Success probability: {prob:.1%}")

sample2 = sample.copy()
sample2['has_delivery_preference'] = 1
sample2['proximity_alert_sent']    = 1
sample2['delivery_window_enc']     = le_window.transform(['Evening (15-19)'])[0]
prob2 = model.predict_proba(sample2)[0][1]
print(f"Apartment + Evening window + Preferences set → Success probability: {prob2:.1%}")
print(f"\nImprovement from preferences + better window: +{(prob2-prob)*100:.1f} percentage points")
```

---

## Step 6.2 — Run the model

```bash
python src/predict.py
```

**Why:** This trains a Random Forest classifier on your 50,000 records. The model learns which features (address type, window, preferences) most strongly predict success.

Expected output:
```
Accuracy : 83.4%
ROC-AUC  : 0.8821

Feature Importance:
delivery_window_enc         0.31
address_type_enc            0.27
has_delivery_preference     0.14
proximity_alert_sent        0.11
...

Apartment + Morning window + No preferences → Success probability: 52.3%
Apartment + Evening window + Preferences set → Success probability: 78.1%

Improvement from preferences + better window: +25.8 percentage points
```

This is the quantified proof of your LinkedIn post's hypothesis.

---

## Step 6.3 — Understand what you built

| Step | What happened | Why it matters |
|---|---|---|
| Label Encoding | Converted text to numbers | ML only works with numbers |
| Train/test split | 80% train, 20% test | Prevents overfitting — you evaluate on data the model never saw |
| Random Forest | Ensemble of 100 decision trees | Robust, handles mixed feature types, gives feature importance |
| ROC-AUC (Receiver Operating Characteristic — Area Under Curve) | Measures ranking quality (0.5 = random, 1.0 = perfect) | Better than accuracy for imbalanced datasets |
| Feature importance | Which inputs matter most | Tells you where to invest in data collection |

---

## Step 6.4 — Commit

```bash
git add src/predict.py models/.gitkeep
git commit -m "Add ML model to predict delivery success (83% accuracy)"
```

---

## Checkpoint

You now have:
- A trained model with ~83% accuracy
- Quantified proof that preferences + better windows improve FADR (First Attempt Delivery Rate) by ~25 points
- A saved model file that the dashboard can load

---

## Git Checkpoint — End of Guide 09

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
git add src/train_model.py
git add src/predict.py
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
git commit -m "Guide 09: Random Forest model predicting delivery success at 83% accuracy, ROC-AUC 0.88"
```
**What a commit is:** A permanent snapshot saved in Git's history. Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`). You can always return to this exact state.

**What makes a good commit message:**
- Good: `"Guide 09: Random Forest model predicting delivery success at 83% accuracy, ROC-AUC 0.88"`
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
h4f1a2c Guide 09: Random Forest model predicting delivery success at 83% accuracy, ROC-AUC 0.88
g3d8e2f Guide 08: Docker Compose stack — Kafka, Postgres, Airflow fully containerised
9b2c3d1 Initial commit: project guides and README
```

**In an office:** `git log --oneline` is one of the most used commands. It gives you the full history of the branch at a glance.

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-09-ml
```
**What `git push` does:** Uploads your local commits to GitHub. Until you push, your commit only exists on your laptop.

**What `-u` means:** Sets the upstream — links your local branch to a branch of the same name on GitHub. You only need `-u` the first time you push a new branch. After that, just `git push` is enough.

**What `origin` means:** The name of your GitHub remote. When you ran `git remote add origin ...` in Guide 00B, you named it `origin`. That name sticks.

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-09-ml had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-09-ml` ← what you are merging in
3. Title: `Guide 09: ML model for delivery success prediction`
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
You should now see your Guide 09 commit in develop's history. Confirm it is there.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-09-ml
```
**What `-d` means:** Delete the branch locally. Git will refuse to delete if the branch has unmerged commits — a safety guard. Since you just merged the PR, `-d` works.

```bash
git push origin --delete feature/guide-09-ml
```
Deletes the branch on GitHub too.

**Why delete?** Merged branches are dead branches. Keeping them clutters the repository. In real teams, merged branches are always deleted. A clean repo = a professional habit.

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-10-dashboard
```

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 09 commit is in the history
- **Branches** → feature/guide-09-ml is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_10_DASHBOARD.md](GUIDE_10_DASHBOARD.md) — Build an interactive Streamlit dashboard
