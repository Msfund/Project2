# encoding:utf-8
# this file used to implement the strategies with the single vtsymbol
# data, and the reslut will make different broker's account and the result value is different
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
from backtrader import Order
import backtrader.indicators as btind

# import the packages we need
import pandas as pd
import numpy as np 
import stat 


# create first strategy's indicator : skewness
class Skn_ind(bt.Indicator):
    # create the indicator line

    lines = ('skn_ind',)
    def __init__(self, window_period):
        self.params.window_prd = window_period
        self.addminperiod(self.params.window_prd)
    def clc_skn_ind(self, dataseries):
        mean = np.mean(dataseries)
        var = np.var(dataseries)
        self.skewness = np.mean((np.array(dataseries - mean)/var)*3)
        return self.skewness
    def next(self):
        closedata = self.data.get(size=self.params.window_prd,line=0)
        adj_fct = self.data.get(size = self.params.window_prd, line=6)
        adj_closedata = np.array(closedata)*np.array(adj_fct)
        self.skn_ind[0] = self.clc_skn_ind(adj_closedata)
        #print('skewness indicator is %s'%self.skn_ind[0])

# Create first Stratey    

class Strategy1(bt.Strategy):
    params = (
        ('exitbars', 5),('skn_window_prd',15),('price_tick',3), ('ordervaliday', 2)
    )
    '''existbars : the holding days less than existbars
       skn_window_prd: the waiting window days uesd to calculate the skewness indicator
       price_tick : the min price change of the asset
       ordervaliday : if the order not be executed over 2 days, it will be set expired
    '''

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

        # add the skewness indicator
        self.Strat_skn_ind = Skn_ind(self.datas[0],window_period = self.params.skn_window_prd)   

    def start(self):
        print('the strategy begin')

    def prenext(self):
        print('I am not ready')

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
            # self.bar_executed 记录成功交易的order在哪个bar上面交易成功的，为之后退出做准备

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            print('----------------------------------------')
            print('order.status is %s'%order.status)
            self.log('Order Canceled/Margin/Rejected/expired') 

        # the order has been completed, set the self.order to none
        self.order = None

    def notify_trade(self, trade):
        # if you want to impose any operation in the trade 
        # here you can do, if you want record the change of your portfolio values
        # every day, you can create an analyser or in the new() method
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            #print('why not stop and self.order.status is %s'%self.order.status)
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.Strat_skn_ind[0] < 0:
                # current close price more than previous skewness indicator
                # BUY !!!!!!!!, using the limit order
                lprice = self.dataclose[0]+self.params.price_tick*(-10)
                self.order = self.buy(exectype= Order.Limit, price= lprice, valid = self.datas[0].datetime.date(0) + \
                                      datetime.timedelta(self.params.ordervaliday))

        else:

            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + self.params.exitbars):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close() 


# creat the second strategy's indicator : Mmt_ind

class Mmt_ind(bt.Indicator):
    lines = ('Mmt_ind',)
    def __init__(self, datafeed, window_period):
        self.data = datafeed
        self.params.window_prd = window_period
        self.addminperiod(self.params.window_prd)
    def Clct_ind(self):
        ret = (self.dataseries[1:self.params.window_prd] - self.dataseries[0:self.params.window_prd-1])/self.dataseries[0:self.params.window_prd-1]
        # Acmlt mean accumulate, surprise, hah
        Acmlt = np.cumprod(1+ret)[-1] - 1
        return Acmlt
    def next(self):
        dataclose = self.data.close.get(size = self.params.window_prd)
        adj_fct = self.data.adj_fct.get(size= self.params.window_prd)
        self.dataseries = np.array(dataclose )* np.array(adj_fct)
        self.Mmt_ind[0] = self.Clct_ind()
        print('the Mmt_ind is %.2f'%self.Mmt_ind[0])
