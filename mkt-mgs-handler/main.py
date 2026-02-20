import functions_framework
import base64
import json
import pprint
import traceback

from googleapiclient.discovery import build
from procurement import Procurement
from database import FirestoreDatabase
   
# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def mkt_msg_handler(cloud_event):
    # Print out the data from Pub/Sub, to prove that it worked
    try:
        data = base64.b64decode(cloud_event.data["message"]["data"])
        payload = json.loads(data)
        print("MESSAGE RECEIVED")
        #print(payload['entitlement']['id'])
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        pprint.pprint(payload)

    # Construct a service for the Partner Procurement API.
        database = FirestoreDatabase()
        procurement = Procurement(database)

        if 'entitlement' in payload:
            procurement.handle_entitlement_message(payload['entitlement'], payload['eventType'])
        elif 'account' in payload:
            procurement.handle_account_message(payload['account'])
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
    return ("", 204)
