# Guide 01 — Environment Setup

**Goal:** Get Python and all required libraries installed and ready. This is the foundation. Nothing else works without this.

---

## What is a terminal and how do you open it?

The terminal is a text window where you type commands instead of clicking. On Windows, use **Git Bash** — it comes installed with Git and understands the Unix-style commands used in this project.

To open Git Bash: right-click anywhere on your Desktop or in a folder → **Git Bash Here**.

When you see a command in this guide inside a code block like this:
```bash
python --version
```
It means: type that exactly into your terminal and press Enter.

---

## Git — Before You Start This Guide

**Guide 01 is special.** Every other guide starts with `git checkout develop` — but that only works after Git has been set up. Guide 01 is where you do that one-time setup. Do these steps in order, top to bottom, without skipping.

---

### Step G0 — Check if Git is already initialised

```bash
git status
```

- If you see `On branch master` or `On branch main` → Git is already initialised, skip to Step G1
- If you see `fatal: not a git repository` → Git is not initialised yet, continue with Step G0A below

---

### Step G0A — Initialise Git (only if needed)

```bash
git init
```

**What this does:** Creates a hidden `.git` folder inside your project folder. This folder is Git's database — it stores every version of every file you ever commit. You never open or touch it. Just know it is there.

Expected output:
```
Initialized empty Git repository in .../Delivery Optimisation/.git/
```

---

### Step G0B — Set your identity for this project

```bash
git config user.email "your-github-email@gmail.com"
git config user.name "Your Name"
```

Replace with your actual name and the email you used to create your GitHub account.

**No `--global` flag here** — this sets identity only for this project, so your other GitHub accounts on the same machine are unaffected.

Verify it is set:
```bash
git config user.email
```
It should print your email back.

---

### Step G0C — Create .gitignore before adding any files

**Why first:** If you add files before creating `.gitignore`, you risk accidentally committing things like passwords or the 500MB `venv/` folder to GitHub.

Create a file called `.gitignore` in your project folder with this content:

