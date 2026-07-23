# Guide 00B — Git Workflow (How Real Teams Use Git)

- Read this fully before starting Guide 01.
- Every command here is explained — not just what to type, but what it means and why it exists.
- If you encounter any abbreviation or term you do not recognise, check [GUIDE_00C_GLOSSARY.md](GUIDE_00C_GLOSSARY.md) — every full form is listed there.

---

## What is Git? What is GitHub? Are they the same?

- They are not the same. People confuse them constantly.

**Git:**
- Software installed on your computer.
- Tracks every change you make to your files.
- Think of it like a detailed save history — every time you save a "version", Git records what changed, when, and why.
- If you break something, you can go back to any previous save.
- Works entirely on your own machine, with no internet needed.

**GitHub:**
- A website (github.com) where you upload your Git history so it is stored online and visible to others.
- Like Google Drive but specifically designed for code.
- Recruiters visit GitHub to see what you have built.
- Teams use it to collaborate.

**The relationship:**
- Git is the tool.
- GitHub is where you store and share what Git tracks.

---

## What is a terminal / command prompt?

- The terminal (also called command prompt, shell, or bash) is a text-based interface where you type commands directly instead of clicking.
- On Windows you can use:
- **Git Bash** — recommended for this project, comes with Git installation
- **Command Prompt** (`cmd`)
- **PowerShell**

- When this guide says "run this command", it means: open your terminal, type that line, press Enter.

---

## What does `cd` mean?

- `cd` stands for "change directory".
- A directory is just a folder.

```bash
cd "c:/Users/DakshaKurhade/OneDrive - AIR INDIA LIMITED/Desktop/Delivery Optimisation"  # cd = change directory, moves terminal here
```

- This moves your terminal's location into the project folder.
- Every command you run after this affects files in that folder.
- Always run `cd` to your project folder at the start of every session.

---

## Why branches exist

- Imagine you are writing a report. You want to try a new section but are not sure it will work. Instead of editing the main document, you make a copy, experiment there, and if it works you paste it back. If it does not work, you just delete the copy.
- A Git branch is that copy — but for code. The original document is `main`. The copy you experiment on is a feature branch.
- In an office, multiple engineers work on the same codebase. Without branches they would overwrite each other's work constantly. With branches each person works on their own copy and merges it back when ready.

Even working alone you use branches because:
- `main` always stays clean — if you break something in a branch, main is unaffected
- Your GitHub history shows professional, organised development
- You build the exact habit every DE (Data Engineer) team expects

---

## The three branches in this project

```
main
  └── develop
        ├── feature/guide-01-setup
        ├── feature/guide-02-data
        └── ... one per guide
```

**`main`:**
- The final, stable, published version.
- You never work directly here.
- A recruiter who visits your GitHub sees this branch.
- It must always be clean and working.

**`develop`:**
- The integration branch.
- All your feature branches merge here first.
- Think of it as "work in progress that is tested and stable".

**`feature/guide-XX-name`:**
- One branch per guide.
- You create it, do the work, commit, push to GitHub, raise a Pull Request, merge into develop, then delete it.
- It is temporary by design.

---

## One-time setup — do this once before Guide 01

### Step 1 — Install Git

- Check if Git is already installed:
```bash
git --version  # asks Git to print its installed version number
```

- If you see `git version 2.x.x` it is installed.
- If you get an error, download Git from https://git-scm.com/downloads — choose Windows, run the installer with default settings.
- After installing, close and reopen your terminal.

---

### Step 2 — Tell Git who you are

- Git records your name and email on every commit (save point) you make.

```bash
# --global: writes the setting to ~/.gitconfig (your home folder), not to the current repo
# without --global:  setting saved in .git/config → applies only to THIS project
# with    --global:  setting saved in ~/.gitconfig → applies to ALL Git projects on this machine
git config --global user.name "Daksha Kurhade"        # saves your name to all future commits
git config --global user.email "your-email@example.com"  # --global = applies to all projects on this machine
```

- `--global` means this applies to all Git projects on your machine, not just this one.
- You only do this once ever.

---

### Step 3 — Navigate to your project folder

```bash
cd "c:/Users/DakshaKurhade/OneDrive - AIR INDIA LIMITED/Desktop/Delivery Optimisation"  # move terminal into the project folder
```

- Verify you are in the right place:
```bash
pwd  # print working directory — shows where your terminal currently is
```
- `pwd` means "print working directory" — it shows you exactly where your terminal is currently pointing.

---

