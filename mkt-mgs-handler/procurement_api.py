from googleapiclient.discovery import build
from utils import get_project_id
PROJECT_ID = get_project_id()
PROCUREMENT_API = 'cloudcommerceprocurement'

class ProcurementAPI(object):
    """Utilities for interacting with the Procurement API."""

    def __init__(self):
        self.service = build(PROCUREMENT_API, 'v1', cache_discovery=False)
        print(f"SERVICE: {self.service}")

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