from googleapiclient.discovery import build
PROCUREMENT_API = 'cloudcommerceprocurement'

class ProcurementAPI(object):
    """Utilities for interacting with the Procurement API."""

    def __init__(self, provider):
        self.service = build(PROCUREMENT_API, 'v1', cache_discovery=False)
        self.provider = provider
        print(f"SERVICE: {self.service}")

    def _get_account_id(self, name):
        return name[len('providers/{}/accounts/'.format(self.provider)):]

    def _get_account_name(self, account_id):
        return 'providers/{}/accounts/{}'.format(self.provider,account_id)

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
        return 'providers/{}/entitlements/{}'.format(self.provider, entitlement_id)

    def get_entitlement(self, entitlement_id):
        """Gets an entitlement from the Procurement Service."""
        name = self._get_entitlement_name(entitlement_id)
        request = self.service.providers().entitlements().get(name=name)
        response = request.execute()
        response['account_id'] = self._get_account_id(response['account'])
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