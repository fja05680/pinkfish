import datetime
import unittest
import pandas as pd
import pinkfish as pf


class TestTrade(unittest.TestCase):

    def setUp(self):
        self.date = datetime.datetime.now().date()
        # keep all the prices at 10, shares and cash at 1000
        self.high = self.low = self.close = 10
        self.shares = self.cash = 1000
        self.state = pf.trade.TradeState.HOLD

    def call_append(self, bal):
        ''' We'll be running this several times. '''
        bal.append(self.date,
                   self.high, self.low, self.close,
                   self.shares, self.cash, self.state)

    def test_daily_balance_state(self):
        ''' For t to be instantiated the trade state must exist.
            Throw an error if the trade state is not valid.
        '''
        bal = pf.DailyBal()
        self.state = None
        with self.assertRaises(pf.trade.TradeStateError):
            self.call_append(bal)

    def test_daily_balance_append(self):
        ''' Check that the daily log grows as expected. '''
        bal = pf.DailyBal()
        df = bal.get_log()
        self.assertTrue(isinstance(df, pd.DataFrame))
        self.assertTrue(len(df.index) == 0)

        self.state = pf.trade.TradeState.OPEN
        self.call_append(bal)
        df = bal.get_log()
        self.assertTrue(len(df.index) == 1)

        self.state = pf.trade.TradeState.HOLD
        self.call_append(bal)
        df = bal.get_log()
        self.assertTrue(len(df.index) == 2)

        self.state = pf.trade.TradeState.CLOSE
        self.call_append(bal)
        df = bal.get_log()
        self.assertTrue(len(df.index) == 3)

        price_columns = ["high", "low", "close"]
        other_columns = ["shares", "cash"]

        # we are keeping the high, low and close the same for this test
        # cash and shares are also kept equal
        portfolio_value = self.high * self.shares + self.cash

        # all prices are $x
        prices = list(set(df[price_columns].values.flatten().tolist()))
        self.assertTrue(len(prices) == 1)
        self.assertTrue(prices[0] == portfolio_value)

        # all other values (except state) are y
        others = list(set(df[other_columns].values.flatten().tolist()))
        self.assertTrue(len(others) == 1)
        self.assertTrue(others[0] == self.shares)

        # check the order of our states
        states = df["state"].values.tolist()
        self.assertTrue(states[0] == pf.trade.TradeState.OPEN)
        self.assertTrue(states[1] == pf.trade.TradeState.HOLD)
        self.assertTrue(states[2] == pf.trade.TradeState.CLOSE)
