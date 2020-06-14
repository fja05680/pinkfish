"""
trade
---------
Assist with trading
"""

# Other imports
import pandas as pd


class TradeLog(object):

    _cash = 0                    # current cash
    _cumul_total = 0             # cumul total profits (loss)
    _share_dict = {}

    def __init__(self):
        self._l = []             # list of trade entry/exit tuples
        self._raw = []           # list raw trade tuples
        self._open_trades = []   # list of open trades
        self._shares = 0         # current shares

    @classmethod
    def initialize(cls, cash):
        cls._cash = cash
        cls._cumul_total = 0
        cls._share_dict.clear()

    @classmethod
    def add_cash(cls, cash):
        cls._cash += cash

    @property
    def shares(self):
        """ return number of shares """
        return self._shares

    def value(self, price):
        """ return total value of shares """
        return self._shares * price

    def percent(self, price):
        """ return percent of portfolio value currently allocated """
        total_equity = TradeLog._cash + self._shares * price
        return ((self._shares * price) / total_equity) * 100

    def num_open_trades(self):
        """ return number of open orders, i.e. not closed out """
        return len(self._open_trades)

    def _qty_open_trade(self, index):
        """ qty of an open trade by index """
        if index >= self.num_open_trades(): return 0
        return self._open_trades[index]['qty']

    def calc_shares(self, price, cash=None):
        """ calculate shares and remaining cash before enter_trade() """
        if cash is None or cash > TradeLog._cash:
            cash = TradeLog._cash
        shares = int(cash / price)
        return shares

    def enter_trade(self, entry_date, entry_price, shares=None, symbol=''):
        """ add entry to open_trades list; update shares and cash """
        if shares == 0:
            return 0

        max_shares = self.calc_shares(entry_price)
        shares = max_shares if shares is None else min(shares, max_shares)

        # date, price, shares, entry_exit
        # record in raw trade log
        t = (entry_date, entry_price, shares, 'entry', symbol)
        self._raw.append(t)

        # add record to open_trades
        d = {'entry_date':entry_date, 'entry_price':entry_price, 'qty':shares,
             'symbol':symbol}
        self._open_trades.append(d)

        # update shares and cash
        self._shares += shares
        TradeLog._share_dict[symbol] = self._shares
        TradeLog._cash -= entry_price * shares
        return shares

    def exit_trade(self, exit_date, exit_price, shares=None, symbol=''):
        """
        record exit in trade log; return -shares exited
        shares = None exits all shares
        shares > 0 exits that number of shares
        shares < 0 indicates the number of positons to exit
        """

        if shares is None or shares > self._shares:
            shares = self._shares
        elif shares < 0:
            positions = -shares
            shares = 0
            for position in range(positions):
                shares += self._qty_open_trade(position)

        if shares == 0:
            return 0

        shares_orig = shares

        # record in raw trade log
        # date, price, shares, entry_exit
        t = (exit_date, exit_price, shares, 'exit', symbol)
        self._raw.append(t)

        for i, open_trade in enumerate(self._open_trades[:]):
            entry_date = open_trade['entry_date']
            entry_price = open_trade['entry_price']
            qty = open_trade['qty']
            pl_points = exit_price - entry_price

            # calculate exit_shares
            exit_shares = qty if shares >= qty else shares
            pl_cash = pl_points * exit_shares
            TradeLog._cumul_total += pl_cash

            # record in trade log
            t = (entry_date, entry_price, exit_date, exit_price,
                 pl_points, pl_cash, exit_shares, TradeLog._cumul_total, symbol)
            self._l.append(t)

            # update shares and cash
            self._shares -= exit_shares
            TradeLog._share_dict[symbol] = self._shares
            TradeLog._cash += exit_price * exit_shares

            #print('i = {}, shares = {}, exit_shares = {}, qty = {}, symbol = {}'
            #      .format(i, shares, exit_shares, qty, symbol))

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

    def adjust_shares(self, date, price, shares, symbol):
        """
        Adjust a position to a target number of shares.
        If the position doesn't already exist, this is equivalent
        to entering a new trade. If the position does exist, this is
        equivalent to entering or exiting a trade for the difference between
        the target number of shares and the current number of shares.
        """
        diff_shares = shares - self._shares
        if diff_shares >= 0:
            shares = self.enter_trade(date, price, diff_shares, symbol)
        else:
            shares = self.exit_trade(date, price, -diff_shares, symbol)
        return shares

    def adjust_value(self, date, price, value, symbol):
        """
        Adjust a position to a target value.
        If the position doesn't already exist, this is equivalent
        to entering a new trade. If the position does exist, this is
        equivalent to entering or exiting a trade for the difference between
        the target value and the current value.
        """
        total_equity = TradeLog._cash + self._shares * price
        shares = int(min(total_equity, value) / price)
        shares = self.adjust_shares(date, price, shares, symbol)
        return shares

    def adjust_percent(self, date, price, weight, symbol):
        """
        Adjust a position to a target percent of the current portfolio value.
        If the position doesn't already exist, this is equivalent
        to entering a new trade. If the position does exist, this is
        equivalent to entering or exiting a trade for the difference between
        the target percent and the current percent.
        """
        weight = weight if weight <= 1 else weight/100
        total_equity = TradeLog._cash + self._shares * price
        value = total_equity * weight
        shares = self.adjust_value(date, price, value, symbol)
        return shares

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
            tlog['entry_price'] = \
                (tlog['entry_price'] * tlog['qty']).sum() / tlog['qty'].sum()
            tlog['exit_date'] = tlog['exit_date'].tail(1)
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
                   'pl_points', 'pl_cash', 'qty', 'cumul_total', 'symbol']
        tlog = pd.DataFrame(self._l, columns=columns)

        if merge_trades:
            tlog = self._merge_trades(tlog)

        return tlog

    def get_log_raw(self):
        """ return Dataframe """
        columns = ['date', 'price', 'shares', 'entry_exit', 'symbol']
        rlog = pd.DataFrame(self._raw, columns=columns)
        return rlog

class TradeState:
    OPEN, HOLD, CLOSE = ['O', '-', 'X']

class DailyBal(object):
    """ Log for daily balance """

    def __init__(self):
        self._l = []  # list of daily balance tuples

    def append(self, date, high, low, close, shares):
        # calculate daily balance values: date, high, low, close, shares, cash
        cash = TradeLog._cash
        t = (date, high*shares + cash, low*shares + cash,
                   close*shares + cash, shares, cash)
        self._l.append(t)

    def get_log(self, tlog):
        """ return Dataframe """
        columns = ['date', 'high', 'low', 'close', 'shares', 'cash']
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
