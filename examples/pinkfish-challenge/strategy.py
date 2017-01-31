"""
stategy
---------
stategy template
"""

# Use future imports for python 3.0 forward compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# Other imports
import pandas as pd
import numpy as np
import datetime
from talib.abstract import *
import pinkfish as pf

class Strategy():
    """ strategy """

    def __init__(self, symbol, capital, start, end, period):
        self._symbol = symbol
        self._capital = capital
        self._start = start
        self._end = end
        self._period = period

    def _algo(self):
        """ Algo:
            1. Buy on the close on the SAME day a new 20 day high is set
        """
        
        cash = self._capital
        shares = 0
        start_flag = True

        for i in range(len(self._ts.index)):

            date = self._ts.index[i]
            high = self._ts['high'][i]
            low = self._ts['low'][i]
            close = self._ts['close'][i]
            period_high = self._ts['period_high'][i-1]

            if pd.isnull(period_high) or self._ts.index[i] < self._start:
                continue
            elif start_flag:
                start_flag = False
                # set start and end
                self._start = self._ts.index[i]
                self._end = self._ts.index[-1]

            # buy
            if self._tlog.num_open_trades() == 0:
                if high > period_high:

                    # calculate shares to buy and remaining cash
                    shares, cash = self._tlog.calc_shares(cash, close)

                    # enter buy in trade log
                    self._tlog.enter_trade(date, close, shares)
                    #print("{0} BUY  {1} {2} @ {3:.2f}".format(date, shares, self._symbol, close))

                    # record daily balance
                    self._dbal.append(date, high, low, close, shares, cash, pf.TradeState.OPEN)

                else:
                    # hold
                    self._dbal.append(date, high, low, close, shares, cash, pf.TradeState.HOLD)

            # sell
            elif (i == len(self._ts.index) - 1):

                # enter sell in trade log
                idx = self._tlog.exit_trade(date, close)
                shares = self._tlog.get_log()['qty'][idx]
                #print("{0} SELL {1} {2} @ {3:.2f}".format(date, shares, self._symbol, close))

                # record daily balance
                self._dbal.append(date, high, low, close, shares, cash, pf.TradeState.CLOSE)   
            
                # update cash
                cash = self._tlog.calc_cash(cash, close, shares)
            
                # update shares
                shares = 0

            # hold
            else:
                self._dbal.append(date, high, low, close, shares, cash, pf.TradeState.HOLD)   

    def run(self):
        self._ts = pf.fetch_timeseries(self._symbol)
        self._ts = pf.select_tradeperiod(self._ts, self._start,
                                         self._end, use_adj=False)
        
        # Add technical indicator: X day high
        period_high = pd.rolling_max(self._ts.high, self._period)
        self._ts['period_high'] = period_high               
        
        self._tlog = pf.TradeLog()
        self._dbal = pf.DailyBal()

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        tlog = self._tlog.get_log()
        dbal = self._dbal.get_log()
        return tlog, dbal


        

