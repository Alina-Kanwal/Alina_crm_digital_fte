import httpx
import os
import json
from dotenv import load_dotenv

# Load from the new env file
load_dotenv(".env.back4app")

APP_ID = os.getenv("BACK4APP_APP_ID")
MASTER_KEY = os.getenv("BACK4APP_MASTER_KEY")
API_URL = os.getenv("BACK4APP_API_URL", "https://parseapi.back4app.com")

HEADERS = {
    "X-Parse-Application-Id": APP_ID,
    "X-Parse-Master-Key": MASTER_KEY,
    "Content-Type": "application/json"
}

def create_class(class_name, schema):
    print(f"Creating class {class_name}...")
    url = f"{API_URL}/schemas/{class_name}"
    
    # Check if class exists
    try:
        response = httpx.get(url, headers=HEADERS)
        if response.status_code == 200:
            print(f"  Class {class_name} already exists. Updating schema...")
            # For update, we use PUT and we don't send existing fields
            # But for simplicity in this script, we'll just try to POST first
            pass
    except Exception as e:
        print(f"  Error checking class: {e}")

    # Create class
    response = httpx.post(f"{API_URL}/schemas/{class_name}", headers=HEADERS, json=schema)
    if response.status_code in [200, 201]:
        print(f"  Successfully created {class_name}")
    else:
        print(f"  Error creating {class_name}: {response.text}")

def setup_schema():
    # Customer Class
    create_class("Customer", {
        "className": "Customer",
        "fields": {
            "email": {"type": "String"},
            "phone": {"type": "String"},
            "firstName": {"type": "String"},
            "lastName": {"type": "String"},
            "leadScore": {"type": "Number"},
            "sessionIds": {"type": "Array"},
            "embedding": {"type": "Array"},
            "metadata": {"type": "Object"},
            "isActive": {"type": "Boolean"}
        }
    })

    # Deal Class
    create_class("Deal", {
        "className": "Deal",
        "fields": {
            "title": {"type": "String"},
            "description": {"type": "String"},
            "amount": {"type": "Number"},
            "stage": {"type": "String"},
            "customer": {"type": "Pointer", "targetClass": "Customer"},
            "owner": {"type": "Pointer", "targetClass": "_User"}
        }
    })

    # Task Class
    create_class("Task", {
        "className": "Task",
        "fields": {
            "title": {"type": "String"},
            "description": {"type": "String"},
            "isCompleted": {"type": "Boolean"},
            "dueDate": {"type": "Date"},
            "customer": {"type": "Pointer", "targetClass": "Customer"},
            "deal": {"type": "Pointer", "targetClass": "Deal"},
            "assignedTo": {"type": "Pointer", "targetClass": "_User"}
        }
    })

    # ConversationThread Class
    create_class("ConversationThread", {
        "className": "ConversationThread",
        "fields": {
            "customer": {"type": "Pointer", "targetClass": "Customer"},
            "threadId": {"type": "String"},
            "channel": {"type": "String"},
            "startedAt": {"type": "Date"},
            "lastActivity": {"type": "Date"},
            "isActive": {"type": "Boolean"}
        }
    })

    # Message Class
    create_class("Message", {
        "className": "Message",
        "fields": {
            "thread": {"type": "Pointer", "targetClass": "ConversationThread"},
            "content": {"type": "String"},
            "channel": {"type": "String"},
            "direction": {"type": "String"},
            "sentiment": {"type": "String"},
            "sentimentScore": {"type": "Number"},
            "timestamp": {"type": "Date"}
        }
    })

    # AuditLog Class
    create_class("AuditLog", {
        "className": "AuditLog",
        "fields": {
            "actionType": {"type": "String"},
            "message": {"type": "String"},
            "entityId": {"type": "String"},
            "entityType": {"type": "String"}
        }
    })

if __name__ == "__main__":
    if not APP_ID or not MASTER_KEY:
        print("Please set BACK4APP_APP_ID and BACK4APP_MASTER_KEY in .env.back4app")
    else:
        setup_schema()
