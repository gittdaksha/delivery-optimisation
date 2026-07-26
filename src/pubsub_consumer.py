from google.cloud import pubsub_v1
import json
import os

PROJECT_ID       = os.environ["GCP_PROJECT_ID"]
TOPIC_ID         = "delivery-events"
SUBSCRIPTION_ID  = "delivery-analytics-sub"

subscriber        = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

try:
    topic_path = f"projects/{PROJECT_ID}/topics/{TOPIC_ID}"
    subscriber.create_subscription(
        request={"name": subscription_path, "topic": topic_path}
    )
    print(f"Created subscription: {subscription_path}")
except Exception:
    print(f"Subscription already exists: {subscription_path}")

def callback(message):
    event = json.loads(message.data.decode("utf-8"))
    print(f"  Received: {event[chr(39)+'city'+chr(39)]} | {event[chr(39)+'status'+chr(39)]} | {event[chr(39)+'timestamp'+chr(39)]}")
    message.ack()

print("Listening for messages...")
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

try:
    streaming_pull_future.result(timeout=30)
except Exception:
    streaming_pull_future.cancel()
    print("Done.")
