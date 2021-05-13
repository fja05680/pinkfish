"""
Benchmark for comparision to a strategy.
"""

import pinkfish as pf


class Benchmark:
    """
    Benchmark for comparison to a strategy.
    """

    def __init__(self, symbol, capital, start, end, use_adj=False):
        """
        Initialize instance variables.

        Parameters
        ----------
        symbol : str
            The symbol for the security to use in the benchmark.
        capital : int
            The amount of money available for trading.
        start : datetime.datetime
            The desired start date for the benchmark.
        end : datetime.datetime
            The desired end date for the benchmark.
        use_adj : bool, optional
            True to adjust prices for dividends and splits
            (default is False).

        Attributes
        ----------
        symbol : str
            The symbol for the security to use in the benchmark.
        capital : int
            The amount of money available for trading.
        start : datetime.datetime
            The desired start date for the benchmark.
        end : datetime.datetime
            The desired end date for the benchmark.
        use_adj : bool, optional
            True to adjust prices for dividends and splits.
        ts : pd.DataFrame
            The timeseries of the symbol used in backtest.
        tlog : pd.DataFrame
            The trade log.
        dbal : pd.DataFrame
            The daily balance.
        stats : pd.Series
            The statistics for the benchmark.
        """
        self.symbol = symbol
        self.capital = capital
        self.start = start
        self.end = end
        self.use_adj = use_adj
        self.ts = None
        self.tlog = None
        self.dbal = None
        self.stats = None

    def _algo(self):
        """
        Use simple buy and hold strategy.
        """
        pf.TradeLog.cash = self.capital
        pf.TradeLog.margin = pf.Margin.CASH

        for i, row in enumerate(self.ts.itertuples()):
            date = row.Index.to_pydatetime()
            end_flag = pf.is_last_row(self.ts, i)

            # Buy.
            if self.tlog.shares == 0:
                self.tlog.buy(date, row.close)
            # Sell.
            elif end_flag:
                self.tlog.sell(date, row.close)

            # Record daily balance.
            self.dbal.append(date, row.high, row.low, row.close)

    def _get_logs(self):
        """
        Get logs for the TradeLog and DailyBal objects.
        """
        self.tlog = self.tlog.get_log()
        self.dbal = self.dbal.get_log(self.tlog)

    def _get_stats(self):
        """
        Get the statistics for the benchmark.
        """
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)

    def run(self):
        """
        Run the backtest.

        Don't adjust the start day because that may cause it not
        to match the start date of the strategy you are benchmarking
        against.  Instead, you should pass in the start date calculated
        for the strategy.
        """
        self.ts = pf.fetch_timeseries(self.symbol)
        self.ts = pf.select_tradeperiod(self.ts, self.start, self.end,
                                         use_adj=self.use_adj)
        self.ts, _ = pf.finalize_timeseries(self.ts, self.start)

        self.tlog = pf.TradeLog(self.symbol)
        self.dbal = pf.DailyBal()

        self._algo()
        self._get_logs()
        self._get_stats()

Strategy = Benchmark
"""
class : Strategy is a class reference to Benchmark, i.e. an alias.
"""
