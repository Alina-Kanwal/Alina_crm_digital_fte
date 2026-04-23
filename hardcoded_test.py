import httpx

APP_ID = "FcVby6MAuPrhrEpGNxoSQkFZGFyZfUl1vNXY5pzD"
MASTER_KEY = "A7Q3WQBIA3ALB2J2UHZAJ2GXGMRGVVQVQIV6UXIWDBRCMK6DLN6A"
API_URL = "https://parseapi.back4app.com"

headers = {
    "X-Parse-Application-Id": APP_ID,
    "X-Parse-Master-Key": MASTER_KEY,
    "Content-Type": "application/json"
}

print(f"Testing App ID: {APP_ID}")
print(f"Testing Master Key: {MASTER_KEY[:10]}...")

try:
    # Try schemas
    r = httpx.get(f"{API_URL}/schemas", headers=headers)
    print(f"Schemas Status: {r.status_code}")
    print(f"Schemas Body: {r.text[:200]}")
    
    # Try classes
    r = httpx.get(f"{API_URL}/classes/_User", headers=headers)
    print(f"Classes Status: {r.status_code}")
    print(f"Classes Body: {r.text[:200]}")

except Exception as e:
    print(f"Error: {e}")
