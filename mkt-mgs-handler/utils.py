import os
from google.cloud import storage

def get_project_id():
    # Try environment variable first
    project_id = os.environ.get("PROJECT_ID")
    if project_id:
        return project_id

    # Try to get from GCS Client
    client = storage.Client()
    return client.project
