"""
Golden Cross / Death Cross S&P 500 index (^GSPC)

1. sma50>sma200, buy
2. sma50<sma200, sell your long position.
"""

import datetime

import matplotlib.pyplot as plt
import pandas as pd

import pinkfish as pf


default_options = {
    'use_adj' : False,
    'use_cache' : True
}

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

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            close = row.close; 
            end_flag = pf.is_last_row(self.ts, i)

            # Buy
            # Note ts['regime'][i-1] is regime for previous day
            # We want to buy only on the day of a moving average crossover
            # i.e. yesteraday regime is negative, today it is positive
            if self.tlog.shares == 0:
                if row.regime > 0 and self.ts['regime'][i-1] < 0:
                    self.tlog.buy(date, close)  
            # Sell
            else:
                if row.regime < 0 or end_flag:
                    self.tlog.sell(date, close)

            # Record daily balance
            self.dbal.append(date, close)

    def run(self):

        # Fetch and selct timeseries
        self.ts = pf.fetch_timeseries(self.symbol, use_cache=self.options['use_cache'])
        self.ts = pf.select_tradeperiod(self.ts, self.start, self.end,
                                        self.options['use_adj'])

        # Add technical indicator: day sma regime filter.
        self.ts['regime'] = \
            pf.CROSSOVER(self.ts, timeperiod_fast=50, timeperiod_slow=200)

        # Finalize timeseries
        self.ts, self.start = pf.finalize_timeseries(self.ts, self.start,
                                                     dropna=True, drop_columns=['open', 'high', 'low'])

        
        self.tlog = pf.TradeLog(self.symbol)
        self.dbal = pf.DailyBal()

        self._algo()
        self._get_logs()
        self._get_stats()

    def _get_logs(self):
        self.rlog = self.tlog.get_log_raw()
        self.tlog = self.tlog.get_log()
        self.dbal = self.dbal.get_log(self.tlog)

    def _get_stats(self):
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)

