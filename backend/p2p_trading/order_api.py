from flask import Flask, request, jsonify

app = Flask(__name__)

# temporary storage for orders
orders = []

@app.route('/submit_order', methods=['POST'])
def submit_order():
    data = request.json # get the data from the request
    orders.append(data) # add the order to the list of orders
    return jsonify({'message': 'Order submitted successfully','orders': orders}) # return a response

@app.route('/get_orders', methods=['GET'])
def get_orders():
    return jsonify({'orders': orders}) # return orders

if __name__ == '__main__':
    app.run(debug=True)