# encoding:utf-8


# test the single Indicator 

from CTA_factor_backtrade.Indicator_Base import Indicator_Fetch
from getdata_project.dataUlt import (EXT_CFE_ALL,EXT_SHFE_ALL, EXT_DCE_ALL)



# 测试自己生成的因子
if __name__ == '__main__':
    
    indicator_name = 'Momentum_ind'
    window_prd = 15
    excode = ['CFE']*len(EXT_CFE_ALL) + ['SHFE']*len(EXT_SHFE_ALL) + ['DCE']*len(EXT_DCE_ALL)
    vt = EXT_CFE_ALL + EXT_SHFE_ALL + EXT_DCE_ALL
    Setting = {'data_setting':{'startdate':'20120101', 'enddate':'20171231', 'vt' : vt, 'excode': excode,
               'COLUMNS':['datetime', 'AdjFactor', 'Open', 'Low', 'High', 'Close', 'Delistdate'],
               'loading_datatype':{'domdata':True, 'subdomdata':False, 'rawdata':False, 'extradata':False} },
               'indsave':True
               }
    #indicator_fetch = Indicator_Fetch()
    Indicator_Fetch.run_indicator(indicator_name= indicator_name, indicator_params = {'window_prd':window_prd}, SETTING = Setting)


# 测试利用talib生成的因子

if __name__ == '__main__':
    indicator_name = 'BBANDS'
    timeperiod = 30
    vt = ['IF']
    excode = ['CFE']
    # 因子需要的数据名称
    dataname = ['Close']
    Setting = {'data_setting':{'startdate':'20120101', 'enddate':'20171231', 'vt' : vt, 'excode': excode,
                               'COLUMNS':['datetime', 'Close','AdjFactor'],
               'loading_datatype':{'domdata':True} },
               'indsave':True
               }    
    Indicator_Fetch.run_indicator(indicator_name= indicator_name, indicator_params = {'window_prd':timeperiod, 'dataname':dataname}, SETTING = Setting)
    
    

