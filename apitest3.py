import os
import requests
from dotenv import load_dotenv

load_dotenv()

base = os.getenv("AZURE_BASE_URL").rstrip("/")
key = os.getenv("AZURE_API_KEY")

anthropic_headers = {
    "x-api-key": key,
    "anthropic-version": "2023-06-01",
    "Content-Type": "application/json",
}

payload = {
    "max_tokens": 5,
    "messages": [{"role": "user", "content": "Hi"}],
}

# The official Anthropic model ID is claude-opus-4-6  ^1^  ^2^
# But PSU gateway may use different deployment names
print("=== CLAUDE on /anthropic/v1/messages ===")
claude_names = [
    # Official Anthropic IDs
    "claude-opus-4-6", "claude-sonnet-4-6",
    "claude-opus-4-5", "claude-sonnet-4-5",
    "claude-opus-4-1", "claude-sonnet-4-1",
    "claude-opus-4-0", "claude-sonnet-4-0",
    "claude-3-5-sonnet", "claude-3-opus",
    # With dates
    "claude-opus-4-6-20260205",
    "claude-sonnet-4-6-20260205",
    # Versioned with dots (non-standard but PSU might use)
    "claude-opus-4.6", "claude-sonnet-4.6",
    # Maybe just the tier name
    "opus", "sonnet",
    # Maybe prefixed
    "anthropic-claude-opus-4-6",
    "anthropic-claude-sonnet-4-6",
]

for name in claude_names:
    r = requests.post(
        f"{base}/anthropic/v1/messages",
        headers=anthropic_headers,
        json={**payload, "model": name},
    )
    marker = "✅" if r.status_code == 200 else "  "
    print(f"{marker} {r.status_code}  {name}")
    if r.status_code == 200:
        print(f"       {r.text[:250]}\n")
    elif r.status_code not in [404]:
        print(f"       {r.text[:200]}\n")


# Now try GPT-5.2 on the OpenAI path with more name variants
print("\n=== GPT-5.2 on /openai/v1/chat/completions ===")
openai_headers = {"api-key": key, "Content-Type": "application/json"}
openai_payload = {"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}

gpt_names = [
    "gpt-5.2", "gpt-5", "gpt-5.2-auto",
    "gpt-52", "gpt-52-auto",
    "o3", "o3-mini", "o4", "o4-mini",
    "gpt-4o-auto", "auto",
]

for name in gpt_names:
    r = requests.post(
        f"{base}/openai/v1/chat/completions",
        headers=openai_headers,
        json={**openai_payload, "model": name},
    )
    marker = "✅" if r.status_code == 200 else "  "
    print(f"{marker} {r.status_code}  {name}")
    if r.status_code == 200:
        print(f"       {r.text[:250]}\n")