from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

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

    def __repr__(self):
        return f"Order('{self.order_type}', '{self.amount}', '{self.price}')"

# Create the database
with app.app_context():
    db.create_all()

def match_orders():
    # Get all buy and sell orders
    buy_orders = Order.query.filter_by(order_type="buy").order_by(Order.price.desc()).all()
    sell_orders = Order.query.filter_by(order_type="sell").order_by(Order.price.asc()).all()

    matched_orders = []

    i,j=0,0

    try:
        while i < len(buy_orders) and j < len(sell_orders):
            buy_order = buy_orders[i]
            sell_order = sell_orders[j]
            
            # Check if the buy order price is greater than or equal to the sell order price
            if buy_order.price >= sell_order.price:
                trade_amount = min(buy_order.amount, sell_order.amount) # get the trade amount

                matched_orders.append({'buyer': buy_order.user, 'seller': sell_order.user, 'amount': trade_amount, 'price': sell_order.price}) # add the trade to the list

                buy_order.amount -= trade_amount # update the buy order amount
                sell_order.amount -= trade_amount # update the sell order amount

                if buy_order.amount == 0:
                    db.session.delete(buy_order) # delete the buy order if the amount is 0
                    i += 1

                if sell_order.amount == 0:
                    db.session.delete(sell_order)
                    j += 1

            else:
                j+=1
    
        db.session.commit() # commit the changes to the database
    
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
    
    return matched_orders


    
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
    order_list = [{'id': order.id, 'user': order.user, 'type': order.order_type, 'amount': order.amount, 'price': order.price} for order in orders] # create a list of orders
    return jsonify(order_list)

if __name__ == '__main__':
    app.run(debug=True)