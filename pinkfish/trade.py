"""
Trading agent.
"""

import pandas as pd


class Direction:
    """
    The direction of the trade.  Either LONG or SHORT.
    """
    LONG, SHORT = ['LONG', 'SHRT']

class Margin:
    """
    The type of margin.  CASH, STANDARD, or PATTERN_DAY_TRADER.
    This is actually the inverse margin, i.e. account leverage.
    """
    CASH, STANDARD, PATTERN_DAY_TRADER = [1, 2, 4]


########################################################################
# TRADE LOG - each symbol has it's own trade log

class TradeLog:
    """
    The trade log for each symbol.
    """

    cash = 0
    """
    int : Current cash, entire portfolio.
    """
    multiplier = 1
    """
    int : Applied to profit calculation.  Used only with futures.
    """
    margin = Margin.CASH
    """
    float : Margin percent.
    """
    buying_power = None
    """
    float : Buying power for Portfolio class.
    """
    seq_num = 0
    """
    int : Sequential number used to order trades in Portfolio class.
    """
    instance = {}
    """
    dict of pf.TradeLog : dict (key=symbol) of TradeLog instances used
    in Portfolio class.
    """

    def __init__(self, symbol, reset=True):
        """
        Initialize instance variables.

        Parameters
        ----------
        symbol : str
            The symbol for a security.
        reset : bool, optional
            Use when starting new portfolio construction to clear the
            dict of TradeLog instances (default is True).

        Attributes
        ----------
        symbol : str
            The symbol for a security.
        shares : int
            Number of shares of the symbol.
        direction : pf.Direction
            The direction of the trade, Long or Short.
        ave_entry_price : float
            The average purchase price per share.
        cumul_total : float
            The cumulative total profits (loss).
        _l : list of tuples
            The list of matching entry/exit trade pairs.  This list
            will become the official trade log.
        _raw : list of tuples
            The list of raw trades, either entry or exit.
        open_trades : list
            The list of open trades, i.e. not closed out.
        """
        self.symbol = symbol
        self.shares = 0
        self.direction = None
        self.ave_entry_price = 0
        self.cumul_total = 0
        self._l = []
        self._raw = []
        self._open_trades = []

        if reset:
            TradeLog.seq_num = 0
            TradeLog.instance.clear()
        TradeLog.instance[symbol] = self

    def share_value(self, price):
        """
        Return the total value of shares of the security.

        Parameters
        ----------
        price : float
            The current price of the security.

        Returns
        -------
        value : float
            The share value.
        """
        value = 0
        if self.direction == Direction.LONG:
            value += price*self.shares
        elif self.direction == Direction.SHORT:
            value += (2*self.ave_entry_price-price)*self.shares
        return value
        
    def total_value(self, price):
        """
        Return the total value which is the total share value plus cash.

        Parameters
        ----------
        price : float
            The current price of the security.

        Returns
        -------
        value : float
            The total value.
        """
        total_value = self.share_value(price)
        if TradeLog.cash > 0:
            total_value += TradeLog.cash
        return total_value

    def equity(self, price):
        """
        Return the equity which is the total value minus loan.
        Loan is negative cash.
        """
        equity = self.total_value(price)
        if TradeLog.cash < 0:
            equity += TradeLog.cash
        return equity

    def leverage(self, price):
        """
        Return the leverage factor of the position given current price.
        """
        return self.total_value(price) / self.equity(price)

    def total_funds(self, price):
        """
        Return the total account funds for trading given current price.
        """
        return self.equity(price) * TradeLog.margin

    def share_percent(self, price):
        """
        Return the share value as a percentage of total funds.
        """
        return self.share_value(price) / self.total_funds(price)

    @property
    def num_open_trades(self):
        """
        Return the number of open orders, i.e. not closed out.
        """
        return len(self._open_trades)

    ####################################################################
    # ENTER TRADE (buy, sell_short)

    def calc_buying_power(self, price):
        """
        Calculate buying power.
        """
        buying_power = (TradeLog.cash * TradeLog.margin
                        + self.share_value(price) * (TradeLog.margin -1))
        return buying_power

    def calc_shares(self, price, cash=None):
        """
        Calculate shares using buying power before enter_trade().

        Parameters
        ----------
        price : float
            The current price of the security.
        cash : float, optional
            The requested amount of cash used to buy shares (default
            is None, which implies use all available cash).

        Returns
        -------
        value : float
            The number of shares that can be purchased with requested
            cash amount.
        """

        # Margin should be equal to or greater than 1.
        if TradeLog.margin < 1: TradeLog.margin = 1

        # Calculate buying power.  TradeLog.buying_power may have
        # already been calculated in portfolio.
        if TradeLog.buying_power is not None:
            buying_power = TradeLog.buying_power
        else:
            buying_power = self.calc_buying_power(price)

        # Cash can't exceed buying power.
        if cash is None or cash > buying_power:
            cash = buying_power

        # Cash can't be negative.
        if cash < 0: cash = 0

        # Calculate shares.
        shares = int(cash / price)
        return shares

    def _enter_trade(self, entry_date, entry_price, shares=None, direction=Direction.LONG):
        """
        This is a lower level function that gets called from
        enter_trade() and sell_short().
        """

        max_shares = self.calc_shares(entry_price)
        shares = max_shares if shares is None else min(shares, max_shares)

        if shares == 0:
            return 0

        # Record in raw trade log.
        t = (entry_date, TradeLog.seq_num, entry_price, shares, 'entry', direction, self.symbol)
        self._raw.append(t)
        TradeLog.seq_num += 1

        # Add record to open_trades.
        d = {'entry_date':entry_date, 'entry_price':entry_price, 'qty':shares,
             'direction':direction, 'symbol':self.symbol}
        self._open_trades.append(d)

        # Update direction.
        if self.direction != direction:
            if self.direction is None or self.shares == 0:
                self.direction = direction
            else:
                raise ValueError('not allowed to change direction from {} to {}, '
                                 'this requires shares = 0'
                                 .format(self.direction, direction))

        # Update average entry price and shares.
        self.ave_entry_price = \
            (self.ave_entry_price*self.shares + entry_price*shares) / (self.shares + shares)
        self.shares += shares

        # Update cash.
        TradeLog.cash -= entry_price * shares

        return shares

    def enter_trade(self, entry_date, entry_price, shares=None):
        """
        Enter a trade on the long side.

        Parameters
        ----------
        entry_date : str
            The entry date.
        entry_price : float
            The entry price.
        shares : int, optional
            The number of shares to buy (default is None, which implies
            buy the maximum number of shares possible with available
            buying power).

        Returns
        -------
        int
            The number of shares bought.

        Notes
        -----
        The `buy' alias can be used to call this function for increasing
        or opening a long position.
        """
        return self._enter_trade(entry_date=entry_date,
                                 entry_price=entry_price,
                                 shares=shares,
                                 direction=Direction.LONG)

    buy = enter_trade
    """
    method : buy is a function reference to enter_trade, i.e. an alias.
    """

    def sell_short(self, entry_date, entry_price, shares=None):
        """
        Enter a trade on the short side.

        Parameters
        ----------
        entry_date : str
            The entry date.
        entry_price : float
            The entry price.
        shares : int
            The number of shares to sell short (default in None, which
            implies to sell short the maximum number of shares
            possible).

        Returns
        -------
        int
            The number of shares sold short.
        """
        return self._enter_trade(entry_date=entry_date,
                                 entry_price=entry_price,
                                 shares=shares,
                                 direction=Direction.SHORT)

    ####################################################################
    # EXIT TRADE (sell, buy2cover)

    def _qty_open_trade(self, index):
        """
        Qty of an open trade by index.
        """
        if index >= self.num_open_trades:
            return 0
        return self._open_trades[index]['qty']

    def _exit_trade(self, exit_date, exit_price, shares=None, direction=Direction.LONG):
        """
        Exit a trade.

        Record exit in trade log. return -shares exited.
        shares = None exits all shares
        shares > 0 exits that number of shares
        shares < 0 indicates the number of open_trades to exit
        """
        if shares is None or shares > self.shares:
            shares = self.shares
        elif shares < 0:
            open_trades = -shares
            shares = 0
            for i in range(open_trades):
                shares += self._qty_open_trade(i)

        if shares == 0:
            return 0

        shares_orig = shares

        # Record in raw trade log.
        t = (exit_date, TradeLog.seq_num, exit_price, shares, 'exit', direction, self.symbol)
        self._raw.append(t)
        TradeLog.seq_num += 1

        for i, open_trade in enumerate(self._open_trades[:]):
            entry_date = open_trade['entry_date']
            entry_price = open_trade['entry_price']
            qty = open_trade['qty']

            if direction == Direction.LONG:
                pl_points = exit_price - entry_price
            else:
                pl_points = -(exit_price - entry_price)

            # Calculate exit_shares and pl_cash.
            exit_shares = qty if shares >= qty else shares
            pl_cash = pl_points * exit_shares * TradeLog.multiplier
            self.cumul_total += pl_cash

            # Record in trade log.
            t = (entry_date, entry_price, exit_date, exit_price,
                 pl_points, pl_cash, exit_shares, self.cumul_total,
                 direction, self.symbol)
            self._l.append(t)

            # Update shares and cash.
            self.shares -= exit_shares
            TradeLog.cash += self.ave_entry_price*exit_shares + pl_cash

            # Update open_trades list.
            if shares == qty:
                del self._open_trades[0]
                break
            elif shares < qty:
                self._open_trades[0]['qty'] -= shares
                break
            else:
                del self._open_trades[0]
                shares -= exit_shares

        return -shares_orig

    def exit_trade(self, exit_date, exit_price, shares=None):
        """
        Exit a trade on the long side.

        Parameters
        ----------
        exit_date : str
            The exit date.
        exit_price : float
            The exit price.
        shares : int, optional
            The number of shares to sell (default is None, which implies
            sell all the shares).

        Returns
        -------
        int
            The number of shares sold.

        Notes
        -----
        The `sell' alias can be used to call this function for reducing
        or closing out a long position.
        """
        return self._exit_trade(exit_date=exit_date,
                                exit_price=exit_price,
                                shares=shares,
                                direction=Direction.LONG)

    sell = exit_trade
    """
    method : sell is a function reference to exit_trade, i.e. an alias.
    """

    def buy2cover(self, exit_date, exit_price, shares=None):
        """
        Exit a trade on the short side, i.e. buy to cover.

        Parameters
        ----------
        exit_date : str
            The exit date.
        exit_price : float
            The exit price.
        shares : int
            The number of shares to buy to cover (default in None,
            which implies close out the short shares).

        Returns
        -------
        int
            The number of shares bought.
        """
        return self._exit_trade(exit_date=exit_date,
                                exit_price=exit_price,
                                shares=shares,
                                direction=Direction.SHORT)

    ####################################################################
    # GET PRICES (get_price, get_prices)

    def get_price(self, row, field='close'):
        """
        Return price given row and field.

        Parameters
        ----------
        row : pd.Series
            The timeseries of the portfolio.
        field : str, optional {'close', 'open', 'high', 'low'}
            The price field (default is 'close').

        Returns
        -------
        float
            The current price.

        """
        return getattr(row, field)

    def get_prices(self, row, fields=['open', 'high', 'low', 'close']):
        """
        Return dict of prices for all symbols given row and fields.

        Parameters
        ----------
        row : pd.Series
            The timeseries of the portfolio.
        fields : list, optional
            The list of fields to use (default is
            ['open', 'high', 'low', 'close']).

        Returns
        -------
        d : dict of floats
            The price indexed by fields.
        """
        d = {}
        for field in fields:
            value = self.get_price(row, field)
            d[field] = value
        return d

    ####################################################################
    # ADJUST POSITION (adjust_shares, adjust_value, adjust_percent)

    def adjust_shares(self, date, price, shares, direction=Direction.LONG):
        """
        Adjust a position to a target number of shares.

        If the position doesn't already exist, this is equivalent
        to entering a new trade. If the position does exist, this is
        equivalent to entering or exiting a trade for the difference
        between the target number of shares and the current number
        of shares.

        Parameters
        ----------
        date : str
            The trade date.
        price : float
            The current price of the security.
        shares : int
            The requested number of target shares.
        direction : pf.Direction, optional
            The direction of the trade (default is Direction.LONG).

        Returns
        -------
        int
            The number of shares bought or sold.
        """
        diff_shares = shares - self.shares
        if direction == Direction.LONG:
            if diff_shares >= 0:
                shares = self.enter_trade(date, price, diff_shares)
            else:
                shares = self.exit_trade(date, price, -diff_shares)
        else:
            if diff_shares >= 0:
                shares = self.sell_short(date, price, diff_shares)
            else:
                shares = self.buy2cover(date, price, -diff_shares)
        return shares

    def adjust_value(self, date, price, value, direction=Direction.LONG):
        """
        Adjust a position to a target value.

        If the position doesn't already exist, this is equivalent
        to entering a new trade. If the position does exist, this is
        equivalent to entering or exiting a trade for the difference
        between the target value and the current value.

        Parameters
        ----------
        date : str
            The trade date.
        price : float
            The current price of the security.
        shares : int
            The requested target value.
        direction : pf.Direction, optional
            The direction of the trade (default is Direction.LONG).

        Returns
        -------
        int
            The number of shares bought or sold.
        """
        total_funds = self.total_funds(price)
        shares = int(min(total_funds, value) / price)
        shares = self.adjust_shares(date, price, shares, direction)
        return shares

    def adjust_percent(self, date, price, weight, direction=Direction.LONG):
        """
        Adjust position to a target percent of the current portfolio
        value.

        If the position doesn't already exist, this is equivalent
        to entering a new trade. If the position does exist, this is
        equivalent to entering or exiting a trade for the difference
        between the target percent and the current percent.

        Parameters
        ----------
        date : str
            The trade date.
        price : float
            The current price of the security.
        weight : int
            The requested target weight, , where 0 <= weight <= 1.
        direction : pf.Direction, optional
            The direction of the trade (default is Direction.LONG).

        Returns
        -------
        int
            The number of shares bought or sold.
        """
        if not (0 <= weight <= 1):
            raise ValueError('weight should be between 0 and 1 (inclusive).')

        total_funds = self.total_funds(price)
        value = total_funds * weight
        shares = self.adjust_value(date, price, value, direction)
        return shares

    ####################################################################
    # GET LOGS (trade log, raw trade log)

    def _merge_trades(self, tlog):
        """
        Merge like trades that occur on the same day.
        """

        def _merge(tlog, merge_type):
            """
             Merge entry trades that occur on the same date.
             """
            if merge_type == 'entry':
                tlog['exit_date'] = tlog['exit_date']
            else:
                tlog['entry_date'] = tlog['entry_date']
            tlog['entry_price'] = \
                (tlog['entry_price'] * tlog['qty']).sum() / tlog['qty'].sum()
            tlog['exit_price'] = \
                (tlog['exit_price'] * tlog['qty']).sum() / tlog['qty'].sum()
            tlog['pl_points'] = tlog['pl_points'].sum()
            tlog['pl_cash'] = tlog['pl_cash'].sum()
            tlog['qty'] = tlog['qty'].sum()
            tlog['cumul_total'] = tlog['cumul_total'].tail(1)
            return tlog

        tlog = tlog.groupby('entry_date', group_keys=False) \
                                         .apply(_merge, merge_type='entry') \
                                         .dropna().reset_index(drop=True)
        tlog = tlog.groupby('exit_date', group_keys=False) \
                                        .apply(_merge, merge_type='exit') \
                                        .dropna().reset_index(drop=True)
        return tlog


    def get_log(self, merge_trades=False):
        """
        Return the trade log.

        The trade log consists of the following columns:
        'entry_date', 'entry_price', 'exit_date', 'exit_price',
        'pl_points', 'pl_cash', 'qty', 'cumul_total',
        'direction', 'symbol'.

        Parameters
        ----------
        merge_trade : bool, optional
            True to merge trades that occur on the same date
            (default is False).

        Returns
        -------
        tlog : pd.DataFrame
            The trade log.
        """
        columns = ['entry_date', 'entry_price', 'exit_date', 'exit_price',
                   'pl_points', 'pl_cash', 'qty', 'cumul_total',
                   'direction', 'symbol']
        tlog = pd.DataFrame(self._l, columns=columns)

        if merge_trades:
            tlog = self._merge_trades(tlog)

        return tlog

    def get_log_raw(self):
        """
        Return the raw trade log.

        The trade log consists of the following columns:
        'date', 'seq_num', 'price', 'shares', 'entry_exit',
        'direction', 'symbol'.

        Returns
        -------
        rlog : pd.DataFrame
            The raw trade log.
        """
        columns = ['date', 'seq_num', 'price', 'shares', 'entry_exit', 'direction', 'symbol']
        rlog = pd.DataFrame(self._raw, columns=columns)
        return rlog

