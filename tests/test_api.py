import pytest
from fastapi.testclient import TestClient
from facilitating_agent.main import app
from facilitating_agent.models.agent_model import AgentRegistration, Message
from datetime import datetime
import asyncio

@pytest.fixture(scope="module")
def test_client():
    client = TestClient(app)
    # Start SPADE agent in background
    async def start_agent():
        from facilitating_agent.agents.facilitating_agent import FacilitatingAgent
        from facilitating_agent.config import settings
        agent = FacilitatingAgent(settings.FACILITATOR_JID, settings.FACILITATOR_PASSWORD)
        await agent.start()
        return agent
    agent = asyncio.run(start_agent())
    app.state.facilitator = agent
    yield client
    asyncio.run(agent.stop())

def test_register_agent(test_client):
    registration_data = {
        "agent_id": "prediction_agent@localhost",
        "role": "prediction",
        "url": "http://localhost:8001"
    }
    response = test_client.post("/api/v1/agents/register/", json=registration_data)
    assert response.status_code == 200
    assert "registered successfully" in response.json()["message"]

def test_duplicate_registration(test_client):
    registration_data = {
        "agent_id": "prediction_agent@localhost",
        "role": "prediction",
        "url": "http://localhost:8001"
    }
    response = test_client.post("/api/v1/agents/register/", json=registration_data)
    assert response.status_code == 400
    # The error detail may be in the "detail" key
    assert "already registered" in response.json().get("detail", "")

def test_send_message(test_client):
    message_data = {
        "sender": "prediction_agent@localhost",
        "receiver_role": "demand_response",
        "content": {"value": 42.0},
        "timestamp": datetime.now().isoformat()
    }
    response = test_client.post("/api/v1/agents/messages/send/", json=message_data)
    assert response.status_code == 200
    assert "forwarded" in response.json()["message"]

def test_send_message_invalid_role(test_client):
    message_data = {
        "sender": "prediction_agent@localhost",
        "receiver_role": "nonexistent_role",
        "content": {"value": 42.0},
        "timestamp": datetime.now().isoformat()
    }
    response = test_client.post("/api/v1/agents/messages/send/", json=message_data)
    assert response.status_code == 404
    # The error detail may be in "detail" or "message"
    assert "No active agents" in response.json().get("detail", "")
