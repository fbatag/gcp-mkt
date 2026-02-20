
# Para rodar, use (não esqueça de criar um python env e instalar as reqs)
# python3 publish_message.py --type account
# python3 publish_message.py --type entitlement

{
  "eventId": "aaa12345",
  "providerId": "bataginpartnerdemotest",
  "account": {
    "id": "5752973e-25d1",
    "updateTime": "2026-02-20T15:01:23Z"
  }
}

import argparse
import json
import os
import uuid
from google.cloud import pubsub_v1

# Default values based on your project configuration
DEFAULT_PROJECT_ID = "mkt-demo-bra"
DEFAULT_TOPIC_ID = "mkt"

def publish_message(project_id, topic_id, message_type):
    """Publishes a message to a Pub/Sub topic."""
    
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    # Generate a random ID for the test
    test_id = str(uuid.uuid4())
    account_id = f"test-account-{test_id[:8]}"
    entitlement_id = f"test-entitlement-{test_id[:8]}"

    payload = {}

    if message_type == "account":
        # Structure based on app.py handle_account_message
        payload = {
            "account": {
                "id": account_id,
                "approvals": [
                    {
                        "name": "signup",
                        "state": "PENDING"
                    }
                ]
            }
        }
        print(f"Preparing Account message for account: {account_id}")

    elif message_type == "entitlement":
        # Structure based on app.py handle_entitlement_message
        payload = {
            "entitlement": {
                "id": entitlement_id,
                "account": f"providers/{project_id}/accounts/{account_id}",
                "product": "test-product",
                "plan": "test-plan",
                "state": "ENTITLEMENT_ACTIVATION_REQUESTED",
                "createTime": "2023-01-01T00:00:00Z"
            },
            "eventType": "ENTITLEMENT_CREATION_REQUESTED"
        }
        print(f"Preparing Entitlement message for entitlement: {entitlement_id}")
    
    else:
        print(f"Unknown message type: {message_type}")
        return

    # Data must be a bytestring
    data = json.dumps(payload).encode("utf-8")

    print(f"Publishing to topic: {topic_path}")
    
    # When you publish a message, the client returns a future.
    try:
        future = publisher.publish(topic_path, data)
        print(f"Published message ID: {future.result()}")
        print("Message payload:")
        print(json.dumps(payload, indent=2))
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Ensure you have set GOOGLE_APPLICATION_CREDENTIALS or run 'gcloud auth application-default login'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish test messages to Pub/Sub topic.")
    parser.add_argument("--project_id", default=DEFAULT_PROJECT_ID, help="Google Cloud Project ID")
    parser.add_argument("--topic_id", default=DEFAULT_TOPIC_ID, help="Pub/Sub Topic ID")
    parser.add_argument("--type", choices=["account", "entitlement"], default="account", help="Type of message to publish")

    args = parser.parse_args()

    publish_message(args.project_id, args.topic_id, args.type)
