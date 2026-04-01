import asyncio
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
try:
    response = client.post("/api/chat", json={"message": "hello", "stream": False})
    print(response.status_code)
    print(response.text)
except Exception as e:
    print(f"ERROR: {e}")
