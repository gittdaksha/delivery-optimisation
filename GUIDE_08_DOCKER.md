# Guide 11 — Containerise Everything with Docker

**Goal:** Package the entire pipeline — Kafka, the Python scripts, and Airflow — into Docker containers using Docker Compose. This is how real data pipelines are deployed in production.

---

## Why Docker on your CV?

Docker appears on **85%+ of data engineering job descriptions**. It is the universal way to package and ship software. If you say "I built a pipeline" but it only runs on your laptop with manual setup, that's a prototype. If you say "it runs with `docker-compose up`", that's production-ready thinking.

**What Docker does:** It wraps your code + its exact dependencies + the operating system layer into a container image. Anyone, anywhere, on any machine, runs the same image and gets identical behaviour. No "it works on my machine" problems.

**What a container is vs a virtual machine:** A virtual machine emulates an entire separate computer including its own operating system — heavy and slow to start. A container shares the host operating system's kernel and only packages the application and its dependencies — lightweight, starts in seconds.

---

## What Docker Compose does

Docker Compose lets you define multiple containers and their relationships in a single `docker-compose.yml` file, then start all of them with one command:

```bash
docker-compose up
```

For this project, Compose will start:
1. **Zookeeper** — Kafka's coordination service
2. **Kafka** — the message broker
3. **Postgres** — Airflow's metadata database (more production-realistic than SQLite)
4. **Airflow Webserver** — the UI at localhost:8080
5. **Airflow Scheduler** — runs DAGs on schedule

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
git checkout -b feature/guide-08-docker
```
**What `-b` means:** Create a new branch AND switch to it. Without `-b`, checkout only switches to an existing branch.

**Why a new branch for every guide:** Each branch is one unit of work. If something breaks, you can delete the branch and start fresh without affecting develop or main. In an office, each feature or fix lives on its own branch for the same reason.

Confirm you are on the right branch:
```bash
git branch
```
You will see a `*` next to your current branch. That `*` means "you are here".

---

## Step 11.1 — Install Docker

Download Docker Desktop from https://www.docker.com/products/docker-desktop/

After install, verify:
```bash
docker --version
docker-compose --version
```

---

## Step 11.2 — Create `docker-compose.yml`

Create the file `docker-compose.yml` in the project root:

**How to create this file:**
```bash
notepad docker-compose.yml
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```yaml
version: '3.8'

networks:
  delivery-net:
    driver: bridge

volumes:
  postgres-db-volume:

services:

  # ── Zookeeper (Kafka dependency) ─────────────────────────────────────────
  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.0
    container_name: zookeeper
    networks: [delivery-net]
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  # ── Kafka Broker ─────────────────────────────────────────────────────────
  kafka:
    image: confluentinc/cp-kafka:7.6.0
    container_name: kafka
    networks: [delivery-net]
    # What depends_on does: tells Docker Compose that this service should only
    # start after the listed services have started. Kafka needs Zookeeper running
    # first; without this, Kafka would crash on startup with a connection error.
    depends_on: [zookeeper]
    # What ports: means: maps a port on your host machine to a port inside the
    # container. "9092:9092" means: when something on your laptop connects to
    # port 9092, Docker routes it into the container's port 9092. The format is
    # always host_port:container_port.
    ports:
      - "9092:9092"     # expose to host so Python scripts can connect
    # What environment: variables are: these set environment variables inside the
    # container — equivalent to running 'export KAFKA_BROKER_ID=1' in the shell
    # before starting Kafka. Each container reads these to configure itself.
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"

  # ── Create Kafka topic on startup ────────────────────────────────────────
  kafka-setup:
    image: confluentinc/cp-kafka:7.6.0
    container_name: kafka-setup
    networks: [delivery-net]
    depends_on: [kafka]
    entrypoint: ["/bin/sh", "-c"]
    command: |
      "
      echo 'Waiting for Kafka...'
      sleep 10
      kafka-topics --create --if-not-exists \
        --bootstrap-server kafka:29092 \
        --topic delivery-events \
        --partitions 3 \
        --replication-factor 1
      echo 'Topic delivery-events created.'
      "

  # ── PostgreSQL (Airflow metadata DB) ─────────────────────────────────────
  postgres:
    image: postgres:15
    container_name: airflow-postgres
    networks: [delivery-net]
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    # What volumes: are: volumes mount a storage location into the container so data
    # persists even when the container is stopped or removed. Without this, all
    # database data would be lost every time the container restarts. Here,
    # 'postgres-db-volume' is a named volume Docker manages — it is like an external
    # hard drive permanently attached to the container.
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    # What healthcheck does: regularly runs a test command inside the container to
    # confirm the service is genuinely ready (not just started). Here it runs
    # pg_isready to confirm Postgres is accepting connections. Other services can
    # use 'condition: service_healthy' in their depends_on to wait for this check
    # to pass before starting — more reliable than just waiting for the container to start.
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5

  # ── Airflow initialisation (runs once) ────────────────────────────────────
  airflow-init:
    image: apache/airflow:2.9.2
    container_name: airflow-init
    networks: [delivery-net]
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    volumes:
      - ./dags:/opt/airflow/dags
    entrypoint: /bin/bash
    command: -c "airflow db init && airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com"

  # ── Airflow Webserver ─────────────────────────────────────────────────────
  airflow-webserver:
    image: apache/airflow:2.9.2
    container_name: airflow-webserver
    networks: [delivery-net]
    depends_on: [airflow-init]
    ports:
      - "8080:8080"
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__WEBSERVER__SECRET_KEY: delivery-opt-secret
    volumes:
      - ./dags:/opt/airflow/dags
      - ./src:/opt/airflow/src
      - ./data:/opt/airflow/data
    command: webserver
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      retries: 5

  # ── Airflow Scheduler ─────────────────────────────────────────────────────
  airflow-scheduler:
    image: apache/airflow:2.9.2
    container_name: airflow-scheduler
    networks: [delivery-net]
    depends_on: [airflow-webserver]
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    volumes:
      - ./dags:/opt/airflow/dags
      - ./src:/opt/airflow/src
      - ./data:/opt/airflow/data
    command: scheduler
```

