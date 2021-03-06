# encoding: utf-8
# the file used to creat the roll over factor

import backtrader as bt
from backtrader import num2date
import numpy as np
from datetime import datetime

class Rollover(bt.Indicator):
    lines = ('Rollover_ind',)
    def __init__(self, datafeed,window_prd):
        # datafeed 是一个品种的所有合约数据, window_prd是因子计算需要是窗口期，
        # datafeed的最后一个feed是用于计时的clock_data，不参与计算,仅用于时间推进
        self.datas = datafeed
        self._clock = datafeed[-1]
        self.params.window_prd = window_prd
        self.tradingday = self._clock.datetime.array
        self.count = window_prd -1
        # 记录还没有上市的合约
        self.un_active_data =[]
        # 记录已经退市的合约
        self.delist_data = []
        self.addminperiod(self.params.window_prd)
        
        # super(Rollover_ind, self).__init__()
        
    def Clct_ind(self):
        ind_data = (np.log(self.nearclose) - np.log(self.longclose))/(self.longdays - self.neardays)
        return ind_data
    def lookfor_contract(self):
        # 寻找远月合约和近月合约
        # 当然展期因子也可以由其他合约构建，这里使用者可以继承
        
        # 调整未上市合约的下标_idx
        for i in self.un_active_data:
            lines = self.datas[i].lines
            for l in lines:
                l.idx += -1
        
        self.un_active_data = []
        
        # 找出目前尚未交易的合约
        trading_date = self.tradingday[self.count]
        # 可能还没有上市， 可能已经退市
        for i,data in enumerate(self.datas[:-1]):
            try:
                date = self.datas[i].datetime[0]
                if date > trading_date + self.params.window_prd + 1:
                    self.un_active_data.append(i)
            except:
                # 已经退市
                if i not in self.delist_data:
                    self.delist_data.append(i)

        self.count += 1    
        # 找出远月合约和近月合约  
        long_con = 'None'
        near_con = 'None'
        longest = float('-inf')
        nearest = float('inf')
        
        for i,data in enumerate(self.datas[:-1]):           
            if i in self.un_active_data + self.delist_data:
                continue
            delistdate = data.delistdate[0]                
            longest = max(delistdate, longest)
            nearest = min(delistdate, nearest)
        for i,data in enumerate(self.datas[:-1]) :
            if i in self.un_active_data + self.delist_data:
                continue
            if data.delistdate[0] == longest:
                long_con = i
            if data.delistdate[0] == nearest:
                near_con = i
        # the type of delistdate in the line is float        
        long_delistdate = datetime.strptime(str(int(self.datas[long_con].delistdate[0])),'%Y%m%d') 
        near_delistdate = datetime.strptime(str(int(self.datas[near_con].delistdate[0])),'%Y%m%d') 
        
        long_closedata = self.datas[long_con].close[0]        
        long_days = long_delistdate.date() - self.datas[long_con].datetime.date(0)    
        near_closedata = self.datas[near_con].close[0]
        near_days = near_delistdate.date() - self.datas[near_con].datetime.date(0)
        
        return(long_closedata, long_days.days, near_closedata, near_days.days)
    def next(self):
        if self.count == 244:
            pass
        self.longclose, self.longdays,self.nearclose,self.neardays = self.lookfor_contract()
        self.Rollover_ind[0] = self.Clct_ind()
        if str(self.Rollover_ind[0]) == 'nan':
            pass
        try:
            print('date: %s the rollover indictor is %s'%(num2date(self.tradingday[self.count]), self.Rollover_ind[0]))
        except:
            print self.count
        
