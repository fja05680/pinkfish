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
from enum import Enum
import pandas as pd


class TradeError(Exception):
    """Base trade exception"""


class TradeStateError(TradeError):
    """ The trade state provided does not exist. """


class TradeLog():

    def __init__(self):
        columns = ['entry_date', 'entry_price', 'long_short', 'qty',
                   'exit_date', 'exit_price', 'pl_points', 'pl_cash',
                   'cumul_total']
        self._tlog = pd.DataFrame(columns=columns)
        self.shares = 0

    def calc_shares(self, cash, price):
        """ calculate shares and remaining cash before entry """
        shares = int(cash / price)
        cash = cash - shares*price
        return shares, cash

    def calc_cash(self, cash, price, shares):
        """ calculate cash after exit """
        cash = cash + price*shares
        return cash

    def enter_trade(self, entry_date, entry_price, shares, long_short='long'):
        """ record trade entry in trade log """
        d = {'entry_date':entry_date, 'entry_price':entry_price, 'qty':shares, 
             'long_short':long_short}
        tmp = pd.DataFrame([d], columns=self._tlog.columns)
        self._tlog = self._tlog.append(tmp, ignore_index=True)

        # update shares
        if long_short == 'long':
            self.shares += shares
        else:
            self.shares -= shares

    def _get_open_trades(self):
        """ find the "integer" index of rows with NaN """
        return pd.isnull(self._tlog).any(1).to_numpy().nonzero()[0]
    
    def num_open_trades(self):
        """ return number of open orders, i.e. not closed out """
        return len(self._get_open_trades())

    def exit_trade(self, exit_date, exit_price, shares=-1, long_short='long'):
        """ record trade exit in trade log """

        rows = self._get_open_trades()
        idx = rows[0]

        entry_price = self._tlog['entry_price'][idx]
        shares = self._tlog['qty'][idx] if shares == -1 else shares
        pl_points = exit_price - entry_price
        pl_cash = pl_points * shares
        if idx == 0:
            cumul_total = pl_cash
        else:
            cumul_total = self._tlog.ix[idx - 1, 'cumul_total'] + pl_cash

        self._tlog.ix[idx, 'exit_date'] = exit_date
        self._tlog.ix[idx, 'exit_price'] = exit_price
        self._tlog.ix[idx, 'long_short'] = 'long'
        self._tlog.ix[idx, 'pl_points'] = pl_points
        self._tlog.ix[idx, 'pl_cash'] = pl_cash
        self._tlog.ix[idx, 'cumul_total'] = cumul_total

        # update shares
        if long_short == 'long':
            self.shares -= shares
        else:
            self.shares +=shares
        return idx

    def get_log(self):
        """ return Dataframe """
        return self._tlog


class TradeState(Enum):
    OPEN, HOLD, CLOSE = range(0, 3)


class DailyBal:
    """ Log for daily balance """

    def __init__(self):
        self._l = []  # list of daily balance tuples

    def _balance(self, date, high, low, close, shares, cash, state):
        """ calculates daily balance values """
        if not isinstance(state, TradeState):
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

