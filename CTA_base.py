# encoding:utf-8
# this file is to parse the strategy setting 
# and load data into backtrader platform
import backtrader as bt
from datetime import datetime
import pandas as pd
import os
from HisDayData import HisDayData
from getdata_project.HdfUtility import HdfUtility
from getdata_project.dataUlt import (EXT_Hdf_Path,EXT_Rawdata ,EXT_Stitch) 

class CTA_setting_parse(object):
    def parse_setting(self, instance, setting):
        self.params = setting
        # basic setting
        # input every basic setting into a dictionary named 'basic_setting'
        if self.params['basic_setting'].get('startcash', None) :
            # set the starting cash
            instance.broker.setcash(self.params['basic_setting']['startcash'])
        if self.params['basic_setting'].get('commission', None) :
            # set the commission
            instance.broker.setcommission(self.params['basic_setting']['commission'])
        if self.params['basic_setting'].get('default_sizer', None) :
            # set the default sizer
            instance.addsizer(bt.sizers.FixedSize, stake=self.params['basic_setting']['default_sizer'])  
        if self.params['basic_setting'].get('analyzer',None):
            # add the analyzers
            analyzers = self.params['basic_setting']['analyzer']
            for analyzer, newname in  analyzers.items():
                instance.addanalyzer(getattr(bt.analyzers, analyzer), _name = newname)
        # self.params.pop('basic_setting')
    
    
    def add2strat(self,instance):
        for strat in instance.strats:
            self.params['vtsymbol_setting'].update(self.params['data_setting'])
            strat[0][0].od_params = self.params['vtsymbol_setting']
    def loading_data(self, instance):
    
        # parse the datasetting
        
        self.datainfo = self.params['data_setting']  
        self.Parse_datasetting()
        
        # create the our datafeed
        CTA_datafeed_name = 'CTA_datafeed'.encode('utf-8')
        # if you have other data form, change the bt.feeds.pandafeed to your favour
        # you must cancel the lines in the dataserise or the lines will over
        self.CTA_datafeed = type(CTA_datafeed_name,(bt.feeds.PandasData,),{'lines':self.lines, 'params':self.data_params})
        
        
        # loading bar data period: 1 day
        getdata_utl = HdfUtility()

        
        for i,vt in enumerate(self.vtsymbol):
            domdata = getdata_utl.hdfRead(EXT_Hdf_Path, self.excode[i], vt, kind1=EXT_Stitch,
                                                  kind2='00',kind3='1d',startdate=self.startdate,enddate=self.enddate)

            # 判断需要加载哪些类型的数据，dom ?, subdom?, rawdata?
            # 是否加载主力合约数据
            if self.datainfo['loading_datatype']['domdata']:
                # choose the columns we need
                # 来自hdf5中的数据的时间列为Date，平台的lines默认的时间名为datetime               
                domdata = domdata.reset_index().rename(columns = {'Date':'datetime'})
                domdata = domdata[self.datainfo['COLUMNS']].set_index('datetime')
                
                # 由于平台只允许datetime为非float类型，所以如果数据中有其他类型需要转化为数值类型
                is_numtype = {c : pd.api.types.is_numeric_dtype(domdata[c]) for c in domdata.columns}
                if False in is_numtype.values():
                    domdata = self.type_change(domdata, is_numtype)
            
                data = self.CTA_datafeed(dataname = domdata)
                # 将主力合约命名形如IF0000
                instance.adddata(data, name = vt+'0000')
            
            # 是否加载次主力合约数据
            if self.datainfo['loading_datatype']['subdomdata']:
                subdom =  getdata_utl.hdfRead(EXT_Hdf_Path, self.excode[i], vt, kind1=EXT_Stitch,
                                                  kind2='01',kind3=None,startdate=self.startdate,enddate=self.enddate)
                subdom = subdom.reset_index().rename(columns = {'Date':'datetime'})                
                subdom = subdom[self.datainfo['COLUMNS']].set_index('datetime')
                
                # 由于平台只允许datetime为非float类型，所以如果数据中有其他类型需要转化为数值类型
                is_numtype = {c : pd.api.types.is_numeric_dtype(subdom[c]) for c in subdom.columns}
                if False in is_numtype.values():
                    subdom = self.type_change(subdom, is_numtype)
            
                data = self.CTA_datafeed(dataname = subdom)
                # 将次主力合约命名形如IF0001
                instance.adddata(data, name = vt+'0001')                
        
        # 是否加载原始数据
        if self.datainfo['loading_datatype']['rawdata']:
            # 如果需要加载原始合约数据，那么每个数据feed的名字就是合约名
            # 将每个合约的数据分别导入回测平台, 注意的是原始合约并没有调整因子
            self.datainfo['COLUMNS'].remove('AdjFactor')            
            for i, vt in enumerate(self.vtsymbol):
                raw_data = getdata_utl.getrawDate(EXT_Hdf_Path,self.excode[i], vt, kind1 = 'Rawdata',kind2=None,kind3='1d',
                                                  startdate = self.startdate, enddate = self.enddate)
                raw_data = raw_data.reset_index().rename(columns = {'Date':'datetime'})                
                contract = pd.unique(raw_data['Asset'])
                for c in contract:
                    data_temp = raw_data.ix[raw_data['Asset'] == c,:]
                    data_temp = data_temp[self.datainfo['COLUMNS']].set_index('datetime')
                    # 由于平台只允许datetime为非float类型，所以如果数据中有其他类型需要转化为数值类型
                    is_numtype = {c : pd.api.types.is_numeric_dtype(data_temp[c]) for c in data_temp.columns}
                    if False in is_numtype.values():
                        data_temp = self.type_change(data_temp, is_numtype)                    
                    
                    
                    
                    data = self.CTA_datafeed(dataname = data_temp)
                    instance.adddata(data, name = c)                    

                    
    def Parse_datasetting(self):
        # lines and params setting
        self.lines = tuple([l.lower() for l in self.datainfo['COLUMNS']])
        self.data_params = (
                ('nocase', True),
                ('datetime', None),
                ('open', -1),
                ('high', -1),
                ('low', -1),
                ('close', -1),
                ('volume', -1),
                ('AdjFactor',-1),
                ('openinterest', -1),
            )
    
        params_name = [name for name, i in self.data_params ]
        add2params = [l for l in self.lines if l not in params_name]
        self.data_params = self.data_params + tuple([(name,-1) for name in add2params])        
    
        self.vtsymbol = self.datainfo['vt']
        self.excode = self.datainfo['excode']
        self.startdate = self.datainfo['startdate'] if self.datainfo.get('startdate', None) else None
        self.enddate   = self.datainfo['enddate'] if self.datainfo.get('enddate', None) else None

        
    
    def type_change(self, data, datatype_dict):
        
        for column, is_numtype in datatype_dict.items():
            if not is_numtype:
                # 这里使用者可以根据各种类型进行调整
                #if pd.api.types.is_bool_dtype(data[column])
                #if pd.api.types.is_string_dtype(data[column])                
                data[column] = data[column].astype(int)
        return data
        
        
        
        
    def add_extrdata(self, instance, extra_data, vt, extra_name):
        extra_data = extra_data.reset_index().rename(columns = {'Date':'datetime'})               
        extra_data = extra_data[self.datainfo['COLUMNS']].set_index('datetime')
        data = self.CTA_datafeed(dataname = extra_data)
        instance.adddata(data, name = vt + extra_name )
        
    
                
                
                
    
    
        
            
        
            
            
        
    

