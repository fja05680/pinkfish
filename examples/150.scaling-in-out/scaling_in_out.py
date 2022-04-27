"""
Scaling in and out of using the double-7s strategy.

1. The SPY is above its 200-day moving average.
2. The SPY closes at a X-day low, buy some shares.  If it sets further
   lows, buy some more.
3. If the SPY closes at a X-day high, sell some.  If it sets further
   highs, sell some more, etc...

    Note:
    This example help demonstrate using some of the lower level
    pinkfish API.  However, an easier approach using adjust_percent()
    is given in strategy.py.
"""

import matplotlib.pyplot as plt
import pandas as pd

import pinkfish as pf


pf.DEBUG = False

default_options = {
    'use_adj' : False,
    'use_cache' : False,
    'stop_loss_pct' : 1.0,
    'margin' : 1,
    'period' : 7,
    'max_open_trades' : 4,
    'enable_scale_in' : True,
    'enable_scale_out' : True
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
        stop_loss = 0

        for i, row in enumerate(self.ts.itertuples()):

            date = row.Index.to_pydatetime()
            close = row.close; 
            end_flag = pf.is_last_row(self.ts, i)
            shares = 0

            max_open_trades = self.options['max_open_trades']
            enable_scale_in = self.options['enable_scale_in']
            enable_scale_out = self.options['enable_scale_out']
            max_open_trades_buy  = max_open_trades if enable_scale_in  else 1
            num_open_trades = self.tlog.num_open_trades

            # Buy Logic
            #  - Buy if still open trades slots left
            #       and bull regime
            #       and price closes at period low
            #       and not end end_flag

            if (num_open_trades < max_open_trades_buy
                and row.regime > 0 and close == row.period_low and not end_flag):

                # Calc number of shares for another cash-equal trade.
                buying_power = self.tlog.calc_buying_power(close)
                cash = buying_power / (max_open_trades_buy - num_open_trades)
                shares = self.tlog.calc_shares(close, cash)

                # Buy more shares if we have the cash.
                if shares > 0:
                    # Enter buy in trade log
                    self.tlog.buy(date, close, shares)
                    # Set stop loss
                    stop_loss = (1-self.options['stop_loss_pct'])*close
                    # set sell_parts to max_open_trades
                    num_out_trades = max_open_trades

            # Sell Logic
            # First we check if we have any open trades, then
            #  - Sell if price closes at X day high.
            #  - Sell if price closes below stop loss.
            #  - Sell if end of data.

            elif (num_open_trades > 0 
                  and (close == row.period_high or close < stop_loss or end_flag)):

                if not enable_scale_out or close < stop_loss or end_flag:
                    # Exit all positions.
                    shares = None
                elif enable_scale_in:
                    # Exit one position.
                    shares = -1
                else:
                    # Scaling out is done here by shares, for example
                    # if there are 100 shares and num trades is 4,
                    # then we reduce by 25 each time.  This is
                    # different than scaling out by percentage of
                    # total fund value as is done in strategy.py.
                    shares = int(self.tlog.shares / num_out_trades)
                    num_out_trades -= 1

                # Enter sell in trade log.
                shares = self.tlog.sell(date, close, shares)

            if shares > 0:
                pf.DBG("{0} BUY  {1} {2} @ {3:.2f}".format(
                    date, shares, self.symbol, close))
            elif shares < 0:
                pf.DBG("{0} SELL {1} {2} @ {3:.2f}".format(
                    date, -shares, self.symbol, close))

            # Record daily balance.
            self.dbal.append(date, close)

    def run(self):

        # Fetch and select timeseries.
        self.ts = pf.fetch_timeseries(self.symbol, use_cache=self.options['use_cache'])
        self.ts = pf.select_tradeperiod(self.ts, self.start, self.end,
                                        use_adj=self.options['use_adj'])

        # Add technical indicator: 200 day sma regime filter.
        self.ts['regime'] = pf.CROSSOVER(self.ts, timeperiod_fast=1, timeperiod_slow=200)

        # Add technical indicators: X day high, and X day low.
        self.ts['period_high'] = pd.Series(self.ts.close).rolling(self.options['period']).max()
        self.ts['period_low'] =  pd.Series(self.ts.close).rolling(self.options['period']).min()

        # Finalize timeseries.
        self.ts, self.start = pf.finalize_timeseries(self.ts, self.start,
                                dropna=True, drop_columns=['open', 'high', 'low'])

        # Create tlog and dbal objects.
        self.tlog = pf.TradeLog(self.symbol)
        self.dbal = pf.DailyBal()

        # Run algo, get logs, and get stats.
        self._algo()
        self._get_logs()
        self._get_stats()

    def _get_logs(self):
        self.rlog = self.tlog.get_log_raw()
        self.tlog = self.tlog.get_log()
        self.dbal = self.dbal.get_log(self.tlog)

    def _get_stats(self):
        self.stats = pf.stats(self.ts, self.tlog, self.dbal, self.capital)


def summary(strategies, metrics):
    """
    Stores stats summary in a DataFrame.

    stats() must be called before calling this function.
    """
    index = []
    columns = strategies.index
    data = []
    # Add metrics.
    for metric in metrics:
        index.append(metric)
        data.append([strategy.stats[metric] for strategy in strategies])

    df = pd.DataFrame(data, columns=columns, index=index)
    return df


def plot_bar_graph(df, metric):
    """
    Plot Bar Graph.

    stats() must be called before calling this function.
    """
    df = df.loc[[metric]]
    df = df.transpose()
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel=metric)
    df.plot(kind='bar', ax=axes, legend=False)
    axes.set_xticklabels(df.index, rotation=0)
