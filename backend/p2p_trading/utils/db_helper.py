import os
import json
import traceback

ORDERS_FILE = "data/orders.json"

class DatabaseManager:
    def __init__(self):
        try:
            print(f"[DB] Initializing database manager")
            print(f"[DB] Current working directory: {os.getcwd()}")
            print(f"[DB] Orders file path: {os.path.abspath(ORDERS_FILE)}")
            
            os.makedirs("data", exist_ok=True)
            print(f"[DB] Data directory created/exists: {os.path.exists('data')}")
            
            if not os.path.exists(ORDERS_FILE):
                print(f"[DB] Creating new orders file")
                with open(ORDERS_FILE, "w") as f:
                    json.dump([], f)
                print(f"[DB] New orders file created: {os.path.exists(ORDERS_FILE)}")
            else:
                print(f"[DB] Orders file already exists")
        except Exception as e:
            print(f"[DB] Error in database initialization: {e}")
            print(traceback.format_exc())

    def store_order(self, order):
        try:
            orders = self.get_all_orders()
            order["id"] = len(orders) + 1  # generate order id
            orders.append(order)
            print(f"[DB] Storing order: {order}")
            print(f"[DB] Total orders after add: {len(orders)}")
            with open(ORDERS_FILE, "w") as f:
                json.dump(orders, f, indent=2)
            print(f"[DB] Order stored successfully to {ORDERS_FILE}")
        except Exception as e:
            print(f"[DB] Error storing order: {e}")
            print(traceback.format_exc())
            # 紧急措施：直接将订单写入备用文件
            try:
                with open("data/emergency_orders.json", "a") as f:
                    f.write(json.dumps(order) + "\n")
                print(f"[DB] Order saved to emergency file")
            except Exception as ee:
                print(f"[DB] Failed to save to emergency file: {ee}")

    def get_all_orders(self):
        try:
            print(f"[DB] Reading all orders from {ORDERS_FILE}")
            if not os.path.exists(ORDERS_FILE):
                print(f"[DB] Orders file does not exist, creating empty file")
                with open(ORDERS_FILE, "w") as f:
                    json.dump([], f)
                return []
            
            with open(ORDERS_FILE, "r") as f:
                orders = json.load(f)
            print(f"[DB] Read {len(orders)} orders from file")
            return orders
        except Exception as e:
            print(f"[DB] Error reading orders: {e}")
            print(traceback.format_exc())
            return []

    def match_orders(self):
        try:
            print(f"[DB] Starting order matching process")
            orders = self.get_all_orders()
            buys = [o for o in orders if o["type"] == "buy" and o["status"] == "open"]
            sells = [o for o in orders if o["type"] == "sell" and o["status"] == "open"]
            print(f"[DB] Found {len(buys)} buy orders and {len(sells)} sell orders")

            matches_found = 0
            for buy in buys:
                for sell in sells:
                    if sell["amount"] == buy["amount"] and sell["price"] <= buy["price"]:
                        buy["status"] = "matched"
                        sell["status"] = "matched"
                        matches_found += 1
                        print(f"[MATCH] {buy['user']} 买入 ← {sell['user']} 卖出 成交！")

            print(f"[DB] Found {matches_found} matching orders")
            if matches_found > 0:
                with open(ORDERS_FILE, "w") as f:
                    json.dump(orders, f, indent=2)
                print(f"[DB] Updated order statuses saved")
        except Exception as e:
            print(f"[DB] Error matching orders: {e}")
            print(traceback.format_exc())

# Path: backend/p2p_trading/utils/db_helper.py
def get_open_orders():
    try:
        print(f"[API] Getting open orders")
        db = DatabaseManager()
        orders = db.get_all_orders()
        open_orders = [o for o in orders if o["status"] == "open"]
        print(f"[API] Found {len(open_orders)} open orders")
        return open_orders
    except Exception as e:
        print(f"[API] Error getting open orders: {e}")
        print(traceback.format_exc())
        return []