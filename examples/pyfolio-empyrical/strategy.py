"""
stategy
---------
"""

import pandas as pd
import matplotlib.pyplot as plt
import datetime
from talib.abstract import *

import pinkfish as pf

pf.DEBUG = False


class Strategy:

    def __init__(self, symbol, capital, start, end, use_adj=False,
                 sma_period=200, percent_band=0):
        self.symbol = symbol
        self.capital = capital
        self.start = start
        self.end = end
        self.use_adj = use_adj
        self.sma_period = sma_period
        self.percent_band = percent_band

    def _algo(self):
        """ Algo:
            1. The SPY closes above its upper band, buy
            2. If the SPY closes below its lower band, sell your long position.
        """
        pf.TradeLog.cash = self.capital

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close; 
            end_flag = pf.is_last_row(self.ts, i)
            shares = 0

            # buy
            if self.tlog.shares == 0:
                if row.regime > 0:
                    shares = self.tlog.buy(date, close)
            # sell
            else:
                if row.regime < 0 or end_flag:
                    shares = self.tlog.sell(date, close)

            if shares > 0:
                pf.DBG("{0} BUY  {1} {2} @ {3:.2f}".format(
                       date, shares, self.symbol, close))
            elif shares < 0:
                pf.DBG("{0} SELL {1} {2} @ {3:.2f}".format(
                       date, -shares, self.symbol, close))

            # record daily balance
            self.dbal.append(date, high, low, close)

    def run(self):
        self.ts = pf.fetch_timeseries(self.symbol)
        self.ts = pf.select_tradeperiod(self.ts, self.start,
                                         self.end, self.use_adj)
        
        # Add technical indicator: day sma regime filter
        self.ts['regime'] = \
            pf.CROSSOVER(self.ts, timeperiod_fast=1, timeperiod_slow=self.sma_period,
                         band=self.percent_band)
        
        self.ts, self.start = pf.finalize_timeseries(self.ts, self.start)

        self.tlog = pf.TradeLog(self.symbol)
        self.dbal = pf.DailyBal()

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        self.rlog = self.tlog.get_log_raw()
        self.tlog = self.tlog.get_log()
        self.dbal = self.dbal.get_log(self.tlog)
        return self.rlog, self.tlog, self.dbal

    def get_stats(self):
        stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)
        return stats

def summary(strategies, metrics):
    """ Stores stats summary in a DataFrame.
        stats() must be called before calling this function """
    index = []
    columns = strategies.index
    data = []
    # add metrics
    for metric in metrics:
        index.append(metric)
        data.append([strategy.stats[metric] for strategy in strategies])

    df = pd.DataFrame(data, columns=columns, index=index)
    return df
    
def plot_bar_graph(df, metric):
    """ Plot Bar Graph: Strategy
        stats() must be called before calling this function """
    df = df.loc[[metric]]
    df = df.transpose()
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel=metric)
    df.plot(kind='bar', ax=axes, legend=False)
    axes.set_xticklabels(df.index, rotation=0)
