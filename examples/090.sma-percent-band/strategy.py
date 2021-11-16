"""
The SMA percent band stategy.

Create a percent band around a SMA.  For example, if the SMA is 200
and the percent band is 5%, then multiply the 200 by 1.05 and 0.95
to create the upper and lower band, respectively.  Buy if the price
closes above the upper band and sell if the price closes below the
lower band.
"""

import datetime

import matplotlib.pyplot as plt
import pandas as pd

import pinkfish as pf


default_options = {
    'use_adj' : False,
    'use_cache' : True,
    'sma' : 200,
    'band' : 0
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
            if self.tlog.shares == 0:
                if row.regime > 0 and self.ts['regime'][i-1] < 0:
                    self.tlog.buy(date, close)
            # Sell
            else:
                if row.regime < 0 or end_flag:
                    self.tlog.sell(date, close)

            # Record daily balance.
            self.dbal.append(date, close)

    def run(self):

        # Fetch and select timeseries
        self.ts = pf.fetch_timeseries(self.symbol, use_cache=self.options['use_cache'])
        self.ts = pf.select_tradeperiod(self.ts, self.start, self.end,
                                        use_adj=self.options['use_adj'])

        # Add technical indicator: sma regime filter
        self.ts['regime'] = \
            pf.CROSSOVER(self.ts, timeperiod_fast=1, timeperiod_slow=self.options['sma'],
                         band=self.options['band'])

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

