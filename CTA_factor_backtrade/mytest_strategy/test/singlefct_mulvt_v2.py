# encoding: utf-8
# the file used to test the single factor using the multiple vtsymbol



from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

import pandas as pd
import numpy as np 
from backtrader import Order
#from backtrader.mystrategy import Setting

# create our factor indicator skewness
class Ctaskn_ind(bt.Indicator):
    # create the indicator line


    lines = ('skn_ind',)

    def __init__(self, window_period, datafeed):
        # add datafeeds to self
        self.datas = [datafeed]
        self.params.window_prd = window_period
        self.addminperiod(self.params.window_prd)
    def clct_skn_ind(self, dataseries):
        mean = np.mean(dataseries)
        var = np.std(dataseries)
        self.skewness = np.mean(((dataseries - mean)/var)**3)
        return self.skewness
    def next(self):
        
        closedata = self.datas[0].get(size = self.params.window_prd,line=0)
        adj_fct = self.datas[0].get(size = self.params.window_prd, line=6)
        adj_closedata = np.array(closedata)*np.array(adj_fct)
        self.skn_ind[0] = self.clct_skn_ind(adj_closedata)
        try:
            print('the time is %s'%self.datas[0].num2date(self.datas[0].datetime[0]))
        except:
            pass
        print('skewness indicator of %s is %s'%(self.datas[0]._name,self.skn_ind[0]))
        
        if self.datas[0]._name == 'IF':
            pass
        if str(self.skn_ind[0]) == 'nan':
            print('why ???')

# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('exitbars', [2,4,6]),('skn_window_prd',15),('price_tick',3), ('ordervaliday', 3)
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

        self.o = {}     # record the datas order, the key is the datafeed
        self.excuted_bar_byorder = {}
        self.skn_ind = {}
        # self.dataclose = self.datas[0].close
        # To keep track of pending orders and buy price/commission
        # self.order = None
        # self.buyprice = None
        # self.buycomm = None
        # keep the mapping relationship between indexs of self.datas and vtsymbol
        
        self.index_mapping_vt = cerebro.index_mapping_vt
        self.vt_mapping_index = cerebro.vt_mapping_index
        # add the skewness indicator
        for i, vt in self.index_mapping_vt.items():        
            if(vt=='IF'):
                self.skn_ind[vt] = Ctaskn_ind(window_period = self.params.skn_window_prd + 20,
                                                      datafeed= self.datas[i]) 
            else:
                self.skn_ind[vt] = Ctaskn_ind(window_period = self.params.skn_window_prd,
                                                      datafeed= self.datas[i])                
            self.skn_ind[vt].plotinfo.plot = False
        print('ok')
    def start(self):
        print('the strategy begin')

    def prenext(self):
        print('I am not ready, need %s days'%self.params.skn_window_prd)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'vtsymbole: %s BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.data._name, 
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                #elf.buyprice = order.executed.price
                #self.buycomm = order.executed.comm
            else:  # Sell
                self.log('vtsymbole: %s SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (   order.data._name,
                             order.executed.price,
                             order.executed.value,
                          order.executed.comm))

            self.excuted_bar_byorder[order.data._name] = len(self)
            # self.bar_executed 记录成功交易的order在哪个bar上面交易成功的，为之后退出做准备

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            print('----------------------------------------')
            print('order.status is %s'%order.status)
            self.log('Order Canceled/Margin/Rejected/expired') 

        # the order has been completed, set the self.order to none
        # self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        date = self.datas[0].datetime.date(0)
        for i, vt in self.index_mapping_vt.items():
            price = self.datas[i].close[0]
            size = self.positions[self.datas[i]].size
            print('the position and closeprice of %s on %s are %.2f and %.2f'%(vt, date, size, price))


            # Check if an order is pending ... if yes, we cannot send a 2nd one
            #if self.order:
                #print('why not stop and self.order.status is %s'%self.order.status)
                #return



        for i, vt in self.index_mapping_vt.items():
            if not self.o.get(vt, None):
                self.o[vt] = []
            # Check if we are in the market
            elif self.o[vt][-1] and self.o[vt][-1].status in (1,2):  # close order type is none
                                                                        # 1 or 2 represent the status of order is uncompleted
                continue



            if not self.positions[self.datas[i]].size :

                # Not yet ... we MIGHT BUY if ...
                if self.skn_ind.lines[i][0] < 0 :
                    # current close price more than previous skewness indicator
                    # BUY !!!!!!!!, using the limit order
                    lprice = self.datas[i].close[0]+self.params.price_tick*(-10)
                    self.o[vt].append(self.buy(data = self.datas[i] ,exectype = Order.Limit, price = lprice, \
                                               valid = self.datas[i].datetime.date(0) + datetime.timedelta(self.params.ordervaliday)))

            else:

                # Already in the market ... we might sell
                if len(self) >= (self.excuted_bar_byorder[vt] + self.params.exitbars[i]):
                    # SELL, SELL, SELL!!! (with all possible default parameters)

                    # Keep track of the created order to avoid a 2nd order
                    self.o[vt].append(self.close(data=self.datas[i])) 
                    self.log('CLOSE ORDDER of %s has been CREATED, %.2f' % (vt, self.datas[i].close[0]))





if __name__ == '__main__':  
    # Create a cerebro entity  
    cerebro = bt.Cerebro()  
    # Add a strategy  
    cerebro.addstrategy(TestStrategy)  

    # set the backtesting time range
    cerebro.setstartdate('2014-12-31')
    cerebro.setenddate('2015-12-31')
    # Add the Data Feed to Cerebro  
    cerebro.AddMultidata(vtsymbol= ('IF','IC','IH'),filepath= r'D:/backtrader/backtrader-master/CTA_factor_backtrade/mytest_strategy/testdata/' )  
    # Set our desired cash start  
    cerebro.broker.setcash(1000000.0)  
    # 设置每笔交易交易的手数  
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)  
    # Set the commission is 0.005%
    cerebro.broker.setcommission(commission=0.00005)  
    # Print out the starting conditions  
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())  
    # Run over everything  
    cerebro.run()  
    # Print out the final result  
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())  
    cerebro.plot()  