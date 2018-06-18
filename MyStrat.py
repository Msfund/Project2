from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime
from HdfUtility import *
from dataUlt import *

import backtrader as bt
import backtrader.indicators as btind

class TestStrategy(bt.Strategy):
    '''
    Every window_period,
    r = high(r_period) - low(r_period),
    r2 = high(r2_period) - low(r2_period),
    long_limit_at = open - long_limit_weight * r,
    stoploss,
    profit_target = profit_target_weight * r
    condition_start <= r2 <= condition_end
    '''
    params = (
        ('window_period', 4),
        ('r_period', 48),
        ('r2_period', 72),
        ('long_limit_weight', 0.12),
        ('stop_loss', 0.005),
        ('profit_target_weight', 0.32),
        ('condition_start', 0.013),
        ('condition_end', 0.019),
    )

    def log(self, txt, dt=None):
        # logging function
        dt = dt or self.data.datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # keep reference to specific line in dataseries
        self.r = btind.MaxN(self.data.close,period = r_period) - btind.MinN(self.data.close,period = r_period)
        self.r2 = btind.MaxN(self.data.close,period = r2_period) - btind.MinN(self.data.close,period = r2_period)
        self.long_limit_at = self.data.open - self.p.long_limit_weight * self.r
        self.profit_target = self.p.profit_target_weight * self.r

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('Buy Executed, Price: %.2f, Cost: %.2f, Comm %.2f' %
                        (order.executed.price,
                         order.executed.value,
                         order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else: # Sell
                self.log('Sell Executed, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

        # avoiding big losses or securing profits
        if self.position:
            stop_loss_price = order.executed.price * (1.0 - self.p.stop_loss)
            stop_profit_price = order
            self.sell(exectype=bt.Order.Stop, price=stop_loss_price)
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('Operation Profit, Gross %.2f, Net %.2f' %
            (trade.pnl, trade.pnlcomm))

    def next(self):

        self.log('Close, %.2f' % self.data.close[0])

        if self.order:
            return

        if not self.position:
            # not in market
            if self.r2 >= self.p.condition_start and self.r2 <= self.p.condition_end:

                self.log('Buy Create, %.2f' % self.data.close[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(exectype=Order.Limit,
                                      price=self.data.close[0] * 1.02,
                                      valid=datetime.datetime.now() + datetime.timedelta(days=self.p.window_period)))

        else:
            # in market
            if self.data.close[0] < self.sma[0]:

                self.log('Sell Create, %.2f' % self.data.close[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


    def stop(self):
        self.log('Ending Value %.2f' %
            (self.broker.getvalue()))

def hdf2bt(data):
    data = data.reset_index().set_index([EXT_Bar_Date])
    data[EXT_Bar_Close] = data[EXT_AdjFactor] * data[EXT_Bar_Close]
    data.drop([EXT_Out_Asset,EXT_AdjFactor,EXT_Bar_PreSettle,EXT_Bar_Settle],axis=1,inplace=True)
    return data

if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # optimize a strategy
#    strats = cerebro.optstrategy(
#        TestStrategy,
#        maperiod=range(10, 31)) # 10-30

    hdf = HdfUtility()
    data0 = hdf.hdfRead(EXT_Hdf_Path,'CFE','IF','Stitch','00','1d',startdate='20120101',enddate='20171231')
    data0 = hdf2bt(data0)
    # Feed data
    data = bt.feeds.PandasData(dataname=data0,
                        fromdate = datetime(2012, 1, 1),
                        todate = datetime(2017, 12, 31)
                        )

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Or Add Resampledata
    # cerebro.resampledata(data, timeframe=bt.TimeFrame.Days)

    # Set desired cash start
    cerebro.broker.setcash(100000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    # Set the commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)

    # Get the starting condition
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over and visulizing
    cerebro.run()
    cerebro.plot()

    # Get the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
