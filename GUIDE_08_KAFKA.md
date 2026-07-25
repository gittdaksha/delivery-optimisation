# Guide 08 — Real-Time Delivery Events with Apache Kafka

**Goal:** Simulate a real-time stream of delivery status events using Apache Kafka. Understand producers, consumers, and topics — then see how real-time data differs from batch processing.

**Why this guide exists:** All the previous guides process data in batches — run a script, process 50,000 rows, done. Kafka handles real-time data — events arriving continuously, like a delivery status updating every second. This is how companies like Swiggy and Zomato track live delivery status. It is a separate skill from batch processing and appears on senior DE job descriptions.

---

## Exact steps to follow in order

**In Codespaces terminal:**

```bash
git checkout develop
git pull origin develop
git checkout -b feature/guide-08-kafka
```
**What this does:**
- `git checkout develop` — switches you to the develop branch first
- `git pull origin develop` — downloads the latest changes from GitHub so you are not working on stale code
- `git checkout -b feature/guide-08-kafka` — creates a new branch for this guide's work
- `-b` = create AND switch in one command; without it Git would error because the branch does not exist yet
- You always create feature branches FROM develop — never from main, never from another feature branch

```bash
docker compose up -d
```
**What this does:**
- Reads `docker-compose.yml` and starts all 7 services: Zookeeper, Kafka, kafka-setup, Postgres, airflow-init, airflow-webserver, airflow-scheduler
- `-d` = detached mode: containers run in the background and you get your terminal back immediately
- Without `-d` your terminal would be locked showing all logs and closing it would stop all containers

```bash
docker ps
```
**What this does:**
- Lists every running container and its status
- What you should see:
  - `zookeeper` — Up
  - `kafka` — Up, port 9092 mapped
  - `kafka-setup` — Exited (0) — correct, it ran once to create the topic then stopped
  - `postgres` — Up (healthy)
  - `airflow-init` — Exited (0) — correct, it ran once to set up the database then stopped
  - `airflow-webserver` — Up
  - `airflow-scheduler` — Up
- If kafka is not in the list, wait 1 more minute and run `docker ps` again

```bash
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```
**What this does:**
- `docker exec kafka` — run a command inside the running `kafka` container
- `kafka-topics --list` — list all topics that exist on this Kafka broker
- `--bootstrap-server localhost:9092` — the address of the Kafka broker to connect to
- You should see `delivery-events` in the output — this was created by the `kafka-setup` container on startup
- If you see nothing, the kafka-setup container may have failed — check with `docker logs kafka-setup`

```bash
pip install kafka-python-ng
```
**What this does:**
- Installs the Python library for Kafka in your Codespaces environment
- `kafka-python-ng` is the maintained fork of `kafka-python` — it supports Python 3.12 which is what Codespaces uses
- The original `kafka-python==2.0.2` has a bug with Python 3.12 (`kafka.vendor.six.moves` missing) — `kafka-python-ng` fixes this
- The import in your scripts stays exactly the same: `from kafka import KafkaProducer` / `from kafka import KafkaConsumer`
- This installs in Codespaces, not inside the Docker containers — your Python scripts run in Codespaces and connect to the Kafka container via port 9092

**Step 6 — create `src/kafka_producer.py`**

