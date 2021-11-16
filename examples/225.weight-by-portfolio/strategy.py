"""
Weight By Portfolio Strategy.

Basic buy and hold that allows weighting by user specified weights,
Equal, Sharpe Ratio, Annual Returns, Std Dev, Vola, or DS Vola.
Rebalance is yearly, monthly, weekly, or daily.  Option to sell
all shares of an investment is regime turns negative.
"""

import datetime
import random

import matplotlib.pyplot as plt
import pandas as pd

import pinkfish as pf


default_options = {
    'use_adj'           : True,
    'use_cache'         : True,
    'margin'            : 1,
    'weights'           : None,
    'weight_by'         : 'equal',
    'rebalance'         : 'monthly',
    'use_regime_filter' : False
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
        
        weight_by = self.options['weight_by']
        rebalance = self.options['rebalance']
        weights = self.options['weights']
        
        for symbol, weight in weights.items():
            if weight and weight > 1:
                weights[symbol] = weight / 100
        
        symbols_no_weights = [k for k,v in weights.items() if v is None]
        symbols_weights    = {k:v for k,v in weights.items() if v is not None}
        remaining_weight   = 1 - sum(symbols_weights.values())
        
        # Price fields
        fields = ['close', 'regime', 'sharpe', 'ret', 'sd', 'vola', 'ds_vola']

        # Loop though timeseries.
        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            end_flag = pf.is_last_row(self.ts, i)
            
            # Get the prices for this row, put in dict p.
            p = self.portfolio.get_prices(row, fields=fields)

            # Determine if it's time to rebalance.
            is_rebalance = ((rebalance == 'yearly'  and row.first_doty) or
                            (rebalance == 'monthly' and row.first_dotm) or
                            (rebalance == 'weekly'  and row.first_dotw) or
                            (rebalance == 'daily') or
                            (i == 0) or 
                            (end_flag))

            # Sums and inverse sums for each row.
            sums = {field : 0 for field in fields}
            for symbol in symbols_no_weights:
                sums['sharpe']  +=     p[symbol]['sharpe']
                sums['ret']     +=     p[symbol]['ret']
                sums['sd']      += 1 / p[symbol]['sd']
                sums['vola']    += 1 / p[symbol]['vola']
                sums['ds_vola'] += 1 / p[symbol]['ds_vola']

            # Loop though each symbol in portfolio.
            for symbol in self.portfolio.symbols:
                
                # Use variables to make code cleaner.
                close    =      p[symbol]['close']
                regime   =      p[symbol]['regime']
                sharpe   =      p[symbol]['sharpe']
                ret      =      p[symbol]['ret']
                sd       =  1 / p[symbol]['sd']
                vola     =  1 / p[symbol]['vola']
                ds_vola  =  1 / p[symbol]['ds_vola']
                
                # Assign weight.
                weight = 0
                if is_rebalance:
                    if end_flag:
                        weight = 0
                    elif regime < 0 and self.options['use_regime_filter']:
                        weight = 0
                    elif symbol in symbols_no_weights:
                        # Calculate weight
                        if weight_by == 'equal':
                            weight = (1 / len(symbols_no_weights)) * remaining_weight
                        elif weight_by in ['sharpe', 'ret', 'sd', 'vola', 'ds_vola']:
                            if   weight_by == 'sharpe':   metric = sharpe
                            elif weight_by == 'ret':      metric = ret
                            elif weight_by == 'sd':       metric = sd
                            elif weight_by == 'vola':     metric = vola
                            elif weight_by == 'ds_vola':  metric = ds_vola
                            weight = (metric / sums[weight_by]) * remaining_weight
                    else:
                        # User specified weight.
                        weight = weights[symbol]
                    self.portfolio.adjust_percent(date, close, weight, symbol, row)

            if is_rebalance:
#                 self.portfolio.print_holdings(date, row, percent=True)
                pass

            # Record daily balance.
            self.portfolio.record_daily_balance(date, row)

    def run(self):
        self.portfolio = pf.Portfolio()
        self.ts = self.portfolio.fetch_timeseries(self.symbols, self.start, self.end,
            fields=['close'], use_cache=self.options['use_cache'],
             use_adj=self.options['use_adj'])

        # Check weight_by for valid value.
        weight_by = self.options['weight_by']
        weight_by_choices = ('equal', 'sharpe', 'ret', 'sd', 'vola', 'ds_vola')
        assert weight_by in weight_by_choices, \
            "Invalid weight_by '{}'".format(weight_by)

        # Check rebalance for valid value.
        rebalance = self.options['rebalance']
        rebalance_choices = ('yearly', 'monthly', 'weekly', 'daily')
        assert rebalance in rebalance_choices, \
            "Invalid rebalance '{}'".format(rebalance)

        # Add calendar columns.
        self.ts = pf.calendar(self.ts)

        # Technical indicator functions.
        @pf.technical_indicator(self.symbols, 'regime', 'close')
        def _crossover(ts, input_column=None):
            """ Technical indicator: 200 sma regime filter for each symbol. """
            return pf.CROSSOVER(ts, timeperiod_fast=1, timeperiod_slow=200,
                                price=input_column, prevday=False)

        @pf.technical_indicator(self.symbols, 'sharpe', 'close')
        def _sharpe_ratio(ts, input_column=None):
            """ Technical indicator: Sharpe Ratio (3 yr annualized). """
            return pf.ANNUALIZED_SHARPE_RATIO(ts, lookback=3, price=input_column)

        @pf.technical_indicator(self.symbols, 'ret', 'close')
        def _annual_return(ts, input_column=None):
            """ Technical indicator: Return (1 yr annualized). """
            return pf.ANNUALIZED_RETURNS(ts, lookback=1, price=input_column)        

        @pf.technical_indicator(self.symbols, 'sd', 'close')
        def _std_dev(ts, input_column=None):
            """ Technical indicator: Standard Deviation (3 yr annualized). """
            return pf.ANNUALIZED_STANDARD_DEVIATION(ts, lookback=3, price=input_column)

        @pf.technical_indicator(self.symbols, 'vola', 'close')
        def _volatility(ts, input_column=None):
            """ Technical indicator: volatility (20 day annualized). """
            return pf.VOLATILITY(ts, lookback=20, downside=False, price=input_column)

        @pf.technical_indicator(self.symbols, 'ds_vola', 'close')
        def _downside_volatility(ts, input_column=None):
            """ Technical indicator: downside volatility (20 day annualized). """
            return pf.VOLATILITY(ts, lookback=20, downside=True, price=input_column)      

        # Add technical indicators.
        self.ts = _crossover(self.ts)
        self.ts = _sharpe_ratio(self.ts)
        self.ts = _annual_return(self.ts)
        self.ts = _std_dev(self.ts)
        self.ts = _volatility(self.ts)
        self.ts = _downside_volatility(self.ts)

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
