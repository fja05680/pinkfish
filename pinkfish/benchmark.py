"""
Benchmark for comparision to a strategy.
"""

import pinkfish as pf


class Benchmark:
    """
    Portfolio Benchmark for comparison to a strategy.
    """

    def __init__(self, symbols, capital, start, end, use_adj=False,
                 use_continuous_calendar=False,
                 force_stock_market_calendar=False):
        """
        Initialize instance variables.

        Parameters
        ----------
        symbols : str or list of str
            The symbol(s) to use in the benchmark.
        capital : int
            The amount of money available for trading.
        start : datetime.datetime
            The desired start date for the benchmark.
        end : datetime.datetime
            The desired end date for the benchmark.
        use_adj : bool, optional
            True to adjust prices for dividends and splits
            (default is False).
        use_continuous_calendar: bool, optional
            True if your timeseries has data for all seven days a week,
            and you want to backtest trading every day, including weekends.
            If this value is True, then `force_stock_market_calendar`
            is set to False (default is False).
        force_stock_market_calendar : bool, optional
            True forces use of stock market calendar on timeseries.
            Normally, you don't need to do this.  This setting is intended
            to transform a continuous timeseries into a weekday timeseries.
            If this value is True, then `use_continuous_calendar` is set
            to False.

        Attributes
        ----------
        symbols : list of str
            The symbols to use in the benchmark.
        capital : int
            The amount of money available for trading.
        start : datetime.datetime
            The desired start date for the benchmark.
        end : datetime.datetime
            The desired end date for the benchmark.
        use_adj : bool, optional
            True to adjust prices for dividends and splits.
        use_continuous_calendar: bool, optional
            True if your timeseries has data for all seven days a week,
            and you want to backtest trading every day, including weekends.
            If this value is True, then `force_stock_market_calendar`
            is set to False (default is False).
        force_stock_market_calendar : bool, optional
            True forces use of stock market calendar on timeseries.
            Normally, you don't need to do this.  This setting is intended
            to transform a continuous timeseries into a weekday timeseries.
            If this value is True, then `use_continuous_calendar` is set
            to False.
        ts : pd.DataFrame
            The timeseries of the symbol used in backtest.
        tlog : pd.DataFrame
            The trade log.
        dbal : pd.DataFrame
            The daily balance.
        stats : pd.Series
            The statistics for the benchmark.
        """

        # If symbols is not a list, cast it to a list.
        if not isinstance(symbols, list):
            symbols = [symbols]

        symbols = list(set(symbols))

        self.symbols = symbols
        self.capital = capital
        self.start = start
        self.end = end
        self.use_adj = use_adj
        self.use_continuous_calendar = use_continuous_calendar
        self.force_stock_market_calendar = force_stock_market_calendar

        self.ts = None
        self.tlog = None
        self.dbal = None
        self.stats = None

    def _algo(self):
        """
        This is a general asset allocation stategy.

        Invest an equal percent in each investment option and
        rebalance every year.
        """
        pf.TradeLog.cash = self.capital
        pf.TradeLog.margin = pf.Margin.CASH

        # These dicts are used to track close and weights for
        # each symbol in portfolio
        prices = {}; weights = {}

        weight = 1 / len(self.portfolio.symbols)
        weights = {symbol:weight for symbol in self.portfolio.symbols}

        # Trading algorithm
        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            end_flag = pf.is_last_row(self.ts, i)
            start_flag = (i==0)
            
            # Buy on first trading day
            # Rebalance on the first trading day of each year
            # Close all positions on last trading day
            if row.first_doty or end_flag or start_flag:

                # If last row, then zero out all weights.
                if end_flag:
                    weights = pf.set_dict_values(weights, 0)

                # Get closing prices for all symbols
                p = self.portfolio.get_prices(row, fields=['close'])
                prices = {symbol:p[symbol]['close'] for symbol in self.portfolio.symbols}
                
                # Adjust weights of all symbols in portfolio
                self.portfolio.adjust_percents(date, prices, weights, row)

            # Record daily balance.
            self.portfolio.record_daily_balance(date, row)

    def run(self):
        self.portfolio = pf.Portfolio()
        self.ts = self.portfolio.fetch_timeseries(
            self.symbols, self.start, self.end, use_adj=self.use_adj,
            use_continuous_calendar=self.use_continuous_calendar,
            force_stock_market_calendar=self.force_stock_market_calendar)
        # Add calendar columns
        self.ts = self.portfolio.calendar(self.ts)

        self.ts, self.start = self.portfolio.finalize_timeseries(self.ts, self.start)
        self.portfolio.init_trade_logs(self.ts)

        self._algo()
        self._get_logs()
        self._get_stats()

    def _get_logs(self):
        self.rlog, self.tlog, self.dbal = self.portfolio.get_logs()

    def _get_stats(self):
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)

Strategy = Benchmark
"""
class : Strategy is a class reference to Benchmark, i.e. an alias.
"""
