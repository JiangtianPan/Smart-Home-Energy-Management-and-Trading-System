import os
import json

ORDERS_FILE = "data/orders.json"

class DatabaseManager:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, "w") as f:
                json.dump([], f)

    def store_order(self, order):
        orders = self.get_all_orders()
        order["id"] = len(orders) + 1  # generate order id
        orders.append(order)
        with open(ORDERS_FILE, "w") as f:
            json.dump(orders, f)

    def get_all_orders(self):
        with open(ORDERS_FILE, "r") as f:
            return json.load(f)

    def match_orders(self):
        orders = self.get_all_orders()
        buys = [o for o in orders if o["type"] == "buy" and o["status"] == "open"]
        sells = [o for o in orders if o["type"] == "sell" and o["status"] == "open"]

        for buy in buys:
            for sell in sells:
                if sell["amount"] == buy["amount"] and sell["price"] <= buy["price"]:
                    buy["status"] = "matched"
                    sell["status"] = "matched"
                    print(f"[MATCH] {buy['user']} 买入 ← {sell['user']} 卖出 成交！")

        with open(ORDERS_FILE, "w") as f:
            json.dump(orders, f)

# Path: backend/p2p_trading/utils/db_helper.py
def get_open_orders():
    db = DatabaseManager()
    orders = db.get_all_orders()
    return [o for o in orders if o["status"] == "open"]
