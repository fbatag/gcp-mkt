import functions_framework
import base64
import json
import pprint
import traceback

from procurement_api import ProcurementAPI
from account import Account
from entitlement import Entitlement
from database import FirestoreDatabase

from utils import get_project_id
PROJECT_ID = get_project_id()

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def mkt_msg_handler(cloud_event):
    # Print out the data from Pub/Sub, to prove that it worked
    try:
        data = base64.b64decode(cloud_event.data["message"]["data"])
        payload = json.loads(data)
        print("MESSAGE RECEIVED")
        #print(json.dumps(payload, indent=2, ensure_ascii=False))
        pprint.pprint(payload)
        print(payload)

    # Construct a service for the Partner Procurement API.
        api = ProcurementAPI(provider=PROJECT_ID)
        database = FirestoreDatabase()
        account = Account(api, database)
        entitlement = Entitlement(api, database)

        if 'entitlement' in payload:
            entitlement.handle_entitlement_message(payload['entitlement'], payload['eventType'])
        elif 'account' in payload:
            account.handle_account_message(payload['account'])
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
    return ("", 204)
