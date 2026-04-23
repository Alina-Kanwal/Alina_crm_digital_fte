import httpx
import os
from dotenv import load_dotenv

load_dotenv(".env.back4app")

APP_ID = os.getenv("BACK4APP_APP_ID")
API_URL = "https://parseapi.back4app.com/parse"

# Keys to test
KEYS = {
    "BiGC...": "BiGC5FNsNPkvOunaytnIWaxuFI1SDkedsUYRbcaB",
    "AFsT...": "AFsTGfriiAmyztcAsscwOeAkmp6FclGgWOEY1wzb",
    "Account": "AZqzJp7QXccjKD1tg3V7GAMpodYHSqmFTFMdKETT"
}

def test_key(name, key):
    print(f"\nTesting key {name}: {key[:10]}...")
    
    # Try as Master Key
    headers = {
        "X-Parse-Application-Id": APP_ID,
        "X-Parse-Master-Key": key
    }
    
    try:
        # Try to get schemas (requires Master Key)
        resp = httpx.get(f"{API_URL}/schemas", headers=headers)
        if resp.status_code == 200:
            print(f"  SUCCESS: This is a valid MASTER KEY.")
            return "MASTER"
        else:
            print(f"  FAILED as Master Key: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"  Error: {e}")

    # Try as REST API Key
    headers = {
        "X-Parse-Application-Id": APP_ID,
        "X-Parse-REST-API-Key": key
    }
    try:
        # Try to get a simple object (doesn't require Master Key)
        resp = httpx.get(f"{API_URL}/classes/_User", headers=headers)
        if resp.status_code == 200:
            print(f"  SUCCESS: This is a valid REST API KEY.")
            return "REST"
        else:
            print(f"  FAILED as REST Key: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"  Error: {e}")
    
    return "INVALID"

if __name__ == "__main__":
    print(f"App ID: {APP_ID}")
    for name, key in KEYS.items():
        test_key(name, key)
