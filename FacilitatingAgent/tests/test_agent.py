import pytest
import asyncio
import time
from facilitating_agent.agents.facilitating_agent import FacilitatingAgent
from facilitating_agent.config import settings
from spade.message import Message as SPADEMessage

@pytest.fixture(scope="module")
def facilitator():
    agent = FacilitatingAgent(settings.FACILITATOR_JID, settings.FACILITATOR_PASSWORD)
    yield agent
    asyncio.run(agent.stop())

@pytest.mark.asyncio
async def test_agent_start_stop():
    agent = FacilitatingAgent("test_facilitator@localhost", "test_password")
    try:
        await agent.start()
        assert agent.is_alive()
    finally:
        await agent.stop()
    assert not agent.is_alive()

@pytest.mark.asyncio
async def test_registration_handler(facilitator):
    await facilitator.start()
    # Create test registration message in the expected format:
    # "REGISTER|<agent_id>|<role>|<url>"
    registration_msg = SPADEMessage(
        to=facilitator.jid,
        body="REGISTER|test_agent@localhost|prediction|http://localhost:8001"
    )
    await facilitator.dispatch(registration_msg)
    await asyncio.sleep(0.5)
    # Expect registration stored keyed by agent_id
    assert "test_agent@localhost" in facilitator.registered_agents
    assert facilitator.registered_agents["test_agent@localhost"]["role"] == "prediction"

@pytest.mark.asyncio
async def test_message_routing(facilitator, mocker):
    # Patch httpx.AsyncClient.post
    mock_client = mocker.patch("httpx.AsyncClient.post", autospec=True)
    # Register a test agent with role "demand_response"
    facilitator.registered_agents["test_agent@localhost"] = {
        "agent_id": "test_agent@localhost",
        "role": "demand_response",
        "url": "http://localhost:8002",
        "last_seen": time.time()
    }
    message_data = {
        "sender": "prediction_agent@localhost",
        "receiver_role": "demand_response",
        "content": {"value": 42.0},
        "timestamp": time.time()
    }
    await facilitator.route_http_message(message_data)
    mock_client.assert_called_once_with(
        "http://localhost:8002/receive",
        json=message_data,
        timeout=2.0
    )

@pytest.mark.asyncio
async def test_cleanup_inactive_agents(facilitator):
    facilitator.registered_agents = {
        "active_agent@localhost": {
            "agent_id": "active_agent@localhost",
            "role": "test",
            "url": "http://localhost:8003",
            "last_seen": time.time()
        },
        "inactive_agent@localhost": {
            "agent_id": "inactive_agent@localhost",
            "role": "test",
            "url": "http://localhost:8004",
            "last_seen": time.time() - 60
        }
    }
    cleanup = facilitator.RegistrationCleanupBehaviour(period=30)
    await cleanup.run()
    assert "active_agent@localhost" in facilitator.registered_agents
    assert "inactive_agent@localhost" not in facilitator.registered_agents
