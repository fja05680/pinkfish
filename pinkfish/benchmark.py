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

class Benchmark(object):

    def __init__(self, symbol, capital, start, end, use_adj=False,
                 slippage_per_trade=0, commissions_per_trade=0):
        self._symbol = symbol
        self._capital = capital
        self._start = start
        self._end = end
        self._use_adj = use_adj
        self._slippage_per_trade = slippage_per_trade
        self._commissions_per_trade = commissions_per_trade

    def _algo(self):
        self._tlog.cash = self._capital
        start_flag = True
        end_flag = False

        for i, row in enumerate(self._ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high
            low = row.low
            close = row.close
            end_flag = True if (i == len(self._ts) - 1) else False
            trade_state = None

            if date < self._start:
                continue
            elif start_flag:
                start_flag = False
                # set start and end
                self._start = date
                self._end = self._ts.index[-1]

            # buy
            if self._tlog.num_open_trades() == 0:

                # enter buy in trade log
                self._tlog.enter_trade(date, close)
                trade_state = pf.TradeState.OPEN
                print("{0} BUY  {1} {2} @ {3:.2f}".format(
                      date, self._tlog.shares, self._symbol, close))

            # sell
            elif end_flag:

                # enter sell in trade log
                shares = self._tlog.exit_trade(date, close)
                trade_state = pf.TradeState.CLOSE
                print("{0} SELL {1} {2} @ {3:.2f}".format(
                      date, shares, self._symbol, close))

            # hold
            else:
                trade_state = pf.TradeState.HOLD

            # record daily balance
            self._dbal.append(date, high, low, close,
                              self._tlog.shares, self._tlog.cash,
                              trade_state)

    def run(self):
        self._ts = pf.fetch_timeseries(self._symbol)
        self._ts = pf.select_tradeperiod(self._ts, self._start, self._end,
                                         use_adj=self._use_adj, pad=False)
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

