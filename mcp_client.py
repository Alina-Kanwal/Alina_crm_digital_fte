import subprocess
import json
import os
import sys

ACCOUNT_KEY = "AZqzJp7QXccjKD1tg3V7GAMpodYHSqmFTFMdKETT"

def run_mcp():
    process = subprocess.Popen(
        ["npx", "@back4app/mcp-server-back4app@latest"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
        env={**os.environ, "BACK4APP_ACCOUNT_KEY": ACCOUNT_KEY}
    )

    def send_request(method, params={}):
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        process.stdin.write(json.dumps(req) + "\n")
        process.stdin.flush()
        line = process.stdout.readline()
        return json.loads(line) if line else None

    try:
        # 1. Initialize
        print("Initializing...")
        init_res = send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "TestClient", "version": "1.0.0"}
        })
        print("Init result:", init_res)

        # 2. Get parse apps
        print("\nGetting Parse Apps...")
        apps_res = send_request("tools/call", {
            "name": "get_parse_apps",
            "arguments": {}
        })
        print("Parse Apps:", json.dumps(apps_res, indent=2))
        
    except Exception as e:
        print("Error:", e)
    finally:
        process.terminate()

if __name__ == "__main__":
    run_mcp()