### Step 4 — Initialise Git in the folder

```bash
git init  # creates the hidden .git folder — Git's database for this project
```

**What this does:**
- Creates a hidden folder called `.git` inside your project folder.
- This folder is Git's database — it stores every version of every file you ever commit.
- You never open or touch `.git` directly.
- Just know it is there and Git manages it.

You will see:
```
Initialized empty Git repository in .../Delivery Optimisation/.git/
```

---

### Step 5 — Check what Git sees

```bash
git status  # shows which files changed, staged, or are untracked
```

**What `git status` does:**
- Shows you the current state — which files exist, which have changed, which are staged (ready to commit), which are untracked (Git sees them but is not tracking them yet).

- You will see all your guide files listed as "untracked files" — Git knows they exist but has not saved a version yet.

---

### Step 6 — Create the .gitignore file

- Before adding any files, create `.gitignore`.
- This file tells Git which files to completely ignore and never track.

- Create a file called `.gitignore` in the project root with this content:

**How to create this file:**
```bash
notepad .gitignore  # opens Notepad to create/edit the .gitignore file
```
- Notepad will open (or ask to create the file — click Yes).
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

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

**What each line means:**
- `venv/` — your virtual environment folder. Hundreds of megabytes. No one needs this, they install their own
- `__pycache__/` and `*.pyc` — Python's compiled bytecode files. Auto-generated, not source code
- `.env` — environment variables file. Often contains passwords or API (Application Programming Interface) keys. NEVER commit this
- `data/raw/*.csv` and `data/*.sqlite` — your generated data files. Large, reproducible by running the script
- `models/*.pkl` — saved ML (Machine Learning) model files. Large binary files, reproducible
- `.DS_Store` — Mac system file, irrelevant to the project

**Why this matters:**
- Without `.gitignore`, if you run `git add .` you might accidentally commit your virtual environment (500MB+) or a file containing passwords.
- `.gitignore` prevents this.

---

### Step 7 — Stage your files

```bash
# GUIDE_*.md: the shell expands * to match any characters → finds all matching filenames
# → GUIDE_*.md → GUIDE_00B_GIT_WORKFLOW.md, GUIDE_01_SETUP.md, GUIDE_02_DATA.md ...
# equivalent to listing every GUIDE file by hand, but one pattern covers all of them
git add .gitignore README.md GUIDE_*.md  # stage specific files; * wildcard matches all GUIDE_*.md files
```

**What "staging" means:**
- Git has a two-step save process.
- First you "stage" files — you tell Git which specific changes to include in the next save.
- Then you "commit" — you actually save the snapshot.
- Think of it like packing a box before shipping it. `git add` puts items in the box. `git commit` seals and ships the box.

**What `GUIDE_*.md` means:**
- The `*` is a wildcard — it matches any filename that starts with `GUIDE_` and ends with `.md`.
- So instead of typing all 14 guide filenames, one pattern matches all of them.

- Verify what got staged:
```bash
git status  # green = staged (ready to commit), red = not staged yet
```

- Staged files appear under "Changes to be committed" in green.

---

### Step 8 — Make your first commit

```bash
git commit -m "Initial commit: project guides and README"  # -m = message flag; saves a snapshot with this description
```

**What `-m` means:**
- The `-m` flag stands for "message".
- Everything in the quotes after it is the commit message — a description of what this save contains.
- Without `-m`, Git opens a text editor and waits for you to type a message there.
- Using `-m` is faster.

**What a commit is:**
- A permanent snapshot of all staged files at this exact moment.
- Git stores this forever.
- You can always return to this exact state.
- Every commit gets a unique ID (a long string of letters and numbers called a hash).

---

### Step 9 — Create a GitHub repository (browser, 2 minutes)

- You cannot create a GitHub repository from the terminal without installing an extra tool (`gh`).
- The browser is faster and does not need admin rights.

1. Open your browser → go to **github.com**
2. Check the profile icon top right — make sure you are signed in with the correct account (the email you want this project under)
3. Click **+** (top right) → **New repository**
4. Fill in:
   - Repository name: `delivery-optimisation`
   - Visibility: **Public** — recruiters can only see public repos
   - Leave everything else unticked — no README, no .gitignore, nothing
5. Click **Create repository**

- GitHub now shows you a page.
- At the top you will see your repository URL — it looks like this:
```
https://github.com/YOUR_USERNAME/delivery-optimisation.git
```

