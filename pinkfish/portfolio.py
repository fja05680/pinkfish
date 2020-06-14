"""
portfolio
---------
Portfolio backtesting
"""

# Other imports
import pandas as pd
import pinkfish as pf


class Portfolio(object):

    def __init__(self):
        self._l = []  # list of daily balance tuples
        self._symbols = []

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

        self._symbols = symbols
        return ts

    def add_technical_indicator(self, ts, ta_func, ta_param, output_column_suffix,
                                input_column_suffix='close'):
        """ add a technical indicator for each symbol """
        for symbol in self._symbols:
            input_column = symbol + '_' + input_column_suffix
            output_column = symbol + '_' + output_column_suffix
            ts[output_column] = ta_func(ts, ta_param, input_column)
        return ts

    def init_trade_logs(self, ts, capital):
        """ add a trade log for each symbol """
        pf.TradeLog.initialize(capital)
        tlogs = pd.Series(dtype=object)
        for symbol in self._symbols:
            tlogs[symbol] = pf.TradeLog()
        return tlogs

    def _total_equity(self, row):
        """ return the total equity in portfolio """
        total_equity = pf.TradeLog._cash
        for symbol, shares in pf.TradeLog._share_dict.items():
            close = getattr(row, symbol + '_close')
            total_equity += close * shares
        return total_equity

    def adjust_shares(self, date, price, shares, symbol, tlog):
        """
        Adjust a position to a target number of shares.
        If the position doesn't already exist, this is equivalent
        to entering a new trade. If the position does exist, this is
        equivalent to entering or exiting a trade for the difference between
        the target number of shares and the current number of shares.
        """
        diff_shares = shares - pf.TradeLog._share_dict.get(symbol, 0)
        if diff_shares >= 0:
            shares = tlog.enter_trade(date, price, diff_shares, symbol)
        else:
            shares = tlog.exit_trade(date, price, -diff_shares, symbol)
        return shares

    def adjust_value(self, date, price, value, symbol, tlog, row):
        """
        Adjust a position to a target value.
        If the position doesn't already exist, this is equivalent
        to entering a new trade. If the position does exist, this is
        equivalent to entering or exiting a trade for the difference between
        the target value and the current value.
        """
        total_equity = self._total_equity(row)
        shares = int(min(total_equity, value) / price)
        shares = self.adjust_shares(date, price, shares, symbol, tlog)
        return shares

    def adjust_percent(self, date, price, weight, symbol, tlog, row):
        """
        Adjust a position to a target percent of the current portfolio value.
        If the position doesn't already exist, this is equivalent
        to entering a new trade. If the position does exist, this is
        equivalent to entering or exiting a trade for the difference between
        the target percent and the current percent.
        """
        weight = weight if weight <= 1 else weight/100
        total_equity = self._total_equity(row)
        value = total_equity * weight
        shares = self.adjust_value(date, price, value, symbol, tlog, row)
        return shares

    def print_holdings(self, date, row):
        """ print snapshot of portfolio holding and values """
        # 2010-02-01 SPY: 54 TLT: 59 GLD:  9 cash:    84.20 total:  9,872.30
        print(date.strftime('%Y-%m-%d'), end=' ')
        for symbol, shares in pf.TradeLog._share_dict.items():
            print('{}:{:3}'.format(symbol, shares), end=' ')
        print('cash: {:8,.2f}'.format(pf.TradeLog._cash), end=' ')
        print('total: {:9,.2f}'.format(self._total_equity(row)))

    def record_daily_balance(self, date, row):
        """ append to daily balance list """
        # calculate daily balance values: date, high, low, close, shares, cash
        total_equity = self._total_equity(row)
        shares = 0
        for _, value in pf.TradeLog._share_dict.items():
            shares += value
        t = (date, total_equity, total_equity, total_equity, shares, pf.TradeLog._cash)
        self._l.append(t)

    def get_logs(self, tlogs):
        """ return raw tradelog, tradelog, and daily balance log """
        rlogs = pd.Series(dtype=object)
        for symbol in self._symbols:
            rlogs[symbol] = tlogs[symbol].get_log_raw()
            tlogs[symbol] = tlogs[symbol].get_log(merge_trades=False)
        rlog = pd.concat([r for r in rlogs]).sort_values(['date', 'entry_exit'],
                         ignore_index=True)
        tlog = pd.concat([t for t in tlogs]).sort_values(['entry_date', 'exit_date'],
                         ignore_index=True)

        dbal = pf.DailyBal()
        dbal._l = self._l
        dbal = dbal.get_log(tlog)

        return rlog, tlog, dbal