---

## Step 11.3 — Create `Dockerfile` for the Python pipeline

Create the file `Dockerfile` in the project root:

**How to create this file:**
```bash
notepad Dockerfile
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY sql/ ./sql/
COPY data/ ./data/

CMD ["python", "src/generate_data.py"]
```

---

## Step 11.4 — Start the full stack

**What this does:** Starts all services defined in `docker-compose.yml` simultaneously.

```bash
docker-compose up -d
```

**What `-d` (detached mode) means:** The `-d` flag runs all containers in the background — your terminal is immediately returned to you instead of streaming all the logs. Without `-d`, closing the terminal would stop all the containers.

**Why `-d`?** In production, services run as background daemons. They don't stop when you close a terminal.

---

## Step 11.5 — Check all containers are running

**What `docker-compose ps` does:** Lists all containers defined in your `docker-compose.yml` along with their current status (running, stopped, healthy). Use this to verify everything started correctly.

```bash
docker-compose ps
```

You should see all 6 containers with status `Up` or `healthy`.

---

## Step 11.6 — Watch logs

**What `docker-compose logs -f` does:** Streams the live log output from a container to your terminal. The `-f` flag means "follow" — it keeps updating in real time, like watching a file grow, rather than printing once and stopping.

```bash
docker-compose logs -f kafka
docker-compose logs -f airflow-webserver
```

`-f` means "follow" — like `tail -f` for Docker logs.

---

## Step 11.7 — Open Airflow UI

Go to `http://localhost:8080`
- Username: `admin`
- Password: `admin`

Your DAG (Directed Acyclic Graph) from Guide 05 is now running inside a Docker container with a PostgreSQL backend — the same architecture as production Airflow at real companies.

---

## Step 11.8 — Stop everything

```bash
docker-compose down
```

