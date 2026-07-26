from google.cloud import pubsub_v1  # Pub/Sub client library
import json  # convert Python dict to JSON string
import os  # read environment variables
from datetime import datetime  # get current timestamp
import random  # pick random city and status

PROJECT_ID = os.environ["GCP_PROJECT_ID"]  # read project ID (set with export command)
TOPIC_ID   = "delivery-events"  # name of the Pub/Sub topic to publish to

publisher  = pubsub_v1.PublisherClient()  # create an authenticated publisher client
# topic_path() is a helper method that builds the full resource path string
# → result: "projects/my-project-123/topics/delivery-events"
# GCP APIs require this full path format; you cannot just pass "delivery-events"
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)  # build full topic resource path

# Create topic if it doesn't exist
try:
    publisher.create_topic(request={"name": topic_path})  # try to create the topic
    print(f"Created topic: {topic_path}")
except Exception:  # topic already exists — that's fine, continue
    print(f"Topic already exists: {topic_path}")

CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Pune']  # list to pick from randomly

for i in range(20):  # publish 20 test events
    event = {
        # f"D{i:04d}" = f-string with :04d format spec
        # :04d = integer, minimum 4 digits, zero-padded on the left
        # → i=1 gives "D0001", i=42 gives "D0042", i=1000 gives "D1000"
        "delivery_id": f"D{i:04d}",  # e.g. D0001, D0002 — zero-padded 4 digits
        "city":        random.choice(CITIES),  # random city from the list
        "status":      random.choice(["DELIVERED", "FAILED", "IN_TRANSIT"]),  # random status
        # datetime.now().isoformat() = current time as a standardised string
        # → e.g. "2024-03-15T14:23:07.123456"  (ISO 8601 format)
        "timestamp":   datetime.now().isoformat(),  # current time as ISO string
    }

    # Pub/Sub requires bytes — encode the JSON
    # json.dumps(event) = Python dict → JSON string: '{"delivery_id": "D0001", ...}'
    # .encode("utf-8") = JSON string → bytes: b'{"delivery_id": "D0001", ...}'
    data = json.dumps(event).encode("utf-8")  # dict → JSON string → bytes

    # publish() is non-blocking — returns a Future
    future = publisher.publish(topic_path, data=data)  # send message to Pub/Sub
    # future.result() blocks until Pub/Sub confirms receipt and returns the message ID
    print(f"  Published message id: {future.result()}")  # .result() waits and returns message ID

print("Done publishing.")
