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
            # Emergency measure: write the order directly to a backup file
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

            # Sort by price (primary) and quantity (secondary)
            # For buys: price descending, amount descending
            buys.sort(key=lambda x: (x["price"], x["amount"]), reverse=True)
            # For sells: price ascending, amount descending (using negative to achieve descending)
            sells.sort(key=lambda x: (x["price"], -x["amount"]))
            
            print(f"[DB] Sorted buy orders: {[(o['id'], o['price'], o['amount']) for o in buys]}")
            print(f"[DB] Sorted sell orders: {[(o['id'], o['price'], o['amount']) for o in sells]}")
            
            matches_found = 0
            matched_ids = set()  # Track already matched order IDs
            new_orders = []  # Store new orders created due to partial matching
            
            # Try to match orders
            for buy in buys:
                if buy["id"] in matched_ids:
                    continue
                    
                for sell in sells:
                    if sell["id"] in matched_ids:
                        continue
                        
                    # Price matching condition: buy price >= sell price
                    if sell["price"] <= buy["price"]:
                        match_time = time.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Case 1: Quantities are equal - Complete match
                        if sell["amount"] == buy["amount"]:
                            # Complete match
                            buy["status"] = "matched"
                            sell["status"] = "matched"
                            buy["matched_with"] = sell["id"]
                            sell["matched_with"] = buy["id"]
                            buy["match_time"] = match_time
                            sell["match_time"] = match_time
                            
                            matched_ids.add(buy["id"])
                            matched_ids.add(sell["id"])
                            matches_found += 1
                            
                            print(f"[MATCH] Complete match: {buy['user']} buys ← {sell['user']} sells! Price: ${buy['price']} Amount: {buy['amount']} kWh")
                            break  # Found a complete match for this buy order, move to next buy order
                        
                        # Case 2: Buy amount > Sell amount - Partial match for buy, complete match for sell
                        elif buy["amount"] > sell["amount"]:
                            # Create complete match for sell order
                            sell["status"] = "matched"
                            sell["matched_with"] = buy["id"]
                            sell["match_time"] = match_time
                            
                            # Create partial match for buy order
                            buy["status"] = "partially_matched"
                            
                            # Create new buy order for remaining amount
                            remaining_amount = buy["amount"] - sell["amount"]
                            new_buy_order = buy.copy()
                            new_buy_order["id"] = None  # Will be generated when saved
                            new_buy_order["status"] = "open"
                            new_buy_order["amount"] = remaining_amount
                            new_buy_order["original_order_id"] = buy["id"]
                            new_orders.append(new_buy_order)
                            
                            # Update original buy order to reflect matched portion
                            buy["amount"] = sell["amount"]
                            buy["matched_with"] = sell["id"]
                            buy["match_time"] = match_time
                            
                            matched_ids.add(buy["id"])
                            matched_ids.add(sell["id"])
                            matches_found += 1
                            
                            print(f"[MATCH] Partial match (buy): {buy['user']} buys {sell['amount']} ← {sell['user']} sells {sell['amount']} kWh, Remaining buy amount: {remaining_amount} kWh")
                            break  # Found a partial match for this buy order, move to next buy order
                            
                        # Case 3: Sell amount > Buy amount - Complete match for buy, partial match for sell
                        elif sell["amount"] > buy["amount"]:
                            # Create complete match for buy order
                            buy["status"] = "matched"
                            buy["matched_with"] = sell["id"]
                            buy["match_time"] = match_time
                            
                            # Create partial match for sell order
                            sell["status"] = "partially_matched"
                            
                            # Create new sell order for remaining amount
                            remaining_amount = sell["amount"] - buy["amount"]
                            new_sell_order = sell.copy()
                            new_sell_order["id"] = None  # Will be generated when saved
                            new_sell_order["status"] = "open"
                            new_sell_order["amount"] = remaining_amount
                            new_sell_order["original_order_id"] = sell["id"]
                            new_orders.append(new_sell_order)
                            
                            # Update original sell order to reflect matched portion
                            sell["amount"] = buy["amount"]
                            sell["matched_with"] = buy["id"]
                            sell["match_time"] = match_time
                            
                            matched_ids.add(buy["id"])
                            matched_ids.add(sell["id"])
                            matches_found += 1
                            
                            print(f"[MATCH] Partial match (sell): {buy['user']} buys {buy['amount']} ← {sell['user']} sells {buy['amount']} kWh, Remaining sell amount: {remaining_amount} kWh")
                            break  # Found a match for this buy order, move to next buy order
            
            # Add new orders created from partial matches
            for new_order in new_orders:
                if new_order["id"] is None:
                    new_order["id"] = len(orders) + 1
                    orders.append(new_order)
                    print(f"[DB] Created new order: User {new_order['user']} {new_order['type']} {new_order['amount']} kWh at ${new_order['price']}")

            print(f"[DB] Found {matches_found} matching orders")
            if matches_found > 0 or len(new_orders) > 0:
                with open(ORDERS_FILE, "w") as f:
                    json.dump(orders, f, indent=2)
                print(f"[DB] Updated order statuses and created {len(new_orders)} new orders")
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
            matched_orders = [o for o in orders if o["status"] == "matched" or o["status"] == "partially_matched"]
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