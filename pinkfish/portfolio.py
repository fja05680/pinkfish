"""
Portfolio backtesting.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn

import pinkfish as pf


class Portfolio:
    """
    A portfolio or collection of securities.

    Methods
    -------
     - fetch_timeseries()  
       Read time series data for symbols.

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
                         use_cache=True, use_adj=True):
        """
        Read time series data for symbols.

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
            ['open', 'high', 'low', 'close']).
        use_cache: bool, optional
            True to use data cache.  False to retrieve from the
            internet (default is True).
        use_adj : bool, optional
            True to adjust prices for dividends and splits
            (default is False).

        Returns
        -------
        pd.DataFrame
            The timeseries of the symbols.
        """
        for i, symbol in enumerate(symbols):

            if i == 0:
                ts = pf.fetch_timeseries(symbol, use_cache=use_cache)
                ts = pf.select_tradeperiod(ts, start, end, use_adj=use_adj)
                self._add_symbol_columns(ts, symbol, ts, fields)
                ts.drop(columns=['open', 'high', 'low', 'close', 'volume', 'adj_close'],
                        inplace=True)
            else:
                # Add another symbol.
                _ts = pf.fetch_timeseries(symbol, use_cache=use_cache)
                _ts = pf.select_tradeperiod(_ts, start, end, use_adj=use_adj)
                self._add_symbol_columns(ts, symbol, _ts, fields)

        self.symbols = symbols
        return ts

    def add_technical_indicator(self, ts, ta_func, ta_param, output_column_suffix,
                                input_column_suffix='close'):
        """
        Add a technical indicator for each symbol in the portfolio.

        A new column will be added for each symbol.  The name of the
        new column will be the symbol name, an underscore, and the
        `output_column_suffix`.  For example, 'SPY_MA30' is the symbol
        SPY with `output_column_suffix` equal to MA30.

        ta_func is a wrapper for a technical analysis function.  The
        actual technical analysis function could be from ta-lib,
        pandas, pinkfish indicator, or a custom user function.
        ta_param is used to pass 1 parameter to the ta_func.  Other
        parameters could be passed to the technical indicator within
        ta_func.  If you need to mass more than 1 paramters to ta_func,
        you could make ta_param a dict.

        Parameters
        ----------
        ts : pd.DataFrame
            The timeseries of the portfolio.
        ta_func : function
            A wrapper for a technical analysis function.
        ta_param : object
            The parameter for ta_func (typically an int).
        output_column_suffix : str
            Output column suffix to use for technical indicator. 
        input_column_suffix : str, {'close', 'open', 'high', 'low'}
            Input column suffix to use for price
            (default is 'close').

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
        >>>     self.ts, ta_func =_period_high, ta_param=self.period,
        >>>     output_column_suffix='period_high'+str(self.period),
        >>>     input_column_suffix='close')
        """
        for symbol in self.symbols:
            input_column = symbol + '_' + input_column_suffix
            output_column = symbol + '_' + output_column_suffix
            ts[output_column] = ta_func(ts, ta_param, input_column)
        return ts

    def calendar(self, ts):
        """
        Add calendar columns.
        """
        return pf.calendar(ts)

    def finalize_timeseries(self, ts, start):
        """
        Finalize timeseries.
        """
        return pf.finalize_timeseries(ts, start)

    ####################################################################
    # GET PRICES (get_price, get_prices)
    
    def get_price(self, row, symbol, field='close'):
        """
        Return price given row, symbol, and field.

        Parameters
        ----------
        row : pd.Series
            The row of data from the timeseries of the portfolio.
        symbol : str
            The symbol for a security.
        field : str, optional {'close', 'open', 'high', 'low'}
            The price field (default is 'close').

        Returns
        -------
        price : float
            The current price.
        
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

    def get_prices(self, row, fields=['open', 'high', 'low', 'close']):
        """
        Return dict of prices for all symbols given row and fields.

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
            The price indexed by symbol and field.
        """
        d = {}
        for symbol in self.symbols:
            d[symbol] = {}
            for field in fields:
                value = self.get_price(row, symbol, field)
                d[symbol][field] = value
        return d

    ####################################################################
    # ADJUST POSITION (adjust_shares, adjust_value, adjust_percent, print_holdings)

    def _share_value(self, row):
        """
        Return total share value in portfolio.
        """
        value = 0
        for symbol, tlog in pf.TradeLog.instance.items():
            close = self.get_price(row, symbol)
            value += tlog.share_value(close)
        return value

    def _total_value(self, row):
        """
        Return total_value = share_value +  cash (if cash > 0).
        """
        total_value = self._share_value(row)
        if pf.TradeLog.cash > 0:
            total_value += pf.TradeLog.cash
        return total_value

    def _equity(self, row):
        """
        Return equity = total_value - loan (loan is negative cash)
        """
        equity = self._total_value(row)
        if pf.TradeLog.cash < 0:
            equity += pf.TradeLog.cash
        return equity

    def _leverage(self, row):
        """
        Return the leverage factor of the position.
        """
        return self._total_value(row) / self._equity(row)

    def _total_funds(self, row):
        """
        Return total account funds for trading.
        """
        return self._equity(row) * pf.TradeLog.margin

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
        tlog = pf.TradeLog.instance[symbol]
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

    def share_percent(self, row, symbol):
        """
        Return share value of symbol as a percentage of `total_funds`.

        Parameters
        ----------
        row : pd.Series
            A row of data from the timeseries of the portfolio.
        symbol : str
            The symbol for a security.

        Returns
        -------
        float
            The share value as a percent.
        """
        close = self.get_price(row, symbol)
        tlog = pf.TradeLog.instance[symbol]
        value = tlog.share_value(close)
        return value / self._total_funds(row) * 100

    def _calc_buying_power(self, row):
        """
        Return the buying power.
        """
        buying_power = (pf.TradeLog.cash * pf.TradeLog.margin
                      + self._share_value(row) * (pf.TradeLog.margin -1))
        return buying_power

    def _adjust_shares(self, date, price, shares, symbol, row, direction):
        """
        Adjust shares.
        """
        tlog = pf.TradeLog.instance[symbol]
        pf.TradeLog.buying_power = self._calc_buying_power(row)
        shares = tlog.adjust_shares(date, price, shares, direction)
        pf.TradeLog.buying_power = None
        return shares

    def _adjust_value(self, date, price, value, symbol, row, direction):
        """
        Adjust value.
        """
        total_funds = self._total_funds(row)
        shares = int(min(total_funds, value) / price)
        shares = self._adjust_shares(date, price, shares, symbol, row, direction)
        return shares

    def adjust_percent(self, date, price, weight, symbol, row,
                       direction=pf.Direction.LONG):
        """
        Adjust symbol to a specified weight (percent) of portfolio.

        Parameters
        ----------
        date : str
            The current date.
        price : float
            The current price of the security.
        weight : float
            The requested weight for the symbol.
        symbol : str
            The symbol for a security.
        row : pd.Series
            A row of data from the timeseries of the portfolio.
        direction : pf.Direction, optional
            The direction of the trade (default is `pf.Direction.LONG`).

        Returns
        -------
        int
            The number of shares bought or sold.
        """
        weight = weight if weight <= 1 else weight/100
        total_funds = self._total_funds(row)
        value = total_funds * weight
        shares = self._adjust_value(date, price, value, symbol, row, direction)
        return shares

    def adjust_percents(self, date, prices, weights, row, directions=None):
        """
        Adjust symbols to a specified weight (percent) of portfolio.

        This function assumes all positions are LONG and weights
        is given for all symbols in the portfolio.

        The ordering of the prices and weights dicts are unimportant.
        They are both indexed by the symbol.

        Parameters
        ----------
        date : str
            The current date.
        prices : dict of floats
            Dict of key value pair of symbol:price.
        weights : dict of floats
            Dict of key value pair of symbol:weight.
        row : pd.Series
            A row of data from the timeseries of the portfolio.
        directions : dict of pf.Direction, optional
            The direction of the trades (default is None, which implies
            that all positions are `pf.Direction.LONG`).

        Returns
        -------
        w : dict of floats
            Dict of key value pair of symbol:weight.
        """
        w = {}

        # Get current weights
        for symbol in self.symbols:
            w[symbol] = self.share_percent(row, symbol)
        
        # If direction is None, this set all to pf.Direction.LONG
        if directions is None:
            directions = {symbol:pf.Direction.LONG for symbol in self.symbols}

        # Reverse sort by weights.  We want current positions first so that
        # if they need to reduced or closed out, then cash is freed for
        # other symbols.
        w = pf.sort_dict(w, reverse=True)

        # Update weights with new values.
        w.update(weights)
        
        # Call adjust_percents() for each symbol.
        for symbol in self.symbols:
            price = prices[symbol]
            weight = w[symbol]
            direction = directions[symbol]
            self.adjust_percent(date, price, weight, symbol, row, direction)
        return w

    def print_holdings(self, date, row):
        """
        Print snapshot of portfolio holding and values.

        Includes all symbols regardless of whether a symbol has shares
        currently allocated to it.

        Parameters
        ----------
        date : str
            The current date.
        row : pd.Series
            A row of data from the timeseries of the portfolio.

        Returns
        -------
        None
        """

        # 2010-02-01 SPY: 54 TLT: 59 GLD:  9 cash:    84.20 total:  9,872.30
        print(date.strftime('%Y-%m-%d'), end=' ')
        for symbol, tlog in pf.TradeLog.instance.items():
            print('{}:{:3}'.format(symbol, tlog.shares), end=' ')
        print('cash: {:8,.2f}'.format(pf.TradeLog.cash), end=' ')
        print('total: {:9,.2f}'.format(self._equity(row)))

    ####################################################################
    # LOGS (init_trade_logs, record_daily_balance, get_logs)

    def init_trade_logs(self, ts, capital, margin=pf.Margin.CASH):
        """
        Add a trade log for each symbol.

        Parameters
        ----------
        ts : pd.DataFrame
            The timeseries of the portfolio.
        capital : int
            The amount of money available for trading.
        margin : float, optional
            Margin percent (default is pf.Margin.CASH)

        Returns
        -------
        None
        """
        pf.TradeLog.cash = capital
        pf.TradeLog.margin = margin
        pf.TradeLog.seq_num = 0
        pf.TradeLog.instance.clear()

        self._ts = ts
        for symbol in self.symbols:
            pf.TradeLog(symbol, False)

    def record_daily_balance(self, date, row):
        """
        Append to daily balance list.
        
        The portfolio version of this function uses closing values
        for the daily high, low, and close. 

        Parameters
        ----------
        date : str
            The current date.
        row : pd.Series
            A row of data from the timeseries of the portfolio.

        Returns
        -------
        None
        """

        # calculate daily balance values: date, high, low, close,
        # shares, cash
        equity = self._equity(row)
        leverage = self._leverage(row)
        shares = 0
        for tlog in pf.TradeLog.instance.values():
            shares += tlog.shares
        t = (date, equity, equity, equity, shares,
             pf.TradeLog.cash, leverage)
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

    ####################################################################
    # PERFORMANCE ANALYSIS (performance_per_symbol, correlation_map)

    def performance_per_symbol(self, weights):
        """
        Returns performance per symbol data, also plots performance.

        Parameters
        ----------
        weights : dict of floats
            A dictionary of weights with symbol as key.

        Returns
        -------
        df : pd.DataFrame
            The dataframe contains performance for each symbol in the
            portfolio.
        """

        def _weight(row, weights):
            return weights[row.name]

        def _currency(row):
            return pf.currency(row['cumul_total'])

        def _plot(df):
            df = df[:-1]
            # Make new figure and set the size.
            fig = plt.figure(figsize=(12, 8))
            axes = fig.add_subplot(111, ylabel='Percentages')
            axes.set_title('Performance by Symbol')
            df.plot(kind='bar', ax=axes)
            axes.set_xticklabels(df.index, rotation=60)
            plt.legend(loc='best')

        # Convert dict to series.
        s = pd.Series(dtype='object')
        for symbol, tlog in pf.TradeLog.instance.items():
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
        new_row = pd.Series(name='TOTAL',
            data={'cumul_total':df['cumul_total'].sum(),
                  'pct_cumul_total': 1.00, 'weight': 1.00,
                  'relative_performance': 1.00})
        df = df.append(new_row, ignore_index=False)
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
            which implies all days.

        Returns
        -------
        df : pd.DataFrame
            The dataframe contains the correlation data for each symbol
            in the portfolio.
        """

        # Filter coloumn names for ''_close''; drop '_close' suffix.
        df = ts.filter(regex='_close')
        df.columns = df.columns.str.strip('_close')

        # Default is all days.
        if days is None:
            days = 0;
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
        seaborn.heatmap(df, cmap='RdYlGn', vmax=1.0, vmin=-1.0 ,
                        mask = mask, linewidths=2.5)
        plt.yticks(rotation=0)
        plt.xticks(rotation=90)
        return df
