#!/usr/bin/env python3
"""Simple test to check if basic FastAPI works"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    client = TestClient(app)
    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")