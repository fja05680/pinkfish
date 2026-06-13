"""
A basic long term trend strategy applied separately to several
securities.

1. S&P 500 index closes above its 200 day moving average
2. The stock closes above its upper band, buy

3. S&P 500 index closes below its 200 day moving average
4. The stock closes below its lower band, sell your long position.
"""

import pinkfish as pf


default_options = {
    'use_adj' : False,
    'use_cache' : True,
    'sma_period': 200,
    'percent_band' : 0,
    'use_regime_filter' : True
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
            close = row.close
            end_flag = pf.is_last_row(self.ts, i)
            upper_band = row.sma * (1 + self.options['percent_band'] / 100)
            lower_band = row.sma * (1 - self.options['percent_band'] / 100)

            # Sell Logic
            # First we check if an existing position in symbol
            # should be sold
            #  - Sell if (use_regime_filter and regime < 0)
            #  - Sell if price closes below lower_band
            #  - Sell if end of data

            if self.tlog.shares > 0:
                if ((self.options['use_regime_filter'] and row.regime < 0)
                        or close < lower_band
                        or end_flag):
                    self.tlog.sell(date, close)

            # Buy Logic
            # First we check to see if there is an existing position,
            # if so do nothing
            #  - Buy if (regime > 0 or not use_regime_filter)
            #            and price closes above upper_band
            #            and (use_regime_filter and regime > 0)

            else:
                if ((row.regime > 0 or not self.options['use_regime_filter'])
                        and close > upper_band):
                    self.tlog.buy(date, close)

            # Record daily balance
            self.dbal.append(date, close) 

    def run(self):
        self.ts = pf.fetch_timeseries(self.symbol, use_cache=self.options['use_cache'])
        self.ts = pf.select_tradeperiod(self.ts, self.start,
                                        self.end, self.options['use_adj'])

        # Add technical indicator:  day sma
        self.ts['sma'] = pf.SMA(self.ts, timeperiod=self.options['sma_period'])

        # add S&P500 200 sma regime filter
        ts = pf.fetch_timeseries('^GSPC')
        ts = pf.select_tradeperiod(ts, self.start, self.end, use_adj=False) 
        self.ts['regime'] = \
            pf.CROSSOVER(ts, timeperiod_fast=1, timeperiod_slow=200)

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
