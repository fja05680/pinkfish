"""
stategy
---------
"""

# other imports
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from talib.abstract import *

# project imports
import pinkfish as pf

pf.DEBUG = False


class Strategy():
    """ strategy """

    def __init__(self, symbol, capital, start, end, use_adj, period):
        self._symbol = symbol
        self._capital = capital
        self._start = start
        self._end = end
        self._use_adj = use_adj
        self._period = period

    def _algo(self):
        """ Algo:
            1. The SPY is above its 200-day moving average
            2. The SPY makes an intraday X-day low, buy.
            3. If the SPY makes an intraday X-day high, sell your long position.
        """
        self._tlog.initialize(self._capital)
        stop_loss = 0

        for i, row in enumerate(self._ts.itertuples()):

            date = row.Index.to_pydatetime()
            high = row.high; low = row.low; close = row.close; 
            end_flag = pf.is_last_row(self._ts, i)
            prev_close = self._ts['close'][i-1]
            sma200 = self._ts['sma200'][i-1]
            period_high = self._ts['period_high'][i-1]
            period_low = self._ts['period_low'][i-1]
            shares = 0

            # buy
            if (self._tlog.num_open_trades() == 0
                and prev_close > sma200
                and low <= period_low
                and not end_flag):

                # adjust price if opened less than period_low
                price = row.open if row.open <= period_low else period_low    
                # enter buy in trade log
                shares = self._tlog.enter_trade(date, price)
                # set stop loss
                stop_loss = 0*low
            # sell
            elif (self._tlog.num_open_trades() > 0
                  and (high >= period_high or low < stop_loss or end_flag)):

                # adjust price if opened greater than period_high; stop_loss; close
                if high >= period_high:
                    price = row.open if row.open >= period_high else period_high
                elif low < stop_loss:
                    price = stop_loss
                else:
                    price = close

                # enter sell in trade log
                shares = self._tlog.exit_trade(date, price)
                #if (low < stop_loss):
                #    print("--------------------STOP-----------------------------")

            if shares > 0:
                pf.DBG("{0} BUY  {1} {2} @ {3:.2f}".format(
                       date, shares, self._symbol, close))
            elif shares < 0:
                pf.DBG("{0} SELL {1} {2} @ {3:.2f}".format(
                       date, -shares, self._symbol, close))

            # record daily balance
            self._dbal.append(date, high, low, close, self._tlog.shares) 

    def run(self):
        self._ts = pf.fetch_timeseries(self._symbol)
        self._ts = pf.select_tradeperiod(self._ts, self._start,
                                         self._end, use_adj=self._use_adj)

        # Add technical indicator: 200 day sma
        sma200 = SMA(self._ts, timeperiod=200)
        self._ts['sma200'] = sma200

        # Add technical indicator: X day high, and X day low
        period_high = pd.Series(self._ts.high).rolling(self._period).max()
        period_low = pd.Series(self._ts.high).rolling(self._period).min()
        self._ts['period_high'] = period_high
        self._ts['period_low'] = period_low
        
        self._ts, self._start = pf.finalize_timeseries(self._ts, self._start)

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

def summary(strategies, *metrics):
    """ Stores stats summary in a DataFrame.
        stats() must be called before calling this function
    """
    index = []
    columns = strategies.index
    data = []
    # add metrics
    for metric in metrics:
        index.append(metric)
        data.append([strategy.stats[metric] for strategy in strategies])

    df = pd.DataFrame(data, columns=columns, index=index)
    return df

def plot_bar_graph(df, metric):
    """ Plot Bar Graph: Strategy
        stats() must be called before calling this function
    """
    df = df.loc[[metric]]
    df = df.transpose()
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel=metric)
    df.plot(kind='bar', ax=axes, legend=False)
    axes.set_xticklabels(df.index, rotation=0)
