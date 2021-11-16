"""
The double-7s-portfolio stategy.

This is double-7s strategy applied to a portfolio.
The simple double 7's strategy was revealed in the book
'Short Term Strategies that Work: A Quantified Guide to Trading Stocks
and ETFs', by Larry Connors and Cesar Alvarez. It's a mean reversion
strategy looking to buy dips and sell on strength and was initially
designed for ETFs.

This module allows us to examine this strategy and try different
period, stop loss percent, margin, and whether to use a regime filter
or not.  We split up the total capital between the symbols in the
portfolio and allocate based on either equal weight or volatility
parity weight (inverse volatility).
"""

import datetime

import matplotlib.pyplot as plt
import pandas as pd

import pinkfish as pf


default_options = {
    'use_adj' : False,
    'use_cache' : True,
    'stop_loss_pct' : 1.0,
    'margin' : 1,
    'period' : 7,
    'use_regime_filter' : True,
    'use_vola_weight' : False
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

        # Create a stop_loss dict for each symbol.
        stop_loss = {symbol:0 for symbol in self.portfolio.symbols}
        
        # stop loss pct should range between 0 and 1, user may have
        # expressed this as a percentage 0-100
        if self.options['stop_loss_pct'] > 1:
            self.options['stop_loss_pct'] /= 100

        period_high_field = 'period_high' + str(self.options['period'])
        period_low_field  = 'period_low'  + str(self.options['period'])

        # Loop though timeseries.
        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            end_flag = pf.is_last_row(self.ts, i)
            
            # Get the prices for this row, put in dict p.
            p = self.portfolio.get_prices(row,
                fields=['close', 'regime', period_high_field, period_low_field, 'vola'])

            # Sum the inverse volatility for each row.
            inverse_vola_sum = 0
            for symbol in self.portfolio.symbols:
                inverse_vola_sum += 1 / p[symbol]['vola']

            # Loop though each symbol in portfolio.
            for symbol in self.portfolio.symbols:

                # Use variables to make code cleaner
                close = p[symbol]['close']
                regime = p[symbol]['regime']
                period_high = p[symbol][period_high_field]
                period_low = p[symbol][period_low_field]
                inverse_vola = 1 / p[symbol]['vola']
                
                # Sell Logic
                # First we check if an existing position in symbol should be sold
                #  - sell if price closes at X day high
                #  - sell if price closes below stop loss
                #  - sell if end of data by adjusted the percent to zero

                if symbol in self.portfolio.positions:
                    if close == period_high or close < stop_loss[symbol] or end_flag:
                        if close < stop_loss[symbol]: print('STOP LOSS!!!')
                        self.portfolio.adjust_percent(date, close, 0, symbol, row)
                        
                # Buy Logic
                # First we check to see if there is an existing position, if so do nothing
                #  - Buy if (regime > 0 or not use_regime_filter) and price closes at X day low

                else:
                    if (regime > 0 or not self.options['use_regime_filter']) and close == period_low:
                        # Use volatility weight.
                        if self.options['use_vola_weight']:
                            weight = inverse_vola / inverse_vola_sum
                        # Use equal weight.
                        else:
                            weight = 1 / len(self.portfolio.symbols)
                        self.portfolio.adjust_percent(date, close, weight, symbol, row)
                        # Set stop loss
                        stop_loss[symbol] = (1-self.options['stop_loss_pct'])*close

            # record daily balance
            self.portfolio.record_daily_balance(date, row)

    def run(self):
        self.portfolio = pf.Portfolio()
        self.ts = self.portfolio.fetch_timeseries(self.symbols, self.start, self.end,
                    fields=['close'],
                    use_cache=self.options['use_cache'],
                    use_adj=self.options['use_adj'])
        
        # Technical indicator functions.
        @pf.technical_indicator(self.symbols, 'regime', 'close')
        def _crossover(ts, input_column=None):
            """ Technical indicator: 200 sma regime filter for each symbol. """
            return pf.CROSSOVER(ts, timeperiod_fast=1, timeperiod_slow=200,
                                price=input_column, prevday=False)

        @pf.technical_indicator(self.symbols, 'vola', 'close') 
        def _volatility(ts, input_column=None):
            """ Technical indicator: volatility. """
            return pf.VOLATILITY(ts, price=input_column)

        period = self.options['period']

        @pf.technical_indicator(self.symbols, 'period_high'+str(period), 'close')
        def _period_high(ts, input_column=None):
            """ Technical indicator: X day high. """ 
            return pd.Series(ts[input_column]).rolling(period).max()

        @pf.technical_indicator(self.symbols, 'period_low'+str(period), 'close')
        def _period_low(ts, input_column=None):
            """ Technical indicator: X day low. """
            return pd.Series(ts[input_column]).rolling(period).min()

        # Add technical indicators.
        self.ts = _crossover(self.ts)
        self.ts = _volatility(self.ts)
        self.ts = _period_high(self.ts)
        self.ts = _period_low(self.ts)

        # Finalize timeseries.
        self.ts, self.start = self.portfolio.finalize_timeseries(self.ts, self.start)

        # Init trade log objects.
        self.portfolio.init_trade_logs(self.ts)

        self._algo()
        self._get_logs()
        self._get_stats()

    def _get_logs(self):
        self.rlog, self.tlog, self.dbal = self.portfolio.get_logs()

    def _get_stats(self):
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)

