# encoding: utf-8
# the file used to creat the basis_momentum factor

import backtrader as bt
from backtrader import num2date
import numpy as np
from datetime import datetime

class Basis_Mmt(bt.Indicator):
    lines = ('Basis_Mmt_ind',)
    def __init__(self, datafeed,window_prd):
        # 我们需要连续近月合约和连续远月合约的数据
        # datafeed的最后一个feed是用于计时的clock_data，不参与计算,仅用于时间推进
        self.datas = datafeed
        self._clock = datafeed[-1]
        self.params.window_prd = window_prd
        self.count = window_prd -1
        self.addminperiod(self.params.window_prd)
        for i, data in enumerate(self.datas[:-1]):
            if 'near_month' in data._name:
                self.near_index = i 
            else:
                self.long_index = i
                
    def Clct_ind(self):
        
        near_ret = (self.nearadjclose[1:] - self.nearadjclose[:-1])/(self.nearadjclose[:-1])
        near_cum = np.cumprod(near_ret+1)[-1] - 1
        long_ret = (self.longadjclose[1:] - self.longadjclose[:-1])/(self.longadjclose[:-1])
        long_cum = np.cumprod(long_ret+1)[-1] -1
        ind_data = near_cum - long_cum
        return ind_data
    
    def next(self):
        self.nearclose = np.array(self.datas[self.near_index].close.get(size=self.params.window_prd))
        self.nearadjclose =  np.array(self.datas[self.near_index].adjfactor.get(size=self.params.window_prd)) * self.nearclose
        self.longclose = np.array(self.datas[self.near_index].adjfactor.get(size=self.params.window_prd))
        self.longadjclose = np.array(self.datas[self.near_index].adjfactor.get(size=self.params.window_prd)) * self.longclose
        self.Basis_Mmt_ind[0] = self.Clct_ind()
        print('date: %s the Basis_Mmt indictor is %s'%(self.datas[-1].datetime.date(0), self.Basis_Mmt_ind[0]))

        
