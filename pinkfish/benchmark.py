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

    def __init__(self, symbol, capital, start, end, use_adj=False):
        self._symbol = symbol
        self._capital = capital
        self._start = start
        self._end = end
        self._use_adj = use_adj

    def _algo(self):
        self._tlog.cash = self._capital

        for i, row in enumerate(self._ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high
            low = row.low
            close = row.close
            end_flag = True if (i == len(self._ts) - 1) else False

            # buy
            if self._tlog.num_open_trades() == 0:

                # enter buy in trade log
                self._tlog.enter_trade(date, close)
                print("{0} BUY  {1} {2} @ {3:.2f}".format(
                      date, self._tlog.shares, self._symbol, close))

            # sell
            elif end_flag:

                # enter sell in trade log
                shares = self._tlog.exit_trade(date, close)
                print("{0} SELL {1} {2} @ {3:.2f}".format(
                      date, -shares, self._symbol, close))

            # record daily balance
            self._dbal.append(date, high, low, close,
                              self._tlog.shares, self._tlog.cash)

    def run(self):
        self._ts = pf.fetch_timeseries(self._symbol)
        self._ts = pf.select_tradeperiod(self._ts, self._start, self._end,
                                         use_adj=self._use_adj, pad=False)
        self._ts, _ = pf.finalize_timeseries(self._ts, self._start)

        self._tlog = pf.TradeLog()
        self._dbal = pf.DailyBal()

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        self.tlog = self._tlog.get_log()
        self.dbal = self._dbal.get_log(self.tlog)
        return self.tlog, self.dbal

    def get_stats(self):
        stats = pf.stats(self._ts, self.tlog, self.dbal, self._capital)
        return stats

