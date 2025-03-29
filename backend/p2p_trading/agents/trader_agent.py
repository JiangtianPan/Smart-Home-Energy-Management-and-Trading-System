from spade import agent, behaviour, message
import json
import time

class TraderAgent(agent.Agent):
    class SendOrderBehaviour(behaviour.OneShotBehaviour):
        def __init__(self, order):
            super().__init__()
            self.order = order

        async def run(self):
            try:
                print(f"[Trader] Preparing to send order: {self.order}")
                msg = message.Message(to="market@localhost")
                msg.set_metadata("performative", "inform")
                msg.body = json.dumps(self.order)
                msg.thread = str(time.time())  # Use current time as thread ID for tracking
                
                print(f"[Trader] Message details:")
                print(f"  - To: {msg.to}")
                print(f"  - Type: {msg.get_metadata('performative')}")
                print(f"  - Body: {msg.body}")
                
                await self.send(msg)
                print(f"[Trader] Message sent successfully")
            except Exception as e:
                print(f"[Trader] Error sending message: {e}")

    async def setup(self):
        print(f"[Trader] Agent {self.jid} started")
        print(f"[Trader] Agent is alive: {self.is_alive()}")

    async def submit_order(self, order):
        print(f"[Trader] Received order submission request: {order}")
        order["status"] = "open"
        print(f"[Trader] Adding 'open' status to order")
        self.add_behaviour(self.SendOrderBehaviour(order))
        print(f"[Trader] SendOrderBehaviour added to agent")