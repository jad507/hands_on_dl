import os
import requests
from dotenv import load_dotenv

load_dotenv()

base = os.getenv("AZURE_BASE_URL").rstrip("/")
key = os.getenv("AZURE_API_KEY")

headers = {
    "x-api-key": key,
    "anthropic-version": "2023-06-01",
    "Content-Type": "application/json",
}

payload = {
    "max_tokens": 5,
    "messages": [{"role": "user", "content": "Hi"}],
}

# === CLAUDE MODEL NAMES ===
print("=== CLAUDE MODELS on /anthropic/v1/messages ===")
claude_names = [
    # Opus 4.6 variants
    "claude-opus-4-6-20260301", "claude-opus-4.6-20260301",
    "claude-4-opus", "claude-4-6-opus",
    "claude-opus-latest", "claude-opus",

    # Sonnet 4.6 variants
    "claude-sonnet-4-6-20260301", "claude-sonnet-4.6-20260301",
    "claude-4-sonnet", "claude-4-6-sonnet",
    "claude-sonnet-latest", "claude-sonnet",

    # Standard Anthropic naming convention
    "claude-opus-4-20250514",
    "claude-sonnet-4-20250514",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
    "claude-3-opus-20240229",
    "claude-3-opus-latest",

    # Maybe just the UI display names lowercased with dashes
    "claude-opus-4.6", "claude-sonnet-4.6",

    # Maybe without version dates
    "claude-opus-4", "claude-sonnet-4",
]

for name in claude_names:
    r = requests.post(
        f"{base}/anthropic/v1/messages",
        headers=headers,
        json={**payload, "model": name},
    )
    marker = "✅" if r.status_code == 200 else "  "
    print(f"{marker} {r.status_code}  {name}")
    if r.status_code == 200:
        print(f"       {r.text[:250]}\n")
    elif r.status_code not in [404]:
        print(f"       {r.text[:250]}\n")

# === GEMINI PATH SWEEP ===
print("\n=== GEMINI PATH SWEEP ===")
gemini_headers_xapi = {"x-api-key": key, "Content-Type": "application/json"}
gemini_headers_apikey = {"api-key": key, "Content-Type": "application/json"}

gemini_paths = [
    "/google/v1beta/chat/completions",
    "/google/v1beta/messages",
    "/vertex/v1/messages",
    "/vertexai/v1/chat/completions",
    "/ai/v1/chat/completions",
    "/inference/v1/chat/completions",
]

for path in gemini_paths:
    for label, hdrs in [("api-key", gemini_headers_apikey), ("x-api-key", gemini_headers_xapi)]:
        r = requests.post(f"{base}{path}", headers=hdrs, json={**payload, "model": "gemini-2.5-flash"})
        if r.status_code != 404:
            print(f"✅ {r.status_code}  POST {path} [{label}]")
            print(f"       {r.text[:200]}\n")

print("\nDone!")