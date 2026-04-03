import os
import requests
from dotenv import load_dotenv

load_dotenv()

base = os.getenv("AZURE_BASE_URL").rstrip("/")
key = os.getenv("AZURE_API_KEY")

headers = {
    "api-key": key,
    "Content-Type": "application/json",
}

payload = {"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}

model_names = [
    # GPT - fill in the gaps
    "gpt-5", "gpt-5.2-auto", "gpt-52-auto", "gpt52-auto", "gpt-5-2-auto",
    "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1",
    "gpt-4o",

    # Claude - try Azure-style naming
    "claude-opus-4-6", "claude-sonnet-4-6",
    "claude-4-6-opus", "claude-4-6-sonnet",
    "claude-4.6", "claude-4",
    "anthropic-claude-opus-4.6", "anthropic-claude-sonnet-4.6",
    "claude-opus", "claude-sonnet",

    # Gemini - try Azure-style naming
    "gemini-25-flash", "gemini-25-pro",
    "gemini-3.0-flash", "gemini-31-pro", "gemini-3.0-pro",
    "google-gemini-2.5-flash", "google-gemini-3-flash",
    "gemini-flash", "gemini-pro",
    "gemini-2-5-flash", "gemini-2-5-pro",
    "gemini-3-0-flash", "gemini-3-1-pro",
]

for name in model_names:
    r = requests.post(
        f"{base}/openai/v1/chat/completions",
        headers=headers,
        json={**payload, "model": name},
    )
    marker = "✅" if r.status_code == 200 else "  "
    print(f"{marker} {r.status_code}  {name}")
    if r.status_code == 200:
        print(f"       {r.text[:200]}\n")