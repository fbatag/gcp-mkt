
# Para rodar, use (não esqueça de criar um python env e instalar as reqs)
# python3 publish_message.py --type account
# python3 publish_message.py --type entitlement

{
  "eventId": "1",
  "providerId": "partnerdemotest",
  "account": {
    "id": "5752973e-25d1",
    "updateTime": "2026-02-20T15:01:23Z"
  }
}

import argparse
import json
import uuid
from datetime import datetime, timezone
from google.cloud import pubsub_v1

# Default values based on your project configuration
DEFAULT_PROJECT_ID = "mkt-demo-bra"
DEFAULT_TOPIC_ID = "mkt"

def publish_message(project_id, topic_id, message_type):
    """Publishes a message to a Pub/Sub topic."""
    
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    # Generate a random ID for the test
    account_id = str(uuid.uuid4())
    entitlement_id = str(uuid.uuid4())

    payload = {}

    if message_type == "account":
        # Structure based on: https://docs.cloud.google.com/marketplace/docs/partners/integrated-saas/manage-user-accounts#create-account
        payload = {
            "eventId": "123",
            "providerId": "bataginpartnerdemotest", # = PARTNER_ID atribuido pelo Mkt e vem nas mensagens - provavelmente o nome do partner - meio menuemonico - mesmo que é usado na submissão ao aceddo do Producer
            "account": {
                "id": account_id,
                "updateTime": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), #isoformat(),
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
        #  Structure based on: https://docs.cloud.google.com/marketplace/docs/partners/integrated-saas/manage-entitlements#approve_an_entitlement
        payload = {
            "eventId": "aaa12345",
            "eventType": "ENTITLEMENT_CREATION_REQUESTED",
            "entitlement": {
                "id": entitlement_id,
                "account": f"providers/{project_id}/accounts/{account_id}", # no doc não diz que vem a account na mensagem
                "updateTime": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), #isoformat(),
                "product": "test-product",
                "plan": "test-plan",
                "newOfferDuration": "P2Y3M",
                "state": "ENTITLEMENT_ACTIVATION_REQUESTED",
                "createTime": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), #isoformat(),
            }
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
