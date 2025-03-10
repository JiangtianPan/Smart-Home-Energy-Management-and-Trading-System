from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# SQLite storage for orders
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Order Model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50), nullable=False)
    order_type = db.Column(db.String(10), nullable=False)  # Buy and sell
    order_mode = db.Column(db.String(10), nullable=False, default='limit')  # Limit and market
    amount = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=True)  # Market order does not require price
    status = db.Column(db.String(20), nullable=False, default='Pending')
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Time of order submission

    def __repr__(self):
        return (f"Order(id={self.id}, user={self.user}, type={self.order_type}, mode={self.order_mode}, "
                f"amount={self.amount}, price={self.price}, status={self.status})")


# Trade Model
class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer = db.Column(db.String(50), nullable=False)
    seller = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Trade('{self.buyer}', '{self.seller}', '{self.amount}', '{self.price}')"


# Create database
with app.app_context():
    db.create_all()


def match_orders():
    """
    Match buy and sell orders, supporting both limit orders and market orders.
    - Market buy orders match the lowest price sell orders.
    - Market sell orders match the highest price buy orders.
    - Limit orders match based on price and FIFO rule.
    """

    # Get market and limit orders
    market_buy_orders = Order.query.filter_by(order_type="buy", order_mode="market", status="Pending").all()
    market_sell_orders = Order.query.filter_by(order_type="sell", order_mode="market", status="Pending").all()

    limit_buy_orders = Order.query.filter(
        Order.order_type == "buy",
        Order.order_mode == "limit",
        Order.status.in_(["Pending", "Partial"])
    ).order_by(Order.price.desc(), Order.timestamp.asc()).all()  # Price descending, time ascending

    limit_sell_orders = Order.query.filter(
        Order.order_type == "sell",
        Order.order_mode == "limit",
        Order.status.in_(["Pending", "Partial"])
    ).order_by(Order.price.asc(), Order.timestamp.asc()).all()  # Price ascending, time ascending

    matched_orders = []

    # Market buy orders
    for buy_order in market_buy_orders:
        while buy_order.amount > 0 and limit_sell_orders:
            sell_order = limit_sell_orders[0]  # Get the lowest price sell order

            trade_amount = min(buy_order.amount, sell_order.amount)
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

            buy_order.amount -= trade_amount
            sell_order.amount -= trade_amount

            if buy_order.amount == 0:
                buy_order.status = 'Completed'
            else:
                buy_order.status = 'Partial'

            if sell_order.amount == 0:
                sell_order.status = 'Completed'
                limit_sell_orders.pop(0)  # Delete the completed sell order
            else:
                sell_order.status = 'Partial'

    # Market sell orders
    for sell_order in market_sell_orders:
        while sell_order.amount > 0 and limit_buy_orders:
            buy_order = limit_buy_orders[0]  # Cancel the highest price buy order

            trade_amount = min(sell_order.amount, buy_order.amount)
            trade = Trade(
                buyer=buy_order.user,
                seller=sell_order.user,
                amount=trade_amount,
                price=buy_order.price
            )
            db.session.add(trade)

            matched_orders.append({
                'buyer': buy_order.user,
                'seller': sell_order.user,
                'amount': trade_amount,
                'price': buy_order.price
            })

            sell_order.amount -= trade_amount
            buy_order.amount -= trade_amount

            if sell_order.amount == 0:
                sell_order.status = 'Completed'
            else:
                sell_order.status = 'Partial'

            if buy_order.amount == 0:
                buy_order.status = 'Completed'
                limit_buy_orders.pop(0)  # Delete the completed buy order
            else:
                buy_order.status = 'Partial'

    db.session.commit()
    return matched_orders


# Submit order API
@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        data = request.json
        new_order = Order(
            user=data['user'],
            order_type=data['type'],
            order_mode=data.get('mode', 'limit'),  # Default limit order
            amount=data['amount'],
            price=data.get('price')  # Market order does not require price
        )
        db.session.add(new_order)
        db.session.commit()

        trades = match_orders()

        return jsonify({'message': 'Order submitted successfully', 'matched_trades': trades})

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {e}'}), 400


# Get all orders API
@app.route('/get_orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    order_list = [{'id': o.id, 'user': o.user, 'type': o.order_type, 'mode': o.order_mode,
                   'amount': o.amount, 'price': o.price, 'status': o.status, 'timestamp': o.timestamp} for o in orders]
    return jsonify(order_list)


# Get all trade records API
@app.route('/get_trades', methods=['GET'])
def get_trades():
    trades = Trade.query.all()
    trade_list = [{'id': t.id, 'buyer': t.buyer, 'seller': t.seller, 'amount': t.amount,
                   'price': t.price, 'timestamp': t.timestamp} for t in trades]
    return jsonify(trade_list)


if __name__ == '__main__':
    app.run(debug=True)
