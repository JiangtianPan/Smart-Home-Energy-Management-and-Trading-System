from spade import agent, behaviour, message
import json
from p2p_trading.utils.db_helper import DatabaseManager

class MarketAgent(agent.Agent):
    class OrderMatchingBehaviour(behaviour.CyclicBehaviour):
        async def run(self):
            print("[Market] Waiting for messages...")
            try:
                msg = await self.receive(timeout=10)  # wait for incoming messages
                if msg:
                    print(f"[Market] Received message from: {msg.sender}")
                    print(f"[Market] Message content: {msg.body}")
                    try:
                        order = json.loads(msg.body)
                        print(f"[Market] Parsed order: {order}")
                        db = DatabaseManager()
                        db.store_order(order)
                        print(f"[Market] Order stored, checking for matches...")
                        db.match_orders()
                    except json.JSONDecodeError as e:
                        print(f"[Market] JSON parsing error: {e}")
                        print(f"[Market] Raw message body: {msg.body}")
                    except Exception as e:
                        print(f"[Market] General error processing order: {e}")
                else:
                    print("[Market] No messages received in this cycle")
            except Exception as e:
                print(f"[Market] Error in receive cycle: {e}")


    # class MessageListener(behaviour.CyclicBehaviour):
    #     async def run(self):
    #         print("[Market] MessageListener active, waiting for messages...")
    #         try:
    #             msg = await self.receive(timeout=30)
    #             if msg:
    #                 print(f"[Market] MessageListener received message from {msg.sender}")
    #                 try:
    #                     order = json.loads(msg.body)
    #                     print(f"[Market] MessageListener parsed order: {order}")
    #                     db = DatabaseManager()
    #                     db.store_order(order)
    #                     print(f"[Market] MessageListener stored order, checking for matches...")
    #                     db.match_orders()
    #                 except json.JSONDecodeError as e:
    #                     print(f"[Market] MessageListener JSON parsing error: {e}")
    #                     print(f"[Market] MessageListener raw message body: {msg.body}")
    #                 except Exception as e:
    #                     print(f"[Market] MessageListener general error processing order: {e}")
    #             else:
    #                 print("[Market] MessageListener timeout, no messages")
    #         except Exception as e:
    #             print(f"[Market] MessageListener error in receive cycle: {e}")

    async def setup(self):
        print(f"[Market] Market Agent {self.jid} starting...")
        print(f"[Market] Agent is alive: {self.is_alive()}")
        
        # two behaviours: order matching and message listener
        self.add_behaviour(self.OrderMatchingBehaviour())
        #self.add_behaviour(self.MessageListener())
        
        print(f"[Market] Market Agent setup complete")