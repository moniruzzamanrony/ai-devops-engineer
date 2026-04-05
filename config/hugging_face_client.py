import requests
from core.config import HF_API_KEY, HF_API_URL, MODEL_AI
import requests



headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

def call_hf(prompt: str):
    payload = {
        "model": MODEL_AI,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.json()