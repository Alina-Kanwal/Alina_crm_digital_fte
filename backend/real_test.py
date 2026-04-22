import requests
import json
import os

# Use environment variable for backend URL, default to 7860 (Docker port)
url = os.getenv("BACKEND_URL", "http://127.0.0.1:7860") + "/api/v1/inquiries/webform"

payload = {
    "id": "test-123",
    "sender": "customer@example.com",
    "name": "Test User",
    "subject": "Testing Deployment",
    "body": "Hello, how can I use your agent?",
    "channel": "webform",
    "metadata": {"source": "manual_test"}
}
headers = {"Content-Type": "application/json"}

try:
    print(f"Sending 'Real' inquiry to {url}...")
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"STATUS: {response.status_code}")
    print("RESPONSE BOHOT ALA HAY:")
    
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"FAILED DETAILS: {response.text}")
        
except Exception as e:
    print(f"FAIL: {e}")
