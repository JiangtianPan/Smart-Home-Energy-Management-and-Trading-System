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
    
@app.route('/submit_order', methods=['POST'])
def submit_order():
    data = request.json # get the data from the request
    new_order = Order(user=data['user'], order_type=data['type'], amount=data['amount'], price=data['price']) # create a new order
    db.session.add(new_order) # add the order to the database
    db.session.commit()
    return jsonify({'message': 'Order submitted successfully'}) # return a message

@app.route('/get_orders', methods=['GET'])
def get_orders():
    orders = Order.query.all() # get all orders from the database
    order_list = [{'id': order.id, 'user': order.user, 'type': order.order_type, 'amount': order.amount, 'price': order.price} for order in orders] # create a list of orders
    return jsonify(order_list)

if __name__ == '__main__':
    app.run(debug=True)