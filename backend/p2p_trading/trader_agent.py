from spade import agent, behaviour, message
import json
import asyncio

class TraderAgent(agent.Agent):
    class SendOrderBehaviour(behaviour.OneShotBehaviour):
        def __init__(self, order):
            super().__init__()
            self.order = order

        async def run(self):
            print(f"[Trader] Sending order: {self.order}")
            msg = message.Message(to="market@localhost")
            msg.set_metadata("performative", "inform")
            msg.body = json.dumps(self.order)
            await self.send(msg)

    async def setup(self):
        print(f"[Trader] Agent {self.jid} started")

    async def submit_order(self, order):
        self.add_behaviour(self.SendOrderBehaviour(order))

async def main():
    trader_agent = TraderAgent("trader@localhost", "password")
    await trader_agent.start()
    await asyncio.sleep(2)
    
    order = {"user": "Alice", "type": "buy", "amount": 5, "price": 100}
    await trader_agent.submit_order(order)

    await asyncio.sleep(5)
    await trader_agent.stop()

if __name__ == "__main__":
    asyncio.run(main())