import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt


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
    """LSTM预测模型"""
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

    # def _init_weights(self):
    #     """权重初始化"""
    #     for name, param in self.lstm.named_parameters():
    #         if 'weight_ih' in name:
    #             nn.init.xavier_normal_(param.data)
    #         elif 'weight_hh' in name:
    #             nn.init.orthogonal_(param.data)
    #         elif 'bias' in name:
    #             param.data.fill_(0)
                
    #     nn.init.kaiming_normal_(self.linear.weight)

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
        # print('LSTM 0:', x.size(), x) # [64, 24, 7]
        out, (h_n, c_n) = self.lstm(x)
        # print('LSTM 1:', out.size(), out) # [64, 24, 64]
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
    def __init__(self, file_path):
        self.eps = 1e-8
        self.file_path = file_path
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        self.lookback = 24    # 时间窗口
        self.forecast_steps = 6  # 预测步长
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.best_val_loss = float('inf')
        self.early_stop_patience = 5
        self.no_improve_count = 0

    def load_data(self):
        """加载并预处理数据"""
        # df = pd.read_csv(self.file_path, parse_dates={'datetime': ['Date', 'Time']})
        df=pd.read_csv('./household_power_consumption.csv')
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

    # def load_data(self):
    #     """数据加载与预处理"""
    #     df = pd.read_csv(self.file_path, parse_dates={'datetime': ['Date', 'Time']})
    #     df.set_index('datetime', inplace=True)
        
    #     features = ['Global_active_power', 'Global_reactive_power', 'Voltage',
    #                'Global_intensity', 'Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']
    #     self.df = df[features]
        
    #     # 处理缺失值
    #     self.df.replace(0, np.nan, inplace=True)
    #     self.df.ffill(inplace=True)
        
    #     # 标准化
    #     self.scaled_data = self.scaler.fit_transform(self.df)

    # def prepare_data(self, test_size=0.2):
    #     """准备数据集"""
    #     train_size = int(len(self.scaled_data) * (1-test_size))
    #     train_data = self.scaled_data[:train_size]
    #     test_data = self.scaled_data[train_size:]
        
    #     self.train_dataset = PowerDataset(train_data, self.lookback, self.forecast_steps)
    #     self.test_dataset = PowerDataset(test_data, self.lookback, self.forecast_steps)
        
    #     self.train_loader = DataLoader(
    #         self.train_dataset, 
    #         batch_size=32, 
    #         shuffle=True
    #     )
    #     self.test_loader = DataLoader(
    #         self.test_dataset, 
    #         batch_size=32, 
    #         shuffle=False
    #     )

    def prepare_data(self, test_size=0.2):
        """改进的数据划分方法"""
        # 时间序列数据必须按时间顺序划分
        train_size = int(len(self.scaled_data) * (1-test_size))
        train_data = self.scaled_data[:train_size]
        test_data = self.scaled_data[train_size-self.lookback:]  # 保持时间连续性
        
        # 数据增强：添加随机噪声
        noise = np.random.normal(0, 1e-3, train_data.shape)
        train_data = np.clip(train_data + noise, 0, 1)
        
        self.train_dataset = PowerDataset(train_data, self.lookback, self.forecast_steps)
        self.test_dataset = PowerDataset(test_data, self.lookback, self.forecast_steps)
        
        # 调整batch_size
        self.train_loader = DataLoader(self.train_dataset, batch_size=64, shuffle=True)
        self.test_loader = DataLoader(self.test_dataset, batch_size=64, shuffle=False)

    def build_model(self, hidden_size=64):
        """构建模型"""
        input_size = self.scaled_data.shape[1]
        self.model = LSTMModel(
            input_size=input_size,
            hidden_size=hidden_size,
            output_steps=self.forecast_steps,
            num_layers=1,  # 单层LSTM
            dropout=0.3  # 更高的dropout比例
        ).to(self.device)

    def train(self, epochs=50):
        """训练模型"""
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=1e-3, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=3)
        train_losses, val_losses = [], []
        
        for epoch in range(epochs):
            # 训练阶段
            self.model.train()
            epoch_train_loss = 0
            iteration = 0
            for X_batch, y_batch in self.train_loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(X_batch)
                # print(X_batch.shape, outputs.shape, y_batch.shape) # torch.Size([64, 24, 7]) torch.Size([64, 6]) torch.Size([64, 6])
                # loss = criterion(outputs, y_batch) + self.eps
                loss = criterion(outputs, y_batch)*1000
                # print(epoch, iteration, loss)
                loss.backward()
                # 梯度裁剪
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                iteration += 1
                
                epoch_train_loss += loss.item()
            train_loss = epoch_train_loss/len(self.train_loader)
            # print(epoch, train_loss)
            if epoch >= 1:
                train_losses.append(train_loss)
            
            # 验证阶段
            self.model.eval()
            epoch_val_loss = 0
            with torch.no_grad():
                for X_val, y_val in self.test_loader:
                    X_val = X_val.to(self.device)
                    y_val = y_val.to(self.device)
                    
                    outputs = self.model(X_val)
                    loss = criterion(outputs, y_val)
                    epoch_val_loss += loss.item()
            val_loss = epoch_val_loss/len(self.test_loader)*1000

            if epoch >= 1:
                val_losses.append(val_loss)
            
            print(f"Epoch {epoch+1}/{epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
            
            # Early stopping
            # if epoch > 10 and val_loss > np.mean(val_losses[-5:]):
            #     print("Early stopping triggered")
            #     break
            
            # 改进的早停机制
            # if val_loss < self.best_val_loss:
            #     self.best_val_loss = val_loss
            #     self.no_improve_count = 0
            #     torch.save(self.model.state_dict(), 'best_model.pth')  # 保存最佳模型
            # else:
            #     self.no_improve_count += 1
                
            # if self.no_improve_count >= self.early_stop_patience:
            #     print(f"Early stopping at epoch {epoch+1}")
            #     self.model.load_state_dict(torch.load('best_model.pth'))  # 加载最佳模型
            #     break
            
            scheduler.step(val_loss)  # 更新学习率
                
        # 绘制损失曲线
        plt.plot(train_losses, label='Train Loss')
        plt.plot(val_losses, label='Validation Loss')
        plt.legend()
        plt.show()
        
    def predict(self, input_data=None):
        """执行预测"""
        if input_data is None:
            input_data = self.scaled_data[-self.lookback:]
            
        self.model.eval()
        with torch.no_grad():
            input_tensor = torch.tensor(input_data, dtype=torch.float)\
                .unsqueeze(0).to(self.device)
            prediction = self.model(input_tensor).cpu().numpy()
            
        # 逆标准化
        dummy = np.zeros((prediction.shape[1], self.scaled_data.shape[1]))
        dummy[:, 0] = prediction[0]
        predicted_power = self.scaler.inverse_transform(dummy)[:, 0]
        return predicted_power
    
    def visualize(self, prediction):
        """可视化结果"""
        plt.figure(figsize=(12, 6))
        plt.plot(self.df['Global_active_power'][-100:], label='Historical')
        plt.plot(np.arange(100, 100+self.forecast_steps), prediction, 
                'r--', label='Predicted')
        plt.legend()
        plt.title('Power Consumption Prediction')
        plt.show()
        
    def run(self):
        """完整流程"""
        self.load_data()
        self.prepare_data()
        self.build_model()
        self.train(epochs=1)
        
        # 预测并可视化
        last_data = self.scaled_data[-self.lookback:]
        print(last_data.shape) # (24, 7)
        ddd
        prediction = self.predict(last_data)
        self.visualize(prediction)

if __name__ == "__main__":
    predictor = PowerPredictor('household_power_consumption.csv')
    predictor.run()