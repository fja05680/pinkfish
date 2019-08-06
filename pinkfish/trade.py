"""
trade
---------
Assist with trading
"""

# Use future imports for python 3.0 forward compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# Other imports
import pandas as pd


class TradeError(Exception):
    """Base trade exception"""

class TradeStateError(TradeError):
    """ The trade state provided does not exist. """

"""
trade
---------
Assist with trading
"""

class TradeError(Exception):
    """ Base trade exception """

class TradeStateError(TradeError):
    """ The trade state provided does not exist. """

class TradeLog(object):

    def __init__(self):
        self._l = []             # list of trade entry/exit tuples
        self._raw = []           # list raw trade tuples
        self._open_trades = []   # list of open trades
        self._cash = 10000       # current cash
        self._shares = 0         # current shares
        self._cumul_total = 0    # cumul total profits (loss)

    def calc_shares(self, price, cash=None):
        """ calculate shares and remaining cash before entry """
        if cash is None or cash > self._cash:
            cash = self._cash
        shares = int(cash / price)
        return shares

    def enter_trade(self, entry_date, entry_price, shares=None):
        """ add entry to open_trades list; update shares and cash """
        if shares == 0:
            return 0
        if shares is None:
            shares = self.calc_shares(entry_price)

        # date, price, shares, entry_exit
        # record in raw trade log
        t = (entry_date, entry_price, shares, 'entry')
        self._raw.append(t)

        # add record to open_trades
        d = {'entry_date':entry_date, 'entry_price':entry_price, 'qty':shares}
        self._open_trades.append(d)

        # update shares and cash
        self._shares += shares
        self._cash -= entry_price * shares
        return shares

    def num_open_trades(self):
        """ return number of open orders, i.e. not closed out """
        return len(self._open_trades)

    def _qty_open_trade(self, index):
        """ qty of an open trade by index """
        if index >= self.num_open_trades(): return 0
        return self._open_trades[index]['qty']

    @property
    def cash(self):
        """ return amount of cash """
        return self._cash

    @cash.setter
    def cash(self, value):
        self._cash = value

    @property
    def shares(self):
        """ return number of shares """
        return self._shares

    def exit_trade(self, exit_date, exit_price, shares=None):
        """
        record exit in trade log; return shares exited
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
        t = (exit_date, exit_price, shares, 'exit')
        self._raw.append(t)

        for i, open_trade in enumerate(self._open_trades[:]):
            entry_date = open_trade['entry_date']
            entry_price = open_trade['entry_price']
            qty = open_trade['qty']
            pl_points = exit_price - entry_price

            # calculate exit_shares
            exit_shares = qty if shares >= qty else shares
            pl_cash = pl_points * exit_shares
            self._cumul_total += pl_cash

            # record in trade log
            t = (entry_date, entry_price, exit_date, exit_price,
                 pl_points, pl_cash, exit_shares, self._cumul_total)
            self._l.append(t)

            # update shares and cash
            self._shares -= exit_shares
            self._cash += exit_price * exit_shares

            #print('i = {}, shares = {}, exit_shares = {}, qty = {}'
            #      .format(i, shares, exit_shares, qty))

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

        return shares_orig

    def get_log(self):
        """ return Dataframe """
        columns = ['entry_date', 'entry_price', 'exit_date', 'exit_price',
                   'pl_points', 'pl_cash', 'qty', 'cumul_total']
        tlog = pd.DataFrame(self._l, columns=columns)
        return tlog

    def get_log_raw(self):
        """ return Dataframe """
        columns = ['date', 'price', 'shares', 'entry_exit']
        rlog = pd.DataFrame(self._raw, columns=columns)
        return rlog

class TradeState:
    OPEN, HOLD, CLOSE = range(0, 3)

class DailyBal(object):
    """ Log for daily balance """

    def __init__(self):
        self._l = []  # list of daily balance tuples

    def _balance(self, date, high, low, close, shares, cash, state):
        """ calculates daily balance values """
        if state not in list(vars(TradeState).values()) or state is None:
            raise TradeStateError

        if state == TradeState.OPEN:
            # date, high, low, close, cash, state
            t = (date, close*shares + cash, close*shares + cash,
                 close*shares + cash, shares, cash, state)
        elif state == TradeState.HOLD:
            t = (date, high*shares + cash, low*shares + cash,
                 close*shares + cash, shares, cash, state)
        elif state == TradeState.CLOSE:
            t = (date, high*shares + cash, low*shares + cash,
                 close*shares + cash, shares, cash, state)
        return t

    def append(self, date, high, low, close, shares, cash, state):
        t = self._balance(date, high, low, close, shares, cash, state)
        self._l.append(t)

    def get_log(self):
        """ return Dataframe """
        columns = ['date', 'high', 'low', 'close', 'shares', 'cash', 'state']
        dbal = pd.DataFrame(self._l, columns=columns)
        dbal.set_index('date', inplace=True)
        return dbal
