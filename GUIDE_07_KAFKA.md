# Guide 07 — Real-Time Delivery Events with Apache Kafka

**Goal:** Simulate a real-time stream of delivery status events using Apache Kafka. Understand producers, consumers, and topics — then consume that stream with PySpark Structured Streaming.

---

## Why Kafka on your CV?

Apache Kafka is the world's most widely used real-time data streaming platform. It's on **75%+ of mid/senior data engineering job descriptions**. Every major logistics company (Amazon, Delhivery, Zomato, Swiggy, FedEx) streams delivery events through Kafka or an equivalent system.

**What a message broker is:** A message broker is a system that sits between services that produce data and services that consume it. Instead of Service A talking directly to Service B, A sends a message to the broker, and B reads it from the broker independently and at its own pace. This decouples the two services — if B crashes, messages queue up safely and B reads them when it recovers. Kafka is the most widely used message broker for high-volume data streams.

The mental model: Kafka is like a massive, durable, real-time message bus. When a delivery partner updates an order status (picked up → in transit → delivered / failed), that event is published to Kafka instantly. Multiple systems — the tracking app, the analytics pipeline, the ML (Machine Learning) model — all consume that stream independently.

---

## Architecture you are building

```
Delivery Partner App
        ↓
   [Kafka Producer]
        ↓
   Kafka Topic: delivery-events
        ↓
   [Kafka Consumer] → SQLite (event log)
   [Spark Streaming] → Real-time FADR counter
```

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
git checkout -b feature/guide-07-kafka
```
**What `-b` means:** Create a new branch AND switch to it. Without `-b`, checkout only switches to an existing branch.

**Why a new branch for every guide:** Each branch is one unit of work. If something breaks, you can delete the branch and start fresh without affecting develop or main. In an office, each feature or fix lives on its own branch for the same reason.

Confirm you are on the right branch:
```bash
git branch
```
You will see a `*` next to your current branch. That `*` means "you are here".

---

## Step 10.1 — Install Kafka Python client

```bash
pip install kafka-python==2.0.2
```

**Why:** `kafka-python` is the most widely used Python library for Kafka. It lets you write producers (publish messages) and consumers (read messages) in Python.

---

## Step 10.2 — Install and start Kafka (local)

Kafka requires Java. Check it is installed:
```bash
java -version
```

If not installed, download JDK 17 from https://adoptium.net/ and install it first.

**Download Kafka:**
```bash
# Download Kafka (Windows PowerShell)
Invoke-WebRequest -Uri "https://downloads.apache.org/kafka/3.7.0/kafka_2.13-3.7.0.tgz" -OutFile "kafka.tgz"
tar -xzf kafka.tgz
```

Or download manually from https://kafka.apache.org/downloads and extract to `C:\kafka\`.

**Start Kafka (3 terminals needed):**

Terminal 1 — Start Zookeeper (Kafka's coordination service):
```bash
C:\kafka\bin\windows\zookeeper-server-start.bat C:\kafka\config\zookeeper.properties
```

Terminal 2 — Start Kafka broker:
```bash
C:\kafka\bin\windows\kafka-server-start.bat C:\kafka\config\server.properties
```

Terminal 3 — Create the topic:
```bash
C:\kafka\bin\windows\kafka-topics.bat --create --topic delivery-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

**Why 3 partitions?** Kafka distributes messages across partitions. Multiple consumers can read in parallel — one per partition. This is how Kafka achieves high throughput.

---

## Step 10.3 — Create `src/kafka_producer.py`

This simulates the delivery partner's app publishing status updates in real time.

**How to create this file:**
```bash
notepad src/kafka_producer.py
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```python
import json
import time
import random
from kafka import KafkaProducer
from faker import Faker
from datetime import datetime

fake = Faker('en_IN')

CITIES          = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Pune', 'Chennai']
ADDRESS_TYPES   = ['Apartment', 'PG/Hostel', 'House', 'Office', 'Gated Community']
WINDOWS         = ['Morning (9-12)', 'Afternoon (12-15)', 'Evening (15-19)', 'Night (19-22)']
STATUSES        = ['PICKED_UP', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED', 'RESCHEDULED']

# What bootstrap_servers means: when a Kafka client first connects, it needs to
# know the address of at least one Kafka broker to bootstrap (get started). After
# that first connection, Kafka tells the client about all other brokers in the cluster.
# 'localhost:9092' is the address of your local Kafka broker.
#
# What value_serializer does: Kafka transmits raw bytes, not Python objects. The
# value_serializer is a function that converts your Python dict into bytes before
# sending. Here: json.dumps(v) converts the dict to a JSON string, .encode('utf-8')
# converts that string to bytes. The consumer does the reverse (deserializer).
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8')
)

