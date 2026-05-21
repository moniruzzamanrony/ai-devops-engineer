import requests
from app.core.config import HF_API_KEY, HF_API_URL, MODEL_AI
import requests



headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

def call_hf(prompt: str):
    return call_hf_messages([{"role": "user", "content": prompt}])


def call_hf_messages(messages: list):
    payload = {
        "model": MODEL_AI,
        "messages": messages,
        "max_tokens": 1500,
        # Low temperature for JSON-structured output: less creative variation
        # in escape sequences and string quoting.
        "temperature": 0.2,
    }

    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.json()