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
#   'earliest' = if this consumer has never run before, start from the very first message ever
#   'latest'   = only read new messages arriving from now
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
    for message in consumer:
        event = message.value  # already a Python dict — value_deserializer ran automatically

        event['consumed_at'] = datetime.now().isoformat()  # stamp when we read it

        # INSERT one row into SQLite for this event
        # VALUES (?, ?, ...) — ? placeholders are filled by the tuple below, in order
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

        count += 1

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
            row = cur.fetchone()  # returns one row as a tuple: (fadr_value, total_count)
            if row[0]:  # row[0] is None if no terminal events yet — only print when data exists
                print(f"  Live FADR: {row[0]}%  |  Total terminal events: {row[1]}")

except KeyboardInterrupt:  # user pressed Ctrl+C
    print(f"\nConsumed {count} messages. Stored in database.")
    conn.close()     # close the database connection cleanly
    consumer.close() # close the Kafka connection cleanly