**How to create this file:**
```bash
notepad .gitignore
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```
venv/
__pycache__/
*.pyc
.env
data/raw/*.csv
data/processed/*.csv
data/*.sqlite
models/*.pkl
.DS_Store
airflow_home/
*.egg-info/
```

**What each line does:**
- `venv/` — your virtual environment folder (hundreds of MB, never commit this)
- `__pycache__/` and `*.pyc` — Python auto-generated files, not your code
- `.env` — environment variables file that can contain passwords
- `data/` entries — large generated data files, reproducible by running scripts
- `models/*.pkl` — saved ML model files, large binary files

---

### Step G0D — Make the first commit

```bash
git add .gitignore README.md GUIDE_*.md
```

**What `GUIDE_*.md` means:** The `*` is a wildcard — matches any file starting with `GUIDE_` and ending with `.md`. One pattern stages all guide files at once.

```bash
git commit -m "Initial commit: project guides and README"
```

**What a commit is:** A permanent snapshot. Git saves this exact state forever. You can always return to it.

---

### Step G0E — Rename branch to main

```bash
git branch -M main
```

**Why:** Older Git versions create a branch called `master` by default. The modern standard is `main`. This renames it. `-M` forces the rename even if a `main` branch already exists.

---

### Step G0F — Create the GitHub repository (browser)

You cannot create a GitHub repository from the terminal without admin rights. Use the browser — it takes 2 minutes.

1. Open browser → go to **github.com**
2. Make sure you are signed in with the correct account — check profile icon top right
3. Click **+** (top right) → **New repository**
4. Fill in:
   - Repository name: `delivery-optimisation`
   - Visibility: **Public**
   - Leave everything else unticked — no README, no .gitignore
5. Click **Create repository**

GitHub shows you a page. At the top you will see your repository URL:
```
https://github.com/YOUR_USERNAME/delivery-optimisation.git
```

**How to find your username:** It is in the URL GitHub just showed you — the part between `github.com/` and `/delivery-optimisation`.

Copy that full URL.

---

### Step G0G — Connect your local folder to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/delivery-optimisation.git
```

Replace `YOUR_USERNAME` with your actual GitHub username from the URL above.

**What `remote` means:** A remote is a copy of your project stored somewhere else — here, on GitHub's servers. `origin` is the standard name for it.

Verify the connection worked:
```bash
git remote -v
```

Expected output:
```
origin  https://github.com/YOUR_USERNAME/delivery-optimisation.git (fetch)
origin  https://github.com/YOUR_USERNAME/delivery-optimisation.git (push)
```

- `fetch` = where Git downloads from
- `push` = where Git uploads to

If you see both lines, the connection is confirmed. If you see nothing, re-run the `git remote add` command.

---

### Step G0H — Push main to GitHub

```bash
git push -u origin main
```

**What happens:** Windows may pop up a login window. Sign in with your GitHub account. If you have two accounts saved, make sure you pick the correct one.

After this, refresh your GitHub repository in the browser — you will see your guide files appear there.

---

### Step G0I — Create the develop branch

```bash
git checkout -b develop
```

**What this does:** Creates a new branch called `develop` and switches to it. `develop` is the integration branch — all your feature branches will merge here first before going to `main`.

```bash
git push -u origin develop
```

Pushes develop to GitHub so it exists there too.

Confirm you are on develop:
```bash
git branch
```

Output:
```
* develop
  main
```

The `*` means you are here — on develop. Good.

---

### Step G1 — Create your feature branch for Guide 01

Now do the standard workflow that every other guide starts with:

```bash
git checkout -b feature/guide-01-setup
```

**What `-b` means:** Create a new branch AND switch to it in one command.

**Why a new branch for every guide:** Each branch is one unit of work. If something breaks, you delete the branch and start fresh — develop and main are unaffected. This is how every real team works.

Confirm you are on the right branch:
```bash
git branch
```

You will see `* feature/guide-01-setup` — the `*` means you are here. You are ready to start the guide work.

---

## Step 1.1 — Check Python is installed

```bash
python --version
```

**What this does:** Asks Python to print its version number.

**What Python is:** Python is a programming language. Every script in this project is written in Python. The terminal command `python` runs the Python interpreter — the program that reads and executes Python code.

Expected output:
```
Python 3.11.x
```

If you see an error or a version below 3.9, download Python from python.org. Choose the latest 3.11 or 3.12 version. During installation, tick the box that says **"Add Python to PATH"** — this is what lets you type `python` in the terminal and have it work.

---

## Step 1.2 — Check pip is installed

```bash
pip --version
```

**What pip is:** pip stands for "Pip Installs Packages". It is Python's package manager — the tool you use to install libraries. A library is someone else's code you can use in your project. Instead of writing a machine learning algorithm from scratch, you install scikit-learn (a library) and use it.

Expected output:
```
pip 24.x.x from ...
```

pip is included with Python automatically. If it is missing, run `python -m ensurepip`.

---

## Step 1.3 — Navigate to your project folder

```bash
cd "c:/Users/DakshaKurhade/OneDrive - AIR INDIA LIMITED/Desktop/Delivery Optimisation"
```

**What `cd` means:** Change Directory. A directory is a folder. This command moves your terminal's working location into the project folder. All commands you run after this will affect files inside this folder.

Verify you are in the right place:
```bash
pwd
```

**What `pwd` means:** Print Working Directory. It prints the full path of where your terminal currently is. Confirm it shows your project folder path.

---

## Step 1.4 — Create a virtual environment

```bash
python -m venv venv
```

**What a virtual environment is:** Imagine you have two projects. Project A needs pandas version 1.5. Project B needs pandas version 2.2. If you install both on your system, they conflict. A virtual environment is an isolated folder that holds a project's libraries separately from everything else on your machine.

**What `-m venv` means:** `-m` tells Python to run a module (a built-in tool) called `venv`. `venv` is the virtual environment creator. The last `venv` is the name of the folder it creates inside your project.

After running this, you will see a new folder called `venv/` in your project. This folder contains a private copy of Python and pip just for this project.

---

## Step 1.5 — Activate the virtual environment

On Windows (Git Bash):
```bash
source venv/Scripts/activate
```

On Windows (Command Prompt):
```bash
venv\Scripts\activate
```

On Windows (PowerShell):
```powershell
venv\Scripts\Activate.ps1
```

**What activating does:** It switches your terminal to use this project's private Python and pip instead of the system-wide ones. From this point, every `pip install` puts the library inside `venv/` — not on your system globally.

**How to confirm it worked:** Your terminal prompt changes. You will see `(venv)` at the start:
```
(venv) DakshaKurhade@LAPTOP:~$
```

That `(venv)` prefix means the virtual environment is active. Every time you open a new terminal window to work on this project, you need to activate it again.

---

## Step 1.6 — Create requirements.txt

**What requirements.txt is:** A plain text file that lists all the libraries this project needs, with their exact version numbers. It is the standard way Python projects declare their dependencies. Anyone who has this file can install everything the project needs with one command.

Create a file called `requirements.txt` in the project root with this content:

**How to create this file:**
```bash
notepad requirements.txt
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```
pandas==2.2.2
numpy==1.26.4
faker==25.0.0
sqlalchemy==2.0.30
scikit-learn==1.5.0
matplotlib==3.9.0
seaborn==0.13.2
streamlit==1.35.0
apache-airflow==2.9.2
dbt-core==1.8.0
dbt-sqlite==1.8.0
jupyter==1.0.0
pytest==8.2.0
python-dotenv==1.0.1
requests==2.32.3
pyspark==3.5.1
kafka-python==2.0.2
google-cloud-bigquery==3.23.0
google-cloud-storage==2.16.0
google-cloud-pubsub==2.21.0
db-dtypes==1.2.0
```

**What each library is for:**

| Library | What it does in this project |
|---|---|
| `pandas` | Loads, manipulates, and analyses tabular data — like Excel but in Python |
| `numpy` | Numbers and arrays — pandas uses it internally, you use it for random seeds |
| `faker` | Generates realistic fake data — names, addresses, UUIDs |
| `sqlalchemy` | Connects Python to databases — used to write DataFrames to SQLite |
| `scikit-learn` | Machine learning — the Random Forest model in Guide 09 |
| `matplotlib` | Creates charts and graphs |
| `seaborn` | Higher-level charts built on matplotlib — the heatmap in the dashboard |
| `streamlit` | Turns Python scripts into interactive web apps |
| `apache-airflow` | Pipeline orchestration — scheduling and monitoring |
| `dbt-core` | SQL (Structured Query Language) transformation framework |
| `dbt-sqlite` | dbt (Data Build Tool) connector for SQLite databases |
| `jupyter` | Notebook environment for exploration |
| `pytest` | Automated testing framework |
| `python-dotenv` | Loads environment variables from a `.env` file |
| `requests` | Makes HTTP (HyperText Transfer Protocol) requests — used for API (Application Programming Interface) ingestion in Guide 02 |
| `pyspark` | Python API for Apache Spark — large-scale data processing |
| `kafka-python` | Python client for Apache Kafka — real-time streaming |
| `google-cloud-bigquery` | Python client for BigQuery |
| `google-cloud-storage` | Python client for Google Cloud Storage |
| `google-cloud-pubsub` | Python client for Pub/Sub |
| `db-dtypes` | Required by the BigQuery client for data type handling |

**What `==2.2.2` means:** The double equals sign followed by a version number pins the exact version. This guarantees that your pipeline runs the same way regardless of when someone installs it. If you wrote just `pandas` without a version, pip would install the latest — which might break your code when a new version changes something.

---

## Step 1.7 — Install all libraries

```bash
pip install -r requirements.txt
```

**What `-r` means:** The `-r` flag tells pip to read a requirements file. Instead of installing one library at a time, it reads `requirements.txt` and installs everything listed.

This will take **5–10 minutes**. You will see lines scrolling past as packages download and install. This is normal. Do not close the terminal.

If a specific package fails, pip will show an error in red. Note the package name and search for the error message online — most installation errors have straightforward fixes.

---

## Step 1.8 — Verify everything installed

```bash
python -c "import pandas, numpy, faker, sklearn, streamlit; print('All libraries installed successfully')"
```

**What `-c` means:** The `-c` flag runs a Python command directly from the terminal without creating a file. Everything in the quotes is the Python code to execute.

**What `import` does:** In Python, `import` loads a library into memory so you can use it. If a library is not installed, `import` throws an error. This command imports 5 key libraries — if all 5 import without error, it prints the success message.

Expected output:
```
All libraries installed successfully
```

If you see `ModuleNotFoundError: No module named 'X'`, that library did not install correctly. Run `pip install X` to install just that one.

---

## Step 1.9 — Create the project directory structure

```bash
mkdir src
mkdir sql
mkdir data
mkdir data\raw
mkdir data\processed
mkdir models
mkdir notebooks
mkdir dags
```

**What `mkdir` means:** Make Directory — creates a new folder. You need these folders before the later guides create files inside them.

**What each folder is for:**

| Folder | What goes inside |
|---|---|
| `src/` | All Python source code files |
| `sql/` | Raw SQL query files |
| `data/raw/` | Generated CSV (Comma-Separated Values) files — raw, untransformed data |
| `data/processed/` | Cleaned outputs, Parquet files, exported marts |
| `models/` | Saved ML (Machine Learning) model files |
| `notebooks/` | Jupyter notebooks for exploration |
| `dags/` | Airflow DAG (Directed Acyclic Graph) definitions |

---

## Checkpoint

You should now have:
- `(venv)` showing in your terminal prompt — virtual environment is active
- All libraries installed — verified with the import check
- All project folders created

---

## Git Checkpoint — End of Guide 01

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
git add requirements.txt
git add src/.gitkeep
git add models/.gitkeep
git add notebooks/.gitkeep
```

**Note:** The folders are empty right now. Git does not track empty folders. Create placeholder files first:
```bash
touch src/.gitkeep
touch models/.gitkeep
touch notebooks/.gitkeep
```
**What `.gitkeep` is:** A convention — an empty file whose only purpose is to make Git track the folder. The name does not matter technically, `.gitkeep` is just the agreed-upon convention.

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
git commit -m "Guide 01: environment setup, requirements.txt, project folder structure"
```
**What a commit is:** A permanent snapshot saved in Git's history. Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`). You can always return to this exact state.

**What makes a good commit message:**
- Good: `"Guide 01: environment setup, requirements.txt, project folder structure"`
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
a3f9c2b Guide 01: environment setup, requirements.txt, project folder structure
9b2c3d1 Initial commit: project guides and README
```

**In an office:** `git log --oneline` is one of the most used commands. It gives you the full history of the branch at a glance.

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-01-setup
```
**What `git push` does:** Uploads your local commits to GitHub. Until you push, your commit only exists on your laptop.

**What `-u` means:** Sets the upstream — links your local branch to a branch of the same name on GitHub. You only need `-u` the first time you push a new branch. After that, just `git push` is enough.

**What `origin` means:** The name of your GitHub remote. When you ran `git remote add origin ...` in Guide 00B, you named it `origin`. That name sticks.

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-01-setup had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-01-setup` ← what you are merging in
3. Title: `Guide 01: environment setup`
4. Description: "Set up Python virtual environment, installed all libraries, created project folder structure"
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
You should now see your Guide 01 commit in develop's history. Confirm it is there.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-01-setup
```
**What `-d` means:** Delete the branch locally. Git will refuse to delete if the branch has unmerged commits — a safety guard. Since you just merged the PR, `-d` works.

```bash
git push origin --delete feature/guide-01-setup
```
Deletes the branch on GitHub too.

**Why delete?** Merged branches are dead branches. Keeping them clutters the repository. In real teams, merged branches are always deleted. A clean repo = a professional habit.

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-02-data
```

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 01 commit is in the history
- **Branches** → feature/guide-01-setup is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_02_DATA.md](GUIDE_02_DATA.md) — Generate and store raw delivery data
