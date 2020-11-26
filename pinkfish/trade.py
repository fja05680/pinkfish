"""
trade
---------
Assist with trading
"""

import pandas as pd
import pinkfish as pf


class Direction:
    LONG, SHORT = ['LONG', 'SHRT']

class Margin:
    CASH, STANDARD, PATTERN_DAY_TRADER = [1, 2, 4]

#####################################################################
# TRADE LOG - each symbol has it's own trade log

class TradeLog:

    cash = 0                       # current cash; entire portfolio
    multiplier = 1                 # applied to profit calculation
    margin = Margin.CASH           # margin percent, default 1:1 no margin
    buying_power = None            # buying power; for Portfolio class only
    seq_num = 0                    # used to order trades in Portfolio class
    instance = {}                  # dict of TradeLog instances, key=symbol

    def __init__(self, symbol, reset=True):
        self.symbol = symbol        # security symbol
        self.shares = 0             # num shares
        self.direction = None       # Long or Short
        self.ave_entry_price = 0    # average purchase price per share
        self.cumul_total = 0        # cumul total profits (loss)
        self._l = []                # list of trade entry/exit tuples
        self._raw = []              # list raw trade tuples
        self._open_trades = []      # list of open trades
        if reset:
            TradeLog.seq_num = 0
            TradeLog.instance.clear()
        TradeLog.instance[symbol] = self

    def share_value(self, price):
        """ return total value of shares """
        value = 0
        if self.direction == Direction.LONG:
            value += price*self.shares
        elif self.direction == Direction.SHORT:
            value += (2*self.ave_entry_price-price)*self.shares
        return value
        
    def total_value(self, price):
        """ total_value = share_value +  cash (if cash > 0) """
        total_value = self.share_value(price)
        if TradeLog.cash > 0:
            total_value += TradeLog.cash
        return total_value

    def equity(self, price):
        """ equity = total_value - loan (loan is negative cash) """
        equity = self.total_value(price)
        if TradeLog.cash < 0:
            equity += TradeLog.cash
        return equity

    def leverage(self, price):
        """ return the leverage factor of the position """
        return self.total_value(price) / self.equity(price)
        
    def total_funds(self, price):
        """ total account funds for trading """
        return self.equity(price) * TradeLog.margin

    def share_percent(self, price):
        """ return share value as a percentage of total_funds """
        return self.share_value(price) / self.total_funds(price) * 100

    def num_open_trades(self):
        """ return number of open orders, i.e. not closed out """
        return len(self._open_trades)

    #####################################################################
    # ENTER TRADE (buy, sell_short)

    def calc_buying_power(self, price):
        """ calculate buying power """
        buying_power = (TradeLog.cash * TradeLog.margin
                      + self.share_value(price) * (TradeLog.margin -1))
        return buying_power

    def calc_shares(self, price, cash=None):
        """ calculate shares and remaining cash before enter_trade() """

        # margin should be equal to or greater than 1
        if TradeLog.margin < 1: TradeLog.margin = 1

        # calculate buying power
        if TradeLog.buying_power is not None:
            buying_power = TradeLog.buying_power
        else:
            buying_power = self.calc_buying_power(price)

        # cash can't exceed buying power
        if cash is None or cash > buying_power:
            cash = buying_power

        # cash can't be negative
        if cash < 0: cash = 0

        # calculate shares
        shares = int(cash / price)
        return shares

    def _enter_trade(self, entry_date, entry_price, shares=None, direction=Direction.LONG):
        """ add entry to open_trades list; update shares and cash """

        max_shares = self.calc_shares(entry_price)
        shares = max_shares if shares is None else min(shares, max_shares)

        if shares == 0:
            return 0

        # record in raw trade log
        t = (entry_date, TradeLog.seq_num, entry_price, shares, 'entry', direction, self.symbol)
        self._raw.append(t)
        TradeLog.seq_num += 1

        # add record to open_trades
        d = {'entry_date':entry_date, 'entry_price':entry_price, 'qty':shares,
             'direction':direction, 'symbol':self.symbol}
        self._open_trades.append(d)

        # update direction
        if self.direction != direction:
            if self.direction is None or self.shares == 0:
                self.direction = direction
            else:
                raise ValueError('not allowed to change direction from {} to {}, '
                                 'this requires shares = 0'
                                 .format(self.direction, direction))

        # update average entry price and shares
        self.ave_entry_price = \
            (self.ave_entry_price*self.shares + entry_price*shares) / (self.shares + shares)
        self.shares += shares

        # update cash
        TradeLog.cash -= entry_price * shares

        return shares

    def enter_trade(self, entry_date, entry_price, shares=None):
        return self._enter_trade(entry_date=entry_date,
                                 entry_price=entry_price,
                                 shares=shares,
                                 direction=Direction.LONG)
    # buy function reference
    buy = enter_trade

    def sell_short(self, entry_date, entry_price, shares=None):
        return self._enter_trade(entry_date=entry_date,
                                 entry_price=entry_price,
                                 shares=shares,
                                 direction=Direction.SHORT)

    #####################################################################
    # EXIT TRADE (sell, buy2cover)

    def _qty_open_trade(self, index):
        """ qty of an open trade by index """
        if index >= self.num_open_trades(): return 0
        return self._open_trades[index]['qty']

    def _exit_trade(self, exit_date, exit_price, shares=None, direction=Direction.LONG):
        """
        record exit in trade log; return -shares exited
        shares = None exits all shares
        shares > 0 exits that number of shares
        shares < 0 indicates the number of positons to exit
        """

        if shares is None or shares > self.shares:
            shares = self.shares
        elif shares < 0:
            positions = -shares
            shares = 0
            for position in range(positions):
                shares += self._qty_open_trade(position)

        if shares == 0:
            return 0

        shares_orig = shares

        # record in raw trade log
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

            # calculate exit_shares and pl_cash
            exit_shares = qty if shares >= qty else shares
            pl_cash = pl_points * exit_shares * TradeLog.multiplier
            self.cumul_total += pl_cash

            # record in trade log
            t = (entry_date, entry_price, exit_date, exit_price,
                 pl_points, pl_cash, exit_shares, self.cumul_total,
                 direction, self.symbol)
            self._l.append(t)

            # update shares and cash
            self.shares -= exit_shares
            TradeLog.cash += self.ave_entry_price*exit_shares + pl_cash
            '''
            if direction == Direction.LONG:
                TradeLog.cash += exit_price * exit_shares * TradeLog.multiplier
            else:
                TradeLog.cash += ((2*self.ave_entry_price-exit_price)
                                  * exit_shares
                                  * TradeLog.multiplier)
           '''

            # update open_trades list
            if shares == qty:
                del self._open_trades[0];
                break
            elif shares < qty:
                self._open_trades[0]['qty'] -= shares
                break
            else:
                del self._open_trades[0]
                shares -= exit_shares

        return -shares_orig

    def exit_trade(self, exit_date, exit_price, shares=None):
        return self._exit_trade(exit_date=exit_date,
                                exit_price=exit_price,
                                shares=shares,
                                direction=Direction.LONG)

    # sell function reference
    sell = exit_trade

    def buy2cover(self, exit_date, exit_price, shares=None):
        return self._exit_trade(exit_date=exit_date,
                                exit_price=exit_price,
                                shares=shares,
                                direction=Direction.SHORT)

    #####################################################################
    # ADJUST POSITION (adjust_shares, adjust_value, adjust_percent)

    def adjust_shares(self, date, price, shares, direction=Direction.LONG):
        """
        Adjust a position to a target number of shares.
        If the position doesn't already exist, this is equivalent
        to entering a new trade. If the position does exist, this is
        equivalent to entering or exiting a trade for the difference between
        the target number of shares and the current number of shares.
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
        equivalent to entering or exiting a trade for the difference between
        the target value and the current value.
        """
        total_funds = self.total_funds(price)
        shares = int(min(total_funds, value) / price)
        shares = self.adjust_shares(date, price, shares, direction)
        return shares

    def adjust_percent(self, date, price, weight, direction=Direction.LONG):
        """
        Adjust a position to a target percent of the current portfolio value.
        If the position doesn't already exist, this is equivalent
        to entering a new trade. If the position does exist, this is
        equivalent to entering or exiting a trade for the difference between
        the target percent and the current percent.
        """
        weight = weight if weight <= 1 else weight/100
        total_funds = self.total_funds(price)
        value = total_funds * weight
        shares = self.adjust_value(date, price, value, direction)
        return shares

    #####################################################################
    # GET LOGS (trade log, raw trade log)

    def _merge_trades(self, tlog):
        """ merge like trades that occur on the same day """

        # merge exit trades that occur on the same date
        def _merge_exits(tlog):
            # tlog is a DataFrame of group values
            tlog['entry_date'] = tlog['entry_date'].head(1)
            tlog['entry_price'] = \
                (tlog['entry_price'] * tlog['qty']).sum() / tlog['qty'].sum()
            tlog['exit_price'] = \
                (tlog['exit_price'] * tlog['qty']).sum() / tlog['qty'].sum()
            tlog['pl_points'] = tlog['pl_points'].sum()
            tlog['pl_cash'] = tlog['pl_cash'].sum()
            tlog['qty'] = tlog['qty'].sum()
            tlog['cumul_total'] = tlog['cumul_total'].sum()
            return tlog

        # merge entry trades that occur on the same date
        def _merge_entrys(tlog):
            # tlog is a DataFrame of group values
            tlog['exit_date'] = tlog['exit_date'].tail(1)
            tlog['entry_price'] = \
                (tlog['entry_price'] * tlog['qty']).sum() / tlog['qty'].sum()
            tlog['exit_price'] = \
                (tlog['exit_price'] * tlog['qty']).sum() / tlog['qty'].sum()
            tlog['pl_points'] = tlog['pl_points'].sum()
            tlog['pl_cash'] = tlog['pl_cash'].sum()
            tlog['qty'] = tlog['qty'].sum()
            tlog['cumul_total'] = tlog['cumul_total'].sum()
            return tlog

        tlog = tlog.groupby('entry_date').apply(_merge_entrys).dropna().reset_index(drop=True)
        tlog = tlog.groupby('exit_date').apply(_merge_exits).dropna().reset_index(drop=True)
        return tlog


    def get_log(self, merge_trades=False):
        """ return Dataframe """
        columns = ['entry_date', 'entry_price', 'exit_date', 'exit_price',
                   'pl_points', 'pl_cash', 'qty', 'cumul_total',
                   'direction', 'symbol']
        tlog = pd.DataFrame(self._l, columns=columns)

        if merge_trades:
            tlog = self._merge_trades(tlog)

        return tlog

    def get_log_raw(self):
        """ return Dataframe """
        columns = ['date', 'seq_num', 'price', 'shares', 'entry_exit', 'direction', 'symbol']
        rlog = pd.DataFrame(self._raw, columns=columns)
        return rlog

#####################################################################
# DAILY BALANCE

class TradeState:
    OPEN, HOLD, CLOSE = ['O', '-', 'X']

class DailyBal:
    """ Log for daily balance """

    def __init__(self):
        self._l = []  # list of daily balance tuples

    def append(self, date, high, low, close):
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
        """ return Dataframe """
        columns = ['date', 'high', 'low', 'close', 'shares', 'cash', 'leverage']
        dbal = pd.DataFrame(self._l, columns=columns)

        def trade_state(row):
            # convert pandas.timestamp to numpy.datetime64
            # see if there was a entry or exit in tlog on date
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
