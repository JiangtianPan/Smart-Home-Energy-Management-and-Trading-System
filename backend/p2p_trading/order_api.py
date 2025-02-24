from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# SQLite storage for orders
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# List of orders
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50), nullable=False)
    order_type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')

    def __repr__(self):
        return (f"Order(id={self.id}, user={self.user}, type={self.order_type}, "
                f"amount={self.amount}, price={self.price}, status={self.status})")


class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer = db.Column(db.String(50), nullable=False)
    seller = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Trade('{self.buyer}', '{self.seller}', '{self.amount}', '{self.price}')"

# Create the database
with app.app_context():
    db.create_all()

def match_orders():
    # Filter only the pending and partial orders
    buy_orders = Order.query.filter(
        Order.order_type == "buy",
        Order.status.in_(["Pending", "Partial"])
    ).order_by(Order.price.desc()).all()

    sell_orders = Order.query.filter(
        Order.order_type == "sell",
        Order.status.in_(["Pending", "Partial"])
    ).order_by(Order.price.asc()).all()

    matched_orders = []
    i, j = 0, 0

    try:
        while i < len(buy_orders) and j < len(sell_orders):
            buy_order = buy_orders[i]
            sell_order = sell_orders[j]

            # Check if the buy order price is high enough to purchase the sell order
            if buy_order.price >= sell_order.price:
                trade_amount = min(buy_order.amount, sell_order.amount)

                # Create and store a Trade record for the successful match
                trade = Trade(
                    buyer=buy_order.user,
                    seller=sell_order.user,
                    amount=trade_amount,
                    price=sell_order.price
                )
                db.session.add(trade)

                matched_orders.append({
                    'buyer': buy_order.user,
                    'seller': sell_order.user,
                    'amount': trade_amount,
                    'price': sell_order.price
                })

                # Update remaining amounts
                buy_order.amount -= trade_amount
                sell_order.amount -= trade_amount

                # Update order statuses instead of deleting
                if buy_order.amount == 0:
                    buy_order.status = 'Completed'
                    i += 1  # move to the next buy order
                else:
                    buy_order.status = 'Partial'

                if sell_order.amount == 0:
                    sell_order.status = 'Completed'
                    j += 1  # move to the next sell order
                else:
                    sell_order.status = 'Partial'

            else:
                # If the current buy price is less than the sell price,
                # no further sell orders will match (they're even more expensive).
                break

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"Error in match_orders: {e}")

    return matched_orders


# Submit order api
@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        data = request.json # get the data from the request
        new_order = Order(user=data['user'], order_type=data['type'], amount=data['amount'], price=data['price']) # create a new order
        db.session.add(new_order) # add the order to the database
        db.session.commit()
        
        trades = match_orders()

        return jsonify({'message': 'Order submitted successfully','matched_trades':trades}) # return a message
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {e}'}), 400

# Get order api
@app.route('/get_orders', methods=['GET'])
def get_orders():
    orders = Order.query.all() # get all orders from the database
    order_list = [{'id': o.id,'user': o.user,'type': o.order_type,'amount': o.amount,'price': o.price,'status': o.status} for o in orders]
    return jsonify(order_list)

# Search order api
@app.route('/get_trades', methods=['GET'])
def get_trades():
    trades = Trade.query.all() # get all trades from the database
    trade_list = [{'id': t.id, 'buyer': t.buyer, 'seller': t.seller, 'amount': t.amount, 'price': t.price, 'timestamp': t.timestamp} for t in trades]
    return jsonify(trade_list)

if __name__ == '__main__':
    app.run(debug=True)