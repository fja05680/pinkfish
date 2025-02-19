"""
A basic price based momentum strategy.

1. The SPY is higher than X months ago, buy
2. If the SPY is lower than X months ago, sell your long position.

A lookback of None means a random lookback = {6-12} months.
"""

import random

import pinkfish as pf


default_options = {
    'use_adj' : False,
    'use_cache' : True,
    'lookback': None,
    'margin': 1
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
        pf.TradeLog.margin = self.options['margin']
        lookback = None

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            close = row.close 
            end_flag = pf.is_last_row(self.ts, i)

            # If lookback is None, then select a random lookback of
            # 6,7,8,...,or 12 months, if not in a position.
            if self.tlog.shares == 0:
                if self.options['lookback'] is None:
                    lookback = random.choice(range(6, 12+1))
                else:
                    lookback = self.options['lookback']

            #mom = getattr(row, 'mom'+str(lookback))
            mom = self.tlog.get_price(row, 'mom'+str(lookback))

            # Sell Logic
            # First we check if an existing position in symbol should be sold
            #  - if first_dotw
            #            sell if mom < 0
            #            sell if end_flag
  
            if self.tlog.shares > 0:
                if ((row.first_dotw and mom < 0) or end_flag):
#                 if ((row.last_dotm and mom < 0) or end_flag):
                    self.tlog.sell(date, close)

            # Buy Logic
            #  - if first_dotw
            #            buy if mom > 0

            else:
                if (row.first_dotw and mom > 0):
#                 if (row.last_dotm and mom > 0):
                    self.tlog.buy(date, close)

            # Record daily balance
            self.dbal.append(date, close)

    def run(self):
        self.ts = pf.fetch_timeseries(self.symbol, use_cache=self.options['use_cache'])
        self.ts = pf.select_tradeperiod(self.ts, self.start,
                                        self.end, self.options['use_adj'])

        # Add calendar columns
        self.ts = pf.calendar(self.ts)

        # Add momentum indicator for 3...18 months
        lookbacks = range(3, 18+1)
        for lookback in lookbacks:
            self.ts['mom'+str(lookback)] = pf.MOMENTUM(self.ts,
                lookback=lookback, time_frame='monthly',
                price='close', prevday=False)

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

