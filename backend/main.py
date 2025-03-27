import asyncio
from backend.p2p_trading.agents.market_agent import MarketAgent
from backend.p2p_trading.agents.trader_agent import TraderAgent
from backend.p2p_trading.utils.config import MARKET_AGENT_JID, TRADER_AGENT_JID, PASSWORD

async def main():
    market_agent = MarketAgent(MARKET_AGENT_JID, PASSWORD)
    trader_agent = TraderAgent(TRADER_AGENT_JID, PASSWORD)

    await market_agent.start()
    await trader_agent.start()

    print("[Main] Agents started and running... Press Ctrl+C to stop.")
    await asyncio.Future()  # execution stops here until Ctrl+C is pressed

if __name__ == "__main__":
    asyncio.run(main())