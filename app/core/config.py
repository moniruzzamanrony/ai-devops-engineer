import os
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")
GIT_USERNAME = os.getenv("GIT_USERNAME")
GIT_ACCESS_TOKEN = os.getenv("GIT_ACCESS_TOKEN")

def get_server_credential(server_name: str, key: str):
    env_key = f"{server_name}_{key}"
    value = os.getenv(env_key)

    if not value:
        return None
    return value


HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

MODEL_AI="meta-llama/Llama-3.1-8B-Instruct"