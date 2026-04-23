import httpx

ACCOUNT_KEY = "AZqzJp7QXccjKD1tg3V7GAMpodYHSqmFTFMdKETT"
BASE_URL = "https://api.back4app.com"

def test_management_api():
    # Try different header combinations
    headers_to_test = [
        {"Authorization": f"Bearer {ACCOUNT_KEY}"},
        {"X-Back4App-Account-Key": ACCOUNT_KEY},
        {"X-Parse-Account-Key": ACCOUNT_KEY},
        {"X-Back4app-Service-Token": ACCOUNT_KEY}
    ]
    
    for headers in headers_to_test:
        print(f"\nTesting headers: {list(headers.keys())[0]}")
        try:
            r = httpx.get(f"{BASE_URL}/apps", headers=headers)
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                print("SUCCESS!")
                print(r.json())
                return
            else:
                print(f"Failed: {r.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_management_api()