**What YOUR_USERNAME is:**
- Your GitHub username — whatever name appears in the URL on that page.
- For example if the URL shows `https://github.com/gittdaksha/delivery-optimisation` then your username is `gittdaksha`.

- Copy that full URL. You will need it in the next step.

---

### Step 10 — Find your GitHub username

- Not sure what your username is? Check it now:

```bash
git config user.email  # reads the email set for this project only (no --global)
```

- No `--global` here — this reads the email set only for this project. If you used `--global`, it would read the system-wide setting instead.
- This shows the email set for this project. Go to github.com, sign in, click your profile icon top right — the name shown there is your username.
- Alternatively, the URL on the repository page GitHub just showed you contains it:
```
https://github.com/YOUR_USERNAME/delivery-optimisation
```

- Everything between `github.com/` and `/delivery-optimisation` is your username.

---

### Step 11 — Connect your local Git to GitHub

- Now paste the URL you copied from GitHub into this command:

```bash
git remote add origin https://github.com/YOUR_USERNAME/delivery-optimisation.git  # links your local repo to GitHub
```

- Replace `YOUR_USERNAME` with your actual GitHub username from Step 10.

**What each part means:**
- `add` — add a new remote connection
- `origin` — the name you are giving this remote. Everyone uses `origin` by convention
- `URL` — the GitHub repository address

**What "remote" means:**
- A remote is a copy of your repository stored somewhere else — in this case on GitHub's servers.
- `origin` is just the conventional name for it. Everyone calls it `origin`.

**What this command does:**
- It tells your local Git "there is a remote called `origin` at this URL (Uniform Resource Locator)".
- After this, Git knows where to push (upload) and pull (download) from.

- Now verify the connection worked:
```bash
# -v = --verbose: adds the URL column next to each remote name
# without -v  →  output:  origin
# with    -v  →  output:  origin  https://github.com/YOU/repo.git (fetch)
#                          origin  https://github.com/YOU/repo.git (push)
git remote -v  # -v = verbose; shows the full URL of your connected GitHub repo
```

**What `git remote -v` does:**
- The `-v` flag means verbose — show full details.
- This prints which GitHub repository your local folder is connected to.

Expected output:
```
origin  https://github.com/YOUR_USERNAME/delivery-optimisation.git (fetch)
origin  https://github.com/YOUR_USERNAME/delivery-optimisation.git (push)
```

- `fetch` = where Git downloads from
- `push` = where Git uploads to
- Both point to the same URL — your GitHub repo

- If you see those two lines, the connection is confirmed.
- If you see nothing or an error, the `git remote add` command did not run correctly — re-run it with the correct URL.

---

### Step 12 — Rename branch to main and push

```bash
# -M = --move --force: rename the branch, even if the target name already exists
# without -M: `git branch -m master main` would fail if `main` already existed
# with    -M: the rename is forced through regardless
git branch -M main  # -M = force rename; renames current branch to main
```

**What this does:**
- Renames your current branch from `master` to `main`.
- Older Git versions create a branch called `master` by default.
- `main` is the modern standard.
- The `-M` flag forces the rename even if a branch called `main` already exists.

```bash
# -u = --set-upstream: permanently records that local `main` tracks `origin/main`
# first push (need -u):   git push -u origin main   → sets the link, uploads commits
# every push after that:  git push                  → Git already knows where to send it
# LOCAL effect:  saves "upstream = origin/main" in .git/config for this branch
# GITHUB effect: creates the `main` branch on GitHub and uploads all commits
git push -u origin main  # -u = set upstream link so future git push needs no extra args
```

**What `git push` does:**
- Uploads your local commits to GitHub.
- Until you push, your commit only exists on your laptop — GitHub knows nothing about it.

**What each part means:**
- `-u` — sets upstream link — permanently links your local `main` branch to `origin/main` on GitHub. After this one-time setup, you can just type `git push` with nothing else and Git knows where to send it
- `origin` — the name of your GitHub remote (the nickname for your GitHub repo URL)
- `main` — the name of the branch you are pushing

**What happens when you push for the first time:**
- Windows will pop up a login window or ask for a username and password.
- Sign in with your GitHub account.
- If you have two GitHub accounts saved on your machine, make sure you pick the correct one.
- After pushing, go to your GitHub repository in the browser and refresh. You will see all your guide files now appear there.

---

### Step 13 — Create the develop branch

