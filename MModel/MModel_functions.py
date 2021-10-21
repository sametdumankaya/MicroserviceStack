import talib
import pandas as pd
import redis
from redistimeseries.client import Client

def getIndexes(ts_names:list,prefix="rts1:01:symbol:",postfix=":volume",redis_host="localhost",redis_port=6381,indexList=['VIX', 'ALPHA', 'BETA', 'EMA','CMA','SMA','RSA'],aggregation_type="last",bucket_size_msec=60000,from_time=0,to_time=-1):
   pass
if __name__ == "__main__":
     pass
 
    # import pandas_datareader.data as web
    # import pandas as pd
    # import numpy as np
    # from talib import RSI, BBANDS
    # import matplotlib.pyplot as plt
    # start = '2015-04-22'
    # end = '2017-04-22'
    
    # symbol = 'CSCO'
    # max_holding = 100
    # price = web.DataReader(name=symbol, data_source='yahoo')
    # price = price.iloc[::-1]
    # price = price.dropna()
    # close = price['Adj Close'].values
    # up, mid, low = BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    # rsi = RSI(close, timeperiod=14)
    # price["RSI"]=rsi
    # print("RSI (first 10 elements)\n", rsi[14:24])
    # index=price.index.values
    # up, mid, low = BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    # bbp = (price['Adj Close'] - low) / (up - low)
    # price["BBP"]=bbp
    # price["BB_up"]=up
    # price["BB_mid"]=mid
    # price["BB_low"]=low
    # holdings = pd.DataFrame(index=price.index, data={'Holdings': np.array([np.nan] * price.index.shape[0])})
    # holdings.loc[((price['RSI'] < 30) & (price['BBP'] < 0)), 'Holdings'] = max_holding
    # holdings.loc[((price['RSI'] > 70) & (price['BBP'] > 1)), 'Holdings'] = 0
    # holdings.ffill(inplace=True)
    # holdings.fillna(0, inplace=True)
    # holdings['Order'] = holdings.diff()
    # holdings.dropna(inplace=True)
    
    # fig, (ax0, ax1, ax2) = plt.subplots(3, 1, sharex=True, figsize=(12, 8))
    # ax0.plot(list(index), price['Adj Close'], label='Adj Close')
    # ax0.set_xlabel('Date')
    # ax0.set_ylabel('Adj Close')
    # ax0.grid()
    # for day, holding in holdings.iterrows():
    #     order = holding['Order']
    #     if order > 0:
    #         ax0.scatter(x=day, y=price.loc[day, 'Adj Close'], color='green')
    #     elif order < 0:
    #         ax0.scatter(x=day, y=price.loc[day, 'Adj Close'], color='red')
    
    # ax1.plot(list(index), price['RSI'], label='RSI')
    # ax1.fill_between(index, y1=30, y2=70, color='#adccff', alpha=0.3)
    # ax1.set_xlabel('Date')
    # ax1.set_ylabel('RSI')
    # ax1.grid()
    
    # ax2.plot(list(index), price['BB_up'], label='BB_up')
    # ax2.plot(list(index), price['Adj Close'], label='Adj Close')
    # ax2.plot(list(index), price['BB_low'], label='BB_low')
    # ax2.fill_between(list(index), y1=price['BB_low'], y2=price['BB_up'], color='#adccff', alpha=0.3)
    # ax2.set_xlabel('Date')
    # ax2.set_ylabel('Bollinger Bands')
    # ax2.grid()
    
    # fig.tight_layout()
    # plt.show()