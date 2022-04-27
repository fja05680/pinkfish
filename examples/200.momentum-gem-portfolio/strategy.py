"""
Global Equities Momentum (GEM)¶

Gary Antonacci’s Dual Momentum approach is simple: by combining both
relative momentum and absolute momentum (i.e. trend following),
Dual Momentum seeks to rotate into areas of relative strength while
preserving the flexibility to shift entirely to safety assets
(e.g. short-term U.S. Treasury bills) during periods of pervasive,
negative trends.

Antonacci’s Global Equities Momentum (GEM) portfolio builds a portfolio
with three assets: U.S. stocks, international stocks and U.S. bonds.
For the retail investor he recommends using low-cost ETFs: for example,
VOO for U.S. stocks; VEU for non-U.S. stocks and AGG for U.S. aggregate
bonds.

Antonacci named his system “Dual Momentum” because he uses both
relative momentum (the measure of the performance of an asset relative
to another asset) and absolute momentum ( the measure of performance
relative to the risk-free rate – absolute excess return.) To keep the
process very simple to implement, he used a 12-month look-back period
and an easy to execute buy and sell system.

Every month the investor places all funds in the equity ETF that has
the best 12-month performance relative to the other equity ETFs,
unless the absolute performance is worse than the return of
six-month U.S. Treasuries (as measured by BIL ETF). If absolute
performance is below the BIL ETF, then the investor places all funds
in AGG, the aggregate bond index.
"""

import random

import pinkfish as pf


default_options = {
    'use_adj' : True,
    'use_cache' : True,
    'lookback': None,
    'margin': 1,
}

class Strategy:

    def __init__(self, symbols, capital, start, end, options=default_options):

        self.symbols = symbols
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

        # These dicts are used to track close, mom, and weights for
        # each symbol in portfolio
        prices = {}
        mom = {}
        weights = {}

        # These variables are assigned to the actual ETFs
        US_STOCKS   = self.symbols['US STOCKS']
        US_BONDS    = self.symbols['US BONDS']
        EXUS_STOCKS = self.symbols['EX-US STOCKS']
        TBILL       = self.symbols['T-BILL']

        # A counter to countdown the number of months a lookback has
        # been in place
        month_count = 0

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            end_flag = pf.is_last_row(self.ts, i)

            if month_count == 0:
                # if period is None, then select a random trading period of
                # 6,7,8,...,or 12 months
                if self.options['lookback'] is None: 
                    lookback = random.choice(range(6, 12+1))
                else:
                    lookback = self.options['lookback']
                month_count = lookback

            # If first day of the month or last row
            if row.first_dotm or end_flag:

                month_count -= 1

                # Get prices for current row
                mom_field = 'mom' + str(lookback)
                p = self.portfolio.get_prices(row, fields=['close', mom_field])

                # Copy data from `p` into prices and mom dicts for
                # convenience, also zero out weights dict. 
                for symbol in self.portfolio.symbols:
                    prices[symbol] = p[symbol]['close']
                    mom[symbol] = p[symbol][mom_field]
                    weights[symbol] = 0

                # Rebalance logic:
                #   Check absolute momenteum first, i.e. US_STOCKS > TBILL.
                #   Check relative momentrum, i.e. US_STOCKS > EXUS_STOCKS.
                #   (see complete description at top of this file)
                #   Finally rebalance

                # GEM strategy
                if end_flag:
                    # Since weights dict is zeroed out, all positions
                    # will be closed out below with adjust_percent()
                    pass
                elif mom[US_STOCKS] > mom[TBILL]:
                    if mom[US_STOCKS] > mom[EXUS_STOCKS]:
                        weights[US_STOCKS] = 1
                    else:
                        weights[EXUS_STOCKS] = 1
                else: 
                    weights[US_BONDS] = 1

                # Rebalance portfolio
                self.portfolio.adjust_percents(date, prices, weights, row)

            # record daily balance
            self.portfolio.record_daily_balance(date, row)

    def run(self):
        self.portfolio = pf.Portfolio()
        self.ts = self.portfolio.fetch_timeseries(self.symbols.values(), self.start, self.end,
                    fields=['close'],
                    use_cache=self.options['use_cache'],
                    use_adj=self.options['use_adj'])

        # Add calendar columns
        self.ts = self.portfolio.calendar(self.ts)

        # Add technical indicator Momenteum for all symbols in portfolio.
        lookbacks = range(3, 18+1)
        for lookback in lookbacks:
            @pf.technical_indicator(self.symbols.values(), 'mom'+str(lookback), 'close')
            def _momentum(ts, input_column=None):
                return pf.MOMENTUM(ts, lookback=lookback, time_frame='monthly',
                                   price=input_column, prevday=False)
            self.ts = _momentum(self.ts)

        self.ts, self.start = self.portfolio.finalize_timeseries(self.ts, self.start)
        self.portfolio.init_trade_logs(self.ts)

        self._algo()
        self._get_logs()
        self._get_stats()

    def _get_logs(self):
        self.rlog, self.tlog, self.dbal = self.portfolio.get_logs()

    def _get_stats(self):
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)
