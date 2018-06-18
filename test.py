import numpy as np
import pandas as pd 
from HdfUtility import HdfUtility
from dataUlt import EXT_Hdf_Path
import backtrader as bt


hdf = HdfUtility()
df = hdf.hdfRead(EXT_Hdf_Path, 'CFE', 'IF', kind1='Stitch', kind2='00',kind3='1d')

sma = bt.indicators.SimpleMovingAverage(df, period=14)

sma.head(5)