**What `src/kafka_producer.py` does and why it exists:**
- **What it does:** Simulates a delivery partner's app publishing live status updates — one event every 0.5 seconds — into the Kafka `delivery-events` topic
- **Why separate from the consumer:** In a real system the producer (delivery partner's app) and consumer (analytics system) are completely separate services run by different teams — they never talk to each other directly, only through Kafka. Keeping them in separate files mirrors that real-world separation
- **Input:** No file — events are generated in memory using `random` and `Faker`
- **Output:** Kafka topic `delivery-events` — a continuous stream of JSON messages
- **Pipeline position:** Kafka broker running → **this script** → events queue up in the topic → consumer reads them

Run this command in Codespaces to create the file:

```bash
cat > src/kafka_producer.py << 'ENDOFFILE'
import json          # converts Python dicts to JSON strings for Kafka
import time          # used for time.sleep to control how fast events are sent
import random        # used to randomly pick cities, statuses, address types
from kafka import KafkaProducer   # Kafka client — lets Python publish messages
from faker import Faker           # generates realistic fake data (UUIDs, names)
from datetime import datetime     # used to timestamp each event

fake = Faker('en_IN')  # Indian locale — gives realistic Indian-style data

# Lists to randomly pick from — mirrors real delivery data categories
CITIES        = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Pune', 'Chennai']
ADDRESS_TYPES = ['Apartment', 'PG/Hostel', 'House', 'Office', 'Gated Community']
WINDOWS       = ['Morning (9-12)', 'Afternoon (12-15)', 'Evening (15-19)', 'Night (19-22)']
STATUSES      = ['PICKED_UP', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED', 'RESCHEDULED']

# KafkaProducer connects to the Kafka broker and prepares to publish messages
# bootstrap_servers='localhost:9092' — the port mapped by docker-compose.yml
#   when your script connects to localhost:9092, Docker routes it to the kafka container
# value_serializer — Kafka only transmits raw bytes, not Python objects
#   lambda v: json.dumps(v).encode('utf-8') means:
#   → json.dumps(v) converts your dict to a JSON string: {'city':'Mumbai'} → '{"city":"Mumbai"}'
#   → .encode('utf-8') converts that string to bytes: '{"city":"Mumbai"}' → b'{"city":"Mumbai"}'
# key_serializer — the routing key also needs to be bytes
#   lambda k: k.encode('utf-8') converts string 'Mumbai' → bytes b'Mumbai'
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8')
)

print("Producing delivery events to Kafka topic 'delivery-events'...")
print("Press Ctrl+C to stop.\n")

count = 0  # tracks how many events have been published
try:
    while True:  # runs forever until you press Ctrl+C
        city         = random.choice(CITIES)        # pick a random city for this event
        address_type = random.choice(ADDRESS_TYPES) # pick a random address type
        status       = random.choice(STATUSES)      # pick a random delivery status

        # Build the event dict — one delivery status update
        event = {
            "delivery_id":  fake.uuid4(),                        # unique ID for this delivery
            "city":         city,                                 # city of the delivery
            "address_type": address_type,                        # type of address
            "window":       random.choice(WINDOWS),              # delivery time window
            "status":       status,                              # current delivery status
            "timestamp":    datetime.now().isoformat(),          # exact time of this event
            "order_value":  round(random.uniform(150, 8000), 2), # order value in rupees
            "attempt":      random.randint(1, 3),                # which attempt this is
        }

        # producer.send() publishes one message to Kafka
        # topic='delivery-events' — which Kafka channel to write to
        # key=city — routing key: same city always goes to the same partition
        #   this guarantees all Mumbai events are in order relative to each other
        # value=event — the Python dict; value_serializer converts it to bytes automatically
        # .send() is asynchronous — it queues the message; producer.flush() forces it out
        producer.send(topic='delivery-events', key=city, value=event)

        count += 1  # increment the published event count

        # Print one status line per event so you can watch events flow
        # Inline if-else: value_if_true  if  condition  else  value_if_false
        # → "✓" if DELIVERED, "✗" if FAILED or RESCHEDULED, "→" for anything else
        symbol = "✓" if status == "DELIVERED" else ("✗" if status in ["FAILED", "RESCHEDULED"] else "→")
        # f-string format specs keep columns aligned:
        # {count:04d} = integer padded to 4 digits: 1→0001, 42→0042
        # {city:12s}  = string padded to 12 characters wide
        print(f"[{count:04d}] {symbol} {city:12s} | {address_type:18s} | {status}")

        time.sleep(0.5)  # wait 0.5 seconds before the next event = 2 events per second

except KeyboardInterrupt:  # user pressed Ctrl+C
    print(f"\nStopped. Published {count} events.")
    producer.flush()  # send any messages still buffered in memory before closing
    producer.close()  # close the connection to Kafka cleanly
ENDOFFILE
```

**What the command `cat > src/kafka_producer.py << 'ENDOFFILE' ... ENDOFFILE` does:**
- `cat >` — write output to a file (overwrites if file already exists)
- `<< 'ENDOFFILE'` — heredoc: everything typed until the word `ENDOFFILE` is the content
- This creates the file in one command without opening a text editor

---

**Step 7 — create `src/kafka_consumer.py`**

**What `src/kafka_consumer.py` does and why it exists:**
- **What it does:** Reads every event from the Kafka `delivery-events` topic and writes each one into a SQLite table, printing a live FADR every 10 events
- **Why separate:** Any service that needs the event data should read independently at its own pace — a separate consumer file means if the consumer crashes, the producer keeps running and events queue safely in Kafka until the consumer restarts
- **Input:** Kafka topic `delivery-events` — the stream published by `kafka_producer.py`
- **Output:** `data/delivery_db.sqlite` — `delivery_events_stream` table, one row per event
- **Pipeline position:** Producer publishing events → **this script** → events stored in SQLite

```bash
cat > src/kafka_consumer.py << 'ENDOFFILE'
import json          # parses incoming JSON bytes back into Python dicts
import sqlite3       # built-in Python library to write events to SQLite
from kafka import KafkaConsumer   # Kafka client — lets Python read messages
from datetime import datetime     # used to record when each event was consumed

DB_PATH = 'data/delivery_db.sqlite'  # path to the project database

# Open (or create) the SQLite database and create the events table
conn = sqlite3.connect(DB_PATH)
# CREATE TABLE IF NOT EXISTS — safe to run every time; no error if table already exists
conn.execute("""
    CREATE TABLE IF NOT EXISTS delivery_events_stream (
        delivery_id  TEXT,    -- unique ID for each delivery
        city         TEXT,    -- city of the delivery
        address_type TEXT,    -- type of address (Apartment, Office, etc.)
        window       TEXT,    -- delivery time window
        status       TEXT,    -- DELIVERED, FAILED, IN_TRANSIT, etc.
        timestamp    TEXT,    -- when the event occurred (from the producer)
        order_value  REAL,    -- value of the order in rupees
        attempt      INTEGER, -- which delivery attempt this is
        consumed_at  TEXT     -- when THIS consumer read the event from Kafka
    )
""")
conn.commit()  # write the CREATE TABLE to disk

# KafkaConsumer connects to Kafka and prepares to read messages
# 'delivery-events' — the name of the topic to read from
# bootstrap_servers='localhost:9092' — same mapped port as the producer
# value_deserializer — the REVERSE of the producer's value_serializer:
#   lambda m: json.loads(m.decode('utf-8')) means:
#   → m.decode('utf-8') converts bytes back to a string: b'{"city":"Mumbai"}' → '{"city":"Mumbai"}'
#   → json.loads(...) converts that string back to a dict: '{"city":"Mumbai"}' → {'city':'Mumbai'}
# auto_offset_reset='earliest' — an offset is the position of a message in a partition
#   'earliest' means: if this consumer has never run before, start from the very first message
#   'latest' would mean: only read new messages arriving from now
# group_id='delivery-analytics' — Kafka tracks how far this consumer group has read
#   if you restart this script, it picks up where it left off — no duplicate reads
consumer = KafkaConsumer(
    'delivery-events',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='delivery-analytics',
)

print("Consuming from 'delivery-events'... (Ctrl+C to stop)")

count = 0  # tracks how many messages have been consumed
try:
    # 'for message in consumer' — the consumer is iterable
    # each iteration blocks until the next message arrives from Kafka
    # this loop runs FOREVER — it never exits on its own (press Ctrl+C to stop)
    # message has attributes: .value (the payload), .key, .topic, .partition, .offset
    for message in consumer:
        event = message.value  # already a Python dict — value_deserializer ran automatically

        event['consumed_at'] = datetime.now().isoformat()  # stamp when we read it

        # INSERT one row into SQLite for this event
        # VALUES (?, ?, ...) — ? placeholders are filled in order by the tuple below
        # using ? instead of f-strings prevents SQL injection attacks
        conn.execute("""
            INSERT INTO delivery_events_stream
            (delivery_id, city, address_type, window, status, timestamp, order_value, attempt, consumed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event['delivery_id'], event['city'], event['address_type'],
            event['window'], event['status'], event['timestamp'],
            event['order_value'], event['attempt'], event['consumed_at']
        ))
        conn.commit()  # write each event to disk immediately (not batched)

        count += 1  # increment consumed message count

        # count % 10 == 0 uses the modulo operator
        # % gives the remainder after division: 10%10=0, 20%10=0, 15%10=5
        # so this is True only every 10th message
        if count % 10 == 0:
            # Query the live FADR from all terminal events seen so far
            # CASE WHEN status='DELIVERED' THEN 1.0 ELSE 0.0 END
            #   → assigns 1.0 for delivered, 0.0 for everything else
            # AVG of 1s and 0s = success rate as a decimal; *100 = percentage
            # Only count terminal statuses (final outcomes) — not in-progress ones
            cur = conn.execute("""
                SELECT ROUND(AVG(CASE WHEN status='DELIVERED' THEN 1.0 ELSE 0.0 END)*100, 1),
                       COUNT(*)
                FROM delivery_events_stream
                WHERE status IN ('DELIVERED','FAILED','RESCHEDULED')
            """)
            row = cur.fetchone()  # fetchone() returns one row as a tuple: (fadr, count)
            if row[0]:  # row[0] is None if no terminal events yet — only print when data exists
                print(f"  Live FADR: {row[0]}%  |  Total terminal events: {row[1]}")

except KeyboardInterrupt:  # user pressed Ctrl+C
    print(f"\nConsumed {count} messages. Stored in database.")
    conn.close()     # close the database connection cleanly
    consumer.close() # close the Kafka connection cleanly
ENDOFFILE
```

**Step 8 — open a second terminal and run producer and consumer side by side**

In Codespaces: click the **+** icon in the terminal panel to open a second terminal.
In VS Code desktop: press **Ctrl+Shift+`** to open a new terminal.

You now have two terminals. Keep them side by side.

**Terminal 1 — start the producer:**
```bash
python src/kafka_producer.py
```
**What you will see:**
- One line printed every 0.5 seconds — city, address type, and delivery status
- `✓` = DELIVERED, `✗` = FAILED or RESCHEDULED, `→` = in-progress status
- This simulates a delivery partner's app sending status updates in real time

**Terminal 2 — start the consumer:**
```bash
python src/kafka_consumer.py
```
**What you will see:**
- The consumer reads every event the producer publishes
- Every 10 events it prints a live FADR percentage — the percentage of terminal events (DELIVERED/FAILED/RESCHEDULED) that were successful
- Each event is also written to `data/delivery_db.sqlite` in the `delivery_events_stream` table

**Why two terminals:**
- Producer and consumer run at the same time but independently
- This is exactly how a real system works — the delivery app (producer) runs on the partner's phone, the analytics system (consumer) runs on a server — they never talk to each other directly, only through Kafka

**To stop:** Press `Ctrl+C` in Terminal 1 first, then `Ctrl+C` in Terminal 2.

```bash
# Step 9 — stage, commit and push
git add src/kafka_producer.py src/kafka_consumer.py
git commit -m "Guide 08: Kafka producer and consumer for real-time delivery event streaming"
git push -u origin feature/guide-08-kafka
```
**What this does:**
- `git add` — stages both new files for the commit
- `git commit` — saves a permanent snapshot with a descriptive message
- `git push -u origin feature/guide-08-kafka` — uploads the branch to GitHub for the first time
- `-u` sets the upstream link so future pushes on this branch only need `git push`

**Step 10 — raise the PR on GitHub**

- Go to your GitHub repository in the browser
- You will see a yellow banner: **"feature/guide-08-kafka had recent pushes"**
- Click **Compare & pull request**
- Check: **base:** `develop` ← **compare:** `feature/guide-08-kafka`
- Title: `Guide 08: Kafka real-time delivery event streaming`
- Description:
```
- Added src/kafka_producer.py — publishes fake delivery events to Kafka at 2/sec
- Added src/kafka_consumer.py — reads from Kafka, stores events in SQLite, prints live FADR
- Kafka running via docker-compose.yml (zookeeper + kafka + kafka-setup)
- delivery-events topic with 3 partitions, keyed by city
```
- Click **Create pull request** → **Merge pull request** → **Confirm merge**

**Step 11 — pull merged changes and clean up**

```bash
git checkout develop
git pull origin develop
git branch -d feature/guide-08-kafka
git push origin --delete feature/guide-08-kafka
```
**What this does:**
- `git checkout develop` — switches back to develop
- `git pull origin develop` — brings the merged PR down to your local machine
- `git branch -d feature/guide-08-kafka` — deletes the branch locally (safe — it is already merged)
- `git push origin --delete feature/guide-08-kafka` — deletes the branch on GitHub too
- Merged branches are always deleted — a clean repo is a professional habit

**Step 12 — create the next guide's branch**

```bash
git checkout -b feature/guide-09-ml
```

You are now on a fresh branch, ready for Guide 09.

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