```bash
# -b = --branch: create then switch, two actions in one
# equivalent long form:  git branch develop    (creates the branch)
#                        git checkout develop  (switches to it)
# without -b:  git checkout develop  → error if branch does not exist yet
# with    -b:  git checkout -b develop → creates AND switches in one step
git checkout -b develop  # -b = create new branch AND switch to it in one command
```

**What `git checkout` does:**
- Switches you to a different branch.

**What `-b` does:**
- The `-b` flag creates a new branch AND switches to it in one command.
- Without `-b`, checkout just switches to an existing branch.
- So `git checkout -b develop` means: "Create a new branch called `develop` and switch to it now."

```bash
# -u = --set-upstream: same logic as for main above
# LOCAL effect:  saves "upstream = origin/develop" in .git/config
# GITHUB effect: creates the `develop` branch on GitHub and uploads the commit
git push -u origin develop  # -u = set upstream; links local develop to GitHub's develop
```

- Pushes the develop branch to GitHub.
- Same `-u` logic as before — links local develop to remote develop.

**What each part means:**
- `-u` — same as `git push -u origin main` above — sets the upstream link for the develop branch so future `git push` commands on this branch work without specifying origin and develop again
- `origin` — the name of your GitHub remote
- `develop` — the branch you are pushing

- Confirm you are on develop:
```bash
git branch  # lists all branches; * marks the one you are currently on
```

Output:
```
* develop
  main
```

- The `*` marks your current branch.
- You are on `develop`.

---

## The workflow you repeat for every guide

- Nine steps. You will do this 13 times. By the third time it will feel automatic.

```
1. Switch to develop, pull latest
2. Create a feature branch
3. Do the guide work
4. Stage your files
5. Commit
6. Push to GitHub
7. Raise a Pull Request on GitHub
8. Merge the PR
9. Pull back locally, delete branch, start next branch
```

---

## Full commands for each step — with explanations

### Before starting any guide

```bash
# Switch to develop
git checkout develop  # switches to the existing develop branch (no -b = switch only)
```
- No `-b` here — this switches to an existing branch. You do not use `-b` when the branch already exists.
- `-b` is only for creating a new branch.
- Always start from develop. Never create a feature branch from a feature branch.

```bash
# Download any changes from GitHub that you do not have locally
git pull origin develop  # downloads and merges GitHub's develop into your local develop
```

**What `git pull` does:**
- Downloads commits from GitHub and merges them into your local branch.
- `pull` = download + merge in one step (it runs `git fetch` then `git merge` automatically).

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub

- When would there be new changes? If you merged a PR on GitHub, those changes exist on GitHub's develop but not on your local develop yet. `git pull` brings them down.

```bash
# Create and switch to a new feature branch
git checkout -b feature/guide-01-setup  # -b = create new branch AND switch to it
```

**What each part means:**
- `-b` — creates a new branch AND switches to it in one command. Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

- The branch name `feature/guide-01-setup` is a naming convention.
- `feature/` is a prefix that signals "this branch adds new functionality".
- The rest describes what it is for.
- You can read it like a folder path — `feature` category, `guide-01-setup` name.

---

### After finishing the guide work

```bash
# See what changed
git status  # red = changed but not staged, green = staged and ready to commit
```

- Read the output carefully.
- Files in red are changed but not staged.
- Files in green are staged and ready to commit.

```bash
# Stage your specific files
git add src/generate_data.py  # stages this file — includes it in the next commit
git add src/ingest.py         # stage each file by name, never use git add . blindly
```

- Always add files by name, not `git add .` (which adds everything including files you might not want).

```bash
# Optional but recommended: review what you are about to commit
# --staged (alias: --cached): shifts what git diff compares
# without --staged:  compares working directory vs staging area   (what you changed but NOT yet added)
# with    --staged:  compares staging area vs last commit         (what you HAVE added, about to commit)
# → green lines (+) = lines you added     → red lines (-) = lines you removed
git diff --staged  # --staged = show only changes already added (about to be committed)
```

**What `git diff --staged` does:**
- Shows you the exact line-by-line changes in all staged files.

**What `--staged` means:**
- Show only the changes you have already staged (added with `git add`).
- Without `--staged`, `git diff` shows only unstaged changes — files you changed but have NOT yet added.
- Green lines with `+` are additions. Red lines with `-` are deletions.
- This is your last chance to review before committing.

- Press `q` to exit the diff view.

```bash
# Commit
git commit -m "Guide 02: data generation, SQLite ingestion, API ingestion pattern"  # -m = message; saves permanent snapshot
```

- A snapshot is now saved in your local Git history.

---

### Push to GitHub

