
class Entitlement(object):

    def __init__(self, proc_api, database):
        self.proc_api = proc_api
        self.database = database

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

        entitlement = self.proc_api.get_entitlement(entitlement_id)

        if not entitlement:
            # Do nothing. The entitlement has to be canceled to be deleted, so
            # this has already been handled by a cancellation message.
            return True

        account_id = entitlement['account_id']
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