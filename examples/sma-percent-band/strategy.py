"""
stategy
---------
stategy template
"""

# Use future imports for python 3.0 forward compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# Other imports
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import datetime
from talib.abstract import *
import pinkfish as pf

class Strategy():
    """ strategy """

    def __init__(self, symbol, capital, start, end, sma_period=200, percent_band=0,
                 slippage_per_trade=0, commissions_per_trade=0):
        self._symbol = symbol
        self._capital = capital
        self._start = start
        self._end = end
        self._sma_period = sma_period
        self._percent_band = percent_band/100
        self._slippage_per_trade = slippage_per_trade
        self._commissions_per_trade = commissions_per_trade

    def _algo(self):
        """ Algo:
            1. The SPY closes above its upper band, buy
            2. If the SPY closes below its lower band, sell your long position.
        """

        cash = self._capital
        shares = 0
        start_flag = True
        end_flag = False
        stop_loss = 0

        for i in range(len(self._ts.index)):

            date = self._ts.index[i]
            high = self._ts['high'][i]
            low = self._ts['low'][i]
            close = self._ts['close'][i]
            sma = self._ts['sma'][i]
            upper_band = sma + sma * self._percent_band
            lower_band = sma - sma * self._percent_band
            end_flag = True if (i == len(self._ts.index) - 1) else False

            if pd.isnull(sma) or self._ts.index[i] < self._start:
                continue
            elif start_flag:
                start_flag = False
                # set start and end
                self._start = self._ts.index[i]
                self._end = self._ts.index[-1]

            # buy
            if self._tlog.num_open_trades() == 0:
                if close > upper_band and not end_flag:

                    # calculate shares to buy and remaining cash
                    shares, cash = self._tlog.calc_shares(cash, close)

                    # enter buy in trade log
                    self._tlog.enter_trade(date, close, shares)
                    #print("{0} BUY  {1} {2} @ {3:.2f}".format(date, shares, self._symbol, close))

                    # record daily balance
                    self._dbal.append(date, high, low, close, shares, cash, pf.TradeState.OPEN)
            
                    # set stop loss
                    stop_loss = 0*close
                else:
                    # hold
                    self._dbal.append(date, high, low, close, shares, cash, pf.TradeState.HOLD)

            # sell
            elif close < lower_band or \
                (low < stop_loss) or \
                end_flag:

                # enter sell in trade log
                idx = self._tlog.exit_trade(date, close)
                shares = self._tlog.get_log()['qty'][idx]
                #print("{0} SELL {1} {2} @ {3:.2f}".format(date, shares, self._symbol, close))
                #if (close < stop_loss):
                #    print("--------------------STOP-----------------------------")

                # record daily balance
                self._dbal.append(date, high, low, close, shares, cash, pf.TradeState.CLOSE)   
            
                # update cash
                cash = self._tlog.calc_cash(cash, close, shares)
            
                # update shares
                shares = 0

            # hold
            else:
                self._dbal.append(date, high, low, close, shares, cash, pf.TradeState.HOLD)   

    def run(self):
        self._ts = pf.fetch_timeseries(self._symbol)
        self._ts = pf.select_tradeperiod(self._ts, self._start,
                                         self._end, use_adj=False)

        # Add technical indicator:  day sma
        sma = SMA(self._ts, timeperiod=self._sma_period)
        self._ts['sma'] = sma          

        self._tlog = pf.TradeLog()
        self._dbal = pf.DailyBal()

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        tlog = self._tlog.get_log()
        dbal = self._dbal.get_log()
        return tlog, dbal

    def stats(self):
        tlog, dbal = self.get_logs()
        
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
        

