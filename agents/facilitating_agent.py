import time
import httpx
import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message as SPADEMessage
from utils.logger import logger

class FacilitatingAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        # Registered agents stored by agent_id
        self.registered_agents = {}

    async def setup(self):
        logger.info("Facilitating Agent setup completed.")
        self.add_behaviour(self.MessageRouter())

    async def route_http_message(self, message_data: dict):
        """
        Find a registered agent by matching receiver_role and forward the message via HTTP.
        """
        for reg in self.registered_agents.values():
            if reg.get("role") == message_data.get("receiver_role"):
                async with httpx.AsyncClient() as client:
                    await client.post(f"{reg['url']}/receive", json=message_data, timeout=2.0)
                return
        raise Exception("No agent found with the specified role")

    class MessageRouter(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg:
                # Handle registration messages
                if msg.body.startswith("REGISTER|"):
                    parts = msg.body.split("|")
                    if len(parts) == 4:
                        _, agent_id, role, url = parts
                        # Check for duplicate registration based on role
                        duplicate = any(reg.get("role") == role for reg in self.agent.registered_agents.values())
                        if duplicate:
                            logger.warning(f"Agent with role {role} already registered.")
                        else:
                            self.agent.registered_agents[agent_id] = {
                                "agent_id": agent_id,
                                "role": role,
                                "url": url,
                                "last_seen": time.time()
                            }
                            logger.info(f"Registered agent {agent_id} with role {role}")
                    else:
                        logger.error("Invalid registration message format.")
                else:
                    # For non-registration messages, assume msg.to holds the intended role
                    recipient = None
                    for reg in self.agent.registered_agents.values():
                        if reg.get("role") == str(msg.to):
                            recipient = reg
                            break
                    if recipient:
                        async with httpx.AsyncClient() as client:
                            try:
                                await client.post(f"{recipient['url']}/receive", json={"message": msg.body})
                                logger.info(f"Message routed to {recipient['agent_id']}")
                            except Exception as e:
                                logger.error(f"Failed to route message: {str(e)}")
                    else:
                        logger.warning(f"Recipient with role {msg.to} not found.")

    class RegistrationCleanupBehaviour(CyclicBehaviour):
        def __init__(self, period: int):
            super().__init__()
            self.period = period

        async def run(self):
            current_time = time.time()
            to_remove = []
            for agent_id, info in list(self.agent.registered_agents.items()):
                if current_time - info.get("last_seen", current_time) > self.period:
                    to_remove.append(agent_id)
            for agent_id in to_remove:
                del self.agent.registered_agents[agent_id]
                logger.info(f"Removed inactive agent {agent_id}")
