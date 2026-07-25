# Guide 06 — Containerise Everything with Docker

**Goal:** Package the entire pipeline — Kafka, Airflow, Postgres — into Docker containers using Docker Compose. This is how real data pipelines are deployed in production.

---

## Why Docker on your CV?

- Docker appears on **85%+ of data engineering job descriptions**
- It is the universal way to package and ship software
- If you say "I built a pipeline" but it only runs on your laptop with manual setup, that is a prototype
- If you say "it runs with `docker compose up`", that is production-ready thinking

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
docker compose up -d
```

For this project, Compose starts:
1. **Zookeeper** — Kafka's coordination service
2. **Kafka** — the message broker
3. **kafka-setup** — one-shot container that creates the `delivery-events` topic then exits
4. **Postgres** — Airflow's metadata database
5. **airflow-init** — one-shot container that initialises the Airflow database then exits
6. **Airflow Webserver** — the UI at port 8080
7. **Airflow Scheduler** — runs DAGs on schedule

---

## Why GitHub Codespaces instead of local Docker

- Airflow requires Linux to run — it will not work on Windows natively
- Company laptops at Air India do not have admin rights to install WSL2 or Docker Desktop
- GitHub Codespaces is a free cloud Linux machine — Docker comes pre-installed, no admin rights needed
- All Docker work in this guide and Guide 07 runs in Codespaces, not your local machine

---

## Git — Before You Start This Guide

### Step G1 — Make sure you are on develop and it is current

```bash
git checkout develop
```
**What this does:**
- Switches you to the develop branch
- You always create feature branches FROM develop

```bash
git pull origin develop
```
**What this does:**
- Downloads any changes from GitHub that you do not have locally

```bash
git status
```
- You should see `On branch develop, nothing to commit, working tree clean`

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-06-docker
```
**What `-b` means:**
- Create a new branch AND switch to it in one command

Confirm you are on the right branch:
```bash
git branch
```
- You will see a `*` next to your current branch

---

## Step 6.1 — Open your project in GitHub Codespaces

- Go to your GitHub repository in the browser
- Click the green **Code** button → **Codespaces** tab → **Create codespace on develop**
- A VS Code window opens in the browser — this is a full Linux machine with Docker already installed
- Your project folder is available inside it — all your files are there

---

## Step 6.2 — Create `requirements.txt`

**What `requirements.txt` does and why it exists:**
- **What it does:** Lists every Python package the pipeline needs, with pinned version numbers
- **Why separate:** The `Dockerfile` references this file to install packages — keeping the package list separate from the build instructions means you can update packages without touching the Dockerfile
- **Input:** None (it is a plain text list)
- **Output:** Used by `pip install -r requirements.txt` and by the `Dockerfile`
- **Pipeline position:** Written once → referenced by both local setup and Docker builds

Create the file `requirements.txt` in the project root:

```
faker==24.3.0
pandas==2.2.1
numpy==1.26.4
requests==2.31.0
kafka-python==2.0.2
scikit-learn==1.4.1.post1
matplotlib==3.8.3
streamlit==1.32.2
```

---

## Step 6.3 — Create `Dockerfile`

**What `Dockerfile` does and why it exists:**
- **What it does:** A recipe that tells Docker how to build a custom image for your Python pipeline — which base OS to use, which packages to install, and which files to copy in
- **Why separate:** `docker-compose.yml` says *which* services to run and how they connect. `Dockerfile` says *how to build* the custom Python image. They answer different questions and are always kept as separate files
- **Input:** `python:3.11-slim` base image + `requirements.txt`
- **Output:** A portable container image that runs your pipeline identically on any machine
- **Pipeline position:** `requirements.txt` + `src/` scripts → **this file** → custom Docker image

Create the file `Dockerfile` in the project root:

