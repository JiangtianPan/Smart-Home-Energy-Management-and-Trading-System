import torch
from torch import nn
from predictor import LSTMModel
 
model = nn.Sequential()
model.add_module('lstm', nn.LSTM(
            input_size=7,
            hidden_size=64,
            num_layers=6,
            batch_first=True,
            dropout=0.3
        ))
model.add_module('layernorm', nn.LayerNorm(64))
model.add_module('dropout', nn.Dropout(0.3))
model.add_module('linear', nn.Linear(64, 6))
 
torch.save(model, 'lstm.pth')  # 保存模型