########################################################################
# DAILY BALANCE

class TradeState:
    """
    The trade state of OPEN, HOLD, or CLOSE.

    In the Daily Balance log, trade state is given by these
    characters: OPEN='O', HOLD='-', and CLOSE='X'
    """
    OPEN, HOLD, CLOSE = ['O', '-', 'X']

class DailyBal:
    """
    Log for daily balance.
    """

    def __init__(self):
        """
        Initialize instance variables.

        Attributes
        ----------
        _l : list of tuples
            The list of daily balance tuples.
        """
        self._l = []

    def append(self, date, close, high=None, low=None):
        """
        Append a new entry to the daily balance log.

        Parameters
        ----------
        date : str
            The current date.
        close : float
            The balance close value of the day.
        high : float, optional
            The balance high value of the day (default is None,
            which implies that the 'high' is the 'close'.  In other
            words, we are not using intra-day prices).
        low : float, optional
            The balance low value of the day (default is None,
            which implies that the 'low' is the 'close'.  In other
            words, we are not using intra-day prices).

        Returns
        -------
        None
        """
        if high is None:  high = close
        if low  is None:  low  = close

        # calculate daily balance values:
        # date, high, low, close, shares, cash, leverage
        cash = TradeLog.cash
        tlog = list(TradeLog.instance.values())[0]
        shares   = tlog.shares
        high_    = tlog.equity(high)
        low_     = tlog.equity(low)
        close_   = tlog.equity(close)
        leverage = tlog.leverage(close)
        #if (close_ < 0):
        #    print('{} WARNING: Margin Call!!!'
        #          .format(date.strftime('%Y-%m-%d')))

        if tlog.direction == Direction.LONG:
            t = (date, high_, low_, close_, shares, cash, leverage)
        else:
            t = (date, low_, high_, close_, shares, cash, leverage)
        self._l.append(t)

    def get_log(self, tlog):
        """
        Return the daily balance log.

        The daily balance log consists of the following columns:
        'date', 'high', 'low', 'close', 'shares', 'cash', 'leverage'

        Parameters
        ----------
        tlog : pd.DataFrame
            The trade log.

        Returns
        -------
        dbal : pd.DataFrame
            The daily balance log.
        """
        columns = ['date', 'high', 'low', 'close', 'shares', 'cash', 'leverage']
        dbal = pd.DataFrame(self._l, columns=columns)

        def trade_state(row):
            """
            Apply function for adding the `state` column to dbal.

            Convert pandas.timestamp to numpy.datetime64.
            See if there was a entry or exit in tlog on date.
            """
            date = row.date.to_datetime64()
            if date in tlog.entry_date.values:
                state = TradeState.OPEN
            elif date in tlog.exit_date.values:
                state = TradeState.CLOSE
            else:
                state = TradeState.HOLD
            return state

        dbal['state'] = dbal.apply(trade_state, axis=1)
        dbal.set_index('date', inplace=True)
        return dbal
