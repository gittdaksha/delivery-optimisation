# Guide 06 — Containerise Everything with Docker

**Goal:** Package the entire pipeline — Kafka, the Python scripts, and Airflow — into Docker containers using Docker Compose. This is how real data pipelines are deployed in production.

---

## Why Docker on your CV?

- Docker appears on **85%+ of data engineering job descriptions**
- It is the universal way to package and ship software
- If you say "I built a pipeline" but it only runs on your laptop with manual setup, that's a prototype
- If you say "it runs with `docker-compose up`", that's production-ready thinking

**What Docker does:**
- Wraps your code + its exact dependencies + the operating system layer into a container image
- Anyone, anywhere, on any machine, runs the same image and gets identical behaviour
- No "it works on my machine" problems

**What a container is vs a virtual machine:**
- A virtual machine emulates an entire separate computer including its own operating system — heavy and slow to start
- A container shares the host operating system's kernel and only packages the application and its dependencies — lightweight, starts in seconds

---

## What Docker Compose does

Docker Compose lets you define multiple containers and their relationships in a single `docker-compose.yml` file, then start all of them with one command:

```bash
docker-compose up  # start all services defined in docker-compose.yml
```

For this project, Compose will start:
1. **Zookeeper** — Kafka's coordination service
2. **Kafka** — the message broker
3. **Postgres** — Airflow's metadata database (more production-realistic than SQLite)
4. **Airflow Webserver** — the UI at localhost:8080
5. **Airflow Scheduler** — runs DAGs on schedule

---

## Git — Before You Start This Guide

- Every guide begins the same way in a real office: you make sure you are on the right branch and it is up to date before touching any files

### Step G1 — Make sure you are on develop and it is current

```bash
git checkout develop  # switch to the existing develop branch
```
**What this does:**
- Switches you to the develop branch
- You always create feature branches FROM develop, never from main and never from another feature branch

- No `-b` here — this switches to an existing branch
- You do not use `-b` when the branch already exists

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
git status  # show all changed and untracked files
```
**What this does:**
- Shows the current state
- You should see `On branch develop, nothing to commit, working tree clean`
- If you see modified files here, deal with them before moving forward — do not carry unrelated changes into a new branch

- No flags here — `git status` always shows full current state

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-06-docker  # -b = create new branch AND switch to it
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
git branch  # list all branches; * marks the one you are on
```
- You will see a `*` next to your current branch
- That `*` means "you are here"

---

## Step 6.1 — Install Docker

Download Docker Desktop from https://www.docker.com/products/docker-desktop/

After install, verify:
```bash
docker --version          # print the installed Docker version
docker-compose --version  # print the installed Compose version
```

---

## Step 6.2 — Create `docker-compose.yml`

Create the file `docker-compose.yml` in the project root:

**How to create this file:**
```bash
notepad docker-compose.yml  # open Notepad; click Yes to create the file
```
- Notepad will open (or ask to create the file — click Yes)
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad

**What `docker-compose.yml` does and why it exists:**
- **What it does:** Declares every service the project needs (Kafka, Postgres, Airflow) and how they connect, so the full stack starts with one command
- **Why separate:** This is infrastructure configuration, not application code — it describes *what to run and how to wire it together*, whereas your Python scripts describe *what the code does*; keeping them separate means you can change the stack without touching any pipeline logic
- **Input:** None (this is a configuration file — it declares services, not data)
- **Output:** Running containers (Zookeeper, Kafka, Postgres, Airflow webserver, Airflow scheduler) accessible at their localhost ports
- **Pipeline position:** All existing Python scripts + Airflow DAGs → **this file** → all services running as containers accessible at their localhost ports

