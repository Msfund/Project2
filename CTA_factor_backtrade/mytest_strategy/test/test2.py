# encoding:utf-8

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import argparse

import backtrader as bt
from backtrader.utils.py3 import range

import pandas as pd


class StFetcher(object):
    _STRATS = []

    @classmethod
    def register(cls, target):
        cls._STRATS.append(target)

    @classmethod
    def COUNT(cls):
        return range(len(cls._STRATS))

    def __new__(cls, *args, **kwargs):
        idx = kwargs.pop('idx')

        obj = cls._STRATS[idx](*args, **kwargs)
        return obj


@StFetcher.register
class St0(bt.SignalStrategy):
    def __init__(self):
        sma1, sma2 = bt.ind.SMA(period=10), bt.ind.SMA(period=30)
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)


@StFetcher.register
class St1(bt.SignalStrategy):
    def __init__(self):
        sma1 = bt.ind.SMA(period=10)
        crossover = bt.ind.CrossOver(self.data.close, sma1)
        self.signal_add(bt.SIGNAL_LONG, crossover)


def runstrat(pargs=None):

    cerebro = bt.Cerebro()
    data = pd.read_csv(r'D:\\backtrader\\backtrader-master\\CTA_factor_backtrade\\mytest_strategy\\testdata\\CFE_IC_dom.csv'
                       ,index_col=0, parse_dates=True)

    data = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data, name='IC')

    cerebro.addanalyzer(bt.analyzers.Returns)
    cerebro.optstrategy(StFetcher, idx=StFetcher.COUNT())
    results = cerebro.run(maxcpus=1, optreturn=False)

    strats = [x[0] for x in results]  # flatten the result
    for i, strat in enumerate(strats):
        rets = strat.analyzers.returns.get_analysis()
        print('Strat {} Name {}:\n  - analyzer: {}\n'.format(
            i, strat.__class__.__name__, rets))



if __name__ == '__main__':
    runstrat()