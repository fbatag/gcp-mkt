import os

from googleapiclient.discovery import build
from utils import get_project_id

PROCUREMENT_API = 'cloudcommerceprocurement'
PROJECT_ID = get_project_id()
FAKE_API = os.environ.get("FAKE_API","").lower == "true"

class Procurement(object):
    """Utilities for interacting with the Procurement API."""

    def __init__(self, database):
        self.service = build(PROCUREMENT_API, 'v1', cache_discovery=False)
        print(f"SERVICE: {self.service}")
        self.database = database

    ##########################
    ### Account operations ###
    ##########################

    def _get_account_id(self, name):
        return name[len('providers/{}/accounts/'.format(PROJECT_ID)):]

    def _get_account_name(self, account_id):
        return 'providers/{}/accounts/{}'.format(PROJECT_ID,account_id)

    def get_account(self, account_id):
        """Gets an account from the Procurement Service."""
        name = self._get_account_name(account_id)
        request = self.service.providers().accounts().get(name=name)
        response = request.execute()
        return response

    def approve_account(self, account_id):
        """Approves the account in the Procurement Service."""
        name = self._get_account_name(account_id)
        request = self.service.providers().accounts().approve(
            name=name, body={'approvalName': 'signup'})
        request.execute()

    def handle_account_message(self, message):
        """Handles incoming Pub/Sub messages about account resources."""

        account_id = message['id']

        if FAKE_API:
            print("FAKING THE ACCOUNT QUERYING")
            account = "FAKE_ACCOUNT"
        else:
            print(f"QUERYING THE account_id {account_id}")
            account = self.get_account(account_id)
            
        customer = self.database.read(account_id)

        ############################## IMPORTANT ##############################
        ### In true integrations, Pub/Sub messages for new accounts should  ###
        ### be ignored. Account approvals are granted as a one-off action   ###
        ### during customer sign up. This codelab does not include the sign ###
        ### up flow, so it chooses to approve accounts here instead.        ###
        ### Production code for real, non-codelab services should never     ###
        ### blindly approve these. The following should be done as a result ###
        ### of a user signing up.                                           ###
        #######################################################################
        if account:
            approval = None
            for account_approval in account['approvals']:
                if account_approval['name'] == 'signup':
                    approval = account_approval
                    break

            if approval:
                if approval['state'] == 'PENDING':
                    # See above note. Actual production integrations should not
                    # approve blindly when receiving a message.
                    self.approve_account(account_id)

                elif approval['state'] == 'APPROVED':
                    # Now that it's approved, store a record in the database.
                    #internal_id = _generate_internal_account_id()
                    customer = {
                        'procurement_account_id': account_id,
                         #'internal_account_id': internal_id, I will use firestore ID
                        'products': {}
                    }
                    self.database.write(account_id, customer)
            else:
                # The account has been deleted, so delete the database record.
                if customer:
                    self.database.delete(account_id)

        # Always ack account messages. We only care about the above scenarios.
        return True

    ##############################
    ### Entitlement operations ###
    ##############################

    def _get_entitlement_name(self, entitlement_id):
        return 'providers/{}/entitlements/{}'.format(PROJECT_ID, entitlement_id)

    def get_entitlement(self, entitlement_id):
        """Gets an entitlement from the Procurement Service."""
        name = self._get_entitlement_name(entitlement_id)
        request = self.service.providers().entitlements().get(name=name)
        response = request.execute()
        return response

    def approve_entitlement(self, entitlement_id):
        """Approves the entitlement in the Procurement Service."""
        name = self._get_entitlement_name(entitlement_id)
        request = self.service.providers().entitlements().approve(
            name=name, body={})
        request.execute()

    def approve_entitlement_plan_change(self, entitlement_id, new_pending_plan):
        """Approves the entitlement plan change in the Procurement Service."""
        name = self._get_entitlement_name(entitlement_id)
        body = {'pendingPlanName': new_pending_plan}
        request = self.service.providers().entitlements().approvePlanChange(
            name=name, body=body)
        request.execute()

    def handle_active_entitlement(self, entitlement, customer, account_id):
        """Updates the database to match the active entitlement."""
        product = {
            'product_id': entitlement['product'],
            'plan_id': entitlement['plan'],
            'start_time': entitlement['createTime'],
        }

        if 'usageReportingId' in entitlement:
            product['consumer_id'] = entitlement['usageReportingId']

        customer['products'][entitlement['product']] = product

        ### TODO: Set up the service for the customer to use. ###
        self.database.write(account_id, customer)

    def handle_entitlement_message(self, message, event_type):
        """Handles incoming Pub/Sub messages about entitlement resources."""
        entitlement_id = message['id']

        entitlement = self.get_entitlement(entitlement_id)

        if not entitlement:
            # Do nothing. The entitlement has to be canceled to be deleted, so
            # this has already been handled by a cancellation message.
            return True

        account_id = self._get_account_id(entitlement['account'])
        customer = self.database.read(account_id)

        state = entitlement['state']

        if not customer:
            # If the record for this customer does not exist, don't ack the
            # message and wait until an account message is handled and a record
            # is created.
            return False

        if event_type == 'ENTITLEMENT_CREATION_REQUESTED':
            if state == 'ENTITLEMENT_ACTIVATION_REQUESTED':
                # Approve the entitlement and wait for another message for when
                # it becomes active before setting up the service for the
                # customer and updating our records.
                self.approve_entitlement(entitlement_id)
                return True

        elif event_type == 'ENTITLEMENT_ACTIVE':
            if state == 'ENTITLEMENT_ACTIVE':
                # Handle an active entitlement by writing to the database.
                self.handle_active_entitlement(entitlement, customer,
                                               account_id)
                return True

        elif event_type == 'ENTITLEMENT_PLAN_CHANGE_REQUESTED':
            if state == 'ENTITLEMENT_PENDING_PLAN_CHANGE_APPROVAL':
                # Don't write anything to our database until the entitlement
                # becomes active within the Procurement Service.
                self.approve_entitlement_plan_change(
                    entitlement_id, entitlement['newPendingPlan'])
                return True

        elif event_type == 'ENTITLEMENT_PLAN_CHANGED':
            if state == 'ENTITLEMENT_ACTIVE':
                # Handle an active entitlement after a plan change.
                self.handle_active_entitlement(entitlement, customer,
                                               account_id)
                return True

        elif event_type == 'ENTITLEMENT_PLAN_CHANGE_CANCELLED':
            # Do nothing. We approved the original change, but we never recorded
            # it or changed the service level since it hadn't taken effect yet.
            return True

        elif event_type == 'ENTITLEMENT_CANCELLED':
            if state == 'ENTITLEMENT_CANCELLED':
                # Clear out our records of the customer's plan.
                if entitlement['product'] in customer['products']:
                    del customer['products'][entitlement['product']]

                    ### TODO: Turn off customer's service. ###
                    self.database.write(account_id, customer)
                return True

        elif event_type == 'ENTITLEMENT_PENDING_CANCELLATION':
            # Do nothing. We want to cancel once it's truly canceled. For now
            # it's just set to not renew at the end of the billing cycle.
            return True

        elif event_type == 'ENTITLEMENT_CANCELLATION_REVERTED':
            # Do nothing. The service was already active, but now it's set to
            # renew automatically at the end of the billing cycle.
            return True

        elif event_type == 'ENTITLEMENT_DELETED':
            # Do nothing. The entitlement has to be canceled to be deleted, so
            # this has already been handled by a cancellation message.
            return True

        return False
