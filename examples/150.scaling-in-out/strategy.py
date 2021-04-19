"""
Scaling in and out of using the double-7s strategy.

1. The SPY is above its 200-day moving average.
2. The SPY closes at a X-day low, buy some shares.  If it sets further
   lows, buy some more.
3. If the SPY closes at a X-day high, sell some.  If it sets further
   highs, sell some more, etc...
"""

import datetime

import matplotlib.pyplot as plt
import pandas as pd
from talib.abstract import *

import pinkfish as pf


default_options = {
    'use_adj' : False,
    'use_cache' : False,
    'stop_loss_pct' : 1.0,
    'margin' : 1,
    'period' : 7,
    'max_open_trades' : 4,
    'enable_scale_in' : True,
    'enable_scale_out' : True
}

def _round_weight(weight):
    if    weight > 99: weight = 100
    elif  weight < 5: weight = 0
    else: weight = round(weight)
    return weight

class Strategy:

    def __init__(self, symbol, capital, start, end, options=default_options):

        self.symbol = symbol
        self.capital = capital
        self.start = start
        self.end = end
        self.options = options.copy()

        self.ts = None
        self.rlog = None
        self.tlog = None
        self.dbal = None
        self.stats = None

    def _algo(self):

        pf.TradeLog.cash = self.capital
        pf.TradeLog.margin = self.options['margin']
        stop_loss = 0

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close; 
            end_flag = pf.is_last_row(self.ts, i)

            max_open_trades = self.options['max_open_trades']
            enable_scale_in = self.options['enable_scale_in']
            enable_scale_out = self.options['enable_scale_out']
            max_open_trades_buy  = max_open_trades if enable_scale_in  else 1
            max_open_trades_sell  = max_open_trades if enable_scale_out  else 1

            # Buy Logic
            #  - Buy if still open trades slots left
            #       and bull regime
            #       and price closes at period low
            #       and not end end_flag

            if (row.regime > 0 and close == row.period_low and not end_flag):
                # Get current, then set new weight
                weight = self.tlog.share_percent(close)
                weight += 1 / max_open_trades_buy * 100
                weight = _round_weight(weight)
                self.tlog.adjust_percent(date, close, weight)

            # Sell Logic
            # First we check if we have any open trades, then
            #  - Sell if price closes at X day high.
            #  - Sell if price closes below stop loss.
            #  - Sell if end of data.

            elif (self.tlog.shares > 0 
                  and (close == row.period_high or low < stop_loss or end_flag)):
                # Get current, then set new weight
                weight = self.tlog.share_percent(close)
                weight -= 1 / max_open_trades_sell * 100
                weight = _round_weight(weight)
                self.tlog.adjust_percent(date, close, weight)

            # Record daily balance.
            self.dbal.append(date, high, low, close)

    def run(self):

        # Fetch and select timeseries.
        self.ts = pf.fetch_timeseries(self.symbol, use_cache=self.options['use_cache'])
        self.ts = pf.select_tradeperiod(self.ts, self.start, self.end, use_adj=self.options['use_adj'])

        # Add technical indicator: 200 day sma regime filter.
        self.ts['regime'] = pf.CROSSOVER(self.ts, timeperiod_fast=1, timeperiod_slow=200)

        # Add technical indicators: X day high, and X day low.
        self.ts['period_high'] = pd.Series(self.ts.close).rolling(self.options['period']).max()
        self.ts['period_low'] =  pd.Series(self.ts.close).rolling(self.options['period']).min()

        # Finalize timeseries.
        self.ts, self.start = pf.finalize_timeseries(self.ts, self.start)

        # Create tlog and dbal objects.
        self.tlog = pf.TradeLog(self.symbol)
        self.dbal = pf.DailyBal()

        # Run algo, get logs, and get stats.
        self._algo()
        self._get_logs()
        self._get_stats()

    def _get_logs(self):
        self.rlog = self.tlog.get_log_raw()
        self.tlog = self.tlog.get_log()
        self.dbal = self.dbal.get_log(self.tlog)

    def _get_stats(self):
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)

def summary(strategies, metrics):
    """
    Stores stats summary in a DataFrame.

    stats() must be called before calling this function.
    """
    index = []
    columns = strategies.index
    data = []
    # Add metrics.
    for metric in metrics:
        index.append(metric)
        data.append([strategy.stats[metric] for strategy in strategies])

    df = pd.DataFrame(data, columns=columns, index=index)
    return df

def plot_bar_graph(df, metric):
    """
    Plot Bar Graph.

    stats() must be called before calling this function.
    """
    df = df.loc[[metric]]
    df = df.transpose()
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel=metric)
    df.plot(kind='bar', ax=axes, legend=False)
    axes.set_xticklabels(df.index, rotation=0)
