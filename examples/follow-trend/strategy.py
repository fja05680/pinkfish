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

    def __init__(self, symbol, capital, start, end, use_adj=True,
                 sma_period=200, percent_band=0, regime_filter=True):
        self.symbol = symbol
        self.capital = capital
        self.start = start
        self.end = end
        self.use_adj = use_adj
        self.sma_period = sma_period
        self.percent_band = percent_band/100
        self.regime_filter = regime_filter

    def _algo(self):
        """ Algo:
            1. S&P 500 index closes above its 200 day moving average
            2. The stock closes above its upper band, buy

            3. S&P 500 index closes below its 200 day moving average
            4. The stock closes below its lower band, sell your long position.
        """
        pf.TradeLog.cash = self.capital
        pf.TradeLog.seq_num = 0

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close; 
            end_flag = pf.is_last_row(self.ts, i)
            upper_band = row.sma + row.sma * self.percent_band
            lower_band = row.sma - row.sma * self.percent_band
            shares = 0
            
            # Sell Logic
            # First we check if an existing position in symbol should be sold
            #  - sell if (use_regime_filter and regime < 0)
            #  - sell if price closes below lower_band
            #  - sell if end of data

            if self.tlog.shares > 0:
                 if ((self.regime_filter and row.regime < 0)
                     or close < lower_band
                     or end_flag):

                    # enter sell in trade log
                    shares = self.tlog.sell(date, close)

            # Buy Logic
            # First we check to see if there is an existing position, if so do nothing
            #  - Buy if (regime > 0 or not use_regime_filter)
            #            and price closes above upper_band
            #            and (use_regime_filter and regime > 0)
            
            else:
                if ((row.regime > 0 or not self.regime_filter)
                    and close > upper_band):

                    # enter buy in trade log
                    shares = self.tlog.buy(date, close)

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

        # Add technical indicator:  day sma
        sma = SMA(self.ts, timeperiod=self.sma_period)
        self.ts['sma'] = sma          
        
        # add S&P500 200 sma regime filter
        ts = pf.fetch_timeseries('^GSPC')
        ts = pf.select_tradeperiod(ts, self.start, self.end, False) 
        self.ts['regime'] = \
            pf.CROSSOVER(ts, timeperiod_fast=1, timeperiod_slow=200)
        
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
