import os
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")
GIT_USERNAME = os.getenv("GIT_USERNAME")
GIT_ACCESS_TOKEN = os.getenv("GIT_ACCESS_TOKEN")

SERVER_HOST = os.getenv("SERVER_HOST")
SERVER_PORT = os.getenv("SERVER_PORT")
SERVER_USERNAME = os.getenv("SERVER_USERNAME")
SERVER_PASSWORD = os.getenv("SERVER_PASSWORD")

def get_server_credential(env_key: str,):
    value = os.getenv(env_key)

    if not value:
        return None
    return value


HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

MODEL_AI="Qwen/Qwen2.5-7B-Instruct"