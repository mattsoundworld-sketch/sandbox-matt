from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY is not set")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

payload = {
    "model": "openrouter/auto",
    "messages": [
        {"role": "user", "content": "Say hello in one sentence."}
    ],
}

response = requests.post(
    OPENROUTER_API_URL,
    headers=headers,
    json=payload,
    timeout=30,
)

# ---- Robust response handling ----
try:
    data = response.json()
except json.JSONDecodeError:
    raise RuntimeError(f"Non‑JSON response: {response.text}")

if response.status_code != 200:
    raise RuntimeError(
        f"HTTP {response.status_code}: {data.get('error', data)}"
    )

if "choices" not in data:
    raise RuntimeError(f"Unexpected response shape: {data}")

print(f"Model: {data.get('model')}")
print(f"Response: {data['choices'][0]['message']['content']}")
