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

    def __init__(self, symbols, capital, start, end, lookback=None, margin=1, use_cache=False):
        self.symbols = symbols
        self.capital = capital
        self.start = start
        self.end = end
        self.lookback = lookback
        self.margin = margin
        self.use_cache = use_cache
        
    def _algo(self):
        """ Algo:
            1. The SPY is higher than X days ago, buy
            2. If the SPY is lower than X days ago, sell your long position.
        """
        pf.TradeLog.cash = self.capital
        pf.TradeLog.margin = self.margin

        prices = {}; mom = {}; weights = {}
        SP500 = self.symbols['SP500'];
        BONDS = self.symbols['BONDS'];
        EXUS  = self.symbols['EXUS'];
        cnt = 0

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            end_flag = pf.is_last_row(self.ts, i)
            
            if cnt == 0:
                # if period is None, then select a random trading period of
                # 6,7,8,...,or 12 months
                if self.lookback is None:
                    lookback = random.choice(range(3, 12+1))
                    cnt = lookback
                else:
                    lookback = self.lookback

            if row.first_dotm or end_flag:
                # reverse sort by last weights
                weights = dict(sorted(weights.items(), key=lambda x: x[1], reverse=True))
                for symbol in self.portfolio.symbols:
                    prices[symbol] = self.portfolio.get_row_column_value(row, symbol)
                    mom[symbol] = self.portfolio.get_row_column_value(row, symbol, field='mom'+str(lookback))
                    weights[symbol] = 0

                if end_flag:
                    pass
                elif mom[SP500] > mom[BONDS]:
                    if mom[SP500] > mom[EXUS]:
                        weights[SP500] = 1
                    else:
                        weights[EXUS] = 1
                else: 
                    weights[BONDS] = 1

                for symbol, weight in weights.items():
                    self.portfolio.adjust_percent(date, prices[symbol], weights[symbol], symbol, row)
                
                if self.lookback is None:
                    cnt -= 1

            # record daily balance
            self.portfolio.record_daily_balance(date, row)

    def run(self):
        self.portfolio = pf.Portfolio()
        self.ts = self.portfolio.fetch_timeseries(
            self.symbols.values(), self.start, self.end, use_cache=self.use_cache)

        # add calendar columns
        self.ts = self.portfolio.calendar(self.ts)
        
        # add techincal indicator Momenteum
        def _momentum(ts, ta_param, input_column):
            return pf.MOMENTUM(ts, lookback=ta_param, time_frame='monthly', price=input_column, prevday=False)
        
        lookbacks = range(3, 18+1)
        for lookback in lookbacks:
            self.ts = self.portfolio.add_technical_indicator(
                self.ts, ta_func=_momentum, ta_param=lookback,
                output_column_suffix='mom'+str(lookback),
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
