"""
Portfolio backtesting.
"""

from functools import wraps

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn

from pinkfish.pfcalendar import calendar
from pinkfish.fetch import (
    fetch_timeseries,
    select_tradeperiod,
    finalize_timeseries
)
import pinkfish.pfstatistics as pfstatistics
import pinkfish.trade as trade
import pinkfish.utility as utility


def technical_indicator(symbols, output_column_suffix,
                        input_column_suffix='close'):
    """
    Decorator for adding a technical indicator to portfolio symbols.

    A new column will be added for each symbol.  The name of the
    new column will be the symbol name, an underscore, and the
    `output_column_suffix`.  For example, 'SPY_MA30' is the symbol
    SPY with `output_column_suffix` equal to MA30.

    `func` is a wrapper for a technical analysis function.  The
    actual technical analysis function could be from ta-lib,
    pandas, pinkfish indicator, or a custom user function.

    'func' must have the positional argument `ts` and keyword argument
    `input_column`.  'ts` is passed in, but input_column (args[1]) is
    assigned in the wrapper before `func` is called.

    Parameters
    ----------
    symbols : list
        The symbols that constitute the portfolio.
    output_column_suffix : str
        Output column suffix to use for technical indicator.
    input_column_suffix : str, {'open', 'high', 'low', 'close'}
        Input column suffix to use for price (default is 'close').

    Returns
    -------
    decorator : function
        A wrapper that adds technical indicators to portfolio
        symbols.

    Examples
    --------
    >>> # Technical indicator: volatility.
    >>> @pf.technical_indicator(symbols, 'vola', 'close')
    >>> def _volatility(ts, input_column=None):
    ...     return pf.VOLATILITY(ts, price=input_column)
    >>> ts = _volatility(ts)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            assert len(args) >= 1, f'func requires at least 1 args, detected {len(args)}'
            assert type(args[0]) == pd.DataFrame, f'args[0] not a pd.DataFrame'
            ts = args[0]
            indicator_column = {}
            for symbol in symbols:
                input_column = symbol + '_' + input_column_suffix
                output_column = symbol + '_' + output_column_suffix
                kwargs['input_column'] = input_column
                indicator_column[output_column] = func(*args, **kwargs)
            
            # Join all the symbol columns to the original DataFrame using pd.concat
            ts = pd.concat([ts, pd.DataFrame(indicator_column)], axis=1)
            return ts
        return wrapper
    return decorator


class Portfolio:
    """
    A portfolio or collection of securities.

    Methods
    -------
     - fetch_timeseries()
       Get time series data for symbols.

     - add_technical_indicator()
       Add a technical indicator for each symbol in the portfolio.

     - calendar()
       Add calendar columns.

     - finalize_timeseries()
       Finalize timeseries.

     - get_price()
       Return price given row, symbol, and field.

     - get_prices()
       Return dict of prices for all symbols given row and fields.

     - shares()
       Return number of shares for given symbol in portfolio.

     - positions
       Gets the active symbols in portfolio as a list.

     - share_percent()
       Return share value of symbol as a percentage of `total_funds`.

     - adjust_percent()
       Adjust symbol to a specified weight (percent) of portfolio.

     - print_holdings()
       Print snapshot of portfolio holding and values.

     - init_trade_logs()
       Add a trade log for each symbol.

     - record_daily_balance()
       Append to daily balance list.

     - get_logs()
       Return raw tradelog, tradelog, and daily balance log.

     - performance_per_symbol()
       Returns performance per symbol data, also plots performance.

     - correlation_map()
       Show correlation map between symbols.
    """

    def __init__(self):
        """
        Initialize instance variables.

        Attributes
        ----------
        _l : list of tuples
            The list of daily balance tuples.
        _ts : pd.DataFrame
            The timeseries of the portfolio.
        symbols : list
            The symbols that constitute the portfolio.
        """
        self._l = []
        self._ts = None
        self.symbols = []

    ####################################################################
    # TIMESERIES (fetch, add_technical_indicator, calender, finalize)

    def _add_symbol_columns(self, ts, symbol, symbol_ts, fields):
        """
        Add column with field suffix for symbol, i.e. SPY_close.
        """
        for field in fields:
            column = symbol + '_' + field
            ts[column] = symbol_ts[field]
        return ts

    def fetch_timeseries(self, symbols, start, end,
                         fields=['open', 'high', 'low', 'close'],
                         dir_name='symbol-cache',
                         use_cache=True, use_adj=True,
                         use_continuous_calendar=False,
                         force_stock_market_calendar=False,
                         check_fields=['close']):
        """
        Fetch time series data for symbols.

        Parameters
        ----------
        symbols : list
            The list of symbols to fetch timeseries.
        start : datetime.datetime
            The desired start date for the strategy.
        end : datetime.datetime
            The desired end date for the strategy.
        fields : list, optional
            The list of fields to use for each symbol (default is
            ['open', 'high', 'low', 'close']).  List must include 
            'close' - will be added if not already in list.
        dir_name : str, optional
            The leaf data dir name (default is 'symbol-cache').
        use_cache: bool, optional
            True to use data cache.  False to retrieve from the
            internet (default is True).
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
            to False (default is False).
        check_fields : list of str, optional {'open', 'high', 'low',
            'close', 'adj_close'}
            Fields to check for for NaN values.  If a NaN value is found
            for one of these fields, that row is dropped
            (default is ['close']).

        Returns
        -------
        pd.DataFrame
            The timeseries of the symbols.
        """
        if 'close' not in fields:
            fields.append('close')

        symbols = list(set(symbols))
        for i, symbol in enumerate(symbols):

            if i == 0:
                ts = fetch_timeseries(symbol, dir_name=dir_name, use_cache=use_cache)
                ts = select_tradeperiod(ts, start, end, use_adj=use_adj,
                                        use_continuous_calendar=use_continuous_calendar,
                                        force_stock_market_calendar=force_stock_market_calendar,
                                        check_fields=check_fields)
                self._add_symbol_columns(ts, symbol, ts, fields)
                ts.drop(columns=['open', 'high', 'low', 'close', 'adj_close', 'volume'],
                        inplace=True)
            else:
                # Add another symbol.
                _ts = fetch_timeseries(symbol, dir_name=dir_name, use_cache=use_cache)
                _ts = select_tradeperiod(_ts, start, end, use_adj=use_adj,
                                         use_continuous_calendar=use_continuous_calendar,
                                         force_stock_market_calendar=force_stock_market_calendar,
                                         check_fields=check_fields)
                self._add_symbol_columns(ts, symbol, _ts, fields)

        ts.dropna(inplace=True)
        self.symbols = symbols
        return ts

    def add_technical_indicator(self, ts, ta_func, ta_param, output_column_suffix,
                                input_column_suffix='close'):
        """
        Add a technical indicator for each symbol in the portfolio.
        
        (Deprecated - use `technical_indicator` decorator instead)

        A new column will be added for each symbol.  The name of the
        new column will be the symbol name, an underscore, and the
        `output_column_suffix`.  For example, 'SPY_MA30' is the symbol
        SPY with `output_column_suffix` equal to MA30.

        `ta_func` is a wrapper for a technical analysis function.  The
        actual technical analysis function could be from ta-lib,
        pandas, pinkfish indicator, or a custom user function.
        `ta_param` is used to pass 1 parameter to `ta_func`.  Other
        parameters could be passed to the technical indicator within
        `ta_func`.  If you need to mass more than 1 paramters to
        `ta_func`, you could make `ta_param` a dict.

        Parameters
        ----------
        ts : pd.DataFrame
            The timeseries of the portfolio.
        ta_func : function
            A wrapper for a technical analysis function.
        ta_param : object
            The parameter for `ta_func` (typically an int).
        output_column_suffix : str
            Output column suffix to use for technical indicator.
        input_column_suffix : str, {'open', 'high', 'low', 'close'}
            Input column suffix to use for price (default is 'close').

        Returns
        -------
        ts : pd.DataFrame
            Timeseries with new column for technical indicator.

        Examples
        --------
        >>> # Add technical indicator: X day high
        >>> def period_high(ts, ta_param, input_column):
        >>>     return pd.Series(ts[input_column]).rolling(ta_param).max()

        >>> ts = portfolio.add_technical_indicator(
        >>>     ts, ta_func=_period_high, ta_param=period,
        >>>     output_column_suffix='period_high'+str(period),
        >>>     input_column_suffix='close')
        """
        indicator_column = {}
        for symbol in self.symbols:
            input_column = symbol + '_' + input_column_suffix
            output_column = symbol + '_' + output_column_suffix
            ts[output_column] = ta_func(ts, ta_param, input_column)
            indicator_column[output_column] = ta_func(ts, ta_param, input_column)
            
        # Join all the symbol columns to the original DataFrame using pd.concat
        ts = pd.concat([ts, pd.DataFrame(indicator_column)], axis=1)
        return ts

    def calendar(self, ts, columns=None):
        """
        Add calendar columns to a timeseries.

        Parameters
        ----------
        ts : pd.DataFrame
            The timeseries of a symbol.
        columns: list of str, optional
            Specify the name of the columns to keep
            (default is None, which implies keeping all columns).

        Returns
        -------
        pd.DataFrame
            The timeseries with calendar columns added.
        """
        return calendar(ts, columns)

    def finalize_timeseries(self, ts, start, dropna=True):
        """
        Finalize timeseries.

        Drop all rows that have nan column values.  Set timeseries to begin
        at start.

        Parameters
        ----------
        ts : pd.DataFrame
            The timeseries of a symbol.
        start : datetime.datetime
            The start date for backtest.
        dropna : bool, optional
            Drop rows that have a NaN value in one of it's columns
            (default is True).

        Returns
        -------
        datetime.datetime
            The start date.
        pd.DataFrame
            The timeseries of a symbol.
        """
        return finalize_timeseries(ts, start, dropna=dropna)

    ####################################################################
    # GET PRICES (get_price, get_prices)

    def get_column_value(self, row, symbol, field='close'):
        """
        Return column value given row, symbol, and field.

        Parameters
        ----------
        row : pd.Series
            The row of data from the timeseries of the portfolio.
        symbol : str
            The symbol for a security.
        field : str, optional {'open', 'high', 'low', 'close'}
            The price field to use (default is 'close').

        Returns
        -------
        price : float
            The current column value.
        """
        symbol += '_' + field
        try:
            price = getattr(row, symbol)
        except AttributeError:
            # This method is slower, but handles column names that
            # don't conform to variable name rules, and thus aren't
            # attributes.
            date = row.Index.to_pydatetime()
            price = self._ts.loc[date, symbol]
        return price
        
    get_price = get_column_value
    """
    method : get_price is a function reference to get_column_value, i.e. an alias.
    """

    def get_column_values(self, row, fields=['open', 'high', 'low', 'close']):
        """
        Return dict of column values for all symbols given row and fields.

        Parameters
        ----------
        row : pd.Series
            A row of data from the timeseries of the portfolio.
        fields : list, optional
            The list of fields to use for each symbol (default is
            ['open', 'high', 'low', 'close']).

        Returns
        -------
        d : dict of floats
            The column value indexed by symbol and field.
        """
        d = {}
        for symbol in self.symbols:
            d[symbol] = {}
            for field in fields:
                value = self.get_column_value(row, symbol, field)
                d[symbol][field] = value
        return d
        
    get_prices = get_column_values
    """
    method : get_prices is a function reference to get_column_values, i.e. an alias.
    """

    ####################################################################
    # ADJUST POSITION (adjust_shares, adjust_value, adjust_percent, print_holdings)

    def _share_value(self, row, field):
        """
        Return total share value in portfolio.
        """
        value = 0
        for symbol, tlog in trade.TradeLog.instance.items():
            price = self.get_price(row, symbol, field)
            value += tlog.share_value(price)
        return value

    def _total_value(self, row, field):
        """
        Return total_value = share_value + cash (if cash > 0).
        """
        total_value = self._share_value(row, field)
        if trade.TradeLog.cash > 0:
            total_value += trade.TradeLog.cash
        return total_value

    def _equity(self, row, field):
        """
        Return equity = total_value - loan (loan is negative cash)
        """
        equity = self._total_value(row, field)
        if trade.TradeLog.cash < 0:
            equity += trade.TradeLog.cash
        return equity

    def _leverage(self, row, field):
        """
        Return the leverage factor of the position.
        """
        return self._total_value(row, field) / self._equity(row, field)

    def _total_funds(self, row, field):
        """
        Return total account funds for trading.
        """
        return self._equity(row, field) * trade.TradeLog.margin

    def shares(self, symbol):
        """
        Return number of shares for given symbol in portfolio.

        Parameters
        ----------
        symbol : str
            The symbol for a security.

        Returns
        -------
        tlog.shares : int
            The number of shares for a given symbol.
        """
        tlog = trade.TradeLog.instance[symbol]
        return tlog.shares

    @property
    def positions(self):
        """
        Return the active symbols in portfolio as a list.

        This returns only those symbols that currently have shares
        allocated to them, either long or short.

        Parameters
        ----------
        None

        Returns
        -------
        list of str
            The active symbols in portfolio.
        """
        return [symbol for symbol in self.symbols if self.shares(symbol) > 0]

    def share_percent(self, row, symbol, field):
        """
        Return share value of symbol as a percentage of `total_funds`.

        Parameters
        ----------
        row : pd.Series
            A row of data from the timeseries of the portfolio.
        symbol : str
            The symbol for a security.
        field : str, {'open', 'high', 'low', 'close'}
            The price field to use.

        Returns
        -------
        float
            The share value as a percent.
        """
        price = self.get_price(row, symbol, field)
        tlog = trade.TradeLog.instance[symbol]
        value = tlog.share_value(price)
        return value / self._total_funds(row, field)

    def _calc_buying_power(self, row, field):
        """
        Return the buying power.
        """
        buying_power = (trade.TradeLog.cash * trade.TradeLog.margin
                      + self._share_value(row, field) * (trade.TradeLog.margin -1))
        return buying_power

    def _adjust_shares(self, row, price, shares, symbol, field, direction):
        """
        Adjust shares.
        """
        date = row.Index.to_pydatetime()
        tlog = trade.TradeLog.instance[symbol]
        trade.TradeLog.buying_power = self._calc_buying_power(row, field)
        shares = tlog.adjust_shares(date, price, shares, direction)
        trade.TradeLog.buying_power = None
        return shares

    def _adjust_value(self, row, value, symbol, field, direction):
        """
        Adjust value.
        """
        total_funds = self._total_funds(row, field)
        price = self.get_price(row, symbol, field)
        shares = int(min(total_funds, value) / price)
        shares = self._adjust_shares(row, price, shares, symbol, field, direction)
        return shares

    def adjust_percent(self, row, weight, symbol, field='close',
                       direction=trade.Direction.LONG):
        """
        Adjust symbol to a specified weight (percent) of portfolio.

        Parameters
        ----------
        row : pd.Series
            A row of data from the timeseries of the portfolio.
        weight : float
            The requested weight for the symbol, where 0 <= weight <=1.
        symbol : str
            The symbol for a security.
        field : str, {'open', 'high', 'low', 'close'}
            The price field to use.
        direction : pf.Direction, optional
            The direction of the trade (default is `pf.Direction.LONG`).

        Returns
        -------
        int
            The number of shares bought or sold.
        """
        if not (0 <= weight <= 1):
            raise ValueError(f'weight should be between 0 and 1 (inclusive), but {symbol}={weight}.')

        total_funds = self._total_funds(row, field)
        value = total_funds * weight
        shares = self._adjust_value(row, value, symbol, field, direction)
        return shares

    def adjust_percents(self, row, weights, field='close', directions=None):
        """
        Adjust symbols to a specified weight (percent) of portfolio.

        This function assumes all positions are LONG.  Prices and
        weights are given for all symbols in the portfolio.  The
        ordering of the prices and weights dicts are unimportant.
        They are dicts which are indexed by the symbol.

        Parameters
        ----------
        row : pd.Series
            A row of data from the timeseries of the portfolio.
        weights : dict of floats
            Dict of key value pair of symbol:weight, where 0 <= weight <=1.
        field : str, {'open', 'high', 'low', 'close'}
            The price field to use.
        directions : dict of pf.Direction, optional
            Dict of key value pair of symbol:direction.  The direction
            of the trades (default is None, which implies that all
            positions are long).

        Returns
        -------
        w : dict of floats
            Dict of key value pair of symbol:weight, where 0 <= weight <=1.
        """
        for symbol, weight in weights.items():
            if not (0 <= weight <= 1):
                raise ValueError(f'weights should be between 0 and 1 (inclusive), but {symbol}={weight}')

        w = {}

        # Get current weights
        for symbol in self.symbols:
            w[symbol] = self.share_percent(row, symbol, field)

        # If direction is None, this set all to pf.Direction.LONG
        if directions is None:
            directions = {symbol:trade.Direction.LONG for symbol in self.symbols}

        # We want to sell current positions first to obtain cash. We need to sort
        # the change of the current weight of the position to the new weight of the
        # position and order negative / sell orders first.
        for k, v in w.items():
            w[k] = weights[k] - v
        w = utility.sort_dict(w)

        # Update weights with new values.
        w.update(weights)

        # Call adjust_percent() for each symbol.
        for symbol, weight in w.items():
            direction = directions[symbol]
            self.adjust_percent(row, weight, symbol, field, direction)
        return w

    def print_holdings(self, row, show_percent=False):
        """
        Print snapshot of portfolio holding and values.

        Includes all symbols regardless of whether a symbol has shares
        currently allocated to it.

        Parameters
        ----------
        row : pd.Series
            A row of data from the timeseries of the portfolio.
        show_percent : bool, optional
            Show each holding as a percent instead of shares.
            (default is False).

        Returns
        -------
        None
        """
        date = row.Index.to_pydatetime()
        field = 'close'
        if show_percent:
            # 2007-11-20 SPY:24.1 TLT:24.9 GLD:24.6 QQQ:24.7 cash:  1.6 total: 100.0
            print(date.strftime('%Y-%m-%d'), end=' ')
            total = 0
            for symbol, tlog in trade.TradeLog.instance.items():
                pct = self.share_percent(row, symbol, field)
                total += pct
                print(f'{symbol}:{pct * 100:4,.1f}', end=' ')
            pct = trade.TradeLog.cash / self._equity(row, field)
            total += abs(pct)
            print(f'cash: {pct * 100:4,.1f}', end=' ')
            print(f'total: {total * 100:4,.1f}')
        else:
            # 2010-02-01 SPY: 54 TLT: 59 GLD:  9 cash:    84.20 total:  9,872.30
            print(date.strftime('%Y-%m-%d'), end=' ')
            for symbol, tlog in trade.TradeLog.instance.items():
                print(f'{symbol}:{tlog.shares:3}', end=' ')
            print(f'cash: {trade.TradeLog.cash:8,.2f}', end=' ')
            print(f'total: {self._equity(row, field):9,.2f}')

    ####################################################################
    # LOGS (init_trade_logs, record_daily_balance, get_logs)

    def init_trade_logs(self, ts):
        """
        Add a trade log for each symbol.

        Parameters
        ----------
        ts : pd.DataFrame
            The timeseries of the portfolio.

        Returns
        -------
        None
        """
        trade.TradeLog.seq_num = 0
        trade.TradeLog.instance.clear()

        self._ts = ts
        for symbol in self.symbols:
            trade.TradeLog(symbol, False)

    def record_daily_balance(self, row):
        """
        Append to daily balance list.

        The portfolio version of this function uses closing values
        for the daily high, low, and close.

        Parameters
        ----------
        row : pd.Series
            A row of data from the timeseries of the portfolio.

        Returns
        -------
        None
        """

        # calculate daily balance values: date, high, low, close,
        # shares, cash
        date = row.Index.to_pydatetime()
        field = 'close'
        equity = self._equity(row, field)
        leverage = self._leverage(row, field)
        shares = 0
        for tlog in trade.TradeLog.instance.values():
            shares += tlog.shares
        t = (date, equity, equity, equity, shares,
             trade.TradeLog.cash, leverage)
        self._l.append(t)

    def get_logs(self):
        """
        Return raw tradelog, tradelog, and daily balance log.

        Parameters
        ----------
        None

        Returns
        -------
        rlog : pd.DataFrame
            The raw trade log.
        tlog : pd.DataFrame
            The trade log.
        dbal : pd.DataFrame
            The daily balance log.
        """
        tlogs = []; rlogs = []
        for tlog in trade.TradeLog.instance.values():
            rlogs.append(tlog.get_log_raw())
            tlogs.append(tlog.get_log(merge_trades=False))
        
        rlogs_non_empty = [r for r in rlogs if not r.empty]
        rlog = pd.concat(rlogs_non_empty).sort_values(['seq_num'])
        
        tlogs_non_empty = [t for t in tlogs if not t.empty]
        tlog = pd.concat(tlogs_non_empty).sort_values(['entry_date', 'exit_date'])

        tlog['cumul_total'] = tlog['pl_cash'].cumsum()

        dbal = trade.DailyBal()
        dbal._l = self._l
        dbal = dbal.get_log(tlog)
        return rlog, tlog, dbal

    ####################################################################
    # PERFORMANCE ANALYSIS (performance_per_symbol, correlation_map)

    def performance_per_symbol(self, weights):
        """
        Returns performance per symbol data, also plots performance.

        Parameters
        ----------
        weights : dict of floats
            A dictionary of weights with symbol as key, where 0 <= weight <=1.

        Returns
        -------
        df : pd.DataFrame
            The dataframe contains performance for each symbol in the
            portfolio.
        """

        def _weight(row, weights):
            return weights[row.name]

        def _currency(row):
            return pfstatistics.currency(row['cumul_total'])

        def _plot(df):
            df = df[:-1]
            # Make new figure and set the size.
            fig = plt.figure(figsize=(12, 8))
            axes = fig.add_subplot(111, ylabel='Percentages')
            axes.set_title('Performance by Symbol')
            df.plot(kind='bar', ax=axes)
            axes.set_xticklabels(df.index, rotation=60)
            plt.legend(loc='best')

        for weight in weights.values():
            if not (0 <= weight <= 1):
                raise ValueError('weights should be between 0 and 1 (inclusive).')

        # Convert dict to series.
        s = pd.Series(dtype='object')
        for symbol, tlog in trade.TradeLog.instance.items():
            s[symbol] = tlog.cumul_total
        # Convert series to dataframe.
        df = pd.DataFrame(s.values, index=s.index, columns=['cumul_total'])
        # Add weight column.
        df['weight'] = df.apply(_weight, weights=weights, axis=1)
        # Add percent column.
        df['pct_cumul_total'] = df['cumul_total'] / df['cumul_total'].sum()
        # Add relative preformance.
        df['relative_performance'] = df['pct_cumul_total'] / df['weight']
        # Add TOTAL row.
        data = {'cumul_total':df['cumul_total'].sum(),
                'pct_cumul_total': 1.00, 'weight': 1.00,
                'relative_performance': 1.00}
        index = ['TOTAL']
        new_row = pd.DataFrame(data=data, index=index)
        df = pd.concat([df, new_row])
        # Format as currency.
        df['cumul_total'] = df.apply(_currency, axis=1)
        # Plot bar graph of performance.
        _plot(df)
        return df

    def correlation_map(self, ts, method='log', days=None):
        """
        Show correlation map between symbols.

        Parameters
        ----------
        ts : pd.DataFrame
            The timeseries of the portfolio.
        method : str, optional {'price', 'log', 'returns'}
            Analysis done based on specified method (default is 'log').
        days : int
            How many days to use for correlation (default is None,
            which implies all days).

        Returns
        -------
        df : pd.DataFrame
            The dataframe contains the correlation data for each symbol
            in the portfolio.
        """

        # Filter coloumn names for ''_close''; remove '_close' suffix.
        df = ts.filter(regex='_close')
        df.columns = df.columns.str.strip('_close')

        # Default is all days.
        if days is None:
            days = 0
        df = df[-days:]

        if method == 'price':
            pass
        elif method == 'log':
            df = np.log(df.pct_change()+1)
        elif method == 'returns':
            df = df.pct_change()

        df = df.corr(method='pearson')
        # Reset symbol as index (rather than 0-X).
        df.head().reset_index()
        # Take the bottom triangle since it repeats itself.
        mask = np.zeros_like(df)
        mask[np.triu_indices_from(mask)] = True
        # Generate plot.
        seaborn.heatmap(df, cmap='RdYlGn', vmax=1.0, vmin=-1.0,
                        mask=mask, linewidths=2.5)
        plt.yticks(rotation=0)
        plt.xticks(rotation=90)
        return df
