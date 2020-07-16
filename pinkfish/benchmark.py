"""
benchmark
---------
Benchmark for comparision to strategies
"""

import pinkfish as pf


class Benchmark:

    def __init__(self, symbol, capital, start, end, use_adj=False):
        self._symbol = symbol
        self._capital = capital
        self._start = start
        self._end = end
        self._use_adj = use_adj

    def _algo(self):
        pf.TradeLog.cash = self._capital
        pf.TradeLog.margin = pf.Margin.CASH
        pf.TradeLog.buying_power = None

        for i, row in enumerate(self._ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close
            end_flag = pf.is_last_row(self._ts, i)

            # buy
            if self._tlog.shares == 0:
                self._tlog.buy(date, close)
                print("{0} BUY  {1} {2} @ {3:.2f}".format(
                      date, self._tlog.shares, self._symbol, close))
            # sell
            elif end_flag:
                shares = self._tlog.sell(date, close)
                print("{0} SELL {1} {2} @ {3:.2f}".format(
                      date, -shares, self._symbol, close))

            # record daily balance
            self._dbal.append(date, high, low, close)

    def run(self):
        self._ts = pf.fetch_timeseries(self._symbol)
        self._ts = pf.select_tradeperiod(self._ts, self._start, self._end,
                                         use_adj=self._use_adj, pad=False)
        self._ts, _ = pf.finalize_timeseries(self._ts, self._start)

        self._tlog = pf.TradeLog(self._symbol)
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

