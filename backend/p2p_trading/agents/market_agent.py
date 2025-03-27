from spade import agent, behaviour, message
import json
from p2p_trading.utils.db_helper import DatabaseManager

class MarketAgent(agent.Agent):
    class OrderMatchingBehaviour(behaviour.CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for incoming messages
            if msg:
                try:
                    order = json.loads(msg.body)
                    print(f"[Market] Received order: {order}")
                    db = DatabaseManager()
                    db.store_order(order)
                    db.match_orders()
                except Exception as e:
                    print(f"[Market] Error processing order: {e}")

    async def setup(self):
        print("[Market] Market Agent started")
        self.add_behaviour(self.OrderMatchingBehaviour())