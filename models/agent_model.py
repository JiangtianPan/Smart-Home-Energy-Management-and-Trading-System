from pydantic import BaseModel
from datetime import datetime

class AgentRegistration(BaseModel):
    agent_id: str
    role: str
    url: str

class Message(BaseModel):
    sender: str
    receiver_role: str
    content: dict
    timestamp: datetime
