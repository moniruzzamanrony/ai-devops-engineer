import os
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")

HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

MODEL_AI="meta-llama/Llama-3.1-8B-Instruct"