print("Producing delivery events to Kafka topic 'delivery-events'...")
print("Press Ctrl+C to stop.\n")

count = 0
try:
    while True:
        city         = random.choice(CITIES)
        address_type = random.choice(ADDRESS_TYPES)
        status       = random.choice(STATUSES)

        event = {
            "delivery_id":   fake.uuid4(),
            "city":          city,
            "address_type":  address_type,
            "window":        random.choice(WINDOWS),
            "status":        status,
            "timestamp":     datetime.now().isoformat(),
            "order_value":   round(random.uniform(150, 8000), 2),
            "attempt":       random.randint(1, 3),
        }

        # Key by city — all events for the same city go to the same partition
        # This guarantees ordering per city (important for tracking)
        producer.send(
            topic='delivery-events',
            key=city,
            value=event
        )

        count += 1
        status_symbol = "✓" if status == "DELIVERED" else ("✗" if status in ["FAILED", "RESCHEDULED"] else "→")
        print(f"[{count:04d}] {status_symbol} {city:12s} | {address_type:18s} | {status}")

        time.sleep(0.5)   # 2 events per second — realistic pace

except KeyboardInterrupt:
    print(f"\nStopped. Published {count} events.")
    producer.flush()
    producer.close()
```

---

## Step 10.4 — Create `src/kafka_consumer.py`

This reads events from Kafka and logs them to SQLite.

**How to create this file:**
```bash
notepad src/kafka_consumer.py
```
Notepad will open (or ask to create the file — click Yes). Paste the content below into it, then press **Ctrl+S** to save and close Notepad.

```python
import json
import sqlite3
from kafka import KafkaConsumer
from datetime import datetime

DB_PATH = 'data/delivery_db.sqlite'

# Create event log table
conn = sqlite3.connect(DB_PATH)
conn.execute("""
    CREATE TABLE IF NOT EXISTS delivery_events_stream (
        delivery_id  TEXT,
        city         TEXT,
        address_type TEXT,
        window       TEXT,
        status       TEXT,
        timestamp    TEXT,
        order_value  REAL,
        attempt      INTEGER,
        consumed_at  TEXT
    )
""")
conn.commit()

consumer = KafkaConsumer(
    'delivery-events',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    # What auto_offset_reset='earliest' means: an "offset" is the position of a
    # message in a Kafka partition (like a line number). When this consumer starts
    # for the first time with no saved position, 'earliest' means "start reading
    # from the very first message ever published to this topic." The alternative
    # 'latest' means "only read new messages arriving from now."
    auto_offset_reset='earliest',
    # What group_id does: the group_id groups this consumer with others reading
    # the same topic. Kafka tracks how far each consumer group has read (its offset).
    # If you restart this consumer, it picks up where it left off — no duplicate reads.
    # If you add a second consumer with the same group_id, Kafka splits the partitions
    # between them so each consumer handles a share of the work.
    group_id='delivery-analytics',
)

print("Consuming from 'delivery-events'... (Ctrl+C to stop)")

# What Kafka offset commits do: in the kafka-python library, offsets (your reading
# position) are committed automatically at a regular interval by default. This is
# the equivalent of message.ack() in Pub/Sub — it tells Kafka "I have successfully
# processed up to this point." If the consumer crashes before committing, Kafka
# re-delivers those messages from the last committed offset when it restarts.

