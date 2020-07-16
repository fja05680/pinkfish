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

    def __init__(self, symbol, capital, start, end, period=7, sma=200, stop_loss_pct=0, margin=pf.Margin.CASH):
        self._symbol = symbol
        self._capital = capital
        self._start = start
        self._end = end
        self._period = period
        self._sma = sma
        self._stop_loss_pct = stop_loss_pct/100
        self._margin = margin
        
    def _algo(self):
        """ Algo:
            1. The SPY is above its 200-day moving average or SPY is above its X-day ma
            2. The SPY closes at a X-day low, buy.
            3. If the SPY closes at a X-day high, sell your long position.
        """
        pf.TradeLog.cash = self._capital
        pf.TradeLog.margin = self._margin
        stop_loss = 0

        for i, row in enumerate(self._ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close 
            end_flag = pf.is_last_row(self._ts, i)
            shares = 0

            # buy
            if (self._tlog.shares == 0
                and (close > row.sma200 or close > row.sma)
                and close == row.period_low
                and not end_flag):

                # enter buy in trade log
                shares = self._tlog.buy(date, close)
                # set stop loss
                stop_loss = self._stop_loss_pct*close
            # sell
            elif (self._tlog.shares > 0
                  and (close == row.period_high or low < stop_loss or end_flag)):

                # enter sell in trade log
                shares = self._tlog.sell(date, close)

            if shares > 0:
                pf.DBG("{0} BUY  {1} {2} @ {3:.2f}".format(
                       date, shares, self._symbol, close))
            elif shares < 0:
                pf.DBG("{0} SELL {1} {2} @ {3:.2f} {4}".format(
                       date, -shares, self._symbol, close, 'STOP' if low < stop_loss else ''))

            # record daily balance
            self._dbal.append(date, high, low, close)

    def run(self):
        self._ts = pf.fetch_timeseries(self._symbol)
        self._ts = pf.select_tradeperiod(self._ts, self._start, self._end, use_adj=True)

        # Add technical indicator: 200 day sma
        sma200 = SMA(self._ts, timeperiod=200)
        self._ts['sma200'] = sma200

        # Add technical indicator: X day sma
        sma = SMA(self._ts, timeperiod=self._sma)
        self._ts['sma'] = sma

        # Add technical indicator: X day high, and X day low
        period_high = pd.Series(self._ts.close).rolling(self._period).max()
        period_low = pd.Series(self._ts.close).rolling(self._period).min()
        self._ts['period_high'] = period_high
        self._ts['period_low'] = period_low
        
        self._ts, self._start = pf.finalize_timeseries(self._ts, self._start)
        
        self._tlog = pf.TradeLog(self._symbol)
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
