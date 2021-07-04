"""
The SMA-ROC-portfolio stategy.

This is SMA-ROC strategy applied to a portfolio.
SMA-ROC is a rate of change calculation smoothed by
a moving average.

This module allows us to examine this strategy and try different
period, stop loss percent, margin, and whether to use a regime filter
or not.  We split up the total capital between the symbols in the
portfolio and allocate based on either equal weight or volatility
parity weight (inverse volatility).
"""

import datetime

import matplotlib.pyplot as plt
import pandas as pd
from talib.abstract import *

import pinkfish as pf


# A custom indicator to use in this strategy.
def SMA_ROC(ts, mom_lookback=1, sma_timeperiod=20, price='close'):
    """ Returns a series which is an SMA with of a daily MOM. """
    mom = pf.MOMENTUM(ts, lookback=mom_lookback, time_frame='daily', price=price)
    sma_mom = SMA(mom, timeperiod=sma_timeperiod)
    return sma_mom



default_options = {
    'use_adj' : False,
    'use_cache' : True,
    'stock_market_calendar' : False,
    'stop_loss_pct' : 1.0,
    'margin' : 1,
    'lookback' : 1,
    'sma_timeperiod': 20,
    'sma_pct_band': 0,
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

        upper_band = self.options['sma_pct_band']/1000
        lower_band = -self.options['sma_pct_band']/1000
        
        # Loop though timeseries.
        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            end_flag = pf.is_last_row(self.ts, i)
            
            # Get the prices for this row, put in dict p.
            p = self.portfolio.get_prices(row,
                fields=['close', 'regime', 'sma_roc', 'vola'])

            # Sum the inverse volatility for each row.
            inverse_vola_sum = 0
            for symbol in self.portfolio.symbols:
                inverse_vola_sum += 1 / p[symbol]['vola']

            # Loop though each symbol in portfolio.
            for symbol in self.portfolio.symbols:

                # Use variables to make code cleaner.
                close = p[symbol]['close']
                regime = p[symbol]['regime']
                sma_roc = p[symbol]['sma_roc']
                inverse_vola = 1 / p[symbol]['vola']
                
                # Sell Logic
                # First we check if an existing position in symbol should be sold
                #  - sell sma_roc < 0
                #  - sell if price closes below stop loss
                #  - sell if end of data by adjusted the percent to zero

                if symbol in self.portfolio.positions:
                    if sma_roc < lower_band or close < stop_loss[symbol] or end_flag:
                        if close < stop_loss[symbol]: print('STOP LOSS!!!')
                        self.portfolio.adjust_percent(date, close, 0, symbol, row)
                        
                # Buy Logic
                # First we check to see if there is an existing position, if so do nothing
                #  - Buy if (regime > 0 or not use_regime_filter) and sma_roc > 0

                else:
                    if (regime > 0 or not self.options['use_regime_filter']) and sma_roc > upper_band:
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
            fields=['close'], use_cache=self.options['use_cache'],
            use_adj=self.options['use_adj'],
            dir_name='currencies',                                      
            stock_market_calendar=self.options['stock_market_calendar'])

        # Add technical indicator: 200 sma regime filter for each symbol.
        def _crossover(ts, ta_param, input_column):
            return pf.CROSSOVER(ts, timeperiod_fast=1, timeperiod_slow=200,
                                price=input_column, prevday=False)

        self.ts = self.portfolio.add_technical_indicator(
            self.ts, ta_func=_crossover, ta_param=None,
            output_column_suffix='regime', input_column_suffix='close')
        
        # Add technical indicator: volatility.
        def _volatility(ts, ta_param, input_column):
            return pf.VOLATILITY(ts, price=input_column)
        
        self.ts = self.portfolio.add_technical_indicator(
            self.ts, ta_func=_volatility, ta_param=None,
            output_column_suffix='vola', input_column_suffix='close')
        
        # Add techincal indicator: X day SMA_ROC.
        def _sma_roc(ts, ta_param, input_column):
            return SMA_ROC(ts, mom_lookback=self.options['lookback'],
                           sma_timeperiod=self.options['sma_timeperiod'],
                           price=input_column)

        self.ts = self.portfolio.add_technical_indicator(
            self.ts, ta_func=_sma_roc, ta_param=None,
            output_column_suffix='sma_roc', input_column_suffix='close')

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

