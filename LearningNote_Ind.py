from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt

class MyTrix(bt.Indicator):

    lines = ('trix',)
    params = (('period', 15),)

    def __init__(self):
        ema1 = bt.indicators.EMA(self.data, period=self.p.period)
        ema2 = bt.indicators.EMA(ema1, period=self.p.period)
        ema3 = bt.indicators.EMA(ema2, period=self.p.period)

        self.lines.trix = 100.0 * (ema3 - ema3(-1)) / ema3(-1)

class MyTrixSignalInherited(MyTrix):

    lines = ('signal',)
    params = (('sigperiod', 9),)

    def __init__(self):
        super(MyTrixSignalInherited, self).__init__()
        self.lines.signal = btind.EMA(self.lines.trix, period=self.p.sigperiod)
