# Guide 08 — Real-Time Delivery Events with Apache Kafka

**Goal:** Simulate a real-time stream of delivery status events using Apache Kafka. Understand producers, consumers, and topics — then see how real-time data differs from batch processing.

**Why this guide exists:** All the previous guides process data in batches — run a script, process 50,000 rows, done. Kafka handles real-time data — events arriving continuously, like a delivery status updating every second. This is how companies like Swiggy and Zomato track live delivery status. It is a separate skill from batch processing and appears on senior DE job descriptions.

---

## Why Kafka on your CV?

- Apache Kafka is the world's most widely used real-time data streaming platform
- It is on **75%+ of mid/senior data engineering job descriptions**
- Every major logistics company (Amazon, Delhivery, Zomato, Swiggy, FedEx) streams delivery events through Kafka or an equivalent system

**What a message broker is:**
- A message broker is a system that sits between services that produce data and services that consume it
- Instead of Service A talking directly to Service B, A sends a message to the broker, and B reads it from the broker independently and at its own pace
- This decouples the two services — if B crashes, messages queue up safely and B reads them when it recovers
- Kafka is the most widely used message broker for high-volume data streams

The mental model:
- Kafka is like a massive, durable, real-time message bus
- When a delivery partner updates an order status (picked up → in transit → delivered / failed), that event is published to Kafka instantly
- Multiple systems — the tracking app, the analytics pipeline, the ML model — all consume that stream independently

---

## Architecture you are building

```
Delivery Partner App
        ↓
   [Kafka Producer]  ← src/kafka_producer.py
        ↓
   Kafka Topic: delivery-events
        ↓
   [Kafka Consumer]  ← src/kafka_consumer.py
        ↓
   SQLite (delivery_events_stream table)
```

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
**What this does:**
- You should see `On branch develop, nothing to commit, working tree clean`

### Step G2 — Create your feature branch

```bash
git checkout -b feature/guide-08-kafka
```
**What `-b` means:**
- Create a new branch AND switch to it in one command

Confirm you are on the right branch:
```bash
git branch
```
- You will see a `*` next to your current branch

---

## How Kafka runs in this project

- Kafka is already defined in `docker-compose.yml` — no separate install needed
- When you ran `docker compose up -d` in Guide 07, three Kafka services started alongside Airflow:
  - `zookeeper` — Kafka's coordination service
  - `kafka` — the message broker
  - `kafka-setup` — a one-shot container that created the `delivery-events` topic and then exited
- The Kafka broker is exposed on port `9092` — your Python scripts connect to it at `localhost:9092`

---

## Step 8.1 — Verify Kafka is running in Codespaces

In the Codespaces terminal, check the containers are up:

```bash
docker ps
```
**What to look for:**
- `zookeeper` — should show `Up`
- `kafka` — should show `Up`
- `kafka-setup` — will show `Exited (0)` — this is correct, it ran once and finished

If Kafka is not running, start it:
```bash
docker compose up -d
```

Verify the `delivery-events` topic was created:
```bash
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```
**What each part means:**
- `docker exec kafka` — run a command inside the running `kafka` container
- `kafka-topics --list` — list all topics
- `--bootstrap-server localhost:9092` — the address of the Kafka broker

You should see `delivery-events` in the output.

---

## Step 8.2 — Install Kafka Python client in Codespaces

In the Codespaces terminal:

```bash
pip install kafka-python==2.0.2
```
**Why:**
- `kafka-python` is the Python library for Kafka — it lets you write producers (publish messages) and consumers (read messages)
- Version 2.0.2 is pinned because later versions have known compatibility issues

---

## Step 8.3 — Create `src/kafka_producer.py`

