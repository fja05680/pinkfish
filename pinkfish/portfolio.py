"""
portfolio
---------
Portfolio backtesting
"""

import pandas as pd
import pinkfish as pf


class Portfolio:

    def __init__(self):
        self._l = []  # list of daily balance tuples
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

    def _total_equity(self, row):
        """ return the total equity in portfolio """
        total_equity = pf.TradeLog.cash
        for symbol, tlog in pf.TradeLog.instance.items():
            close = getattr(row, symbol + '_close')
            total_equity += tlog._total_equity(close) - pf.TradeLog.cash
        return total_equity

    def adjust_shares(self, date, price, shares, symbol, direction=pf.Direction.LONG):
        tlog = pf.TradeLog.instance[symbol]
        shares = tlog.adjust_shares(date, price, shares, direction)
        return shares

    def adjust_value(self, date, price, value, symbol, row, direction=pf.Direction.LONG):
        total_equity = self._total_equity(row)
        shares = int(min(total_equity, value) / price)
        shares = self.adjust_shares(date, price, shares, symbol, direction)
        return shares

    def adjust_percent(self, date, price, weight, symbol, row, direction=pf.Direction.LONG):
        weight = weight if weight <= 1 else weight/100
        total_equity = self._total_equity(row)
        value = total_equity * weight
        shares = self.adjust_value(date, price, value, symbol, row, direction)
        return shares

    def print_holdings(self, date, row):
        """ print snapshot of portfolio holding and values """
        # 2010-02-01 SPY: 54 TLT: 59 GLD:  9 cash:    84.20 total:  9,872.30
        print(date.strftime('%Y-%m-%d'), end=' ')
        for symbol, tlog in pf.TradeLog.instance.items():
            print('{}:{:3}'.format(symbol, tlog.shares), end=' ')
        print('cash: {:8,.2f}'.format(pf.TradeLog.cash), end=' ')
        print('total: {:9,.2f}'.format(self._total_equity(row)))

    #####################################################################
    # LOGS (init_trade_logs, record_daily_balance, get_logs)

    def init_trade_logs(self, ts, capital):
        """ add a trade log for each symbol """
        pf.TradeLog.cash = capital
        for symbol in self.symbols:
            pf.TradeLog(symbol, False)

    def record_daily_balance(self, date, row):
        """ append to daily balance list """
        # calculate daily balance values: date, high, low, close, shares, cash
        total_equity = self._total_equity(row)
        shares = 0
        for tlog in pf.TradeLog.instance.values():
            shares += tlog.shares
        t = (date, total_equity, total_equity, total_equity, shares, pf.TradeLog.cash)
        self._l.append(t)

    def get_logs(self):
        """ return raw tradelog, tradelog, and daily balance log """
        tlogs = []; rlogs = []
        for tlog in pf.TradeLog.instance.values():
            rlogs.append(tlog.get_log_raw())
            tlogs.append(tlog.get_log(merge_trades=False))
        rlog = pd.concat([r for r in rlogs]).sort_values(['date', 'entry_exit'],
                         ignore_index=True)
        tlog = pd.concat([t for t in tlogs]).sort_values(['entry_date', 'exit_date'],
                         ignore_index=True)
        tlog['cumul_total'] = tlog['pl_cash'].cumsum()

        dbal = pf.DailyBal()
        dbal._l = self._l
        dbal = dbal.get_log(tlog)
        return rlog, tlog, dbal

