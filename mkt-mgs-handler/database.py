from google.cloud import firestore

class FirestoreDatabase(object):
    """Firestore-based implementation of the database."""

    def __init__(self):
        self.db = firestore.Client()
        self.collection_name = 'customers'

    def read(self, key):
        """Read the record with the given key from the database, if it exists."""
        doc_ref = self.db.collection(self.collection_name).document(key)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    def write(self, key, value):
        """Write the record with the given key to the database."""
        doc_ref = self.db.collection(self.collection_name).document(key)
        doc_ref.set(value)

    def delete(self, key):
        """Delete the record with the given key from the database, if it exists."""
        doc_ref = self.db.collection(self.collection_name).document(key)
        doc_ref.delete()

    def items(self):
        """Provides a way to iterate over all elements in the database."""
        # This matches the behavior of dict.items() which returns (key, value) tuples
        docs = self.db.collection(self.collection_name).stream()
        for doc in docs:
            yield (doc.id, doc.to_dict())