count = 0
try:
    for message in consumer:
        event = message.value
        event['consumed_at'] = datetime.now().isoformat()

        conn.execute("""
            INSERT INTO delivery_events_stream
            (delivery_id, city, address_type, window, status, timestamp, order_value, attempt, consumed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event['delivery_id'], event['city'], event['address_type'],
            event['window'], event['status'], event['timestamp'],
            event['order_value'], event['attempt'], event['consumed_at']
        ))
        conn.commit()

        count += 1
        if count % 10 == 0:
            # Print live FADR from the stream
            cur = conn.execute("""
                SELECT
                    ROUND(AVG(CASE WHEN status='DELIVERED' THEN 1.0 ELSE 0.0 END)*100, 1) as live_fadr,
                    COUNT(*) as total_events
                FROM delivery_events_stream
                WHERE status IN ('DELIVERED','FAILED','RESCHEDULED')
            """)
            row = cur.fetchone()
            if row[0]:
                print(f"  Live FADR: {row[0]}%  |  Total terminal events: {row[1]}")

except KeyboardInterrupt:
    print(f"\nConsumed {count} messages. Stored in database.")
    conn.close()
    consumer.close()
```

---

## Step 10.5 — Run producer and consumer together

Open **two terminals** side by side.

Terminal 1 (producer — simulates delivery events):
```bash
python src/kafka_producer.py
```

Terminal 2 (consumer — reads and stores them):
```bash
python src/kafka_consumer.py
```

You will see events flowing in Terminal 1 and being processed in Terminal 2 in real time, with a live FADR (First Attempt Delivery Rate) updating every 10 events.

---

## Step 10.6 — Key Kafka concepts for interviews

| Concept | What it is | Why it matters |
|---|---|---|
| Topic | A named channel — like a table, but for events | Where producers write and consumers read |
| Partition | A topic is split into N partitions for parallelism | More partitions = more consumers = higher throughput |
| Offset | Position of a message in a partition | Kafka tracks where each consumer group has read to |
| Consumer Group | Group of consumers sharing the work | Each message goes to ONE consumer in the group |
| Key | Message routing key — same key → same partition | Guarantees ordering per key (e.g. per city) |
| Retention | Kafka stores messages for N days by default | Consumers can re-read history — unlike a queue |

---

## Common interview questions this prepares you for

- *"What is the difference between a queue and Kafka?"*
  Answer: A queue deletes a message once consumed. Kafka retains messages for a configurable period — multiple consumer groups can all read the same data independently.

- *"Why do you partition a Kafka topic?"*
  Answer: Parallelism. Each consumer in a group reads one partition, so N partitions = N consumers reading simultaneously.

- *"What happens if a consumer crashes mid-read?"*
  Answer: Kafka tracks offsets per consumer group. When the consumer restarts, it picks up from the last committed offset — no data is lost.

---

## Step 10.7 — Commit

```bash
git add src/kafka_producer.py src/kafka_consumer.py
git commit -m "Add Kafka producer/consumer for real-time delivery event streaming"
```

---

## Checkpoint

You now have:
- A Kafka producer simulating real delivery events
- A consumer reading and persisting them
- Live FADR computed from the stream
- Understanding of topics, partitions, offsets, consumer groups

---

## Git Checkpoint — End of Guide 07

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
git add src/kafka_producer.py
git add src/kafka_consumer.py
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
git commit -m "Guide 07: Kafka producer and consumer for real-time delivery event streaming"
```
**What a commit is:** A permanent snapshot saved in Git's history. Every commit gets a unique ID (called a hash — a long string like `a3f9c2b`). You can always return to this exact state.

**What makes a good commit message:**
- Good: `"Guide 07: Kafka producer and consumer for real-time delivery event streaming"`
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
f1b7c3d Guide 07: Kafka producer and consumer for real-time delivery event streaming
e2c5a9b Guide 06: Airflow DAG orchestrating 5-task delivery pipeline with daily schedule
9b2c3d1 Initial commit: project guides and README
```

**In an office:** `git log --oneline` is one of the most used commands. It gives you the full history of the branch at a glance.

---

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-07-kafka
```
**What `git push` does:** Uploads your local commits to GitHub. Until you push, your commit only exists on your laptop.

**What `-u` means:** Sets the upstream — links your local branch to a branch of the same name on GitHub. You only need `-u` the first time you push a new branch. After that, just `git push` is enough.

**What `origin` means:** The name of your GitHub remote. When you ran `git remote add origin ...` in Guide 00B, you named it `origin`. That name sticks.

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-07-kafka had recent pushes"**.

---

### Step G10 — Raise a Pull Request on GitHub

A Pull Request (PR) is a formal request to merge your branch into another branch. You are asking: "I finished this work, please review it and bring it into develop."

1. Click **Compare & pull request** in the yellow banner
2. Check the top settings:
   - **base:** `develop` ← where the code will go
   - **compare:** `feature/guide-07-kafka` ← what you are merging in
3. Title: `Guide 07: Kafka real-time event streaming`
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
You should now see your Guide 07 commit in develop's history. Confirm it is there.

---

### Step G12 — Delete the feature branch

```bash
git branch -d feature/guide-07-kafka
```
**What `-d` means:** Delete the branch locally. Git will refuse to delete if the branch has unmerged commits — a safety guard. Since you just merged the PR, `-d` works.

```bash
git push origin --delete feature/guide-07-kafka
```
Deletes the branch on GitHub too.

**Why delete?** Merged branches are dead branches. Keeping them clutters the repository. In real teams, merged branches are always deleted. A clean repo = a professional habit.

---

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-08-docker
```

You are now on a fresh branch, ready for the next guide.

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR with your title and description
- **develop branch → commits** → your Guide 07 commit is in the history
- **Branches** → feature/guide-07-kafka is gone (deleted)

This is exactly what a professional Git history looks like.

**Next:** [GUIDE_08_DOCKER.md](GUIDE_08_DOCKER.md) — Package everything with Docker
