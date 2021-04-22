"""
Dual Momentum Sector Rotation (DMSR)

'Relative momentum looks at price strength with respect to other assets.
Absolute momentum uses an asset’s own past performance to infer future
performance. Absolute momentum can reduce downside exposure as well
enhance returns. The best approach is to use both types of momentum
together. That is what dual momentum is all about.'
https://www.optimalmomentum.com/momentum/

Buy Signal: When the S&P 500 is above its 10-month simple moving
average, buy the sectors with the biggest gains over a three-month
timeframe.  10-months is about 200 trading days.

Sell Signal: Exit all positions when the S&P 500 moves below its
10-month simple moving average on a monthly closing basis.

Rebalance: Once per month, sell sectors that fall out of the
top tier (three) and buy the sectors that move into the top tier
(two or three).
"""

import datetime
import random

import matplotlib.pyplot as plt
import pandas as pd
from talib.abstract import *

import pinkfish as pf


default_options = {
    'use_adj' : False,
    'use_cache' : True,
    'lookback': None,
    'margin': 1,
    'use_absolute_mom': False,
    'use_regime_filter': False,
    'top_tier': 3
}

class Strategy:

    def __init__(self, symbols, capital, start, end, options=default_options):

        self.symbols = symbols
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

        # These dicts are used to track close, mom, and weights for
        # each symbol in portfolio
        prices = {}; mom = {}; weights = {}

        # A counter to countdown the number of months a lookback has
        # been in place
        month_count = 0

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            end_flag = pf.is_last_row(self.ts, i)

            if month_count == 0:
                # if period is None, then select a random trading period of
                # 6,7,8,...,or 12 months
                if self.options['lookback'] is None: 
                    lookback = random.choice(range(6, 12+1))
                else:
                    lookback = self.options['lookback']
                month_count = lookback

            # If first day of the month or last row
            if row.first_dotm or end_flag:

                month_count -= 1
                
                  # Get prices for current row
                mom_field = 'mom' + str(lookback)
                p = self.portfolio.get_prices(row, fields=['close', mom_field])

                # Copy data from `p` into prices and mom dicts for
                # convenience, also zero out weights dict. 
                for symbol in self.portfolio.symbols:
                    prices[symbol] = p[symbol]['close']
                    mom[symbol] = p[symbol][mom_field]
                    weights[symbol] = 0

                # Rebalance logic:
                #   Assign weights using relative momentum
                #   Then assign using absolute momentum if enabled
                #   Finally rebalance

                # Set weights to zero if last row or using regime 
                # filter and regime has turned bearish.
                if end_flag or (self.options['use_regime_filter'] and row.regime < 0):
                    # Since weights dict is already zeroed out, all positions
                    # will be closed out below with adjust_percent()
                    pass
                else:
                    # Relative momentum: Sort by highest momentum.
                    mom = pf.sort_dict(mom, reverse=True)

                    # Get the top tier momentum symbols; assign
                    # equal weight to top tier symbols
                    for i in range(self.options['top_tier']):
                        symbol = list(mom.keys())[i]
                        weights[symbol] = 1 / self.options['top_tier']

                # Absolute momentum: Set weight to zero if percent
                # change is negative.
                if self.options['use_absolute_mom']:
                    for symbol, pct_change in mom.items():
                        if pct_change < 0: weights[symbol] = 0

                # Rebalance portfolio
                self.portfolio.adjust_percents(date, prices, weights, row)

            # record daily balance
            self.portfolio.record_daily_balance(date, row)

    def run(self):
        self.portfolio = pf.Portfolio()
        self.ts = self.portfolio.fetch_timeseries(self.symbols, self.start, self.end,
            use_cache=self.options['use_cache'], use_adj=self.options['use_adj'])

        # Add S&P500 200 sma regime filter
        ts = pf.fetch_timeseries('^GSPC')
        ts = pf.select_tradeperiod(ts, self.start, self.end, use_adj=False) 
        self.ts['regime'] = \
            pf.CROSSOVER(ts, timeperiod_fast=1, timeperiod_slow=200, band=3.5)

        # Add calendar columns
        self.ts = self.portfolio.calendar(self.ts)

        # Add technical indicator Momenteum for all symbols in portfolio.
        def _momentum(ts, ta_param, input_column):
            return pf.MOMENTUM(ts, lookback=ta_param, time_frame='monthly',
                               price=input_column, prevday=False)

        lookbacks = range(3, 18+1)
        for lookback in lookbacks:
            self.ts = self.portfolio.add_technical_indicator(
                self.ts, ta_func=_momentum, ta_param=lookback,
                output_column_suffix='mom'+str(lookback),
                input_column_suffix='close')

        self.ts, self.start = self.portfolio.finalize_timeseries(self.ts, self.start)
        self.portfolio.init_trade_logs(self.ts, self.capital, self.options['margin'])

        self._algo()
        self._get_logs()
        self._get_stats()

    def _get_logs(self):
        self.rlog, self.tlog, self.dbal = self.portfolio.get_logs()

    def _get_stats(self):
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)

