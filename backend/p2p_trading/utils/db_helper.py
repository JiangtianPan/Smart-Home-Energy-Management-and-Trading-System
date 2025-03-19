import sqlite3

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect("orders.db")
        self.cursor = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                order_type TEXT,
                amount REAL,
                price REAL,
                status TEXT DEFAULT 'Pending'
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer TEXT,
                seller TEXT,
                amount REAL,
                price REAL
            )
        """)
        self.conn.commit()

    def store_order(self, order):
        self.cursor.execute("INSERT INTO orders (user, order_type, amount, price) VALUES (?, ?, ?, ?)",
                            (order['user'], order['type'], order['amount'], order['price']))
        self.conn.commit()

    def match_orders(self):
        self.cursor.execute("SELECT * FROM orders WHERE order_type='buy' ORDER BY price DESC")
        buy_orders = self.cursor.fetchall()
        self.cursor.execute("SELECT * FROM orders WHERE order_type='sell' ORDER BY price ASC")
        sell_orders = self.cursor.fetchall()

        matched_orders = []
        while buy_orders and sell_orders:
            buy_order = buy_orders[0]
            sell_order = sell_orders[0]
            if buy_order[3] >= sell_order[3]:  # buy price >= sell price
                trade_amount = min(buy_order[2], sell_order[2])
                self.cursor.execute("INSERT INTO trades (buyer, seller, amount, price) VALUES (?, ?, ?, ?)",
                                    (buy_order[1], sell_order[1], trade_amount, sell_order[3]))
                self.conn.commit()
                buy_orders.pop(0)
                sell_orders.pop(0)
        return matched_orders