**Why this matters:** The entire infrastructure — Kafka, Postgres, Airflow — starts with one command and stops with one command. No manual setup, no "which process is running", no version conflicts.

---

## Step 11.9 — Key Docker concepts for interviews

| Concept | What it is | Why it matters |
|---|---|---|
| Image | Blueprint for a container (like a class) | You build once, run anywhere |
| Container | Running instance of an image (like an object) | Isolated, disposable, reproducible |
| Volume | Persistent storage mounted into a container | Data survives container restarts |
| Network | Virtual network containers communicate on | Services find each other by container name |
| `depends_on` | Service A waits for B to start | Prevents startup race conditions |
| `healthcheck` | Checks if a service is truly ready | More reliable than `depends_on` alone |
| `docker-compose up -d` | Start all services, detached | How you start things in production |

---

## Common interview questions

- *"Why use Docker for a data pipeline?"*
  Answer: Reproducibility and portability. The pipeline runs identically in dev, staging, and production. No dependency conflicts. Rolling back is as simple as pointing to a previous image tag.

- *"What is the difference between an image and a container?"*
  Answer: An image is the static blueprint. A container is the running instance. One image can run as many containers simultaneously.

- *"How would you scale this if load increased 10x?"*
  Answer: Increase Kafka partitions and consumer replicas. Swap LocalExecutor for CeleryExecutor in Airflow (multiple workers). Use Kubernetes (K8s) to auto-scale containers. This is the growth path from this project to enterprise-scale.

---

## Step 11.10 — Commit

```bash
git add docker-compose.yml Dockerfile
git commit -m "Add Docker Compose stack: Kafka + Postgres + Airflow fully containerised"
```

---

## Checkpoint

You now have the full production-like stack running locally with one command.

---

## Git Checkpoint — End of Guide 08

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
git add docker-compose.yml
git add Dockerfile
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
git commit -m "Guide 08: Docker Compose stack — Kafka, Postgres, Airflow fully containerised"
```
**What a commit is:** A permanent snapshot saved in Git's history. Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`). You can always return to this exact state.

**What makes a good commit message:**
- Good: `"Guide 08: Docker Compose stack — Kafka, Postgres, Airflow fully containerised"`
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
g3d8e2f Guide 08: Docker Compose stack — Kafka, Postgres, Airflow fully containerised
f1b7c3d Guide 07: Kafka producer and consumer for real-time delivery event streaming
9b2c3d1 Initial commit: project guides and README
```

**In an office:** `git log --oneline` is one of the most used commands. It gives you the full history of the branch at a glance.

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-08-docker
```
**What `git push` does:** Uploads your local commits to GitHub. Until you push, your commit only exists on your laptop.

**What `-u` means:** Sets the upstream — links your local branch to a branch of the same name on GitHub. You only need `-u` the first time you push a new branch. After that, just `git push` is enough.

**What `origin` means:** The name of your GitHub remote. When you ran `git remote add origin ...` in Guide 00B, you named it `origin`. That name sticks.

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-08-docker had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-08-docker` ← what you are merging in
3. Title: `Guide 08: Docker containerisation`
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
You should now see your Guide 08 commit in develop's history. Confirm it is there.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-08-docker
```
**What `-d` means:** Delete the branch locally. Git will refuse to delete if the branch has unmerged commits — a safety guard. Since you just merged the PR, `-d` works.

```bash
git push origin --delete feature/guide-08-docker
```
Deletes the branch on GitHub too.

**Why delete?** Merged branches are dead branches. Keeping them clutters the repository. In real teams, merged branches are always deleted. A clean repo = a professional habit.

**Note — good point to also promote to main:** You now have a fully working containerised stack. This is a meaningful milestone:
```bash
git checkout main
git merge develop
git push origin main
git checkout develop
```

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-09-ml
```

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 08 commit is in the history
- **Branches** → feature/guide-08-docker is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_09_ML.md](GUIDE_09_ML.md) — Build an ML (Machine Learning) model to predict delivery success
