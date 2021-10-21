import pandas as pd
import backtrader as bt
from data_manager import DataManager
from datetime import datetime, timedelta


class MySignal(bt.Indicator):
    lines = ('signal',)
    params = (('period', 30),)

    def __init__(self):
        self.lines.signal = bt.indicators.PctChange() - 10.5


data_manager = DataManager("localhost", 6379, "localhost", 6379)
now = datetime.now()
df = data_manager.get_prices(int((now - timedelta(seconds=60)).timestamp() * 1000),
                             int(now.timestamp() * 1000),
                             "SYMSET=ACTIVE_PRICE",
                             1000)
df["datetime"] = pd.to_datetime(df["datetime"], unit="ms")
df.set_index("datetime", inplace=True)
df_test = df[["stock_6"]].copy(deep=True)
df_test["open"] = df_test["stock_6"].copy(deep=True)
df_test["high"] = df_test["stock_6"].copy(deep=True)
df_test["low"] = df_test["stock_6"].copy(deep=True)
df_test["volume"] = 1000

df_test.rename(columns={'stock_6': 'close'}, inplace=True)
df_test.sort_index(inplace=True, ascending=True)

cerebro = bt.Cerebro()

cerebro.add_signal(bt.SIGNAL_LONGSHORT, MySignal)
data = bt.feeds.PandasData(dataname=df_test)
cerebro.adddata(data)
cerebro.broker.setcash(100000)


# Print out the starting conditions
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Run over everything

cerebro.run()

# Print out the final result
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
