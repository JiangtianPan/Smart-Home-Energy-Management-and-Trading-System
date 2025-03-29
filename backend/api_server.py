from flask import Flask, request, jsonify
from flask import send_from_directory
import os
import asyncio
import threading
import traceback
from p2p_trading.agents.trader_agent import TraderAgent
from p2p_trading.agents.market_agent import MarketAgent
from p2p_trading.utils.db_helper import get_open_orders
from p2p_trading.utils.config import TRADER_AGENT_JID, MARKET_AGENT_JID, PASSWORD
import time

app = Flask(__name__)

# create a new event loop for the agents
# This is necessary because Flask and Spade both use asyncio, and we need to manage them separately
event_loop = asyncio.new_event_loop()

# initialize agents
trader_agent = None
market_agent = None

# spade agent 
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

# initialize and start the agent thread
agent_thread = threading.Thread(target=run_agents, daemon=True)
agent_thread.start()

# api submit_order
@app.route("/submit_order", methods=["POST"])
def submit_order():
    try:
        print("[API] Received order submission request")
        data = request.json
        print(f"[API] Order data: {data}")
        
        required = ["user", "type", "amount", "price"]
        if not all(k in data for k in required):
            print(f"[API] Missing required fields in order")
            return jsonify({"error": "Missing fields"}), 400

        # ensure the order is valid
        if trader_agent is None or not trader_agent.is_alive():
            print(f"[API] Trader agent not ready")
            return jsonify({"error": "Trading system not ready"}), 503

        # create a new order
        print(f"[API] Submitting order to trader agent")
        future = asyncio.run_coroutine_threadsafe(trader_agent.submit_order(data), event_loop)
        future.result(timeout=5)  # wait for the order to be processed
        
        print(f"[API] Order submitted successfully")
        return jsonify({"message": "Order submitted"})
    except Exception as e:
        print(f"[API] Error submitting order: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# api get_orders
@app.route("/orders", methods=["GET"])
def get_orders():
    try:
        print("[API] Received request for open orders")
        orders = get_open_orders()
        print(f"[API] Returning {len(orders)} open orders")
        return jsonify(orders)
    except Exception as e:
        print(f"[API] Error getting orders: {e}")
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

# health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    try:
        agent_status = {
            "trader_agent": "running" if trader_agent and trader_agent.is_alive() else "not running",
            "market_agent": "running" if market_agent and market_agent.is_alive() else "not running"
        }
        return jsonify({
            "status": "ok",
            "agents": agent_status
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    try:
        # wait for agents to initialize
        print("[Server] Waiting for agents to initialize...")
        time.sleep(2)
        
        print("[Server] Starting Flask server...")
        app.run(port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[Server] Server startup error: {e}")
        print(traceback.format_exc())