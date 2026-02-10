from fastapi import FastAPI
from pydantic import BaseModel
from assistant.ai.client import ask_ai

app = FastAPI(title="SignalTrust Assistant API")

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    answer = ask_ai(req.prompt)
    return ChatResponse(response=answer)
