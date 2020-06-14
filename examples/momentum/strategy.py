"""
stategy
---------
"""

# other imports
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from talib.abstract import *
import random

# project imports
import pinkfish as pf

pf.DEBUG = False
TRADING_DAYS_PER_MONTH = 21
TRADING_DAYS_PER_YEAR = 252


class Strategy():

    def __init__(self, symbol, capital, start, end, period=None):
        self._symbol = symbol
        self._capital = capital
        self._start = start
        self._end = end
        self._period = period
        
    def _algo(self):
        """ Algo:
            1. The SPY is higher than X days ago, buy
            2. If the SPY is lower than X days ago, sell your long position.
        """
        self._tlog.initialize(self._capital)
        start_flag = True
        stop_loss = 0
        periods = range(TRADING_DAYS_PER_MONTH*3, TRADING_DAYS_PER_MONTH*13, TRADING_DAYS_PER_MONTH)

        for i, row in enumerate(self._ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close; 
            end_flag = pf.is_last_row(self._ts, i)
            shares = 0

            if i < TRADING_DAYS_PER_YEAR*2:
                continue
            elif start_flag:
                start_flag = False
                # set start
                self._start = date
                
            if self._tlog.num_open_trades() == 0:
                # if period is None, then select a random trading period of
                # 3,4,5,...,or 12 months
                if self._period is None:
                    period = random.choice(periods)
                else:
                    period = self._period

            lookback = self._ts['close'][i-period]
            
            # buy (and row.first_dotm)
            if (self._tlog.num_open_trades() == 0
                and row.first_dotm
                and close > lookback
                and not end_flag):

                # enter buy in trade log
                shares = self._tlog.enter_trade(date, close)
                # set stop loss
                stop_loss = 0*close
            # sell
            elif (self._tlog.num_open_trades() > 0
                  and row.first_dotm
                  and (close < lookback or low < stop_loss or end_flag)):

                # enter sell in trade log
                shares = self._tlog.exit_trade(date, close)

            if shares > 0:
                pf.DBG("{0} BUY  {1} {2} @ {3:.2f}".format(
                       date, shares, self._symbol, close))
            elif shares < 0:
                pf.DBG("{0} SELL {1} {2} @ {3:.2f}".format(
                       date, -shares, self._symbol, close))

            # record daily balance
            self._dbal.append(date, high, low, close, self._tlog.shares)

    def run(self):
        self._ts = pf.fetch_timeseries(self._symbol)
        self._ts = pf.select_tradeperiod(self._ts, self._start,
                                         self._end, use_adj=True)

        # add calendar columns
        self._ts = pf.calendar(self._ts)
        
        self._ts, self._start = pf.finalize_timeseries(self._ts, self._start)
        
        self._tlog = pf.TradeLog()
        self._dbal = pf.DailyBal()

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        self.tlog = self._tlog.get_log()
        self.dbal = self._dbal.get_log(self.tlog)
        return self.tlog, self.dbal

    def get_stats(self):
        stats = pf.stats(self._ts, self.tlog, self.dbal, self._capital)
        return stats

def summary(strategies, *metrics):
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
