import time
import httpx
from fastapi import APIRouter, HTTPException
from models.agent_model import AgentRegistration, Message
from utils.logger import logger

router = APIRouter(prefix="/api/v1/agents")

# Registered agents stored by agent_id
registered_agents = {}

def get_agent_by_role(role: str):
    for agent_id, info in registered_agents.items():
        if info.get("role") == role:
            return info
    return None

@router.post("/register/")
async def register_agent(agent: AgentRegistration):
    # Check if any agent is already registered with the same role
    for reg in registered_agents.values():
        if reg.get("role") == agent.role:
            raise HTTPException(status_code=400, detail="Agent already registered for this role")
    registered_agents[agent.agent_id] = {
        "agent_id": agent.agent_id,
        "role": agent.role,
        "url": agent.url,
        "last_seen": time.time()
    }
    logger.info(f"Agent registered: {agent.agent_id} with role {agent.role}")
    return {"message": f"Agent {agent.agent_id} registered successfully"}

@router.post("/messages/send/")
async def send_message(message: Message):
    recipient = get_agent_by_role(message.receiver_role)
    if not recipient:
        raise HTTPException(status_code=404, detail="No active agents")
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{recipient['url']}/receive", json=message.dict())
            return {"message": "Message forwarded successfully"}
        except Exception as e:
            logger.error(f"Message delivery failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Message delivery failed")