```dockerfile
# Start from the official slim Python 3.11 image
# slim = stripped-down version; smaller size, no GUI tools, no compilers
# → full python:3.11 image is ~900MB; slim is ~130MB
FROM python:3.11-slim

# Set the working directory inside the container
# → all subsequent commands (COPY, RUN, CMD) run from /app
# → if /app does not exist, Docker creates it automatically
WORKDIR /app

# Copy requirements.txt first — before copying source code
# → Docker builds images in layers; each instruction is one layer
# → Docker caches layers that have not changed
# → requirements.txt changes rarely; src/ changes often
# → this order means pip install is only re-run when requirements.txt changes,
#   not every time you edit a Python file — much faster rebuilds
COPY requirements.txt .

# Install Python packages
# --no-cache-dir = do not store the pip download cache inside the image
# → saves ~50-100MB of image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and data into the container
COPY src/ ./src/
COPY data/ ./data/

# Default command when the container starts
# → docker run <image> runs this unless you override it
# → CMD is overridable: docker run <image> python src/ingest.py runs ingest instead
CMD ["python", "src/generate_data.py"]
```

---

## Step 6.4 — Create `docker-compose.yml`

**What `docker-compose.yml` does and why it exists:**
- **What it does:** Declares every service the project needs and how they connect, so the full stack starts with one command
- **Why separate:** This is infrastructure configuration, not application code — it describes *what to run and how to wire it together*
- **Input:** None (configuration file — declares services, not data)
- **Output:** Running containers accessible at their ports (Airflow on 8080, Kafka on 9092)
- **Pipeline position:** All Python scripts + Airflow DAGs → **this file** → all services running as containers

Create the file `docker-compose.yml` in the project root:

```yaml
services:

  # ── Zookeeper ─────────────────────────────────────────────────────────────
  # → Kafka needs Zookeeper to coordinate its brokers (leader election, config)
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: zookeeper
    networks: [delivery-net]
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181   # port Kafka uses to talk to Zookeeper
      ZOOKEEPER_TICK_TIME: 2000     # heartbeat interval in milliseconds

  # ── Kafka ─────────────────────────────────────────────────────────────────
  # → the message broker: producers write to it, consumers read from it
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: kafka
    networks: [delivery-net]
    depends_on: [zookeeper]         # Kafka cannot start without Zookeeper
    ports:
      - "9092:9092"                 # external port so your Python scripts can connect
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      # PLAINTEXT://localhost:9092 — advertise localhost so Python scripts running in
      # the Codespaces terminal (outside Docker) can connect via the mapped port
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1            # 1 broker = 1 replica is enough

  # ── Kafka Setup ───────────────────────────────────────────────────────────
  # → one-shot container that creates the Kafka topic then exits
  kafka-setup:
    image: confluentinc/cp-kafka:7.5.0
    container_name: kafka-setup
    networks: [delivery-net]
    depends_on: [kafka]
    entrypoint: /bin/bash
    command: >-
      -c "echo 'Waiting for Kafka...' &&
      cub kafka-ready -b kafka:9092 1 30 &&
      kafka-topics --create --if-not-exists --bootstrap-server kafka:9092 --topic delivery-events --partitions 3 --replication-factor 1 &&
      echo 'Topic created.'"

  # ── Postgres ──────────────────────────────────────────────────────────────
  # → Airflow stores its metadata (DAG runs, task states) in this database
  postgres:
    image: postgres:15
    container_name: airflow-postgres
    networks: [delivery-net]
    environment:
      POSTGRES_USER: airflow       # database username
      POSTGRES_PASSWORD: airflow   # database password
      POSTGRES_DB: airflow         # database name
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]  # check Postgres is accepting connections
      interval: 5s
      retries: 5

  # ── Airflow Init ──────────────────────────────────────────────────────────
  # → one-shot container: initialises the Airflow database and creates admin user
  # → runs once then exits — webserver waits for it to finish before starting
  airflow-init:
    image: apache/airflow:2.9.2
    container_name: airflow-init
    networks: [delivery-net]
    depends_on:
      postgres:
        condition: service_healthy  # wait until Postgres passes its healthcheck
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    volumes:
      - ./dags:/opt/airflow/dags  # mount your DAG files into the container
    entrypoint: /bin/bash
    command: -c "airflow db init && airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com"

  # ── Airflow Webserver ─────────────────────────────────────────────────────
  airflow-webserver:
    image: apache/airflow:2.9.2
    container_name: airflow-webserver
    networks: [delivery-net]
    depends_on: [airflow-init]
    ports:
      - "8080:8080"               # Airflow UI available at localhost:8080
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__WEBSERVER__SECRET_KEY: delivery-opt-secret
      # → installs these Python packages inside the container on every startup
      # → needed because the base Airflow image does not include faker, pandas, numpy
      _PIP_ADDITIONAL_REQUIREMENTS: "faker pandas numpy dbt-core==1.8.0 dbt-sqlite==1.8.1"
    volumes:
      - ./dags:/opt/airflow/dags          # your DAG files
      - ./src:/opt/airflow/src            # your Python scripts
      - ./data:/opt/airflow/data          # your data files
      - ./delivery_dbt:/opt/airflow/delivery_dbt  # dbt project folder
    command: webserver
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      retries: 5

  # ── Airflow Scheduler ─────────────────────────────────────────────────────
  # → reads DAG files, decides when tasks are due, sends them to the executor
  airflow-scheduler:
    image: apache/airflow:2.9.2
    container_name: airflow-scheduler
    networks: [delivery-net]
    depends_on: [airflow-webserver]
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      # → same packages needed here — the scheduler is the process that actually runs tasks
      _PIP_ADDITIONAL_REQUIREMENTS: "faker pandas numpy dbt-core==1.8.0 dbt-sqlite==1.8.1"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./src:/opt/airflow/src
      - ./data:/opt/airflow/data
      - ./delivery_dbt:/opt/airflow/delivery_dbt
    command: scheduler

# ── Shared network ────────────────────────────────────────────────────────
# → all containers join this network so they can reach each other by container_name
networks:
  delivery-net:
    driver: bridge
```

