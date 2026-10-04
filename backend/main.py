from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data import start_session
from agent import run_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    conversation_id: str
    today: str
    turns: list[str]

@app.get("/")
def home():
    return {"message": "SwasthiQ Clinic Agent API"}

@app.post("/agent/run")
def run_agent_endpoint(request: AgentRequest):
    start_session()
    return run_agent(
        request.conversation_id,
        request.today,
        request.turns
    )