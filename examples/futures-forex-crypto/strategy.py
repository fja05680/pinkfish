"""
stategy
---------
"""

import pandas as pd
import matplotlib.pyplot as plt
import datetime
from talib.abstract import *

import pinkfish as pf

pf.DEBUG = False


class Strategy:

    def __init__(self, symbol, capital, start, end):

        self.symbol = symbol
        self.capital = capital
        self.start = start
        self.end = end

        # options
        self.stop_loss_pct = 0
        self.margin = 1
        self.multiplier = 1
        self.timeperiod_fast = 1
        self.timeperiod_slow = 200
        self.percent_band = 0/100
        self.enable_shorts = False

    def _algo(self):
        """ Algo:
            - The future closes above its upper band, buy
            - The future closes below its lower band, sell your long position.
        """
        pf.TradeLog.cash = self.capital
        pf.TradeLog.margin = self.margin
        pf.TradeLog.multiplier = self.multiplier
        stop_loss = 0

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close; 
            end_flag = pf.is_last_row(self.ts, i)
            regime = row.regime
            
            # this yahoo futures data hasn't been cleaned well.  there are zero values in here.
            
            if end_flag:
                if self.tlog.shares > 0:
                    self.tlog._exit_trade(date, close, shares=None, direction=self.tlog.direction)
            
            # Sell Logic
            # First we check if an existing position in symbol should be sold
            #  - sell if price closes at X day low
            #  - sell if price closes below stop loss

            elif regime < 0:
                if self.tlog.shares > 0:
                    if self.tlog.direction == pf.Direction.LONG:
                        # exit long trade; enter short trade
                        self.tlog._exit_trade(date, close, direction=pf.Direction.LONG)
                        if self.enable_shorts:
                            cash = self.tlog.calc_buying_power(close) 
                            shares = self.tlog.calc_shares(close, cash=cash/self.multiplier)
                            self.tlog._enter_trade(date, close, shares=shares, direction=pf.Direction.SHORT)
                            stop_loss = (2-self.stop_loss_pct)*close
                    else:
                        pass
                        if self.enable_shorts:
                            if close > stop_loss:
                                print('STOP LOSS!!!')
                                self.tlog._exit_trade(date, close, direction=pf.Direction.SHORT)
                else:
                    if self.enable_shorts:
                        # enter new short position
                        cash = self.tlog.calc_buying_power(close)
                        shares = self.tlog.calc_shares(close, cash=cash/self.multiplier)
                        self.tlog._enter_trade(date, close, shares=shares, direction=pf.Direction.SHORT)
                        # set stop loss
                        stop_loss = (2-self.stop_loss_pct)*close

            # Buy Logic
            # First we check if an existing position in symbol should be bought
            #  - buy if price closes at X day high
            #  - buy if price closes below stop loss

            elif regime > 0:
                if self.tlog.shares > 0:
                    if self.tlog.direction == pf.Direction.SHORT:
                        # exit short trade; enter long trade
                        if self.enable_shorts:
                            self.tlog._exit_trade(date, close, direction=pf.Direction.SHORT)
                        cash = self.tlog.calc_buying_power(close)
                        shares = self.tlog.calc_shares(close, cash=cash/self.multiplier)
                        self.tlog._enter_trade(date, close, shares=shares, direction=pf.Direction.LONG)
                        stop_loss = self.stop_loss_pct*close
                    else:
                        if close < stop_loss:
                            print('STOP LOSS!!!')
                            self.tlog._exit_trade(date, close, direction=pf.Direction.LONG)
                else:
                    # enter new long position
                    cash = self.tlog.calc_buying_power(close)
                    shares = self.tlog.calc_shares(close, cash=cash/self.multiplier)
                    self.tlog._enter_trade(date, close, shares=shares, direction=pf.Direction.LONG)
                    # set stop loss
                    stop_loss = self.stop_loss_pct*close

            # record daily balance
            self.dbal.append(date, high, low, close)

    def run(self):
        self.ts = pf.fetch_timeseries(self.symbol)
        self.ts = pf.select_tradeperiod(self.ts, self.start, self.end)       
        
        # add regime filter 
        self.ts['regime'] = \
            pf.CROSSOVER(self.ts,
                         timeperiod_fast=self.timeperiod_fast,
                         timeperiod_slow=self.timeperiod_slow,
                         band=self.percent_band)
        
        self.ts, self.start = pf.finalize_timeseries(self.ts, self.start)
        
        self.tlog = pf.TradeLog(self.symbol)
        self.dbal = pf.DailyBal()

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        self.rlog = self.tlog.get_log_raw()
        self.tlog = self.tlog.get_log()
        self.dbal = self.dbal.get_log(self.tlog)
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