```yaml
version: '3.8'  # Compose file format version; 3.8 supports healthchecks

networks:
  delivery-net:          # name of the shared virtual network
    driver: bridge       # bridge = containers on same host find each other by name

volumes:
  postgres-db-volume:    # named volume so database data survives container restarts

services:

  # ── Zookeeper (Kafka dependency) ─────────────────────────────────────────
  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.0  # official Confluent Zookeeper image
    container_name: zookeeper               # fixed name so other services can reference it
    networks: [delivery-net]                # join the shared network above
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181   # port Kafka uses to talk to Zookeeper
      ZOOKEEPER_TICK_TIME: 2000     # heartbeat interval in milliseconds

  # ── Kafka Broker ─────────────────────────────────────────────────────────
  kafka:
    image: confluentinc/cp-kafka:7.6.0  # official Confluent Kafka image
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
    # → format: "host_machine_port:inside_container_port"
    # → "9092:9092"  means  your laptop:9092  →  Docker routes to  →  container:9092
    # → if you wrote "9999:9092" instead, your script would connect to localhost:9999
    #   and Docker would silently route that traffic to port 9092 inside the container
    ports:
      - "9092:9092"     # expose to host so Python scripts can connect
    # What environment: variables are: these set environment variables inside the
    # container — equivalent to running 'export KAFKA_BROKER_ID=1' in the shell
    # before starting Kafka. Each container reads these to configure itself.
    # → each key: value pair becomes an env var the app reads at startup
    # → KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181 means "find Zookeeper at hostname
    #   'zookeeper' (the container_name above), port 2181" — Docker's bridge network
    #   lets containers find each other by container_name, like a tiny internal DNS
    environment:
      KAFKA_BROKER_ID: 1                          # unique ID for this broker
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181     # where Kafka finds Zookeeper
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092  # how broker announces itself
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT  # no encryption (dev only)
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT  # listener used between brokers
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1    # 1 = no replication (fine for dev)
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"      # create topics on first use

  # ── Create Kafka topic on startup ────────────────────────────────────────
  kafka-setup:
    image: confluentinc/cp-kafka:7.6.0  # reuse Kafka image; it has the CLI tools
    container_name: kafka-setup
    networks: [delivery-net]
    depends_on: [kafka]           # wait for Kafka before running
    entrypoint: ["/bin/sh", "-c"] # override default entrypoint to run a shell script
    command: |
      "
      echo 'Waiting for Kafka...'
      sleep 10                    # give Kafka time to fully start before creating topic
      kafka-topics --create --if-not-exists \
        --bootstrap-server kafka:29092 \
        --topic delivery-events \
        --partitions 3 \          # 3 partitions = 3 consumers can read in parallel
        --replication-factor 1    # 1 = no replication (fine for single-broker dev)
      echo 'Topic delivery-events created.'
      "

  # ── PostgreSQL (Airflow metadata DB) ─────────────────────────────────────
  postgres:
    image: postgres:15            # official Postgres 15 image
    container_name: airflow-postgres
    networks: [delivery-net]
    environment:
      POSTGRES_USER: airflow      # database username Airflow will use
      POSTGRES_PASSWORD: airflow  # password (keep simple for dev)
      POSTGRES_DB: airflow        # name of the database to create
    # What volumes: are: volumes mount a storage location into the container so data
    # persists even when the container is stopped or removed. Without this, all
    # database data would be lost every time the container restarts. Here,
    # 'postgres-db-volume' is a named volume Docker manages — it is like an external
    # hard drive permanently attached to the container.
    # → format: "volume_name_or_host_path:path_inside_container"
    # → "postgres-db-volume:/var/lib/postgresql/data" means:
    #   take the named volume 'postgres-db-volume' (Docker manages its location on your disk)
    #   and mount it at /var/lib/postgresql/data inside the container
    #   (that is where Postgres writes its database files)
    # → stopping/removing the container does NOT touch the volume — data survives
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data  # where Postgres stores its files
    # What healthcheck does: regularly runs a test command inside the container to
    # confirm the service is genuinely ready (not just started). Here it runs
    # pg_isready to confirm Postgres is accepting connections. Other services can
    # use 'condition: service_healthy' in their depends_on to wait for this check
    # to pass before starting — more reliable than just waiting for the container to start.
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]  # run pg_isready inside container
      interval: 10s  # check every 10 seconds
      retries: 5     # mark unhealthy after 5 consecutive failures

  # ── Airflow initialisation (runs once) ────────────────────────────────────
  airflow-init:
    image: apache/airflow:2.9.2  # official Airflow image
    container_name: airflow-init
    networks: [delivery-net]
    depends_on:
      postgres:
        condition: service_healthy  # wait until Postgres passes its healthcheck
    environment:
      # → connection string format: dialect+driver://username:password@hostname/database
      # → "postgresql+psycopg2://airflow:airflow@postgres/airflow" breaks down as:
      #   postgresql+psycopg2 = Postgres via the psycopg2 Python driver
      #   airflow:airflow     = username:password (set in the postgres service above)
      #   @postgres           = hostname 'postgres' (the container_name of the DB container)
      #   /airflow            = the database name to connect to
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow  # DB connection string
      AIRFLOW__CORE__EXECUTOR: LocalExecutor  # run tasks locally (not distributed)
    volumes:
      # → "./dags:/opt/airflow/dags" = host folder on left, container path on right
      # → any file you save to ./dags on your laptop instantly appears at
      #   /opt/airflow/dags inside the container — no rebuild needed
      - ./dags:/opt/airflow/dags  # mount your DAG files into the container
    entrypoint: /bin/bash         # run as a shell script
    command: -c "airflow db init && airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com"  # set up DB + create admin user

  # ── Airflow Webserver ─────────────────────────────────────────────────────
  airflow-webserver:
    image: apache/airflow:2.9.2
    container_name: airflow-webserver
    networks: [delivery-net]
    depends_on: [airflow-init]  # wait for DB init to finish before starting
    # → depends_on: [airflow-init] means Docker Compose will not start
    #   airflow-webserver until the airflow-init container has finished running
    # → prevents the webserver crashing because the database tables do not exist yet
    ports:
      # → "8080:8080" = your browser visits localhost:8080 → Docker routes → container:8080
      - "8080:8080"  # Airflow UI available at localhost:8080
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__WEBSERVER__SECRET_KEY: delivery-opt-secret  # secret for session cookies
    volumes:
      - ./dags:/opt/airflow/dags    # your DAG files
      - ./src:/opt/airflow/src      # your Python scripts
      - ./data:/opt/airflow/data    # your data files
    command: webserver              # start the web UI process
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]  # hit the health endpoint
      interval: 30s  # check every 30 seconds
      retries: 5     # mark unhealthy after 5 failures

  # ── Airflow Scheduler ─────────────────────────────────────────────────────
  airflow-scheduler:
    image: apache/airflow:2.9.2
    container_name: airflow-scheduler
    networks: [delivery-net]
    depends_on: [airflow-webserver]  # start after webserver is up
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    volumes:
      - ./dags:/opt/airflow/dags
      - ./src:/opt/airflow/src
      - ./data:/opt/airflow/data
    command: scheduler  # start the scheduler process (triggers DAG runs on schedule)
```