**Key concepts in this file:**

**What `depends_on` does:**
- Controls startup order — `airflow-webserver: depends_on: [airflow-init]` means the webserver will not start until airflow-init has finished
- Without this, the webserver would crash on startup because the database tables do not exist yet

**What `volumes` does:**
- A volume mount shares a folder from your machine into the container
- `./dags:/opt/airflow/dags` means: your local `dags/` folder appears inside the container at `/opt/airflow/dags/`
- Changes you make locally are immediately visible inside the container — no rebuild needed

**What `healthcheck` does:**
- Defines a command Docker runs periodically to confirm the service is genuinely ready
- Other services use `condition: service_healthy` to wait for this before starting

**What `_PIP_ADDITIONAL_REQUIREMENTS` does:**
- The base Airflow image does not include `faker`, `pandas`, or `numpy`
- This variable tells the container to `pip install` those packages on every startup
- Set on BOTH webserver and scheduler — the scheduler is the process that actually runs task code

---

## Step 6.5 — Fix folder permissions in Codespaces

The Airflow container runs as a non-root user. It will get "Permission denied" when writing to your mounted `data/` folder unless you fix this first.

```bash
mkdir -p data/raw data/processed
```
**What this does:**
- Creates `data/raw/` and `data/processed/` if they do not exist
- `-p` means: create parent folders too, no error if already exists

```bash
sudo chmod -R 777 data
```
**What each part means:**
- `sudo` — run as superuser (needed to change permissions)
- `chmod` — change file permissions
- `-R` — recursive: applies to the folder AND everything inside it
- `777` — gives full read/write/execute to owner, group, and everyone else (including the container user)
- `data` — the folder to apply this to

---

## Step 6.6 — Start the full stack

In the Codespaces terminal:

```bash
docker compose up -d
```
**What each part means:**
- `docker compose` — Docker Compose CLI tool, reads `docker-compose.yml`
- `up` — start all services defined in the file
- `-d` — detached mode: runs containers in the background, gives you the terminal back

Wait about 2 minutes for all containers to start and for Airflow to install pip packages. Check status:

```bash
docker ps
```
**What to look for:**
- All containers show `Up` or `(healthy)` in the STATUS column
- `kafka-setup` and `airflow-init` will show `Exited (0)` — this is correct, they ran once and finished
- `airflow-webserver` takes the longest — it is installing packages via `_PIP_ADDITIONAL_REQUIREMENTS`

---

## Step 6.7 — Open the Airflow UI

