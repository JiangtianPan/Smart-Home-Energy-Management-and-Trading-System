import os
import json
import traceback
import time

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

            # 按价格排序 - 买方降序（最高出价优先），卖方升序（最低售价优先）
            buys.sort(key=lambda x: x["price"], reverse=True)
            sells.sort(key=lambda x: x["price"])
            
            matches_found = 0
            matched_ids = set()  # 跟踪已匹配的订单ID
            
            # 尝试匹配
            for buy in buys:
                if buy["id"] in matched_ids:
                    continue
                    
                for sell in sells:
                    if sell["id"] in matched_ids:
                        continue
                        
                    # 匹配条件：数量相等且买入价格 >= 卖出价格
                    if sell["amount"] == buy["amount"] and sell["price"] <= buy["price"]:
                        # 匹配成功
                        buy["status"] = "matched"
                        sell["status"] = "matched"
                        buy["matched_with"] = sell["id"]
                        sell["matched_with"] = buy["id"]
                        buy["match_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                        sell["match_time"] = buy["match_time"]
                        
                        matched_ids.add(buy["id"])
                        matched_ids.add(sell["id"])
                        matches_found += 1
                        
                        print(f"[MATCH] {buy['user']} 买入 ← {sell['user']} 卖出 成交! 价格: ${buy['price']} 数量: {buy['amount']} kWh")
                        break  # 已为此买单找到匹配，移至下一个买单

            print(f"[DB] Found {matches_found} matching orders")
            if matches_found > 0:
                with open(ORDERS_FILE, "w") as f:
                    json.dump(orders, f, indent=2)
                print(f"[DB] Updated order statuses saved")
            return matches_found
        except Exception as e:
            print(f"[DB] Error matching orders: {e}")
            print(traceback.format_exc())
            return 0

    def delete_order(self, order_id):
        try:
            print(f"[DB] Deleting order with ID: {order_id}")
            orders = self.get_all_orders()
            filtered_orders = [o for o in orders if o.get('id') != order_id]
            
            if len(filtered_orders) == len(orders):
                print(f"[DB] Order with ID {order_id} not found")
                return False
            
            with open(ORDERS_FILE, "w") as f:
                json.dump(filtered_orders, f, indent=2)
            print(f"[DB] Order {order_id} deleted successfully")
            return True
        except Exception as e:
            print(f"[DB] Error deleting order: {e}")
            print(traceback.format_exc())
            return False
    
    def get_matched_orders(self):
        try:
            orders = self.get_all_orders()
            matched_orders = [o for o in orders if o["status"] == "matched"]
            print(f"[DB] Found {len(matched_orders)} matched orders")
            return matched_orders
        except Exception as e:
            print(f"[DB] Error getting matched orders: {e}")
            print(traceback.format_exc())
            return []

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