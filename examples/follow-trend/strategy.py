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
                 sma_period=200, percent_band=0, regime_filter=False):
        self._symbol = symbol
        self._capital = capital
        self._start = start
        self._end = end
        self._use_adj = use_adj
        self._sma_period = sma_period
        self._percent_band = percent_band/100
        self._regime_filter = regime_filter

    def _algo(self):
        """ Algo:
            1. S&P 500 index closes above its 200 day moving average
            2. The stock closes above its upper band, buy

            3. S&P 500 index closes below its 200 day moving average
            4. The stock closes below its lower band, sell your long position.
        """
        pf.TradeLog.cash = self._capital

        for i, row in enumerate(self._ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close; 
            end_flag = pf.is_last_row(self._ts, i)
            upper_band = row.sma + row.sma * self._percent_band
            lower_band = row.sma - row.sma * self._percent_band
            shares = 0

            # buy
            if (self._tlog.shares == 0
                and (row.regime > 0 or not self._regime_filter)
                and close > upper_band
                and not end_flag):

                # enter buy in trade log
                shares = self._tlog.buy(date, close)
            # sell
            elif (self._tlog.shares > 0
                  and ((self._regime_filter and row.regime < 0)
                       or close < lower_band
                       or end_flag)):

                # enter sell in trade log
                shares = self._tlog.sell(date, close)

            if shares > 0:
                pf.DBG("{0} BUY  {1} {2} @ {3:.2f}".format(
                       date, shares, self._symbol, close))
            elif shares < 0:
                pf.DBG("{0} SELL {1} {2} @ {3:.2f}".format(
                       date, -shares, self._symbol, close))

            # record daily balance
            self._dbal.append(date, high, low, close) 

    def run(self):
        self._ts = pf.fetch_timeseries(self._symbol)
        self._ts = pf.select_tradeperiod(self._ts, self._start,
                                         self._end, self._use_adj)       

        # Add technical indicator:  day sma
        sma = SMA(self._ts, timeperiod=self._sma_period)
        self._ts['sma'] = sma          
        
        # add S&P500 200 sma regime filter
        ts = pf.fetch_timeseries('^GSPC')
        ts = pf.select_tradeperiod(ts, self._start, self._end, False) 
        self._ts['regime'] = \
            pf.CROSSOVER(ts, timeperiod_fast=1, timeperiod_slow=200)
        
        self._ts, self._start = pf.finalize_timeseries(self._ts, self._start)
        
        self._tlog = pf.TradeLog(self._symbol)
        self._dbal = pf.DailyBal()

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        self.rlog = self._tlog.get_log_raw()
        self.tlog = self._tlog.get_log()
        self.dbal = self._dbal.get_log(self.tlog)
        return self.rlog, self.tlog, self.dbal

    def get_stats(self):
        stats = pf.stats(self._ts, self.tlog, self.dbal, self._capital)
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
