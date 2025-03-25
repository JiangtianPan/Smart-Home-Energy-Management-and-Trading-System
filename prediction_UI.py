import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import os

# 设置页面布局
st.set_page_config(
    page_title="Power Consumption Visualization System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stFileUploader>div>div>div>div {
        color: #4CAF50;
    }
    .plot-container {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .header {
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# 应用标题
st.title("⚡ Power Consumption Visualization System")
st.markdown("---")

# 创建两列布局
col1, col2 = st.columns([1, 3])

with col1:
    st.header("DATA VISUALIZATION SETTING")
    
    # 文件上传区域
    uploaded_file = st.file_uploader("data.npy", type=["npy"])
    
    # 模拟数据选项
    # use_sample_data = st.checkbox("使用示例数据", value=True)
    
    # 时间设置
    start_date = st.date_input("Start Time", datetime.now() - timedelta(days=30))
    time_interval = st.selectbox("Time Step", ["Hour", "Day", "Week"], index=0)
    
    # 预测设置
    forecast_horizon = st.slider("Prediction (Time Step)", 1, 24, 6)
    
    # 刷新按钮
    if st.button("Renew Data"):
        st.experimental_rerun()

# 数据加载函数
def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            data = np.load(uploaded_file)
            return data
        except Exception as e:
            st.error(f"File Load Fail: {e}")
            return None
    else:
        # 生成示例数据
        np.random.seed(42)
        actual = np.cumsum(np.random.normal(10, 3, 720))  # 30天的每小时数据
        forecast = actual + np.random.normal(0, 5, 720)
        return np.column_stack((actual, forecast))

# 主展示区域
with col2:
    st.header("Real Electric Data vs Prediction Data")
    
    # 进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 加载数据
    data = load_data("data.npy")
    # data = np.load("data.npy")
    # print(data[:,0])
    # print(data[:,1])
    # ddd
    
    if data is not None:
        # 创建时间序列
        if time_interval == "Each Hour":
            dates = pd.date_range(start=start_date, periods=len(data), freq='H')
        elif time_interval == "Each Day":
            dates = pd.date_range(start=start_date, periods=len(data), freq='D')
        else:
            dates = pd.date_range(start=start_date, periods=len(data), freq='W')
        
        # 创建DataFrame
        df = pd.DataFrame({
            'Time': dates,
            'Real Data': data[:, 1],
            'Prediction Data': data[:, 0]
        })
        
        # 显示数据摘要
        with st.expander("Data Summary"):
            st.dataframe(df.describe())
        
        # 动态展示图表
        chart_placeholder = st.empty()
        
        # 初始化图表
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_xlabel('Time')
        ax.set_ylabel('Electrical Consuming (kWh)')
        ax.set_title('Real Electric Data vs Prediction Data')
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # 动态更新图表
        for i in range(1, len(df)+1):
            # 更新进度条
            progress_bar.progress(i/len(df))
            status_text.text(f"Loading... {i}/{len(df)}")
            
            # 更新图表
            plt.cla()  # 清除当前轴
            # print('-------', df['Time'][:i], '--------')
            # print(df['Prediction Data'][:i], df['Real Data'][:i])
            ax.plot(df['Time'][:i], df['Real Data'][:i], 
                   label='Real Data', color='#3498db', linewidth=2)
            ax.plot(df['Time'][:i], df['Prediction Data'][:i], 
                   label='Prediction Data', color='#e74c3c', linestyle='--', linewidth=2)
            
            # 添加预测区间
            if forecast_horizon > 0 and i > forecast_horizon:
                ax.fill_between(df['Time'][i-forecast_horizon:i], 
                               df['Real Data'][i-forecast_horizon:i], 
                               df['Prediction Data'][i-forecast_horizon:i],
                               color='#f39c12', alpha=0.2, label='Prediction Interval')
            
            ax.legend(loc='upper left')
            ax.set_xlim(df['Time'].min(), df['Time'].max())
            
            # 显示图表
            chart_placeholder.pyplot(fig)
            
            # 控制更新速度
            time.sleep(0.05)
        
        # 完成加载
        progress_bar.empty()
        status_text.success("Loading Finish!")
        
        # 显示完整图表
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df['Time'], df['Real Data'], 
               label='Real Data', color='#3498db', linewidth=2)
        ax.plot(df['Time'], df['Prediction Data'], 
               label='Prediction Data', color='#e74c3c', linestyle='--', linewidth=2)
        
        # 添加预测区间
        if forecast_horizon > 0:
            ax.fill_between(df['Time'][-forecast_horizon:], 
                           df['Real Data'][-forecast_horizon:], 
                           df['Prediction Data'][-forecast_horizon:],
                           color='#f39c12', alpha=0.2, label='Prediction Interval')
        
        ax.set_xlabel('Time')
        ax.set_ylabel('Electrical Consuming (kWh)')
        ax.set_title('Real Electric Data vs Prediction Data')
        ax.legend(loc='upper left')
        ax.grid(True, linestyle='--', alpha=0.6)
        
        chart_placeholder.pyplot(fig)
        
        # 显示原始数据
        with st.expander("查看原始数据"):
            st.dataframe(df)
    else:
        st.warning("请上传数据文件或使用示例数据")

# 侧边栏信息
st.sidebar.header("关于")
st.sidebar.info("""
这是一个用电量预测可视化系统，可以:
- 上传.npy格式的用电量数据
- 动态展示实际用电量与预测用电量
- 分析预测误差和趋势
""")

# 运行说明
st.sidebar.header("使用说明")
st.sidebar.markdown("""
1. 上传.npy文件或使用示例数据
2. 设置时间范围和间隔
3. 调整预测周期
4. 点击"刷新数据"更新图表
""")