```bash
# -u = --set-upstream: links local branch to GitHub branch of the same name
# first push:          git push -u origin feature/guide-01-setup  → uploads + sets link
# all later pushes:    git push                                    → Git knows the destination
# LOCAL effect:  records upstream in .git/config so bare `git push` works forever after
# GITHUB effect: creates feature/guide-01-setup on GitHub and uploads your commits
git push -u origin feature/guide-01-setup  # -u = set upstream link (only needed first time)
```

- This uploads your feature branch to GitHub.
- The first time you push a new branch you need `-u`.
- After that, just `git push`.

**What each part means:**
- `-u` — sets upstream link so future `git push` on this branch needs no extra arguments. You only need this the first time you push a new branch
- `origin` — the name of your GitHub remote
- `feature/guide-01-setup` — the branch you are pushing

---

### Raise a Pull Request on GitHub

- A Pull Request (PR) is a formal request to merge your feature branch into another branch.
- In an office, a colleague reviews your PR before approving it.
- Here you will review and merge it yourself — but the process is identical to how real teams work.

1. Go to your GitHub repository in the browser
2. You will see a yellow banner: **"feature/guide-01-setup had recent pushes"**
3. Click **Compare & pull request**
4. Check the settings at the top:
   - **base:** `develop` ← this is where the code will go
   - **compare:** `feature/guide-01-setup` ← this is what you are merging in
5. Title: `Guide 01: environment setup`
6. In the description, write 1-2 lines about what you did
7. Click **Create pull request**
8. Click **Merge pull request** → **Confirm merge**

- Your feature branch code is now inside `develop` on GitHub.

---

### Pull back locally and clean up

```bash
# Switch to develop
git checkout develop  # switches to develop (no -b because it already exists)

# Download the merged changes from GitHub
git pull origin develop  # downloads the merged PR from GitHub into your local develop
```

- No `-b` on `git checkout develop` — this switches to an existing branch.
- `-b` is only used when creating a new branch.

**What each part of `git pull origin develop` means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub

- Your local develop now has everything from the merged PR.

```bash
# Delete the feature branch locally — it is merged, no longer needed
# -d = --delete (safe): only deletes if the branch is fully merged into the current branch
# → if branch has unmerged commits Git refuses: "error: branch not fully merged"
# → use -D (capital) only to force-delete without checking (dangerous — you lose those commits)
# LOCAL effect:  removes the branch pointer from your machine (.git/refs/heads/feature/guide-01-setup deleted)
# GITHUB effect: none — the branch still exists on GitHub until you run the push --delete below
git branch -d feature/guide-01-setup  # -d = delete locally; safe because branch is merged
```

**What `-d` means:**
- Delete — deletes the branch locally.
- Git will refuse if the branch has unmerged commits (safety guard).
- Since you merged the PR, `-d` works fine.
- Use `-D` (capital D) only if you want to force-delete without merging.

```bash
# Delete the feature branch on GitHub too
# --delete: tells GitHub to remove the branch reference on its server
# syntax:  git push <remote> --delete <branch-name>
# LOCAL effect:  none — your local branch is already gone (deleted above)
# GITHUB effect: branch feature/guide-01-setup disappears from GitHub's branch list immediately
git push origin --delete feature/guide-01-setup  # --delete = remove this branch from GitHub
```

**What each part means:**
- `origin` — push this action to GitHub (not just locally)
- `--delete` — delete the named branch on GitHub

**Why delete it?**
- Keeping old merged branches clutters the repository.
- In real teams, merged branches are always deleted.
- Clean repo = professional habit.

---

### Start the next guide's branch immediately

```bash
git checkout -b feature/guide-02-data  # -b = create new branch AND switch to it
```

**What `-b` means:**
- Creates a new branch AND switches to it in one command.
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist.

- You are ready for the next guide.

---

## Merging develop into main

- Do this after every 2-3 guides when everything is running correctly.
- `main` should reflect a stable, working state.

```bash
# git checkout main: switches to main; no -b because main already exists
# LOCAL effect:  your working directory now reflects main's files
# GITHUB effect: none — checkout never touches GitHub
git checkout main          # switch to main (no -b because it already exists)

# git merge develop: replays develop's commits onto main
# before:  main  → commit A → commit B
#          develop → commit A → commit B → commit C → commit D
# after:   main  → commit A → commit B → commit C → commit D  (same as develop)
# GITHUB effect: none yet — the merge only exists locally until you push
git merge develop          # bring develop's commits into main

# git push origin main: uploads the newly merged main to GitHub
# LOCAL effect:  no change to files — just sends commits to GitHub
# GITHUB effect: GitHub's main branch now shows all the merged commits
git push origin main       # upload updated main to GitHub

# git checkout develop: switches back so you continue working on develop, not main
git checkout develop       # switch back to develop to continue working
```

