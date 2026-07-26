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

        # Inline if-else: value_if_true  if  condition  else  value_if_false
        # → "✓" if DELIVERED, "✗" if FAILED or RESCHEDULED, "→" for anything else
        symbol = "✓" if status == "DELIVERED" else ("✗" if status in ["FAILED", "RESCHEDULED"] else "→")
        # f-string format specs keep columns aligned:
        # {count:04d} = integer padded to 4 digits: 1→0001, 42→0042
        # {city:12s}  = string padded to 12 characters wide
        print(f"[{count:04d}] {symbol} {city:12s} | {address_type:18s} | {status}")

        time.sleep(0.5)  # wait 0.5 seconds = 2 events per second

except KeyboardInterrupt:  # user pressed Ctrl+C
    print(f"\nStopped. Published {count} events.")
    producer.flush()  # send any messages still buffered in memory before closing
    producer.close()  # close the connection to Kafka cleanly
