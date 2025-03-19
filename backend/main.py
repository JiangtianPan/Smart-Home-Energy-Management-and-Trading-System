import asyncio
from agents.market_agent import MarketAgent
from agents.trader_agent import TraderAgent
from utils.config import MARKET_AGENT_JID, TRADER_AGENT_JID, PASSWORD

async def main():
    market_agent = MarketAgent(MARKET_AGENT_JID, PASSWORD)
    trader_agent = TraderAgent(TRADER_AGENT_JID, PASSWORD)
    
    await market_agent.start()
    await trader_agent.start()
    
    await asyncio.sleep(2)

    # send test order
    order = {"user": "Alice", "type": "buy", "amount": 10, "price": 100}
    await trader_agent.submit_order(order)

    await asyncio.sleep(10)

    await market_agent.stop()
    await trader_agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
