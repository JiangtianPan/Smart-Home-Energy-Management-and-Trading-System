import numpy as np
import matplotlib.pyplot as plt
import random

# 加载单个数组
data = np.load('data.npy')
print(data)  # 输出: [1 2 3 4 5]

# 绘制折线图
fig, ax1 = plt.subplots(figsize=(8, 5))# 设置图像大小

ax1.plot(data[:, 0], label=f'Power Prediction')
ax1.plot(data[:, 1], label=f'Power Label')
# 添加图例和标签
ax1.set_xlabel('Time')
ax1.set_ylabel('kW', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True)  # 添加网格线
ax1.legend()
fig.savefig('kW_Time.png')


# fig, ax2 = plt.subplots(figsize=(8, 5))# 设置图像大小
# ratio_data = np.clip(data[:, 2], 0, 21) + (np.random.random()*2-1)*1

# ratio_mean = ratio_data.copy()
# print(ratio_data.shape)
# for i in range(ratio_data.shape[0]):
#     ratio_mean[i] = np.mean(ratio_data[0:i])
# # ax2 = ax1.twinx()
# # ax2.plot(ratio_data, color='red', linestyle='', marker='*', label='diff ratio')
# ax2.plot(ratio_data, color='red', label='diff ratio')
# ax2.plot(ratio_mean, color='black', label='diff ratio mean')
# ax2.tick_params(axis='y', labelcolor='red')

# ax2.set_xlabel('Time')
# ax2.set_ylabel('Diff Ratio %', color='red')
# ax2.tick_params(axis='y', labelcolor='red')
# ax2.grid(True)  # 添加网格线
# ax2.legend()
# fig.savefig('diff_Time.png')

# 显示图像
plt.show()