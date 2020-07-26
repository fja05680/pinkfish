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
                 stop_loss_pct=0, margin=1, period=7, max_positions=4, ):
        self.symbol = symbol
        self.capital = capital
        self.start = start
        self.end = end
        self.use_adj = use_adj
        self.period = period
        self.max_positions = max_positions
        self.stop__loss_pct = stop_loss_pct/100
        self.margin = margin
        
    def _algo(self):
        """ Algo:
            1. The SPY is above its 200-day moving average
            2. The SPY closes at a X-day low, buy with full capital.
            3. If the SPY closes at a X-day high, sell some.
               If it sets further highs, sell some more, etc...
            4. If you have free cash, use it all when fresh lows are set.
        """
        pf.TradeLog.cash = self.capital
        pf.TradeLog.margin = self.margin
        stop_loss = 0

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close; 
            end_flag = pf.is_last_row(self.ts, i)
            shares = 0

            # buy
            if (self.tlog.num_open_trades() < self.max_positions
                and row.regime > 0
                and close == row.period_low
                and not end_flag):
                
                # calc number of shares
                buying_power = self.tlog.calc_buying_power(price=close)
                shares = self.tlog.calc_shares(price=close, cash=buying_power)
                
                # if we have enough cash to buy any shares, then buy them
                if shares > 0:

                    # enter buy in trade log
                    self.tlog.buy(date, close, shares)
                    # set stop loss
                    stop_loss = 0*close
                    # set positions to max_positions
                    self.positions = self.max_positions

            # sell
            elif (self.tlog.num_open_trades() > 0
                  and (close == row.period_high
                       or low < stop_loss
                       or end_flag)):
                
                if end_flag:
                    shares = self.tlog.shares
                else:
                    shares = int(self.tlog.shares / (self.positions))
                    self.positions -= 1

                # enter sell in trade log
                shares = self.tlog.sell(date, close, shares)

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
                                         self.end, use_adj=False)

        # Add technical indicator: day sma regime filter
        self.ts['regime'] = \
            pf.CROSSOVER(self.ts, timeperiod_fast=1, timeperiod_slow=200)

        # Add technical indicator: X day high, and X day low
        period_high = pd.Series(self.ts.close).rolling(self.period).max()
        period_low = pd.Series(self.ts.close).rolling(self.period).min()
        self.ts['period_high'] = period_high
        self.ts['period_low'] = period_low
        
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
