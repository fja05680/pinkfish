"""
stategy
---------
"""

import pandas as pd
import matplotlib.pyplot as plt
import datetime
from talib.abstract import *
import random

import pinkfish as pf


class Strategy:

    def __init__(self, symbols, capital, start, end, stop_loss_pct=0, margin=1, period=7,
                 use_cache=False, use_regime_filter=False):
        self.symbols = symbols
        self.capital = capital
        self.start = start
        self.end = end
        self.period = period
        self.stop_loss_pct = stop_loss_pct/100
        self.margin = margin
        self.use_cache = use_cache
        self.use_regime_filter = use_regime_filter

    def _algo(self):
        """ Algo:
            1. The SPY is higher than X days ago, buy
            2. If the SPY is lower than X days ago, sell your long position.
        """
        pf.TradeLog.cash = self.capital
        pf.TradeLog.margin = self.margin

        stop_loss = {symbol:0 for symbol in self.portfolio.symbols}

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            end_flag = pf.is_last_row(self.ts, i)
            
            # get symbol row data
            for symbol in self.portfolio.symbols:
                price = self.portfolio.get_row_column_value(row, symbol)
                regime = \
                    self.portfolio.get_row_column_value(row, symbol, field='regime')
                period_high = \
                    self.portfolio.get_row_column_value(row, symbol,
                        field='period_high'+str(self.period))
                period_low = \
                    self.portfolio.get_row_column_value(row, symbol,
                        field='period_low'+str(self.period))
                
                """ 
                Sell Logic
                First we check if an existing position in symbol should be sold
                * sell if price closes at X day high
                * sell if price closes below stop loss
                * sell if end of data
                """
                if symbol in self.portfolio.positions():
                    if (price == period_high or price < stop_loss[symbol] or end_flag):
                        if (price < stop_loss[symbol]): print('STOP LOSS!!!')
                        self.portfolio.adjust_percent(date, price, 0, symbol, row)
                #"""
                #Buy Logic
                #First we check to see if there is an existing position, if so do nothing
                #Buy if (regime > 0 or not use_regime_filter) and price closes at X day low
                #"""
                else:
                    if (regime > 0 or not self.use_regime_filter) and price == period_low:
                        weight = 1 / len(self.portfolio.symbols)
                        self.portfolio.adjust_percent(date, price, weight, symbol, row)
                        # set stop loss
                        stop_loss[symbol] = self.stop_loss_pct*price

            # record daily balance
            self.portfolio.record_daily_balance(date, row)

    def run(self):
        self.portfolio = pf.Portfolio()
        self.ts = self.portfolio.fetch_timeseries(
            self.symbols, self.start, self.end, use_cache=self.use_cache)

        # Add technical indicator: 200 sma regime filter for each symbol
        def _crossover(ts, ta_param, input_column):
            return pf.CROSSOVER(ts, timeperiod_fast=1, timeperiod_slow=200,
                                price=input_column, prevday=False)

        self.ts = self.portfolio.add_technical_indicator(
            self.ts, ta_func=_crossover, ta_param=None,
            output_column_suffix='regime', input_column_suffix='close')

        # Add technical indicator: X day high
        def _period_high(ts, ta_param, input_column):
            return pd.Series(ts[input_column]).rolling(ta_param).max()

        self.ts = self.portfolio.add_technical_indicator(
            self.ts, ta_func=_period_high, ta_param=self.period,
            output_column_suffix='period_high'+str(self.period),
            input_column_suffix='close')

        # Add technical indicator: X day low
        def _period_low(ts, ta_param, input_column):
            return pd.Series(ts[input_column]).rolling(ta_param).min()

        self.ts = self.portfolio.add_technical_indicator(
            self.ts, ta_func=_period_low, ta_param=self.period,
            output_column_suffix='period_low'+str(self.period),
            input_column_suffix='close')

        self.ts, self.start = self.portfolio.finalize_timeseries(self.ts, self.start)

        self.portfolio.init_trade_logs(self.ts, self.capital, self.margin)

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        self.rlog, self.tlog, self.dbal = self.portfolio.get_logs()
        return self.rlog, self.tlog, self.dbal

    def get_stats(self):
        stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)
        return stats

def summary(strategies, metrics):
    """ Stores stats summary in a DataFrame.
        stats() must be called before calling this function """
    index = []
    columns = strategies.index
    data = []
    # add metrics
    for metric in metrics:
        index.append(metric)
        data.append([strategy.stats[metric] for strategy in strategies])

    df = pd.DataFrame(data, columns=columns, index=index)
    return df

def plot_bar_graph(df, metric):
    """ Plot Bar Graph: Strategy
        stats() must be called before calling this function """
    df = df.loc[[metric]]
    df = df.transpose()
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel=metric)
    df.plot(kind='bar', ax=axes, legend=False)
    axes.set_xticklabels(df.index, rotation=0)
