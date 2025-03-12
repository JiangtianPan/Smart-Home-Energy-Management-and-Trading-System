from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour, CyclicBehaviour
from spade.message import Message
import torch
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import json
import asyncio

from prediction_agent import LSTMModel

# 继承原有预测类（仅保留预测相关部分）
class PowerPredictor:
    def __init__(self, model_path='best_model.pth'):
        # input_size = self.scaled_data.shape[1]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = LSTMModel(
            input_size=7,
            hidden_size=64,
            output_steps=6,
            num_layers=1,  # 单层LSTM
            dropout=0.3  # 更高的dropout比例
        ).to(self.device)
        # self.model = torch.load(model_path, map_location='cpu')
        self.model.load_state_dict(torch.load('best_model.pth'))
        self.model.eval()
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.lookback = 24  # 与训练时一致的窗口大小
        
        # 加载训练时的scaler参数（假设已保存）
        # self.scaler_params = np.load('scaler_params.npy', allow_pickle=True).item()
        # self.scaler.min_ = self.scaler_params['min']
        # self.scaler.scale_ = self.scaler_params['scale']
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def preprocess(self, raw_data):
        """实时数据预处理（与训练时一致）"""
        # 1. 填充缺失值
        raw_data.fillna(method='ffill', inplace=True)
        raw_data.fillna(method='bfill', inplace=True)
        
        # 2. 标准化
        # scaled = self.scaler.transform(raw_data)
        scaled = self.scaler.fit_transform(raw_data)
        
        # 3. 构建输入序列
        return scaled[-self.lookback:].reshape(1, self.lookback, -1)

    def predict(self, input_data):
        """执行预测"""
        with torch.no_grad():
            tensor_data = torch.tensor(input_data, dtype=torch.float32)
            prediction = self.model(tensor_data).numpy()
        
        # 逆标准化
        dummy = np.zeros((prediction.shape[1], 7))  # 7个特征
        dummy[:, 0] = prediction[0]  # 假设预测第一个特征（Global_active_power）
        return self.scaler.inverse_transform(dummy)[:, 0]

# SPADE Agent 实现
class PredictionAgent(Agent):
    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        self.predictor = PowerPredictor()
        self.latest_data = None
        self.current_prediction = None

    async def setup(self):
        # 注册核心行为
        self.add_behaviour(self.DataFetchBehaviour(period=300))   # 5分钟获取数据
        self.add_behaviour(self.PredictionBehaviour(period=3600)) # 每小时预测
        self.add_behaviour(self.MessageHandlerBehaviour())       # 处理请求

    # 行为1：模拟数据获取
    class DataFetchBehaviour(PeriodicBehaviour):
        async def run(self):
            """模拟实时数据获取（实际应替换为真实数据源）"""
            try:
                # 示例：生成随机数据（保留特征结构）
                new_data = pd.DataFrame({
                    'Global_active_power': np.random.uniform(0.1, 5.0, 60),
                    'Global_reactive_power': np.random.uniform(0.0, 0.5, 60),
                    'Voltage': np.random.normal(240, 2, 60),
                    # ... 其他特征 ...
                })
                self.agent.latest_data = new_data
                print(f"[Prediction] Fetched {len(new_data)} new samples")
            except Exception as e:
                print(f"Data fetch error: {str(e)}")

    # 行为2：周期预测
    class PredictionBehaviour(PeriodicBehaviour):
        async def run(self):
            if self.agent.latest_data is not None:
                try:
                    # 打印原始输入数据
                    print("\n[Input Raw] 原始输入数据维度：", self.agent.latest_data.shape)
                    # 预处理
                    processed = self.agent.predictor.preprocess(self.agent.latest_data)
                    
                    # 执行预测
                    prediction = self.agent.predictor.predict(processed)
                    self.agent.current_prediction = {
                        'timestamp': pd.Timestamp.now().isoformat(),
                        'hourly_production': float(prediction[0]),  # 示例值
                        'hourly_consumption': float(prediction[1])
                    }

                    # 打印预测结果
                    print("\n[Output Prediction] 预测结果：")
                    print(f"生产预测: {self.agent.current_prediction['hourly_production']} kW")
                    print(f"消费预测: {self.agent.current_prediction['hourly_consumption']} kW")
                    
                    # 发送给协商Agent
                    msg = Message(to="negotiation_agent@your_domain")
                    msg.set_metadata("performative", "inform")
                    msg.body = json.dumps(self.agent.current_prediction)
                    await self.send(msg)
                    print("[Prediction] Sent new prediction")
                except Exception as e:
                    print(f"预测失败: {str(e)}")
                    error_msg = Message(to="monitor@your_domain")
                    error_msg.body = json.dumps({
                        "agent": str(self.agent.jid),
                        "error": f"Prediction failed: {str(e)}"
                    })
                    await self.send(error_msg)

    # 行为3：处理外部请求
    class MessageHandlerBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                # 处理预测结果请求
                if msg.body == "REQUEST_PREDICTION":
                    response = msg.make_reply()
                    response.body = json.dumps(
                        self.agent.current_prediction or {"status": "no_data"}
                    )
                    await self.send(response)

                # 处理数据更新指令
                elif "UPDATE_DATA" in msg.body:
                    try:
                        new_data = pd.read_json(msg.body.split("|")[1])
                        self.agent.latest_data = new_data
                        print("[Prediction] Received new data update")
                    except Exception as e:
                        print(f"Data update error: {str(e)}")

if __name__ == "__main__":
    agent = PredictionAgent(
        "prediction_agent@your_xmpp_server",
        "password"
    )
    agent.start()
    
    # 保持Agent运行
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()

# // 发送给协商Agent的预测消息
# {
#   "timestamp": "2023-10-01T14:30:00",
#   "hourly_production": 12.5,
#   "hourly_consumption": 9.8
# }

# // 错误报告消息
# {
#   "agent": "prediction_agent@your_domain",
#   "error": "Prediction failed: invalid input shape"
# }