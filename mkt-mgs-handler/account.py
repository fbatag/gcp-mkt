
class Account(object):

    def __init__(self, proc_api, database):
        self.proc_api = proc_api
        self.database = database

    def get_account(self, account_id):
        response = self.proc_api.get_account(account_id)
        return response
    
    def approve_account(self, account_id):
        self.proc_api.approve_account(account_id)

    def handle_account_message(self, message):
        """Handles incoming Pub/Sub messages about account resources."""

        account_id = message['id']
        print(f"QUERYING THE account_id {account_id}")
        account = self.get_account(account_id)
            
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
                        'name': account['name'],
                        'createTime': account['createTime'],
                        'updateTime': account['updateTime'],
                        #'procurement_account_id': account_id,
                        #'internal_account_id': internal_id, I will use firestore ID
                        'products': {}
                    }
                    self.database.write(account_id, customer)

        if not account or not approval:
            # The account has been deleted, so delete the database record.
            customer = self.database.read(account_id)
            if customer:
                self.database.delete(account_id)