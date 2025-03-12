# test_request.py
from spade.agent import Agent
from spade.message import Message
import asyncio
from spade.behaviour import CyclicBehaviour

class TesterAgent(Agent):
    async def setup(self):
        self.add_behaviour(self.RequestBehaviour())
        
    class RequestBehaviour(CyclicBehaviour):
        async def run(self):
            # 发送请求
            msg = Message(to="prediction_agent@your_xmpp_server")
            msg.body = "REQUEST_PREDICTION"
            await self.send(msg)
            print("\n[Test] 已发送预测请求")
            
            # 等待响应
            response = await self.receive(timeout=30)
            if response:
                print("[Test] 收到预测结果：", response.body)
            else:
                print("[Test] 请求超时")
            
            await asyncio.sleep(60)  # 每分钟请求一次

if __name__ == "__main__":
    tester = TesterAgent("tester@your_xmpp_server", "password")
    tester.start()
    
    try:
        while True:
            input("按 Enter 退出...\n")
    except KeyboardInterrupt:
        tester.stop()