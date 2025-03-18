from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour, CyclicBehaviour
from spade.message import Message
import torch
from torch.utils.data import DataLoader
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import json
import asyncio
import random

from predictor import LSTMModel

# 配置日志
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PredictionAgent")

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
        

    def load_data(self, data_path='./household_power_consumption.csv'):
        """加载并预处理数据"""
        # df = pd.read_csv(self.file_path, parse_dates={'datetime': ['Date', 'Time']})
        df=pd.read_csv(data_path)
        df=df.drop('index',axis=1)
        df['Date']=pd.to_datetime(df['Date'])
        df['Time']=pd.to_datetime(df['Time'])
        df=df.sort_values('Date')
        df['Sub_metering_1']=df['Sub_metering_1'].replace({'?':'0'})
        df['Sub_metering_2']=df['Sub_metering_2'].replace({'?':'0'})
        df['Sub_metering_1']=pd.DataFrame(np.array(df['Sub_metering_1'],dtype='float32'))
        df['Sub_metering_2']=pd.DataFrame(np.array(df['Sub_metering_2'],dtype='float32'))
        # df['Sub_metering_3']=df['Sub_metering_3'].fillna(method='bfill')
        df['Global_active_power']=df['Global_active_power'].replace({'?':0.214})
        df['Global_reactive_power']=df['Global_reactive_power'].replace({'?':0.1})
        df[['Global_reactive_power','Global_active_power']]=pd.DataFrame(np.array(df[['Global_reactive_power','Global_active_power']],dtype='float32'))
        df['Voltage']=df['Voltage'].replace({'?':240})
        df['Voltage']=pd.DataFrame(np.array(df['Voltage'],dtype='float32'))
        df['Global_intensity']=df['Global_intensity'].replace({'?':1.4})
        df['Global_intensity']=pd.DataFrame(np.array(df['Global_intensity'],dtype='float32'))
        # df.set_index('datetime', inplace=True)

        # 选择特征列
        features = ['Global_active_power', 'Global_reactive_power', 'Voltage',
                    'Global_intensity', 'Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']
        self.df = df[features]
        # print(self.df)

        # 处理缺失值
        self.df.replace(0, np.nan, inplace=True)
        self.df.ffill(inplace=True)
        self.df.bfill(inplace=True)
        # print(self.df)

        # 处理常数列问题
        for col in self.df.columns:
            if np.isclose(self.df[col].std(), 0):  # 标准差接近0
                self.df[col] += np.random.normal(0, 1e-6, size=len(self.df))  # 添加噪声

        # 数据标准化
        # self.scaled_data = self.scaler.fit_transform(self.df)

        # 改进的标准化流程
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.scaled_data = self.scaler.fit_transform(self.df)
        
        # 数据校验
        assert not np.isnan(self.scaled_data).any(), "存在NaN值"
        assert not np.isinf(self.scaled_data).any(), "存在无穷值"

        data_length = len(self.scaled_data)

        start = random.randint(0, data_length)
        
        scaled_data = self.scaled_data[start:start+self.lookback]
        return scaled_data

    def predict(self, input_data):
        """执行预测"""
        with torch.no_grad():
            input_tensor = torch.tensor(input_data, dtype=torch.float)\
                .unsqueeze(0).to(self.device)
            prediction = self.model(input_tensor).cpu().numpy()
        
        # 逆标准化
        dummy = np.zeros((prediction.shape[1], 7))  # 7个特征
        dummy[:, 0] = prediction[0]  # 假设预测第一个特征（Global_active_power）
        return self.scaler.inverse_transform(dummy)[:, 0]

# SPADE Agent 实现
class PredictionAgent(Agent):
    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        self.predictor = PowerPredictor(model_path="best_model.pth")
        self.latest_data = None
        self.current_prediction = None

    async def setup(self):
        # 注册核心行为
        self.add_behaviour(self.DataFetchBehaviour(period=1))   # 5分钟获取数据
        self.add_behaviour(self.PredictionBehaviour(period=12)) # 每小时预测
        self.add_behaviour(self.MessageHandlerBehaviour())       # 处理请求

    # 行为1：模拟数据获取
    class DataFetchBehaviour(PeriodicBehaviour):
        async def run(self):
            """模拟实时数据获取（实际应替换为真实数据源）"""
            try:
                # 示例：生成随机数据（保留特征结构）
                # new_data = pd.DataFrame({
                #     'Global_active_power': np.random.uniform(0.1, 5.0, 60),
                #     'Global_reactive_power': np.random.uniform(0.0, 0.5, 60),
                #     'Voltage': np.random.normal(240, 2, 60),
                #     # ... 其他特征 ...
                # })
                new_data = self.agent.predictor.load_data(data_path='household_power_consumption.csv')
                self.agent.latest_data = new_data
                print(f"[Prediction] Fetched {len(new_data)} new samples")
            except Exception as e:
                print(f"Data fetch error: {str(e)}")

    # 行为2：周期预测
    class PredictionBehaviour(PeriodicBehaviour):
        async def run(self):
            if self.agent.latest_data is not None:
                print("[DEBUG] 预测行为被触发")  # 添加调试语句
                try:
                    # 打印原始输入数据
                    print("\n[Input Raw] 原始输入数据维度：", self.agent.latest_data.shape)
                    # 预处理
                    # processed = self.agent.predictor.preprocess(self.agent.latest_data)
                    
                    # 执行预测
                    prediction = self.agent.predictor.predict(self.agent.latest_data)
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
            else:
                print("[Prediction] NO DATA !!!")

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

async def run_agent():
    # 使用 sure.im 前需通过其官网注册账户：https://www.sure.im/
    agent = PredictionAgent("prediction_agent@sure.im", "123456")
    await agent.start()  # 关键：使用await
    
    # 保持Agent运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await agent.stop()

# if __name__ == "__main__":
#     agent = PredictionAgent(
#         "prediction_agent@your_xmpp_server",
#         "password"
#     )
#     agent.start()
    
#     # 保持Agent运行
#     import time
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         agent.stop()

if __name__ == "__main__":
    asyncio.run(run_agent())  # 通过事件循环启动

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