import asyncio
import traceback
from backend.p2p_trading.agents.market_agent import MarketAgent
from backend.p2p_trading.agents.trader_agent import TraderAgent
from backend.p2p_trading.utils.config import MARKET_AGENT_JID, TRADER_AGENT_JID, PASSWORD

async def main():
    try:
        print("[Main] Starting P2P Trading System")
        print("[Main] Initializing market agent...")
        market_agent = MarketAgent(MARKET_AGENT_JID, PASSWORD)
        
        print("[Main] Initializing trader agent...")
        trader_agent = TraderAgent(TRADER_AGENT_JID, PASSWORD)
        
        print("[Main] Starting market agent...")
        await market_agent.start()
        print(f"[Main] Market agent started: {market_agent.jid}, alive: {market_agent.is_alive()}")
        
        print("[Main] Starting trader agent...")
        await trader_agent.start()
        print(f"[Main] Trader agent started: {trader_agent.jid}, alive: {trader_agent.is_alive()}")
        
        print("[Main] Agents started and running... Press Ctrl+C to stop.")
        
        # 可选：添加一些测试订单
        # test_order = {"user": "test_user", "type": "buy", "amount": 1.0, "price": 100.0}
        # print(f"[Main] Submitting test order: {test_order}")
        # await trader_agent.submit_order(test_order)
        
        await asyncio.Future()  # execution stops here until Ctrl+C is pressed
    except KeyboardInterrupt:
        print("[Main] Shutting down by user request (Ctrl+C)")
    except Exception as e:
        print(f"[Main] Error in main: {e}")
        print(traceback.format_exc())
    finally:
        print("[Main] Stopping agents...")
        try:
            if market_agent:
                await market_agent.stop()
            if trader_agent:
                await trader_agent.stop()
            print("[Main] Agents stopped")
        except Exception as e:
            print(f"[Main] Error stopping agents: {e}")

if __name__ == "__main__":
    asyncio.run(main())