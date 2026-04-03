import os
import requests
from dotenv import load_dotenv

load_dotenv()

base = os.getenv("AZURE_BASE_URL").rstrip("/")
key = os.getenv("AZURE_API_KEY")

openai_headers = {"api-key": key, "Content-Type": "application/json"}
openai_payload = {"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}

# GPT-5.2 Auto - the UI shows it, let's try everything
print("=== GPT-5.2 on /openai/v1/chat/completions ===")
gpt_names = [
    "gpt-5.2-auto", "gpt-5.2", "gpt-5-2", "gpt-5-2-auto",
    "gpt52-auto", "gpt52", "gpt-5.2-turbo",
    "chatgpt-5.2-auto", "chatgpt-5.2",
    # Maybe it's an o-series reasoning model
    "o3", "o3-mini", "o4-mini", "o3-pro",
    # Maybe just a different GPT-4 variant
    "gpt-4.1-turbo", "gpt-4-turbo",
]

for name in gpt_names:
    r = requests.post(f"{base}/openai/v1/chat/completions", headers=openai_headers, json={**openai_payload, "model": name})
    marker = "✅" if r.status_code == 200 else "  "
    print(f"{marker} {r.status_code}  {name}")
    if r.status_code == 200:
        print(f"       {r.text[:200]}\n")

# Gemini - try on ALL three auth/path combos that have worked
print("\n=== GEMINI - TRYING ALL KNOWN WORKING PATHS ===")

gemini_names = [
    "gemini-2.5-flash", "gemini-2.5-pro",
    "gemini-3-flash", "gemini-3.1-pro", "gemini-3-pro",
    "gemini-2-5-flash", "gemini-2-5-pro",
    "gemini-3-0-flash", "gemini-3-1-pro",
    "gemini-25-flash", "gemini-25-pro",
    "gemini-3flash", "gemini-31-pro",
    "google-gemini-2.5-flash", "google-gemini-3-flash",
]

# Try OpenAI-compatible path
print("\n--- /openai/v1/chat/completions (api-key) ---")
for name in gemini_names:
    r = requests.post(f"{base}/openai/v1/chat/completions", headers=openai_headers, json={**openai_payload, "model": name})
    marker = "✅" if r.status_code == 200 else "  "
    if r.status_code != 404:
        print(f"{marker} {r.status_code}  {name}")
        print(f"       {r.text[:200]}\n")

# Try Anthropic path (unlikely but thorough)
anthropic_headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
anthropic_payload = {"max_tokens": 5, "messages": [{"role": "user", "content": "Hi"}]}

print("--- /anthropic/v1/messages (x-api-key) ---")
for name in gemini_names[:5]:
    r = requests.post(f"{base}/anthropic/v1/messages", headers=anthropic_headers, json={**anthropic_payload, "model": name})
    if r.status_code != 404:
        print(f"   {r.status_code}  {name}: {r.text[:200]}\n")

# Try Google-specific paths with both auth methods
print("\n--- GOOGLE PATH SWEEP (broader) ---")
google_paths = [
    "/google/v1/chat/completions",
    "/google/v1beta/chat/completions",
    "/google/v1/messages",
    "/vertex/v1beta1/chat/completions",
    "/gemini/v1beta/chat/completions",
    "/inference/chat/completions",
    "/models/gemini-2.5-flash:generateContent",
    "/v1beta/models/gemini-2.5-flash:generateContent",
]

for path in google_paths:
    for label, hdrs in [("api-key", openai_headers), ("x-api-key", anthropic_headers)]:
        r = requests.post(f"{base}{path}", headers=hdrs, json=openai_payload)
        if r.status_code not in [404, 405]:
            print(f"✅ {r.status_code}  {label}  POST {path}")
            print(f"       {r.text[:200]}\n")

print("\nDone!")