# creat the second strategy
class Strategy2(bt.Strategy):
    params = (
        ('exitbars', 5),('Mmt_window_prd',15+1),('price_tick',3), ('ordervaliday', 2), ('upopen_limit', 0.05),
        ('downopen_limit', -0.05)
    )
    '''existbars : the holding days less than existbars
       Mmt_window_prd: the waiting window days uesd to calculate the Momentum indicator
       price_tick : the min price change of the asset
       ordervaliday : if the order not be executed over 2 days, it will be set expired
       upopen_limit: if the indicator overpasses the param, then we send buyorder
       dowopen_limit: if the indicator is less than the param, then we send sellorder
    '''

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

        # add the skewness indicator
        self.Strat_Mmt_ind = Mmt_ind(datafeed=self.datas[0],window_period = self.params.Mmt_window_prd)   

    def start(self):
        print('the strategy begin')

    def prenext(self):
        print('I am not ready')

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
            # self.bar_executed 记录成功交易的order在哪个bar上面交易成功的，为之后退出做准备

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            print('----------------------------------------')
            print('order.status is %s'%order.status)
            self.log('Order Canceled/Margin/Rejected/expired') 

        # the order has been completed, set the self.order to none
        self.order = None

    def notify_trade(self, trade):
        # if you want to impose any operation in the trade 
        # here you can do, if you want record the change of your portfolio values
        # every day, you can create an analyser or in the new() method
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            #print('why not stop and self.order.status is %s'%self.order.status)
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.Strat_Mmt_ind[0] > self.params.upopen_limit:
                # current close price more than previous momentum indicator
                # BUY !!!!!!!!, using the limit order
                lprice = self.dataclose[0]+self.params.price_tick
                self.order = self.buy(exectype= Order.Limit, price= lprice, valid = self.datas[0].datetime.date(0) + \
                                      datetime.timedelta(self.params.ordervaliday))
            elif self.Strat_Mmt_ind[0] < self.params.downopen_limit:
                lprice = self.dataclose[0] - self.params.price_tick
                self.order = self.sell(exectype= Order.Limit, price= lprice, valid = self.datas[0].datetime.date(0) + \
                                                  datetime.timedelta(self.params.ordervaliday))                

        else:

            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + self.params.exitbars):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close()     
        


# creat another class the run strategies above
# the strategies as the optimization params

class stFetch(object):
    Strat = [Strategy1, Strategy2]
    def  __new__(cls, *args, **kwargs):
        idx = kwargs.pop('idx')
        strategy = cls.Strat[idx](*args, **kwargs)
        return strategy
        


# run the multistrategies

if __name__ == '__main__':  
    # Create a cerebro entity  
    cerebro = bt.Cerebro()  
    # use the optstrategy the run the different strategise
    # the purpose is to create different broker accounts
    cerebro.optstrategy(stFetch, idx=[0,1])  
    # set the first column as index
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, r'testdata/CFE_IC_dom.csv') 
    dataframe = pd.read_csv(datapath, index_col=0, parse_dates=True)  
    data = bt.feeds.PandasData(dataname=dataframe, fromdate = datetime.datetime(2017,01,01), todate = datetime.datetime(2017,12,01))  
    # Add the Data Feed to Cerebro  
    cerebro.adddata(data)  
    # Add the analyzer
    cerebro.addanalyzer(bt.analyzers.Returns)
    # Set our desired cash start  
    cerebro.broker.setcash(1000000.0)  
    # 设置每笔交易交易的手数  
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)  
    # Set the commission is 0.005%
    cerebro.broker.setcommission(commission=0.00005)  
    # Print out the starting conditions  
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())  
    # Run over everything  
    result = cerebro.run(maxcpus = 1, optreturn= False)
    analyzer_info = result
    
    print('the returns of strategy1 is %s'%analyzer_info[0][0].analyzers.returns.get_analysis())
    print('the return of strategy2 is %s'%analyzer_info[1][0].analyzers.returns.get_analysis())
    # Print out the final result  
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())  
    
    cerebro.plot()  