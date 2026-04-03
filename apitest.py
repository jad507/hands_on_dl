import os
import requests
from dotenv import load_dotenv

load_dotenv()

base = os.getenv("AZURE_BASE_URL").rstrip("/")
key = os.getenv("AZURE_API_KEY")

headers = {
    "api-key": key,
    "Ocp-Apim-Subscription-Key": key,
}

# The 403 on /openai/models suggests this path structure works.
# Let's try POST requests and different model/deployment names.

# First, let's try listing models with POST
print("=== Trying to list models ===")
r = requests.get(f"{base}/openai/models?api-version=2024-10-21", headers=headers)
print(f"GET  /openai/models  → {r.status_code}: {r.text[:300]}\n")

# Now try POST to chat/completions with various deployment names
payload = {
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 5
}

deployment_names = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4",
    "gpt-35-turbo",
    "gpt-3.5-turbo",
    "gpt-4-turbo",
    "gpt-4o-mini-2024-07-18",
    "claude-3-5-sonnet",
    "claude-3-sonnet",
    "claude-sonnet-4",
]

print("=== Trying deployment names ===")
for name in deployment_names:
    url = f"{base}/openai/deployments/{name}/chat/completions?api-version=2024-10-21"
    r = requests.post(url, headers=headers, json=payload)
    marker = "✅" if r.status_code != 404 else "  "
    print(f"{marker} {r.status_code}  {name}")
    if r.status_code != 404:
        print(f"       {r.text[:200]}\n")