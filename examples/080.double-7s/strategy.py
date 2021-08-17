"""
The double-7s stategy.

The simple double 7's strategy was revealed in the book
'Short Term Strategies that Work: A Quantified Guide to Trading Stocks
and ETFs', by Larry Connors and Cesar Alvarez. It's a mean reversion
strategy looking to buy dips and sell on strength and was initially
designed for ETFs.

This module allows us to examine this strategy and try different
period, stop loss percent, margin, and whether to use a regime filter
or not.  We can also overide the regime filter and start trading again
by setting `sma` below 200 (50-100 works well for this).  The idea is
that then security has bottomed and there are some opportunities for
good trades before the regime filter would allow us to trade again.
"""

import datetime

import matplotlib.pyplot as plt
import pandas as pd
from talib.abstract import *

import pinkfish as pf


pf.DEBUG = False

default_options = {
    'use_adj' : False,
    'use_cache' : True,
    'stop_loss_pct' : 1.0,
    'margin' : 1,
    'period' : 7,
    'sma' : 200,
    'use_regime_filter' : True
}

class Strategy:

    def __init__(self, symbol, capital, start, end, options=default_options):

        self.symbol = symbol
        self.capital = capital
        self.start = start
        self.end = end
        self.options = options.copy()
        
        self.ts = None
        self.tlog = None
        self.dbal = None
        self.stats = None
        
    def _algo(self):

        pf.TradeLog.cash = self.capital
        pf.TradeLog.margin = self.options['margin']
        stop_loss = 0

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close 
            end_flag = pf.is_last_row(self.ts, i)
            
            # Sell Logic
            # First we check if we have any shares, then
            #  - Sell if price closes at X day high.
            #  - Sell if price closes below stop loss.
            #  - Sell if end of data.

            if self.tlog.shares > 0:
                if close == row.period_high or low < stop_loss or end_flag:
                    if close < stop_loss: print('STOP LOSS!!!')
                    self.tlog.sell(date, close)
            
            # Buy Logic
            #  - Buy if (regime > 0 or close > row.sma) or not using regime filter)
            #            and price closes at X day low.

            else:
                if (((row.regime > 0 or close > row.sma) or not self.options['use_regime_filter'])
                      and close == row.period_low):
                    self.tlog.buy(date, close)
                    # Set stop loss.
                    stop_loss = (1-self.options['stop_loss_pct'])*close

            # Record daily balance.
            self.dbal.append(date, high, low, close)

    def run(self):
        
        # Fetch and select timeseries.
        self.ts = pf.fetch_timeseries(self.symbol, use_cache=self.options['use_cache'])
        self.ts = pf.select_tradeperiod(self.ts, self.start, self.end, use_adj=self.options['use_adj'])

        # Add technical indicator: 200 sma regime filter.
        self.ts['regime'] = pf.CROSSOVER(self.ts, timeperiod_fast=1, timeperiod_slow=200)

        # Add technical indicator: X day sma.
        self.ts['sma'] = SMA(self.ts, timeperiod=self.options['sma'])

        # Add technical indicator: X day high, and X day low.
        self.ts['period_high'] = pd.Series(self.ts.close).rolling(self.options['period']).max()
        self.ts['period_low'] =  pd.Series(self.ts.close).rolling(self.options['period']).min()
        
        # Finalize timeseries.
        self.ts, self.start = pf.finalize_timeseries(self.ts, self.start, dropna=True)
        
        # Create tlog and dbal objects.
        self.tlog = pf.TradeLog(self.symbol)
        self.dbal = pf.DailyBal()

        # Run algo, get logs, and get stats.
        self._algo()
        self._get_logs()
        self._get_stats()

    def _get_logs(self):
        self.tlog = self.tlog.get_log()
        self.dbal = self.dbal.get_log(self.tlog)

    def _get_stats(self):
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)

