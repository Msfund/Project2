# encoding:utf-8
# the file is to create the momentum indicator

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
# import the packages we need
import numpy as np 

class Mmt_ind(bt.Indicator):
    lines = ('Mmt_ind',)
    def __init__(self, window_period, datafeed):
        # 平台默认第一个数据集为计时器，由于不同的品种可能上市时间不同
        # 这里取自身作为计时器
         
        self.datas = [datafeed]
        self._clock = datafeed
        self.params.window_prd = window_period
        self.addminperiod(self.params.window_prd)
    
    def Clct_ind(self):
        ret = (self.dataseries[1:self.params.window_prd] - \
               self.dataseries[0:self.params.window_prd-1])/self.dataseries[0:self.params.window_prd-1]
        # Acmlt mean accumulate, surprise, right? hah 
        Acmlt = np.cumprod(1+ret)[-1] - 1
        return Acmlt
    
    def next(self):
        
        dataclose = self.datas[0].close.get(size = self.params.window_prd)
        adj_fct = self.datas[0].adjfactor.get(size= self.params.window_prd)
        self.dataseries = np.array(dataclose )* np.array(adj_fct)
        self.Mmt_ind[0] = self.Clct_ind()
        print('time : %s the Mmt_ind of %s is %.2f'%(self.datas[0].datetime.date(0),
                                                     self.datas[0]._name, self.Mmt_ind[0]))


# cross momentum indicator 
#class Cross_Mmt_ind(bt.Indicator):
    ## actually, this indicator is the special example of Time_Mmt_ind with the window_prd is 2
    #lines = ('Cross_Mmt_ind',)
    #def __init__(self, window_period, datafeeds, datafeed):
        ## datafeeds mean the datas strategy deals with 
        #self.datas = datafeeds
        ## datafeed means the data useed to calculate the indicator
        #self.data = datafeed
        #self.params.window_prd = window_period
        #self.addminperiod(self.params.window_prd)
    #def Clct_ind(self):
        #ret = (self.dataseries[1:self.params.window_prd] - self.dataseries[0:self.params.window_prd-1])/self.dataseries[0:self.params.window_prd-1]
        ## Acmlt mean accumulate, surprise, right? hah 
        #Acmlt = np.cumprod(1+ret)[-1] - 1
        #return Acmlt
    #def next(self):
        #dataclose = self.data.close.get(size = self.params.window_prd)
        #adj_fct = self.data.adj_fct.get(size= self.params.window_prd)
        #self.dataseries = np.array(dataclose )* np.array(adj_fct)
        #self.Cross_Mmt_ind[0] = self.Clct_ind()
        #print('the Cross_Mmt_ind is %.2f'%self.Cross_Mmt_ind[0])    