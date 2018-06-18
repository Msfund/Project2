# Neural Network Strategy

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime
from HdfUtility import *
from dataUlt import *
import backtrader as bt
import pandas as pd
import numpy as np
from sklearn.neural_network import MLPClassifier

class TestStrategy(bt.Strategy):
    '''
    This strategy uses indicators within valid range as features 
    to implement binary classification based on logistic regression
    '''
    params = (
        ('maperiod', 15),
        ('windowperiod',30),
        ('printlog', False),
        ('buycheck',0.01),
        ('sellcheck',0.0),
    )

    def log(self, txt, dt=None):
        # logging function
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # updown is used to indentify whether the price is going up or down compared to yesterday.
        self.updown = self.datas[0].close > self.datas[0].close(-1)

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add indicators
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)
        self.macdhisto = bt.indicators.MACDHisto(
            self.datas[0])
        # # Indicators for the plotting show
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25,
        #                                     subplot=True)
        # bt.indicators.StochasticSlow(self.datas[0])
        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # bt.indicators.ATR(self.datas[0], plot=False)

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

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('Operation Profit, Gross %.2f, Net %.2f' %
            (trade.pnl, trade.pnlcomm))

    def next(self):

        self.log('Close, %.2f' % self.datas[0].close[0])

        if self.order:
            return

        X = np.hstack((self.sma[-self.params.windowperiod:-1],
                       self.macd[-self.params.windowperiod:-1]))
        y = self.ret[-self.params.windowperiod+1:0]
        # Decision Tree Regressor
        self.model.fit(x,y)
        x0 = np.hstack((self.sma[0],
                        self.macd[0]))
        y0 = self.model.predict(x0)

        if not self.position:
            # in market
            if y0 > self.params.buycheck:

                self.log('Buy Create, %.2f' % self.datas[0].close[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:
            # not in market
            if  y0 < self.params.sellcheck:

                self.log('Sell Create, %.2f' % self.datas[0].close[0])

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
