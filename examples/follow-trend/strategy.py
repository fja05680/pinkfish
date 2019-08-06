"""
stategy
---------
"""

# use future imports for python 3.x forward compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# other imports
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from talib.abstract import *

# project imports
import pinkfish as pf

class Strategy():

    def __init__(self, symbol, capital, start, end, use_adj=False,
                 sma_period=200, percent_band=0, regime_filter=False,
                 slippage_per_trade=0, commissions_per_trade=0):
        self._symbol = symbol
        self._capital = capital
        self._start = start
        self._end = end
        self._use_adj = use_adj
        self._sma_period = sma_period
        self._percent_band = percent_band/100
        self._regime_filter = regime_filter
        self._slippage_per_trade = slippage_per_trade
        self._commissions_per_trade = commissions_per_trade

    def _algo(self):
        """ Algo:
            1. S&P 500 index closes above its 200 day moving average
            2. The stock closes above its upper band, buy

            3. S&P 500 index closes below its 200 day moving average
            4. The stock closes below its lower band, sell your long position.
        """
        self._tlog.cash = self._capital
        start_flag = True
        end_flag = False

        for i, row in enumerate(self._ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high
            low = row.low
            close = row.close
            sma = row.sma
            upper_band = sma + sma * self._percent_band
            lower_band = sma - sma * self._percent_band
            regime = row.regime
            end_flag = True if (i == len(self._ts) - 1) else False
            trade_state = None

            if pd.isnull(sma) or date < self._start:
                continue
            elif start_flag:
                start_flag = False
                # set start and end
                self._start = date
                self._end = self._ts.index[-1]

            # buy
            if (self._tlog.num_open_trades() == 0
                and (regime > 0 or not self._regime_filter)
                and close > upper_band
                and not end_flag):

                # enter buy in trade log
                shares = self._tlog.enter_trade(date, close)
                trade_state = pf.TradeState.OPEN
                #print("{0} BUY  {1} {2} @ {3:.2f}".format(
                #      date, shares, self._symbol, close))

            # sell
            elif (self._tlog.num_open_trades() > 0
                  and ((self._regime_filter and regime < 0)
                       or close < lower_band
                       or end_flag)):

                # enter sell in trade log
                shares = self._tlog.exit_trade(date, close)
                trade_state = pf.TradeState.CLOSE
                #print("{0} SELL {1} {2} @ {3:.2f}".format(
                #      date, shares, self._symbol, close))

            # hold
            else:
                trade_state = pf.TradeState.HOLD

            # record daily balance
            self._dbal.append(date, high, low, close,
                              self._tlog.shares, self._tlog.cash,
                              trade_state)

    def run(self):
        self._ts = pf.fetch_timeseries(self._symbol)
        self._ts = pf.select_tradeperiod(self._ts, self._start,
                                         self._end, self._use_adj)       

        # Add technical indicator:  day sma
        sma = SMA(self._ts, timeperiod=self._sma_period)
        self._ts['sma'] = sma          

        self._tlog = pf.TradeLog()
        self._dbal = pf.DailyBal()
        
        # add S&P500 200 sma regime filter
        ts = pf.fetch_timeseries('^GSPC')
        ts = pf.select_tradeperiod(ts, self._start, self._end, False)
        ts['sma200'] = SMA(ts, timeperiod=200)
        self._ts['regime'] = ts.apply(pf.Regime().apply, axis=1) 

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        rlog = self._tlog.get_log_raw()
        tlog = self._tlog.get_log()
        dbal = self._dbal.get_log()
        return rlog, tlog, dbal

    def stats(self):
        _, tlog, dbal = self.get_logs()
        
        stats = pf.stats(self._ts, tlog, dbal,
                         self._start, self._end, self._capital)
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
