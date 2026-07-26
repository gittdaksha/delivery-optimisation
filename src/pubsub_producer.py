from google.cloud import pubsub_v1
import json, os, random
from datetime import datetime

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
TOPIC_ID = "delivery-events"
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

try:
    publisher.create_topic(request={"name": topic_path})
    print(f"Created topic: {topic_path}")
except Exception:
    print(f"Topic already exists: {topic_path}")

CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Pune"]
for i in range(20):
    event = {"delivery_id": f"D{i:04d}", "city": random.choice(CITIES), "status": random.choice(["DELIVERED", "FAILED", "IN_TRANSIT"]), "timestamp": datetime.now().isoformat()}
    data = json.dumps(event).encode("utf-8")
    future = publisher.publish(topic_path, data=data)
    print(f"  Published message id: {future.result()}")
print("Done publishing.")
