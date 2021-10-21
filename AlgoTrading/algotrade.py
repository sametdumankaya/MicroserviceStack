import pandas as pd
import backtrader as bt
from data_manager import DataManager
from datetime import datetime, timedelta
import strategies


data_manager = DataManager("localhost", 6379, "localhost", 6379)
now = datetime.now()
df = data_manager.get_prices(int((now - timedelta(seconds=60)).timestamp() * 1000),
                             int(now.timestamp() * 1000),
                             "SYMSET=ACTIVE_PRICE",
                             1000)
df["datetime"] = pd.to_datetime(df["datetime"], unit="ms")
df.set_index("datetime", inplace=True)
df.sort_index(inplace=True, ascending=True)

strategy_list = [strategies.TestStrategy30Percent]

for strategy in strategy_list:
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy)
    cerebro.addsizer(bt.sizers.FixedSize, stake=5)

    for col in df.columns.tolist():
        df_stock = df[[col]].copy(deep=True)
        df_stock["open"] = df_stock[col]
        df_stock["high"] = df_stock[col]
        df_stock["low"] = df_stock[col]
        df_stock["volume"] = 1000
        df_stock.rename(columns={col: 'close'}, inplace=True)
        data = bt.feeds.PandasData(dataname=df_stock)
        cerebro.adddata(data)
    cerebro.broker.setcash(100000)

    # Print out the starting conditions
    print(strategy.__name__)
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything

    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f\n' % cerebro.broker.getvalue())
