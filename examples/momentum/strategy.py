"""
stategy
---------
"""

import pandas as pd
import matplotlib.pyplot as plt
import datetime
from talib.abstract import *
import random

import pinkfish as pf


class Strategy:

    def __init__(self, symbol, capital, start, end, period=None, margin=1):
        self.symbol = symbol
        self.capital = capital
        self.start = start
        self.end = end
        self.period = period
        self.margin = margin
        
    def _algo(self):
        """ Algo:
            1. The SPY is higher than X days ago, buy
            2. If the SPY is lower than X days ago, sell your long position.
        """
        pf.TradeLog.cash = self.capital
        pf.TradeLog.margin = self.margin
        stop_loss = 0

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close 
            end_flag = pf.is_last_row(self.ts, i)
            shares = 0
                
            if self.tlog.shares == 0:
                # if period is None, then select a random trading period of
                # 6,7,8,...,or 12 months
                if self.period is None:
                    period = random.choice(range(6, 12+1))
                else:
                    period = self.period

            mom = getattr(row, 'mom'+str(period))
            
            # buy (and row.first_dotm)
            if self.tlog.shares == 0:
                #if (row.first_dotm
                if (row.first_dotw
                    and mom > 0):
                    # enter buy in trade log
                    shares = self.tlog.buy(date, close)
                    # set stop loss
                    stop_loss = 0*close
            # sell
            else:
                #if (row.first_dotm
                if (row.first_dotw
                    and (mom < 0 or low < stop_loss or end_flag)):
                    # enter sell in trade log
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
                                         self.end, use_adj=True)

        # add calendar columns
        self.ts = pf.calendar(self.ts)
        
        # add momentum indicator for 3...12 months
        lookbacks = range(3, 18+1)
        for lookback in lookbacks:
            self.ts['mom'+str(lookback)] = pf.MOMENTUM(self.ts,
                lookback=lookback, time_frame='monthly',
                price='close', prevday=False)

        self.ts, self.start = pf.finalize_timeseries(self.ts, self.start)
        
        self.tlog = pf.TradeLog(self.symbol)
        self.dbal = pf.DailyBal()

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        self.tlog = self.tlog.get_log()
        self.dbal = self.dbal.get_log(self.tlog)
        return self.tlog, self.dbal

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
