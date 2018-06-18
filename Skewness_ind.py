# encoding:utf-8
# the file is to create the skewness indicator

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

# import the packages we need
import numpy as np 


# create first strategy's indicator : skewness
class Skn_ind(bt.Indicator):
    # create the indicator line

    lines = ('skn_ind',)
    def __init__(self, window_period, datafeed):
        self.datas = [datafeed]
        self.params.window_prd = window_period
        self.addminperiod(self.params.window_prd)
    def clc_skn_ind(self, dataseries):
        mean = np.mean(dataseries)
        var = np.var(dataseries)
        self.skewness = np.mean((np.array(dataseries - mean)/var)*3)
        return self.skewness
    def next(self):
        closedata = self.datas[0].get(size=self.params.window_prd,line=0)
        adj_fct = self.datas[0].get(size = self.params.window_prd, line=6)
        adj_closedata = np.array(closedata)*np.array(adj_fct)
        self.skn_ind[0] = self.clc_skn_ind(adj_closedata)
        print ('time : %s'%self.datas[0].datetime.date(0))
        print('skewness indicator of %s is %s'%(self.datas[0]._name,self.skn_ind[0]))