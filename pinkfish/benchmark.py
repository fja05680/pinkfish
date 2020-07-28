"""
benchmark
---------
Benchmark for comparision to strategies
"""

import pinkfish as pf


class Benchmark:

    def __init__(self, symbol, capital, start, end, use_adj=False):
        self.symbol = symbol
        self.capital = capital
        self.start = start
        self.end = end
        self.use_adj = use_adj

    def _algo(self):
        pf.TradeLog.cash = self.capital
        pf.TradeLog.margin = pf.Margin.CASH

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close
            end_flag = pf.is_last_row(self.ts, i)

            # buy
            if self.tlog.shares == 0:
                self.tlog.buy(date, close)
                print("{0} BUY  {1} {2} @ {3:.2f}".format(
                      date, self.tlog.shares, self.symbol, close))
            # sell
            elif end_flag:
                shares = self.tlog.sell(date, close)
                print("{0} SELL {1} {2} @ {3:.2f}".format(
                      date, -shares, self.symbol, close))

            # record daily balance
            self.dbal.append(date, high, low, close)

    def run(self):
        self.ts = pf.fetch_timeseries(self.symbol)
        self.ts = pf.select_tradeperiod(self.ts, self.start, self.end,
                                         use_adj=self.use_adj)
        self.ts, _ = pf.finalize_timeseries(self.ts, self.start)

        self.tlog = pf.TradeLog(self.symbol)
        self.dbal = pf.DailyBal()

        self._algo()

    def get_logs(self):
        """ return DataFrames """
        self.tlog = self.tlog.get_log()
        self.dbal = self.dbal.get_log(self.tlog)
        return self.tlog, self.dbal

    def get_stats(self):
        stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)
        return stats

