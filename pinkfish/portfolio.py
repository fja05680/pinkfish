"""
portfolio
---------
Portfolio backtesting
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn
import pinkfish as pf


class Portfolio:

    def __init__(self):
        self._l = []      # list of daily balance tuples
        self._ts = None   # reference to timeseries
        self.symbols = []

    #####################################################################
    # TIMESERIES (fetch, add_technical_indicator, calender, finalize)

    def _add_symbol_columns(self, ts, symbol, symbol_ts, fields):
        """ add column with field suffix for symbol, i.e. SPY_close """
        for field in fields:
            column = symbol + '_' + field
            ts[column] = symbol_ts[field]
        return ts

    def fetch_timeseries(self, symbols, start, end,
                         fields=['high', 'low', 'close'], use_cache=True):
        """ read time series data for symbols """
        for i, symbol in enumerate(symbols):

            if i == 0:
                ts = pf.fetch_timeseries(symbol, use_cache=use_cache)
                ts = pf.select_tradeperiod(ts, start, end, use_adj=True)
                self._add_symbol_columns(ts, symbol, ts, fields)
                ts.drop(columns=['high', 'low', 'open', 'close', 'volume', 'adj_close'],
                        inplace=True)
            else:
                # add another symbol
                _ts = pf.fetch_timeseries(symbol, use_cache=use_cache)
                _ts = pf.select_tradeperiod(_ts, start, end, use_adj=True)
                self._add_symbol_columns(ts, symbol, _ts, fields)

        self.symbols = symbols
        return ts

    def add_technical_indicator(self, ts, ta_func, ta_param, output_column_suffix,
                                input_column_suffix='close'):
        """ add a technical indicator for each symbol """
        for symbol in self.symbols:
            input_column = symbol + '_' + input_column_suffix
            output_column = symbol + '_' + output_column_suffix
            ts[output_column] = ta_func(ts, ta_param, input_column)
        return ts

    def calendar(self, ts):
        return pf.calendar(ts)

    def finalize_timeseries(self, ts, start):
        return pf.finalize_timeseries(ts, start)

    #####################################################################
    # ADJUST POSITION (adjust_shares, adjust_value, adjust_percent, print_holdings)

    def get_row_column_value(self, row, symbol, field='close'):
        """ return price given row and symbol """
        symbol += '_' + field
        try:
            price = getattr(row, symbol)
        except AttributeError:
            # this method is slower, but handles column names that don't
            # conform to variable name rules, and thus aren't attributes
            date = row.Index.to_pydatetime()
            price = self._ts.loc[date, symbol]
        return price

    def _share_value(self, row):
        """ total share value in portfolio """
        value = 0
        for symbol, tlog in pf.TradeLog.instance.items():
            close = self.get_row_column_value(row, symbol)
            value += tlog.share_value(close)
        return value
        
    def _total_value(self, row):
        """ total_value = share_value +  cash (if cash > 0) """
        total_value = self._share_value(row)
        if pf.TradeLog.cash > 0:
            total_value += pf.TradeLog.cash
        return total_value

    def _equity(self, row):
        """ return the equity in portfolio """
        return pf.TradeLog.cash + self._share_value(row)

    def _equity(self, row):
        """ equity = total_value - loan (loan is negative cash) """
        equity = self._total_value(row)
        if pf.TradeLog.cash < 0:
            equity += pf.TradeLog.cash
        return equity

    def _leverage(self, row):
        """ return the leverage factor of the position """
        return self._total_value(row) / self._equity(row)

    def _total_funds(self, row):
        """ total account funds for trading """
        return self._equity(row) * pf.TradeLog.margin

    def share_percent(self, row, symbol):
        """ return share value of symbol as a percentage of total_funds """
        close = self.get_row_column_value(row, symbol)
        tlog = pf.TradeLog.instance[symbol]
        value = tlog.share_value(close)
        return value / self._total_funds(row) * 100

    def _calc_buying_power(self, row):
        """ calculate buying power """
        buying_power = (pf.TradeLog.cash * pf.TradeLog.margin
                      + self._share_value(row) * (pf.TradeLog.margin -1))
        return buying_power

    def _adjust_shares(self, date, price, shares, symbol, row, direction=pf.Direction.LONG):
        tlog = pf.TradeLog.instance[symbol]
        pf.TradeLog.buying_power = self._calc_buying_power(row)
        shares = tlog.adjust_shares(date, price, shares, direction)
        pf.TradeLog.buying_power = None
        return shares

    def _adjust_value(self, date, price, value, symbol, row, direction=pf.Direction.LONG):
        total_funds = self._total_funds(row)
        shares = int(min(total_funds, value) / price)
        shares = self._adjust_shares(date, price, shares, symbol, row, direction)
        return shares

    def adjust_percent(self, date, price, weight, symbol, row, direction=pf.Direction.LONG):
        weight = weight if weight <= 1 else weight/100
        total_funds = self._total_funds(row)
        value = total_funds * weight
        shares = self._adjust_value(date, price, value, symbol, row, direction)
        return shares

    def print_holdings(self, date, row):
        """ print snapshot of portfolio holding and values """
        # 2010-02-01 SPY: 54 TLT: 59 GLD:  9 cash:    84.20 total:  9,872.30
        print(date.strftime('%Y-%m-%d'), end=' ')
        for symbol, tlog in pf.TradeLog.instance.items():
            print('{}:{:3}'.format(symbol, tlog.shares), end=' ')
        print('cash: {:8,.2f}'.format(pf.TradeLog.cash), end=' ')
        print('total: {:9,.2f}'.format(self._equity(row)))

    #####################################################################
    # LOGS (init_trade_logs, record_daily_balance, get_logs)

    buying_power = None            # buying power; for Portfolio class only
    seq_num = 0                    # used to order trades in Portfolio class
    instance = {}                  # dict of TradeLog instances, key=symbol

    def init_trade_logs(self, ts, capital, margin=pf.Margin.CASH):
        """ add a trade log for each symbol """
        
        pf.TradeLog.cash = capital
        pf.TradeLog.margin = margin
        pf.TradeLog.seq_num = 0
        pf.TradeLog.instance.clear()

        self._ts = ts
        for symbol in self.symbols:
            pf.TradeLog(symbol, False)

    def record_daily_balance(self, date, row):
        """ append to daily balance list """
        # calculate daily balance values: date, high, low, close, shares, cash
        equity = self._equity(row)
        leverage = self._leverage(row)
        shares = 0
        for tlog in pf.TradeLog.instance.values():
            shares += tlog.shares
        t = (date, equity, equity, equity, shares,
             pf.TradeLog.cash, leverage)
        self._l.append(t)

    def get_logs(self):
        """ return raw tradelog, tradelog, and daily balance log """
        tlogs = []; rlogs = []
        for tlog in pf.TradeLog.instance.values():
            rlogs.append(tlog.get_log_raw())
            tlogs.append(tlog.get_log(merge_trades=False))
        rlog = pd.concat([r for r in rlogs]).sort_values(['seq_num'],
                         ignore_index=True)
        tlog = pd.concat([t for t in tlogs]).sort_values(['entry_date', 'exit_date'],
                         ignore_index=True)
        tlog['cumul_total'] = tlog['pl_cash'].cumsum()

        dbal = pf.DailyBal()
        dbal._l = self._l
        dbal = dbal.get_log(tlog)
        return rlog, tlog, dbal

    #####################################################################
    # PERFORMANCE ANALYSIS (performance_per_symbol, correlation_map)

    def performance_per_symbol(self, weights):
        """ returns data from containing performace per symbol; also plots perf """

        def _weight(row, weights):
            return weights[row.name]

        def _currency(row):
            return pf.currency(row['cumul_total'])

        def _plot(df):
            df = df[:-1]
            # Make new figure and set the size.
            fig = plt.figure(figsize=(12, 8))
            # The first subplot, planning for 3 plots high, 1 plot wide,
            # this being the first.
            axes = fig.add_subplot(111, ylabel='Percentages')
            axes.set_title('Performance by Symbol')
            df.plot(kind='bar', ax=axes)
            axes.set_xticklabels(df.index, rotation=60)
            plt.legend(loc='best')

        # convert dict to series
        s = pd.Series(dtype='object')
        for symbol, tlog in pf.TradeLog.instance.items():
            s[symbol] = tlog.cumul_total
        # convert series to dataframe
        df = pd.DataFrame(s.values, index=s.index, columns=['cumul_total'])
        # add weight column
        df['weight'] = df.apply(_weight, weights=weights, axis=1)
        # add percent column
        df['pct_cumul_total'] = df['cumul_total'] / df['cumul_total'].sum()
        # add relative preformance
        df['relative_performance'] = df['pct_cumul_total'] / df['weight']
        # add TOTAL row
        new_row = pd.Series(name='TOTAL',
            data={'cumul_total':df['cumul_total'].sum(),
                  'pct_cumul_total': 1.00, 'weight': 1.00,
                  'relative_performance': 1.00})
        df = df.append(new_row, ignore_index=False)
        # format as currency
        df['cumul_total'] = df.apply(_currency, axis=1)
        # plot bar graph of performance
        _plot(df)
        return df

    def correlation_map(self, ts):
        """ return correlation dataframe; show correlation map between symbols"""

        # filter coloumn names for ''_close''; drop '_close' suffix
        df = ts.filter(regex='_close')
        df.columns = df.columns.str.strip('_close')

        df = df.corr(method='pearson')
        # reset symbol as index (rather than 0-X)
        df.head().reset_index()
        # del df.index.name
        df.head(20)
        # take the bottom triangle since it repeats itself
        mask = np.zeros_like(df)
        mask[np.triu_indices_from(mask)] = True
        # generate plot
        seaborn.heatmap(df, cmap='RdYlGn', vmax=1.0, vmin=-1.0 ,
                        mask = mask, linewidths=2.5)
        plt.yticks(rotation=0)
        plt.xticks(rotation=90)
        return df