- In Codespaces, click the **PORTS** tab at the bottom of the screen
- Find port `8080`
- Right-click it → **Port Visibility** → **Public**
- Click the globe icon next to port `8080`

Login:
- Username: `admin`
- Password: `admin`

---

## Step 6.8 — Stop everything

```bash
docker compose down
```
**What this does:**
- Stops and removes all containers
- Named volumes (database data) are kept — your data survives

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
| `docker compose up -d` | Start all services, detached | How you start things in production |

---

## Common interview questions

- *"Why use Docker for a data pipeline?"*
  Answer: Reproducibility and portability. The pipeline runs identically in dev and production. No dependency conflicts. Rolling back is as simple as pointing to a previous image tag.

- *"What is the difference between an image and a container?"*
  Answer: An image is the static blueprint. A container is the running instance. One image can run as many containers simultaneously.

- *"What is the difference between `docker compose up` and `docker run`?"*
  Answer: `docker run` starts a single container. `docker compose up` reads a YAML file and starts all defined services together, with networking and dependencies handled automatically.

---

## Step 6.10 — Commit

```bash
git add docker-compose.yml Dockerfile requirements.txt
git commit -m "Guide 06: Docker Compose stack with Kafka, Postgres, Airflow; add Dockerfile and requirements.txt"
```

---

## Checkpoint

You now have:
- The full stack (Kafka, Postgres, Airflow) running with one command
- A `Dockerfile` that packages your Python pipeline portably
- A `requirements.txt` that pins all Python dependencies
- Understanding of images, containers, volumes, networks, and healthchecks

---

## Git Checkpoint — End of Guide 06

### Step G3 — Check what changed

```bash
git status
```
**What to look for:**
- `docker-compose.yml`, `Dockerfile`, `requirements.txt` listed as new or modified files

### Step G4 — Review your changes

```bash
git diff
```
Press `q` to exit.

### Step G5 — Stage your files

```bash
git add docker-compose.yml Dockerfile requirements.txt
```
**Why not `git add .`?**
- Using `.` adds everything including data files and logs — always add by name

### Step G6 — Verify what is staged

```bash
git diff --staged
```
Press `q` to exit.

### Step G7 — Commit

```bash
git commit -m "Guide 06: Docker Compose stack with Kafka, Postgres, Airflow; add Dockerfile and requirements.txt"
```

### Step G8 — Check your commit was saved

```bash
git log --oneline
```
Example output:
```
a1b2c3d Guide 06: Docker Compose stack with Kafka, Postgres, Airflow; add Dockerfile and requirements.txt
d1a774d Guide 04: dbt project with staging, mart models and data quality tests
```

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-06-docker
```

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-06-docker had recent pushes"**

### Step G10 — Raise a Pull Request on GitHub

**PR title:** `Guide 06: Docker Compose stack — Kafka, Postgres, Airflow containerised`

**PR description:**
```
- Added docker-compose.yml: 7 services — Zookeeper, Kafka, kafka-setup, Postgres, airflow-init, airflow-webserver, airflow-scheduler
- Added Dockerfile: Python 3.11-slim image for pipeline scripts
- Added requirements.txt: pinned versions for all Python dependencies
- Stack starts with: docker compose up -d
- Runs in GitHub Codespaces (no admin rights needed on company laptop)
```

Steps in GitHub:
1. Click **Compare & pull request**
2. Check: **base:** `develop` ← **compare:** `feature/guide-06-docker`
3. Paste the title and description above
4. Click **Create pull request**
5. Click **Merge pull request** → **Confirm merge**

### Step G11 — Pull the merged changes back locally

```bash
git checkout develop
```
```bash
git pull origin develop
```
```bash
git log --oneline
```

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-06-docker
```
```bash
git push origin --delete feature/guide-06-docker
```

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-07-airflow
```

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR: `Guide 06: Docker Compose stack — Kafka, Postgres, Airflow containerised`
- **develop branch → commits** → your Guide 06 commit is in the history
- **Branches** → `feature/guide-06-docker` is gone (deleted)

**Next:** [GUIDE_07_AIRFLOW.md](GUIDE_07_AIRFLOW.md) — Schedule and monitor the pipeline with Apache Airflow
