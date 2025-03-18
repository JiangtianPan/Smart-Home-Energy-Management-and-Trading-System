import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import Dataset, DataLoader

class PowerDataset(Dataset):
    """自定义时间序列数据集"""
    def __init__(self, data, lookback, forecast_steps):
        self.X, self.y = [], []
        for i in range(len(data)-lookback-forecast_steps):
            self.X.append(data[i:(i+lookback)])
            self.y.append(data[i+lookback : i+lookback+forecast_steps, 0])
        
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return torch.tensor(self.X[idx], dtype=torch.float), \
               torch.tensor(self.y[idx], dtype=torch.float)

class LSTMModel(nn.Module):
    """精简后的LSTM预测模型"""
    def __init__(self, input_size, hidden_size, output_steps, num_layers=2, dropout=0.1):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers>1 else 0
        )
        # 添加层标准化
        self.ln1 = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(dropout)
        # 修改初始化方式
        self.linear = nn.Linear(hidden_size, output_steps)
        self._init_weights()
    
    def _init_weights(self):
        """改进的权重初始化"""
        for name, param in self.lstm.named_parameters():
            if 'weight_ih' in name:
                nn.init.kaiming_normal_(param.data)
            elif 'weight_hh' in name:
                nn.init.orthogonal_(param.data)
            elif 'bias' in name:
                nn.init.constant_(param.data, 0)
        nn.init.xavier_normal_(self.linear.weight)
        
    def forward(self, x):
        # LSTM层
        # print('LSTM 0:', x.size(), x)
        out, (h_n, c_n) = self.lstm(x)
        # print('LSTM 1:', out.size(), out) # [24, 64]
        # 取最后一个时间步的输出
        out = out[:, -1, :]  
        # print('LSTM 2:', out.size(), out)
        out = self.ln1(out)
        # Dropout
        out = self.dropout(out)
        # print('LSTM 3:', out.size(), out)
        # 全连接层
        out = self.linear(out)
        # print('LSTM 4:', out.size(), out)
        return out

class PowerPredictor:
    """精简后的预测类"""
    def __init__(self, model_path):
        # 加载预训练模型
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = LSTMModel(
            input_size=7,       # 根据数据特征数设定
            hidden_size=64,
            output_steps=6,
            num_layers=1,
            dropout=0.3
        ).to(self.device)
        self.model.load_state_dict(torch.load(model_path))
        self.model.eval()  # 设置为预测模式
        
        # 加载标准化参数
        self.scaler = MinMaxScaler()
        # scaler_params = np.load(scaler_params_path, allow_pickle=True).item()
        # self.scaler.min_ = scaler_params['min']
        # self.scaler.scale_ = scaler_params['scale']
        
        self.lookback = 24  # 与训练时一致的时间窗口

    def load_data(self, file_path):
        """加载并预处理数据"""
        # df = pd.read_csv(self.file_path, parse_dates={'datetime': ['Date', 'Time']})
        df=pd.read_csv(file_path)
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
        scaled_data = self.scaled_data[-self.lookback:]
        return scaled_data

    # def prepare_data(self, test_size=0.2):
    #     """改进的数据划分方法"""
    #     # 时间序列数据必须按时间顺序划分
    #     train_size = int(len(self.scaled_data) * (1-test_size))
    #     # train_data = self.scaled_data[:train_size]
    #     test_data = self.scaled_data[train_size-self.lookback:]  # 保持时间连续性
        
    #     # 数据增强：添加随机噪声
    #     # noise = np.random.normal(0, 1e-3, train_data.shape)
    #     # train_data = np.clip(train_data + noise, 0, 1)
        
    #     # self.train_dataset = PowerDataset(train_data, self.lookback, self.forecast_steps)
    #     self.test_dataset = PowerDataset(test_data, self.lookback, self.forecast_steps)
        
    #     # 调整batch_size
    #     # self.train_loader = DataLoader(self.train_dataset, batch_size=64, shuffle=True)
    #     self.test_loader = DataLoader(self.test_dataset, batch_size=64, shuffle=False)

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

# 使用示例
if __name__ == "__main__":
    # 初始化预测器（需预先保存模型和scaler参数）
    predictor = PowerPredictor(model_path="best_model.pth")
    
    # 模拟实时数据输入（应替换为实际数据接口）
    # test_data = pd.read_csv('household_power_consumption.csv').tail(24)
    scaled_data = predictor.load_data(file_path='household_power_consumption.csv')
    
    # 执行预测
    # processed_data = predictor.prepare_data(0.2)
    prediction = predictor.predict(scaled_data)
    print(f"未来6小时的预测值：{prediction}")