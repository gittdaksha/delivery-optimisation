from google.cloud import pubsub_v1  # Pub/Sub client library
import json  # parse JSON bytes back to a Python dict
import os  # read environment variables

PROJECT_ID       = os.environ["GCP_PROJECT_ID"]  # read project ID from environment
TOPIC_ID         = "delivery-events"  # topic name to subscribe to
SUBSCRIPTION_ID  = "delivery-analytics-sub"  # subscription name (each subscriber has its own)

subscriber       = pubsub_v1.SubscriberClient()  # create authenticated subscriber client
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)  # full resource path

# Create subscription if needed
try:
    topic_path = f"projects/{PROJECT_ID}/topics/{TOPIC_ID}"  # full topic path string
    subscriber.create_subscription(
        request={"name": subscription_path, "topic": topic_path}  # link subscription to topic
    )
    print(f"Created subscription: {subscription_path}")
except Exception:  # subscription already exists — continue
    print(f"Subscription already exists: {subscription_path}")

# callback is a function passed as an argument to subscriber.subscribe()
# Pub/Sub calls this function automatically whenever a new message arrives
# you do not call callback() yourself — the subscriber library calls it for you
def callback(message):  # called automatically for each message received
    # message.data is bytes; .decode("utf-8") converts bytes → string
    # json.loads() converts the JSON string → Python dict so you can use ['city'] etc.
    event = json.loads(message.data.decode("utf-8"))  # bytes → string → Python dict
    print(f"  Received: {event['city']} | {event['status']} | {event['timestamp']}")
    # message.ack() = "I have processed this message successfully"
    # without ack(), Pub/Sub re-delivers the message after a timeout (it assumes failure)
    message.ack()   # acknowledge — tells Pub/Sub this message was processed

print("Listening for messages...")
# subscriber.subscribe() starts a background thread that listens for messages
# callback=callback passes your function so the library knows what to call per message
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)  # start listening

try:
    # .result(timeout=30) = wait here for up to 30 seconds
    # if no messages arrive within 30s, a TimeoutError is raised → caught by except below
    streaming_pull_future.result(timeout=30)  # listen for up to 30 seconds then stop
except Exception:
    # .cancel() tells the background thread to stop pulling messages and clean up
    streaming_pull_future.cancel()  # cleanly stop the streaming pull
    print("Done.")