---

## Step 6.3 — Create `Dockerfile` for the Python pipeline

Create the file `Dockerfile` in the project root:

**How to create this file:**
```bash
notepad Dockerfile  # open Notepad; click Yes to create the file
```
- Notepad will open (or ask to create the file — click Yes)
- Paste the content below into it, then press **Ctrl+S** to save and close Notepad

**What `Dockerfile` does and why it exists:**
- **What it does:** A recipe that tells Docker how to build a custom image for your Python pipeline — which base OS to use, which packages to install, and which files to copy in
- **Why separate:** `docker-compose.yml` says *which* services to run and how they connect; `Dockerfile` says *how to build* the custom image for your own Python code — they answer different questions and are always kept as separate files
- **Input:** `python:3.11-slim` base image + `requirements.txt` (list of Python packages to install)
- **Output:** Custom Docker image with all dependencies installed, ready to run any pipeline script on any machine
- **Pipeline position:** `requirements.txt` + `src/` scripts + `data/` files → **this file** → a portable container image that runs your pipeline identically on any machine

```dockerfile
FROM python:3.11-slim  # start from official slim Python 3.11 image

WORKDIR /app  # set /app as the working directory inside the container

COPY requirements.txt .  # copy requirements first (Docker caches this layer)
RUN pip install --no-cache-dir -r requirements.txt  # --no-cache-dir keeps image smaller

COPY src/ ./src/    # copy your pipeline scripts into the container
COPY sql/ ./sql/    # copy SQL files
COPY data/ ./data/  # copy data files

CMD ["python", "src/generate_data.py"]  # default command when container starts
```

---

## Step 6.4 — Start the full stack

**What this does:** Starts all services defined in `docker-compose.yml` simultaneously.

```bash
docker-compose up -d  # -d = detached; runs in background, returns terminal to you
```

**What `-d` (detached mode) means:**
- The `-d` flag runs all containers in the background
- Your terminal is immediately returned to you instead of streaming all the logs
- Without `-d`, closing the terminal would stop all the containers

**Why `-d`?**
- In production, services run as background daemons
- They don't stop when you close a terminal

---

## Step 6.5 — Check all containers are running

**What `docker-compose ps` does:**
- Lists all containers defined in your `docker-compose.yml` along with their current status (running, stopped, healthy)
- Use this to verify everything started correctly

```bash
docker-compose ps  # list all containers and their current status
```

You should see all 6 containers with status `Up` or `healthy`.

---

## Step 6.6 — Watch logs

**What `docker-compose logs -f` does:**
- Streams the live log output from a container to your terminal
- The `-f` flag means "follow" — it keeps updating in real time, like watching a file grow, rather than printing once and stopping

```bash
docker-compose logs -f kafka            # -f = follow; streams live log output
docker-compose logs -f airflow-webserver  # watch webserver logs in real time
```

`-f` means "follow" — like `tail -f` for Docker logs.

---

## Step 6.7 — Open Airflow UI

Go to `http://localhost:8080`
- Username: `admin`
- Password: `admin`

- Your DAG (Directed Acyclic Graph) from Guide 05 is now running inside a Docker container with a PostgreSQL backend
- This is the same architecture as production Airflow at real companies

---

## Step 6.8 — Stop everything

```bash
docker-compose down  # stop and remove all containers (volumes are kept)
```

**Why this matters:**
- The entire infrastructure — Kafka, Postgres, Airflow — starts with one command and stops with one command
- No manual setup, no "which process is running", no version conflicts

