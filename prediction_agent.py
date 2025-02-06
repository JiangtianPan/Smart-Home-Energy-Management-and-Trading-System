import os
# for dirname, _, filenames in os.walk('/kaggle/input'):
#     for filename in filenames:
#         print(os.path.join(dirname, filename))
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
import seaborn as sns
import pandas as pd
import sklearn
import warnings
warnings.filterwarnings('ignore')

df=pd.read_csv('./household_power_consumption.csv')

df=df.drop('index',axis=1)
df['Date']=pd.to_datetime(df['Date'])
df['Time']=pd.to_datetime(df['Time'])
df=df.sort_values('Date')

df['Sub_metering_1']=df['Sub_metering_1'].replace({'?':'0'})
df['Sub_metering_2']=df['Sub_metering_2'].replace({'?':'0'})
df['Sub_metering_2']=df['Sub_metering_2'].replace({'?':'0'})
df.groupby(['Sub_metering_1']).count()
df['Sub_metering_1']=pd.DataFrame(np.array(df['Sub_metering_1'],dtype='float32'))
df['Sub_metering_2']=pd.DataFrame(np.array(df['Sub_metering_2'],dtype='float32'))
df['Sub_metering_3']=df['Sub_metering_3'].fillna(method='bfill')

df.groupby(['Time']).mean().rolling(60).mean().plot(linewidth=1)
plt.title('1-HOUR AVERAGE')

df.groupby(['Date']).mean().rolling(10).mean().plot(linewidth=1)
plt.title('10-DAY AVERAGE')

# PLOTTING 10-DAY AVERAGE FOR ACTIVE AND REACTIVE POWER
df['Global_active_power']=df['Global_active_power'].replace({'?':0.214})
df['Global_reactive_power']=df['Global_reactive_power'].replace({'?':0.1})
# THESE ARE THE MOST COMMONLY OCCURING VALUES IN THE FEATURE

df[['Global_reactive_power','Global_active_power']]=pd.DataFrame(np.array(df[['Global_reactive_power','Global_active_power']],dtype='float32'))
##df.groupby(['Date']).mean()[['Global_active_power','Global_reactive_power']].plot(linewidth=2)
df.groupby(['Date']).mean()[['Global_active_power','Global_reactive_power']].rolling(10).mean().plot(linewidth=2)
plt.title('10-DAY AVERAGE')
plt.show()

# PLOTTING VOLTAGE OVER DATE/TIME
#df.groupby(['Voltage']).count().sort_values('Time',ascending=False)
df['Voltage']=df['Voltage'].replace({'?':240})
df['Voltage']=pd.DataFrame(np.array(df['Voltage'],dtype='float32'))
df.groupby(['Time']).mean()['Voltage'].rolling(10).mean().plot(linewidth=2)
plt.ylabel('Voltage')

df.groupby(['Date']).mean()['Voltage'].rolling(7).mean().plot(linewidth=2)
plt.ylabel('Voltage')

# PLOTTING GLOBAL INTENSITY OVER TIME
#df.groupby(['Global_intensity']).count().sort_values('Time',ascending=False)
df['Global_intensity']=df['Global_intensity'].replace({'?':1.4})
df['Global_intensity']=pd.DataFrame(np.array(df['Global_intensity'],dtype='float32'))
df.groupby(['Time']).mean()['Global_intensity'].rolling(10).mean().plot(linewidth=2)
plt.ylabel('Global Intensity')

df.groupby(['Date']).mean()['Global_intensity'].rolling(7).mean().plot(linewidth=2)
plt.ylabel('Global Intensity')
plt.title('Weekly Average')

# MORE IS THE POWER CONSUMPTION MORE ARE THE METER READINGS
df.groupby(['Global_active_power']).mean()[['Sub_metering_2','Sub_metering_3']][:8].rolling(20).mean().plot(linewidth=1)
plt.title('Mean Readings')
df.groupby(['Global_active_power']).std()[['Sub_metering_2','Sub_metering_3']][:8].rolling(10).mean().plot(linewidth=1)
plt.title('Std Readings')
plt.show()