**What each command does:**
- `git checkout main` — switches to the main branch. No `-b` here because `main` already exists
- `git merge develop` — takes all the commits from develop and applies them to your current branch (main)
- `git push origin main` — uploads to GitHub. `origin` = the GitHub remote, `main` = the branch being pushed. No `-u` needed here because `main`'s upstream was set in the original `git push -u origin main`
- `git checkout develop` — switches back to develop. No `-b` because develop already exists

**What `git merge` does:**
- Takes all the commits from the branch you name (develop) and applies them to your current branch (main).
- After this, main has everything develop has.

---

## Commands reference — every command explained once

| Command | What it does |
|---|---|
| `git init` | Creates a new Git repository in the current folder |
| `git status` | Shows current state — changed files, staged files, current branch |
| `git add filename` | Stages a file — includes it in the next commit |
| `git diff --staged` | Shows line-by-line changes in staged files before committing |
| `git commit -m "msg"` | Saves a permanent snapshot with a description |
| `git log --oneline` | Shows commit history, one line per commit |
| `git branch` | Lists all branches, `*` marks current one |
| `git checkout -b name` | Creates a new branch and switches to it |
| `git checkout name` | Switches to an existing branch |
| `git push -u origin name` | Pushes branch to GitHub, sets upstream (first time) |
| `git push` | Pushes current branch to GitHub (after first time) |
| `git pull origin develop` | Downloads and merges changes from GitHub |
| `git merge branch-name` | Merges named branch into current branch |
| `git branch -d name` | Deletes a branch locally (must be merged first) |
| `git push origin --delete name` | Deletes a branch on GitHub |
| `git remote add origin URL` | Links local repo to a GitHub repo |
| `git remote -v` | Shows which GitHub repo you are connected to |

---

## What good commit messages look like

```bash
# Good — specific and readable
git commit -m "Guide 02: add data generator with 50k delivery records"
git commit -m "Guide 04: dbt staging and mart models with quality tests"
git commit -m "Fix: FADR (First Attempt Delivery Rate) calculation was including null attempts"

# Bad — useless
git commit -m "update"
git commit -m "done"
git commit -m "asdfgh"
```

- Rule: your future self reading this 3 months later should immediately know what changed, without looking at the code.

---

## What your GitHub looks like when the project is complete

- **`main` branch** — 3 merge commits from develop, always stable
- **`develop` branch** — 13 merge commits, one per guide
- **Pull Requests tab** — 13 closed PRs with titles and descriptions
- **Commit history** — clean, named, chronological

- A recruiter or interviewer who opens this repo sees a project built with professional discipline. That is the point.

---

## Quick reference — branch name per guide

| Guide | Branch name to create |
|---|---|
| Guide 01 | `feature/guide-01-setup` |
| Guide 02 | `feature/guide-02-data` |
| Guide 03 | `feature/guide-03-sql` |
| Guide 04 | `feature/guide-04-dbt` |
| Guide 05 | `feature/guide-05-pyspark` |
| Guide 06 | `feature/guide-06-airflow` |
| Guide 07 | `feature/guide-07-kafka` |
| Guide 08 | `feature/guide-08-docker` |
| Guide 09 | `feature/guide-09-ml` |
| Guide 10 | `feature/guide-10-dashboard` |
| Guide 11 | `feature/guide-11-bigquery` |
| Guide 12 | `feature/guide-12-cicd` |
| Guide 13 | `feature/guide-13-github` |

---

## When you are ready to start

```bash
cd "c:/Users/DakshaKurhade/OneDrive - AIR INDIA LIMITED/Desktop/Delivery Optimisation"  # move terminal into the project folder
git checkout develop                   # switch to develop branch (already exists, no -b)
git checkout -b feature/guide-01-setup  # -b = create this new branch AND switch to it
```

**What each part means:**
- `git checkout develop` — switches to the develop branch. No `-b` because develop already exists
- `git checkout -b feature/guide-01-setup` — creates a new branch AND switches to it. `-b` is required here because this branch does not exist yet

- Open [GUIDE_01_SETUP.md](GUIDE_01_SETUP.md) and begin.