---

## Step 6.9 — Key Docker concepts for interviews

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

## Step 6.10 — Commit

```bash
git add docker-compose.yml Dockerfile  # stage both new files for commit
git commit -m "Add Docker Compose stack: Kafka + Postgres + Airflow fully containerised"  # save snapshot
```

---

## Checkpoint

You now have the full production-like stack running locally with one command.

---

## Git Checkpoint — End of Guide 06

- This is the full Git workflow you do at the end of every guide
- In a real office this is called "raising a PR (Pull Request)"
- You will do this 13 times — by the third time it feels automatic

---

### Step G3 — Check what changed

```bash
git status  # show modified files (red) and untracked files (red)
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
git diff  # show exact lines added (+) and deleted (-) in every modified file
```
**What this shows:**
- The exact lines you added (in green with `+`) and deleted (in red with `-`) in every modified file
- This is your chance to review your own work before anyone else sees it

**What to check:**
- Did I accidentally leave a `print("test123")` debugging line?
- Did I hardcode a password anywhere?
- Does the change make sense — does it do what I intended?

- Press `q` to exit the diff view

**In an office:**
- Senior engineers always do `git diff` before staging
- It catches mistakes before they become commits

---

### Step G5 — Stage your files

```bash
git add docker-compose.yml  # stage this file (select it for the next commit)
git add Dockerfile           # stage this file
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
git diff --staged  # show only the changes you have staged (about to commit)
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
git commit -m "Guide 06: Docker Compose stack — Kafka, Postgres, Airflow fully containerised"  # save staged changes permanently
```
**What a commit is:**
- A permanent snapshot saved in Git's history
- Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`)
- You can always return to this exact state

**What makes a good commit message:**
- Good: `"Guide 06: Docker Compose stack — Kafka, Postgres, Airflow fully containerised"`
- Bad: `"done"`, `"update"`, `"changes"`
- Rule: your future self reading this 3 months later should know exactly what changed without looking at the code

---

### Step G8 — Check your commit was saved

```bash
git log --oneline  # --oneline = one line per commit; newest at top
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
g3d8e2f Guide 06: Docker Compose stack — Kafka, Postgres, Airflow fully containerised
f1b7c3d Guide 07: Kafka producer and consumer for real-time delivery event streaming
9b2c3d1 Initial commit: project guides and README
```

**In an office:**
- `git log --oneline` is one of the most used commands
- It gives you the full history of the branch at a glance

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-06-docker  # -u = set upstream so future pushes just need 'git push'
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
- You will see a yellow banner: **"feature/guide-06-docker had recent pushes"**

---

### Step G10 — Raise a Pull Request on GitHub

- A Pull Request (PR) is a formal request to merge your branch into another branch
- You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-06-docker` ← what you are merging in
3. Title: `Guide 06: Docker containerisation`
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
git checkout develop  # switch back to develop (no -b; branch already exists)
```
- Switches you back to develop
- No `-b` here — `develop` already exists, you are just switching to it

```bash
git pull origin develop  # download the merged PR from GitHub into local develop
```
- Downloads the merged PR from GitHub into your local develop
- Your local develop now has everything from the feature branch you just merged

**What each part means:**
- `origin` — download from GitHub (the remote)
- `develop` — specifically from the develop branch on GitHub
- `pull` — download + merge in one step (it runs `git fetch` then `git merge` automatically)

```bash
git log --oneline  # confirm your Guide 08 commit appears in develop's history
```
- You should now see your Guide 08 commit in develop's history
- Confirm it is there

**What `--oneline` means:**
- Show one line per commit instead of the full multi-line format

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-06-docker  # -d = delete local branch (safe; refuses if unmerged)
```
**What `-d` means:**
- Delete the branch locally
- Git will refuse to delete if the branch has unmerged commits — a safety guard
- Since you just merged the PR, `-d` works

```bash
git push origin --delete feature/guide-06-docker  # delete the branch on GitHub too
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

**Note — good point to also promote to main:**
- You now have a fully working containerised stack
- This is a meaningful milestone:
```bash
git checkout main          # switch to main branch
git merge develop          # bring develop's commits into main
git push origin main       # upload main to GitHub
git checkout develop       # switch back to develop for next guide
```

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-09-ml  # -b = create new branch AND switch to it
```

**What `-b` means:**
- Creates a new branch AND switches to it in one command
- Without `-b`, checkout only switches to an existing branch and would error if the branch does not exist

- You are now on a fresh branch, ready for the next guide

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 08 commit is in the history
- **Branches** → feature/guide-06-docker is gone (deleted)

- This is exactly what a professional Git history looks like

**Next:** [GUIDE_09_ML.md](GUIDE_09_ML.md) — Build an ML (Machine Learning) model to predict delivery success
