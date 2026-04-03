import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("AZURE_API_KEY"),
    base_url=os.getenv("AZURE_BASE_URL").rstrip("/") + "/openai/v1",
    default_headers={"Ocp-Apim-Subscription-Key": os.getenv("AZURE_API_KEY")},
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Explain why finetuning can improve task-specific performance."}
    ]
)

print(response.choices[0].message.content)