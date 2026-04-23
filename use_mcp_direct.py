import subprocess
import json
import os

ACCOUNT_KEY = "A7Q3WQBIA3ALB2J2UHZAJ2GXGMRGVVQVQIV6UXIWDBRCMK6DLN6A"

# Define the JSON-RPC request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "list-apps",
    "params": {}
}

# Run the MCP server and pipe the request
try:
    process = subprocess.Popen(
        ["npx", "-y", "@back4app/mcp-server-back4app@latest"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
        env={**os.environ, "BACK4APP_ACCOUNT_KEY": ACCOUNT_KEY}
    )
    
    stdout, stderr = process.communicate(input=json.dumps(request), timeout=60)
    
    print("STDOUT:", stdout)
    print("STDERR:", stderr)

except Exception as e:
    print("Error:", e)
