from flask import Flask, request, jsonify, session, send_from_directory
import os
import asyncio
import threading
import traceback
import functools
import time
from p2p_trading.agents.trader_agent import TraderAgent
from p2p_trading.agents.market_agent import MarketAgent
from p2p_trading.utils.db_helper import get_open_orders, DatabaseManager
from p2p_trading.utils.user_manager import UserManager
from p2p_trading.utils.model_interface import ModelInterface
from p2p_trading.utils.config import TRADER_AGENT_JID, MARKET_AGENT_JID, PASSWORD

app = Flask(__name__)
app.secret_key = "p2p-trading-secret-key"  # Used for session management

# Initialize event loop for agents
event_loop = asyncio.new_event_loop()

# Initialize agents
trader_agent = None
market_agent = None

# Initialize user manager
user_manager = UserManager()

# Initialize model interface
model_interface = ModelInterface()

# Login required decorator
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# SPADE agent initialization
async def start_agents():
    global trader_agent, market_agent
    try:
        print("[Server] Starting market agent...")
        market_agent = MarketAgent(MARKET_AGENT_JID, PASSWORD)
        await market_agent.start()
        print(f"[Server] Market agent started: {market_agent.jid}, alive: {market_agent.is_alive()}")
        
        print("[Server] Starting trader agent...")
        trader_agent = TraderAgent(TRADER_AGENT_JID, PASSWORD)
        await trader_agent.start()
        print(f"[Server] Trader agent started: {trader_agent.jid}, alive: {trader_agent.is_alive()}")
        
        print("[Server] Both agents are now running")
    except Exception as e:
        print(f"[Server] Error starting agents: {e}")
        print(traceback.format_exc())

def run_agents():
    try:
        print("[Server] Setting up agent thread")
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(start_agents())
        print("[Server] Agents started, now running event loop forever")
        event_loop.run_forever()
    except Exception as e:
        print(f"[Server] Error in agent thread: {e}")
        print(traceback.format_exc())

# Initialize and start the agent thread
agent_thread = threading.Thread(target=run_agents, daemon=True)
agent_thread.start()

