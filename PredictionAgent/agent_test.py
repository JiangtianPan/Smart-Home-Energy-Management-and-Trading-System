# # test_request.py
# from spade.agent import Agent
# from spade.message import Message
# import asyncio
# from spade.behaviour import CyclicBehaviour

# class TesterAgent(Agent):
#     async def setup(self):
#         self.add_behaviour(self.RequestBehaviour())
        
#     class RequestBehaviour(CyclicBehaviour):
#         async def run(self):
#             # 发送请求
#             msg = Message(to="prediction_agent@your_xmpp_server")
#             msg.body = "REQUEST_PREDICTION"
#             await self.send(msg)
#             print("\n[Test] 已发送预测请求")
            
#             # 等待响应
#             response = await self.receive(timeout=30)
#             if response:
#                 print("[Test] 收到预测结果：", response.body)
#             else:
#                 print("[Test] 请求超时")
            
#             await asyncio.sleep(60)  # 每分钟请求一次

# if __name__ == "__main__":
#     tester = TesterAgent("tester@your_xmpp_server", "password")
#     tester.start()
    
#     try:
#         while True:
#             input("按 Enter 退出...\n")
#     except KeyboardInterrupt:
#         tester.stop()

import logging
logging.basicConfig(level=logging.DEBUG)
from prediction_agent_v2 import PredictionAgent
import asyncio

async def run_agent():
    # 使用 sure.im 前需通过其官网注册账户：https://www.sure.im/
    agent = PredictionAgent("prediction_agent@sure.im", "123456")
    await agent.start()
    await asyncio.sleep(5)  # 保持连接5秒
    await agent.stop()

asyncio.run(run_agent())