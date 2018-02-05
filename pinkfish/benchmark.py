"""
benchmark
---------
Benchmark for comparision to strategies
"""

# Use future imports for python 3.0 forward compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# Other imports
import pinkfish as pf

class Benchmark():
    """ benchmark """

    def __init__(self, symbol, capital, start, end,
                 slippage_per_trade=0, commissions_per_trade=0):
        self._symbol = symbol
        self._capital = capital
        self._start = start
        self._end = end
        self._slippage_per_trade = slippage_per_trade
        self._commissions_per_trade = commissions_per_trade

    def _algo(self):
        cash = self._capital
        shares = 0
        start_flag = True
        end_flag = False

        for i in range(len(self._ts.index)):

            date = self._ts.index[i]
            high = self._ts['high'][i]
            low = self._ts['low'][i]
            close = self._ts['close'][i]
            end_flag = True if (i == len(self._ts.index) - 1) else False

            if self._ts.index[i] < self._start:
                continue
            elif start_flag:
                start_flag = False
                # set start and end
                self._start = self._ts.index[i]
                self._end = self._ts.index[-1]

            # buy
            if self._tlog.num_open_trades() == 0:

                # calculate shares
                shares, cash = self._tlog.calc_shares(cash, close)

                # enter buy in trade log
                self._tlog.enter_trade(date, close, shares)
                print("{0} BUY  {1} {2} @ {3:.2f}".format(date, shares, 
                      self._symbol, close))

                # record daily balance
                self._dbal.append(date, high, low, close, shares, cash,
                                  pf.TradeState.OPEN)

            # sell 
            elif end_flag:

                # enter sell in trade log
                idx = self._tlog.exit_trade(date, close)
                shares = self._tlog.get_log()['qty'][idx]
                print("{0} SELL {1} {2} @ {3:.2f}".format(date, shares,
                      self._symbol, close))

                # record daily balance
                self._dbal.append(date, high, low, close, shares,
                                  cash, pf.TradeState.CLOSE)   

                # update cash
                cash = self._tlog.calc_cash(cash, close, shares)
                
                # update shares
                shares = 0

            # hold
            else:
                self._dbal.append(date, high, low, close, shares,
                                  cash, pf.TradeState.HOLD)

    def run(self):
        self._ts = pf.fetch_timeseries(self._symbol)
        self._ts = pf.select_tradeperiod(self._ts, self._start,
                                         self._end, True, False)
        self._tlog = pf.TradeLog()
        self._dbal = pf.DailyBal()

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        tlog = self._tlog.get_log()
        dbal = self._dbal.get_log()
        return tlog, dbal

    def stats(self):
        tlog, dbal = self.get_logs()
        
        stats = pf.stats(self._ts, tlog, dbal,
                         self._start, self._end, self._capital)
        return stats

