from fastapi import FastAPI
from services.ai_service import ask_devops as ask_devops_service
from dto.dev_ops_request import DevOpsRequest

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/ask_devops")
async def ask_devops(request: DevOpsRequest):
    return ask_devops_service(request)