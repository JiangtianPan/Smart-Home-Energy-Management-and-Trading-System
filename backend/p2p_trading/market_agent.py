from spade import agent, behaviour, message
import json
from database.db_manager import DatabaseManager

class MarketAgent(agent.Agent):
    class OrderMatchingBehaviour(behaviour.CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                order = json.loads(msg.body)
                print(f"[Market] Received order: {order}")
                db = DatabaseManager()
                db.store_order(order)
                db.match_orders()

    async def setup(self):
        print("[Market] Market Agent started")
        self.add_behaviour(self.OrderMatchingBehaviour())

if __name__ == "__main__":
    market_agent = MarketAgent("market@localhost", "password")
    market_agent.start()