"""
Futures Trend Following portfolio stategy.

 1. The Security closes with 50/100 ma > 0, buy.
 2. If the Security closes 50/100 ma < 0, sell your long position.

"""

import datetime

import matplotlib.pyplot as plt
import pandas as pd

import pinkfish as pf


default_options = {
    'use_adj' : False,
    'use_cache' : True,
    'sell_short' : True,
    'force_stock_market_calendar' : True,
    'margin' : 1,
    'lookback' : 1,
    'sma_timeperiod_slow': 100,
    'sma_timeperiod_fast': 50,
    'use_vola_weight' : True
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
        
        # Loop though timeseries.
        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            end_flag = pf.is_last_row(self.ts, i)
            
            # Get the prices for this row, put in dict p.
            p = self.portfolio.get_prices(row,
                fields=['close', 'regime', 'vola'])

            # Sum the inverse volatility for each row.
            inverse_vola_sum = 0
            for symbol in self.portfolio.symbols:
                inverse_vola_sum += 1 / p[symbol]['vola']

            # Loop though each symbol in portfolio.
            for symbol in self.portfolio.symbols:

                # Use variables to make code cleaner.
                close = p[symbol]['close']
                regime = p[symbol]['regime']
                inverse_vola = 1 / p[symbol]['vola']
                
                # Use volatility weight.
                if self.options['use_vola_weight']:
                    weight = inverse_vola / inverse_vola_sum
                # Use equal weight.
                else:
                    weight = 1 / len(self.portfolio.symbols)
                

                if end_flag:
                    self.portfolio.adjust_percent(date, close, 0, symbol, row)
                
                # Sell Logic
                #  - sell regime == -1

                elif regime == -1:
                    self.portfolio.adjust_percent(date, close, 0, symbol, row,
                                                  direction=pf.Direction.LONG)
                    if self.options['sell_short']:
                        self.portfolio.adjust_percent(date, close, weight, symbol, row,
                                                      direction=pf.Direction.SHORT)
                        
                # Buy Logic
                #  - Buy if regime == 1

                elif regime == 1:
                    if self.options['sell_short']:
                        self.portfolio.adjust_percent(date, close, 0, symbol, row,
                                                      direction=pf.Direction.SHORT)
                    self.portfolio.adjust_percent(date, close, weight, symbol, row,
                                                  direction=pf.Direction.LONG)

            # record daily balance
            self.portfolio.record_daily_balance(date, row)

    def run(self):
        self.portfolio = pf.Portfolio()
        self.ts = self.portfolio.fetch_timeseries(self.symbols, self.start, self.end,
            fields=['close'], use_cache=self.options['use_cache'],
            use_adj=self.options['use_adj'],
            dir_name='futures',                                      
            force_stock_market_calendar=self.options['force_stock_market_calendar'])

        # Technical indicator functions.
        @pf.technical_indicator(self.symbols, 'regime', 'close')
        def _crossover(ts, input_column=None):
            """ Technical indicator: 50/100 sma regime filter for each symbol. """
            return pf.CROSSOVER(ts, timeperiod_fast=self.options['sma_timeperiod_fast'],
                                timeperiod_slow=self.options['sma_timeperiod_slow'],
                                price=input_column, prevday=False)

        @pf.technical_indicator(self.symbols, 'vola', 'close')
        def _volatility(ts, input_column=None):
            """ Technical indicator: volatility. """
            return pf.VOLATILITY(ts, price=input_column)

        # Add technical indicators.
        self.ts = _crossover(self.ts)
        self.ts = _volatility(self.ts)

        # Finalize timeseries.
        self.ts, self.start = self.portfolio.finalize_timeseries(self.ts, self.start, dropna=True)

        # Init trade log objects.
        self.portfolio.init_trade_logs(self.ts)

        self._algo()
        self._get_logs()
        self._get_stats()

    def _get_logs(self):
        self.rlog, self.tlog, self.dbal = self.portfolio.get_logs()

    def _get_stats(self):
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)