# User authentication endpoints
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        if "username" not in data or "password" not in data:
            return jsonify({"error": "Username and password required"}), 400
        
        success, result = user_manager.authenticate_user(data["username"], data["password"])
        
        if success:
            session["username"] = data["username"]
            return jsonify({"success": True, "username": data["username"]}), 200
        else:
            return jsonify({"error": result}), 401
    except Exception as e:
        print(f"[API] Login error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"success": True, "message": "Logged out successfully"}), 200

@app.route("/current_user", methods=["GET"])
def current_user():
    if "username" in session:
        return jsonify({"logged_in": True, "username": session["username"]}), 200
    else:
        return jsonify({"logged_in": False}), 200

# API: submit order
@app.route("/submit_order", methods=["POST"])
@login_required
def submit_order():
    try:
        print("[API] Received order submission request")
        data = request.json
        print(f"[API] Order data: {data}")
        
        required = ["type", "amount", "price"]
        if not all(k in data for k in required):
            print(f"[API] Missing required fields in order")
            return jsonify({"error": "Missing fields"}), 400

        # Add the current user to the order
        data["user"] = session["username"]
        
        # Ensure the order is valid
        if trader_agent is None or not trader_agent.is_alive():
            print(f"[API] Trader agent not ready")
            return jsonify({"error": "Trading system not ready"}), 503

        # Create a new order
        print(f"[API] Submitting order to trader agent")
        future = asyncio.run_coroutine_threadsafe(trader_agent.submit_order(data), event_loop)
        future.result(timeout=5)  # Wait for the order to be processed
        
        print(f"[API] Order submitted successfully")
        return jsonify({"message": "Order submitted"}), 200
    except Exception as e:
        print(f"[API] Error submitting order: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# API: get orders
@app.route("/orders", methods=["GET"])
@login_required
def get_orders():
    try:
        print("[API] Received request for open orders")
        orders = get_open_orders()
        
        # For demo purposes, show all orders
        # In a real system, you might want to filter or tag orders differently
        print(f"[API] Returning {len(orders)} open orders")
        return jsonify(orders), 200
    except Exception as e:
        print(f"[API] Error getting orders: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# API: get user's orders only
@app.route("/my_orders", methods=["GET"])
@login_required
def get_my_orders():
    try:
        print(f"[API] Received request for {session['username']}'s orders")
        db = DatabaseManager()
        all_orders = db.get_all_orders()
        
        # Filter orders to only show the current user's orders
        user_orders = [o for o in all_orders if o.get("user") == session["username"]]
        
        print(f"[API] Found {len(user_orders)} orders for {session['username']}")
        return jsonify(user_orders), 200
    except Exception as e:
        print(f"[API] Error getting user orders: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# API: delete order
@app.route("/delete_order/<int:order_id>", methods=["DELETE"])
@login_required
def delete_order(order_id):
    try:
        print(f"[API] Received request to delete order: {order_id}")
        db = DatabaseManager()
        
        # Get the order
        orders = db.get_all_orders()
        order = next((o for o in orders if o.get('id') == order_id), None)
        
        # Check if order exists
        if not order:
            return jsonify({"error": "Order not found"}), 404
            
        # Check if the order belongs to the current user
        if order["user"] != session["username"]:
            return jsonify({"error": "You can only delete your own orders"}), 403
        
        # Delete the order
        result = db.delete_order(order_id)
        
        if result:
            return jsonify({"message": f"Order {order_id} deleted successfully"}), 200
        else:
            return jsonify({"error": "Order not found or could not be deleted"}), 404
    except Exception as e:
        print(f"[API] Error deleting order: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# API: get trade history
@app.route("/trade_history", methods=["GET"])
@login_required
def get_trade_history():
    try:
        print("[API] Received request for trade history")
        db = DatabaseManager()
        matched_orders = db.get_matched_orders()
        
        # For demo purposes, show all matched orders
        # In a real system, you might want to filter by user or provide more context
        print(f"[API] Found {len(matched_orders)} matched orders")
        return jsonify(matched_orders), 200
    except Exception as e:
        print(f"[API] Error getting trade history: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# Model Interface API endpoints

# API: predict energy production
@app.route("/api/predict_production", methods=["POST"])
@login_required
def predict_production():
    try:
        data = request.json
        if "location" not in data or "time_period" not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        result = model_interface.predict_energy_production(
            data["location"], data["time_period"]
        )
        return jsonify(result), 200
    except Exception as e:
        print(f"[API] Prediction error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# API: predict energy consumption
@app.route("/api/predict_consumption", methods=["POST"])
@login_required
def predict_consumption():
    try:
        data = request.json
        if "user_profile" not in data or "time_period" not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        result = model_interface.predict_energy_consumption(
            data["user_profile"], data["time_period"]
        )
        return jsonify(result), 200
    except Exception as e:
        print(f"[API] Prediction error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# API: get optimal price
@app.route("/api/optimal_price", methods=["POST"])
@login_required
def get_optimal_price():
    try:
        data = request.json
        if "order_type" not in data or "market_data" not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        result = model_interface.get_optimal_price(
            data["order_type"], data["market_data"]
        )
        return jsonify(result), 200
    except Exception as e:
        print(f"[API] Optimal price error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# API: get appliance priorities
@app.route("/api/appliance_priority", methods=["POST"])
@login_required
def get_appliance_priority():
    try:
        data = request.json
        if "user_id" not in data or "appliances" not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        result = model_interface.get_appliance_priority(
            data["user_id"], data["appliances"]
        )
        return jsonify(result), 200
    except Exception as e:
        print(f"[API] Appliance priority error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# API: get demand response action
@app.route("/api/demand_response", methods=["POST"])
@login_required
def get_demand_response_action():
    try:
        data = request.json
        if "grid_status" not in data or "user_profile" not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        result = model_interface.get_demand_response_action(
            data["grid_status"], data["user_profile"]
        )
        return jsonify(result), 200
    except Exception as e:
        print(f"[API] Demand response error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# API: get model status
@app.route("/api/model_status", methods=["GET"])
@login_required
def get_model_status():
    try:
        return jsonify({
            "models_available": model_interface.models_available,
            "message": "These interfaces are reserved for future integration with mathematical models"
        }), 200
    except Exception as e:
        print(f"[API] Model status error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    try:
        print("[API] Serving frontend index.html")
        frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
        print(f"[API] Frontend path: {frontend_path}")
        return send_from_directory(frontend_path, 'index.html')
    except Exception as e:
        print(f"[API] Error serving frontend: {e}")
        print(traceback.format_exc())
        return f"Error: {str(e)}", 500

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    try:
        agent_status = {
            "trader_agent": "running" if trader_agent and trader_agent.is_alive() else "not running",
            "market_agent": "running" if market_agent and market_agent.is_alive() else "not running"
        }
        return jsonify({
            "status": "ok",
            "agents": agent_status,
            "user_logged_in": "username" in session,
            "models_available": model_interface.models_available
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    try:
        # Wait for agents to initialize
        print("[Server] Waiting for agents to initialize...")
        time.sleep(2)
        
        print("[Server] Starting Flask server...")
        app.run(port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[Server] Server startup error: {e}")
        print(traceback.format_exc())