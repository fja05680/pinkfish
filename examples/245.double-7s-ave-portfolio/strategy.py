"""
The double-7s-ave-portfolio stategy.

This is double-7s strategy applied to a portfolio.
The simple double 7's strategy was revealed in the book
'Short Term Strategies that Work: A Quantified Guide to Trading Stocks
and ETFs', by Larry Connors and Cesar Alvarez. It's a mean reversion
strategy looking to buy dips and sell on strength and was initially
designed for ETFs.

This module allows us to examine this strategy and try different
number of periods.  Each period is represented using a different
symbol, for example SPY_7 for 7 day high/low.  This allows us to
compare the periods as if we were comparing different stocks in a
portfolio.
"""

import pandas as pd

import pinkfish as pf


default_options = {
    'use_adj' : False,
    'use_cache' : True,
    'margin' : 1.0,
    'periods' : [7],
    'sma' : 200,
    'use_regime_filter' : True,
}

class Strategy:

    def __init__(self, symbol, capital, start, end, options=default_options):
    
        self.symbol = symbol
        self.capital = capital
        self.start = start
        self.end = end
        self.options = options.copy()
        
        self.symbols = None
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
            p = self.portfolio.get_prices(row, fields=['close'])

            # Loop though each symbol in portfolio.
            for symbol in self.portfolio.symbols:

                period_high_field = 'period_high' + str(symbol.split('_')[1])
                period_low_field  = 'period_low'  + str(symbol.split('_')[1])
                period_high = getattr(row, period_high_field)
                period_low = getattr(row, period_low_field)
                
                # Use variables to make code cleaner.
                close = p[symbol]['close']
                
                # Sell Logic
                # First we check if an existing position in symbol should be sold
                #  - sell if price closes at X day high
                #  - sell if end of data by adjusted the percent to zero

                if symbol in self.portfolio.positions:
                    if close == period_high or end_flag:
                        self.portfolio.adjust_percent(date, close, 0, symbol, row)

                # Buy Logic
                # First we check to see if there is an existing position, if so do nothing
                #  - Buy if (regime > 0 or not use_regime_filter) and price closes at X day low

                else:
                    if (((row.regime > 0 or close > row.sma) or not self.options['use_regime_filter'])
                          and close == period_low):
                        # Use equal weight.
                        weight = 1 / len(self.portfolio.symbols)
                        self.portfolio.adjust_percent(date, close, weight, symbol, row)

            # record daily balance
            self.portfolio.record_daily_balance(date, row)

    def run(self):
        # Build the list of symbols.
        periods = self.options['periods']
        self.symbols = []
        for period in periods:
            symbol = self.symbol + '_' + str(period)
            self.symbols.append(symbol)

        self.portfolio = pf.Portfolio()
        self.ts = self.portfolio.fetch_timeseries(self.symbols, self.start, self.end,
                    fields=['close'],
                    use_cache=self.options['use_cache'],
                    use_adj=self.options['use_adj'])

        # Fetch symbol time series.
        ts = pf.fetch_timeseries(self.symbol, use_cache=self.options['use_cache'])
        ts = pf.select_tradeperiod(ts, self.start, self.end, use_adj=self.options['use_adj']) 

        # Add technical indicator: 200 sma regime filter.
        self.ts['regime'] = pf.CROSSOVER(ts, timeperiod_fast=1, timeperiod_slow=200)

        # Add technical indicator: X day sma.
        self.ts['sma'] = pf.SMA(ts, timeperiod=self.options['sma'])

        # Add technical indicator: X day high, and X day low.
        for period in periods:
            self.ts['period_high'+str(period)] = pd.Series(ts.close).rolling(period).max()
            self.ts['period_low'+str(period)]  = pd.Series(ts.close).rolling(period).min()

        # Finalize timeseries.
        self.ts, self.start = pf.finalize_timeseries(self.ts, self.start, dropna=True)

        # Init trade log objects.
        self.portfolio.init_trade_logs(self.ts)

        self._algo()
        self._get_logs()
        self._get_stats()

    def _get_logs(self):
        self.rlog, self.tlog, self.dbal = self.portfolio.get_logs()

    def _get_stats(self):
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)
