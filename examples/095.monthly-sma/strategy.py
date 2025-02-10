"""
The Monthly SMA.

Entry and Exit Points
Entry (Buy Signal): Buy when the S&P 500 closes above the 10-month moving
average at the end of the month.

Exit (Sell Signal): Sell when the S&P 500 closes below the 10-month moving
average at the end of the month.
"""

import pinkfish as pf


default_options = {
    'use_adj' : False,
    'use_cache' : True,
    'monthly_sma' : 10
}

class Strategy:

    def __init__(self, symbol, capital, start, end, options=default_options):

        self.symbol = symbol
        self.capital = capital
        self.start = start
        self.end = end
        self.options = options.copy()

        self.ts = None
        self.rlog = None
        self.tlog = None
        self.dbal = None
        self.stats = None

    def _algo(self):

        pf.TradeLog.cash = self.capital

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            close = row.close; 
            end_flag = pf.is_last_row(self.ts, i)

            # Buy
            if self.tlog.shares == 0:
                if row.last_dotm and row.close > row.monthly_sma:
                    self.tlog.buy(date, close)
            # Sell
            else:
                if (row.last_dotm and close < row.monthly_sma) or end_flag:
                    self.tlog.sell(date, close)
            

            # Record daily balance.
            self.dbal.append(date, close)

    def run(self):

        # Fetch and select timeseries
        self.ts = pf.fetch_timeseries(self.symbol, use_cache=self.options['use_cache'])
        self.ts = pf.select_tradeperiod(self.ts, self.start, self.end,
                                        use_adj=self.options['use_adj'])

        # Step 1: Resample to get the last closing price of each month
        df_monthly = self.ts["close"].resample('ME').last()  # 'M' ensures robustness

        # Step 2: Compute the 10-month moving average
        df_monthly_sma = df_monthly.rolling(window=self.options['monthly_sma'],
                                            min_periods=self.options['monthly_sma']).mean()

        # Step 3: Reindex the monthly SMA to the daily index and forward-fill
        self.ts['monthly_sma'] = df_monthly_sma.reindex(self.ts.index, method='ffill')
        
        # Add calendar columns.
        self.ts = pf.calendar(self.ts, columns=['last_dotm'])
        
        # Finalize timeseries
        self.ts, self.start = pf.finalize_timeseries(self.ts, self.start,
                                dropna=True, drop_columns=['open', 'high', 'low'])

        self.tlog = pf.TradeLog(self.symbol)
        self.dbal = pf.DailyBal()

        self._algo()
        self._get_logs()
        self._get_stats()

    def _get_logs(self):
        self.rlog = self.tlog.get_log_raw()
        self.tlog = self.tlog.get_log()
        self.dbal = self.dbal.get_log(self.tlog)

    def _get_stats(self):
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)
