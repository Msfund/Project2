# quick start
# encoding:utf-8
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

import pandas as pd


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('exitbars', 5),
    )
    

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        print (self.datas)

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)
            print('bar_executed is %s'%self.bar_executed)
            # self.bar_executed 记录成功交易的order在哪个bar上面交易成功的，为之后退出做准备

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:
                # current close less than previous close

                if self.dataclose[-1] < self.dataclose[-2]:
                    # previous close less than the previous close

                    # BUY, BUY, BUY!!! (with default parameters)
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])

                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:

            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + self.params.exitbars):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()



#class Mydatafeed(bt.feeds.PandasData):
    #lines = ('datetime', 'open', 'high', 'low', 'close', 'volume','AdjFactor','openinterest')
    #params = (
    #('nocase', True),

    ## Possible values for datetime (must always be present)
    ##  None : datetime is the "index" in the Pandas Dataframe
    ##  -1 : autodetect position or case-wise equal name
    ##  >= 0 : numeric index to the colum in the pandas dataframe
    ##  string : column name (as index) in the pandas dataframe
    #('datetime', None),

    ## Possible values below:
    ##  None : column not present
    ##  -1 : autodetect position or case-wise equal name
    ##  >= 0 : numeric index to the colum in the pandas dataframe
    ##  string : column name (as index) in the pandas dataframe
    #('open', -1),
    #('high', -1),
    #('low', -1),
    #('close', -1),
    #('volume', -1),
    #('AdjFactor',-1),
    #('openinterest', -1),
#)

    
    



if __name__ == '__main__':
    #extralines = 2
    
    
    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=True)

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere

    datapath = r'D:\\backtrader\\backtrader-master\\CTA_factor_backtrade\\mytest_strategy\\testdata\\CFE_IC_dom.csv'
    
    ### my test
    dataframe = pd.read_csv(datapath,parse_dates = True,index_col=0)
    
    loadingdata_classname = 'loading_data'.encode('utf-8')
    
    lines = ('datetime', 'open', 'high', 'low', 'close', 'volume','AdjFactor','openinterest','delist')
    params =  (
        ('nocase', True),
        ('datetime', None),
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('AdjFactor',-1),
        ('openinterest', -1),
        ('delist', -1)
    )
    mylodingclass = type(loadingdata_classname, (bt.feeds.PandasData,),{ 'lines':  lines, 'params':params} )
    data = mylodingclass(dataname=dataframe,fromdate = datetime.datetime(2015,10,27),high=1)
    
    # data = bt.feeds.PandasData(dataname=dataframe,fromdate = datetime.datetime(2015,05,05),high=1)


    data.open
    
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.001)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())