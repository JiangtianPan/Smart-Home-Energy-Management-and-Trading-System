from flask import Flask, request, jsonify
import asyncio
import threading
from p2p_trading.agents.trader_agent import TraderAgent
from p2p_trading.agents.market_agent import MarketAgent
from p2p_trading.utils.db_helper import get_open_orders
from p2p_trading.utils.config import TRADER_AGENT_JID, MARKET_AGENT_JID, PASSWORD

app = Flask(__name__)

# initialize agents
trader_agent = TraderAgent(TRADER_AGENT_JID, PASSWORD)
market_agent = MarketAgent(MARKET_AGENT_JID, PASSWORD)

# spade agent 
async def start_agents():
    await market_agent.start()
    await trader_agent.start()

def run_agents():
    asyncio.run(start_agents())

threading.Thread(target=run_agents).start()

# api submit_order
@app.route("/submit_order", methods=["POST"])
def submit_order():
    data = request.json
    required = ["user", "type", "amount", "price"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(trader_agent.submit_order(data))
    return jsonify({"message": "Order submitted"})

# api get_orders
@app.route("/orders", methods=["GET"])
def get_orders():
    return jsonify(get_open_orders())

if __name__ == "__main__":
    app.run(port=5000, debug=True)
