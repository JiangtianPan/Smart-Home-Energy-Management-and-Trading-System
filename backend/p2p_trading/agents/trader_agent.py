from spade import agent, behaviour, message
import json

class TraderAgent(agent.Agent):
    class SendOrderBehaviour(behaviour.OneShotBehaviour):
        def __init__(self, order):
            super().__init__()
            self.order = order

        async def run(self):
            print(f"[Trader] Sending order: {self.order}")
            msg = message.Message(to="market@localhost")  # send order to market agent
            msg.set_metadata("performative", "inform")
            msg.body = json.dumps(self.order)
            await self.send(msg)

    async def setup(self):
        print(f"[Trader] Agent {self.jid} started")

    async def submit_order(self, order):
        order["status"] = "open"
        self.add_behaviour(self.SendOrderBehaviour(order))