**What `src/kafka_producer.py` does and why it exists:**
- **What it does:** Simulates a delivery partner's app by continuously generating fake delivery status events and publishing them to the Kafka `delivery-events` topic in real time
- **Why separate:** The producer and consumer are deliberately split because in a real system they are run by completely different teams and services — the delivery app publishes events without knowing or caring who reads them. Keeping them in separate files mirrors that real-world separation
- **Input:** Generated delivery events (created in memory using Python's `random` and `Faker` libraries — no file is read)
- **Output:** Kafka topic `delivery-events` — a continuous real-time stream of JSON delivery status messages, published at ~2 events per second
- **Pipeline position:** Kafka broker is running and the `delivery-events` topic exists → **this script** → messages queue up in the Kafka topic, ready for the consumer to read

Create the file `src/kafka_producer.py`:

```python
import json  # needed to convert dicts to JSON strings for Kafka
import time  # needed for time.sleep to control message rate
import random  # needed to randomly pick cities, statuses, etc.
from kafka import KafkaProducer  # Kafka client class for publishing messages
from faker import Faker  # generates realistic fake data (names, UUIDs, etc.)
from datetime import datetime  # needed to timestamp each event

fake = Faker('en_IN')  # Faker with Indian locale for realistic Indian data

CITIES          = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Pune', 'Chennai']
ADDRESS_TYPES   = ['Apartment', 'PG/Hostel', 'House', 'Office', 'Gated Community']
WINDOWS         = ['Morning (9-12)', 'Afternoon (12-15)', 'Evening (15-19)', 'Night (19-22)']
STATUSES        = ['PICKED_UP', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED', 'RESCHEDULED']

# What bootstrap_servers means: when a Kafka client first connects, it needs to
# know the address of at least one Kafka broker to bootstrap (get started). After
# that first connection, Kafka tells the client about all other brokers in the cluster.
# 'localhost:9092' is the port we mapped from the kafka container in docker-compose.yml.
#
# What value_serializer does: Kafka transmits raw bytes, not Python objects. The
# value_serializer is a function that converts your Python dict into bytes before
# sending. Here: json.dumps(v) converts the dict to a JSON string, .encode('utf-8')
# converts that string to bytes. The consumer does the reverse (deserializer).
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',  # Kafka broker port mapped by docker-compose.yml
    # lambda v: ... = an anonymous function: 'v' is the Python dict you pass to .send()
    # → json.dumps(v) converts dict to JSON string: {'city': 'Mumbai'} → '{"city": "Mumbai"}'
    # → .encode('utf-8') converts string to bytes: '{"city": "Mumbai"}' → b'{"city": "Mumbai"}'
    # → Kafka requires bytes — it stores and transmits raw byte sequences, not Python strings
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),  # dict → JSON string → bytes
    # lambda k: ... = anonymous function: 'k' is the key string you pass to .send()
    # → k.encode('utf-8') converts the string key to bytes: 'Mumbai' → b'Mumbai'
    # → Kafka also requires the routing key as bytes, not a Python string
    key_serializer=lambda k: k.encode('utf-8')  # convert string key to bytes
)

print("Producing delivery events to Kafka topic 'delivery-events'...")
print("Press Ctrl+C to stop.\n")

count = 0  # track how many events we have published
try:
    while True:  # keep producing events until Ctrl+C is pressed
        city         = random.choice(CITIES)  # pick a random city
        address_type = random.choice(ADDRESS_TYPES)  # pick a random address type
        status       = random.choice(STATUSES)  # pick a random delivery status

        event = {  # build the event dict — one delivery status update
            "delivery_id":   fake.uuid4(),  # unique ID for this delivery
            "city":          city,  # city of the delivery
            "address_type":  address_type,  # type of delivery address
            "window":        random.choice(WINDOWS),  # chosen delivery time window
            "status":        status,  # current delivery status
            "timestamp":     datetime.now().isoformat(),  # exact time of this event
            "order_value":   round(random.uniform(150, 8000), 2),  # random order value in rupees
            "attempt":       random.randint(1, 3),  # which delivery attempt this is
        }

        # Key by city — all events for the same city go to the same partition
        # This guarantees ordering per city (important for tracking)
        # producer.send(topic, key=..., value=...) = publish one message to Kafka
        # → topic='delivery-events'  = the name of the Kafka channel to write to
        # → key=city                 = routing key; same key always lands on the same partition
        # → value=event              = the Python dict; value_serializer converts it to bytes
        producer.send(  # publish the event to Kafka
            topic='delivery-events',  # which Kafka topic to publish to
            key=city,  # routing key — same city always goes to same partition
            value=event  # the event dict (serializer converts it to bytes)
        )

        count += 1  # increment published event counter
        # Inline if-else: value_if_true  if  condition  else  value_if_false
        status_symbol = "✓" if status == "DELIVERED" else ("✗" if status in ["FAILED", "RESCHEDULED"] else "→")
        # f-string format specs:
        # → {count:04d} = integer padded to 4 digits: 1 → 0001
        # → {city:12s}  = string padded to 12 chars wide (keeps columns aligned)
        print(f"[{count:04d}] {status_symbol} {city:12s} | {address_type:18s} | {status}")

        time.sleep(0.5)   # 2 events per second — realistic pace

except KeyboardInterrupt:  # user pressed Ctrl+C
    print(f"\nStopped. Published {count} events.")
    # producer.flush() = block until ALL buffered messages have been sent to Kafka
    # → .send() is async and queues messages internally; flush() drains that queue
    # → without flush(), buffered messages can be lost when the program exits
    producer.flush()  # send any buffered messages before closing
    producer.close()  # close connection cleanly
```

---

## Step 8.4 — Create `src/kafka_consumer.py`

**What `src/kafka_consumer.py` does and why it exists:**
- **What it does:** Continuously reads delivery status events from the Kafka topic and writes each one into a SQLite table, while printing a live FADR every 10 events
- **Why separate:** If the consumer logic were merged into the producer, you would lose the core benefit of Kafka — decoupling. Any service that needs the event data (analytics, ML model, tracking app) should be able to read independently, at its own pace, without the producer knowing about it
- **Input:** Kafka topic `delivery-events` — the real-time stream of JSON messages published by `kafka_producer.py`
- **Output:** `data/delivery_db.sqlite` — specifically the `delivery_events_stream` table (rows inserted in real time, one per Kafka message consumed)
- **Pipeline position:** Producer is publishing events → **this script** → events stored row by row in SQLite

Create the file `src/kafka_consumer.py`:

```python
import json  # needed to parse incoming JSON bytes back into Python dicts
import sqlite3  # built-in Python library to save events to SQLite
from kafka import KafkaConsumer  # Kafka client class for reading messages
from datetime import datetime  # needed to record when each event was consumed

DB_PATH = 'data/delivery_db.sqlite'  # path to the project database file

# Create event log table
conn = sqlite3.connect(DB_PATH)  # open (or create) the SQLite database
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
conn.commit()  # write the CREATE TABLE statement to disk

consumer = KafkaConsumer(
    'delivery-events',  # name of the Kafka topic to read from
    bootstrap_servers='localhost:9092',  # Kafka broker port mapped by docker-compose.yml
    # lambda m: ... = anonymous function; 'm' is the raw bytes Kafka delivers
    # → m.decode('utf-8') converts bytes back to a string
    # → json.loads(...) converts that JSON string back to a Python dict
    # → this is the exact REVERSE of the producer's value_serializer
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),  # bytes → JSON string → dict
    # auto_offset_reset='earliest': when this consumer starts for the first time with
    # no saved position, 'earliest' means "start reading from the very first message
    # ever published to this topic." The alternative 'latest' means "only read new
    # messages arriving from now."
    auto_offset_reset='earliest',  # start from oldest message if no offset saved
    # group_id: the group_id groups this consumer with others reading the same topic.
    # Kafka tracks how far each consumer group has read (its offset).
    # If you restart this consumer, it picks up where it left off — no duplicate reads.
    group_id='delivery-analytics',  # consumer group name — tracks reading position
)

print("Consuming from 'delivery-events'... (Ctrl+C to stop)")

count = 0  # track how many messages we have consumed
try:
    # 'for message in consumer:' = Kafka consumer is iterable; each iteration blocks
    # until the next message arrives from the topic
    # → this loop runs FOREVER — it never exits on its own (use Ctrl+C to stop it)
    for message in consumer:  # loop forever; each iteration is one Kafka message
        # message.value = the payload, already processed by value_deserializer
        # → already a Python dict; no manual decoding needed here
        event = message.value  # the deserialized dict
        event['consumed_at'] = datetime.now().isoformat()  # stamp when we read it

        # conn.execute(sql, values_tuple) = run a parameterised SQL statement
        # → the VALUES (?, ?, ...) placeholders are filled in order by the tuple
        # → using ? prevents SQL injection
        conn.execute("""
            INSERT INTO delivery_events_stream
            (delivery_id, city, address_type, window, status, timestamp, order_value, attempt, consumed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event['delivery_id'], event['city'], event['address_type'],
            event['window'], event['status'], event['timestamp'],
            event['order_value'], event['attempt'], event['consumed_at']
        ))
        conn.commit()  # write each event to disk immediately

        count += 1
        # count % 10 == 0 uses the modulo operator: % gives the remainder after division
        # → e.g. 10 % 10 = 0, 20 % 10 = 0, 15 % 10 = 5
        # → so this is True only when count is a multiple of 10 (every 10th message)
        if count % 10 == 0:  # every 10 messages, print a live summary
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

except KeyboardInterrupt:  # user pressed Ctrl+C
    print(f"\nConsumed {count} messages. Stored in database.")
    conn.close()  # close the database connection cleanly
    consumer.close()  # close the Kafka consumer connection cleanly
```

---

## Step 8.5 — Run producer and consumer together

You need **two terminals** side by side in Codespaces. Open a second terminal with the `+` button in the terminal panel.

**Terminal 1 — start the producer:**
```bash
python src/kafka_producer.py
```

**Terminal 2 — start the consumer:**
```bash
python src/kafka_consumer.py
```

**What you will see:**
- Terminal 1 prints one line per event published — city, address type, status
- Terminal 2 prints a live FADR every 10 events
- Press `Ctrl+C` in each terminal to stop

---

## Step 8.6 — Key Kafka concepts for interviews

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

## Step 8.7 — Commit

```bash
git add src/kafka_producer.py src/kafka_consumer.py
git commit -m "Guide 08: Kafka producer and consumer for real-time delivery event streaming"
```

---

## Checkpoint

You now have:
- A Kafka producer simulating real delivery events
- A consumer reading and persisting them to SQLite
- Live FADR computed from the stream
- Understanding of topics, partitions, offsets, consumer groups

---

## Git Checkpoint — End of Guide 08

### Step G3 — Check what changed

```bash
git status
```
**What to look for:**
- `src/kafka_producer.py` and `src/kafka_consumer.py` listed as new files under "Untracked files"

### Step G4 — Review your changes

```bash
git diff --staged
```

### Step G5 — Stage your files

```bash
git add src/kafka_producer.py src/kafka_consumer.py
```

### Step G6 — Verify what is staged

```bash
git diff --staged
```

### Step G7 — Commit

```bash
git commit -m "Guide 08: Kafka producer and consumer for real-time delivery event streaming"
```

### Step G8 — Check your commit was saved

```bash
git log --oneline
```
Example output:
```
a1b2c3d Guide 08: Kafka producer and consumer for real-time delivery event streaming
8e9e2b0 Guide 07: Airflow DAG with Docker, all 5 tasks passing via sqlite3
fcf3d50 Replace dbt BashOperators with Python sqlite3 to avoid dbt version issues
```

### Step G9 — Push to GitHub

```bash
git push -u origin feature/guide-08-kafka
```

After pushing, go to your GitHub repository in the browser. You will see a yellow banner: **"feature/guide-08-kafka had recent pushes"**

### Step G10 — Raise a Pull Request on GitHub

**PR title:** `Guide 08: Kafka real-time delivery event streaming`

**PR description:**
```
- Added src/kafka_producer.py — publishes fake delivery events to Kafka at 2/sec
- Added src/kafka_consumer.py — reads from Kafka, stores events in SQLite, prints live FADR
- Kafka already running via docker-compose.yml (zookeeper + kafka + kafka-setup)
- delivery-events topic with 3 partitions, keyed by city
```

Steps in GitHub:
1. Click **Compare & pull request**
2. Check: **base:** `develop` ← **compare:** `feature/guide-08-kafka`
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
git branch -d feature/guide-08-kafka
```
```bash
git push origin --delete feature/guide-08-kafka
```

### Step G13 — Create the next guide's branch

```bash
git checkout -b feature/guide-09-spark
```

---

### What your GitHub looks like after this

- **Pull Requests tab** → one closed PR: `Guide 08: Kafka real-time delivery event streaming`
- **develop branch → commits** → your Guide 08 commit is in the history
- **Branches** → `feature/guide-08-kafka` is gone (deleted)

**Next:** [GUIDE_09_SPARK.md](GUIDE_09_SPARK.md) — Analyse delivery data at scale with PySpark
