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

class Regime(object):
    """
    This indicator is used to represent regime, i.e. Bull or Bear market
    If _r is 0, then sma is nan
    If _r > 0, then bull market, price > sma
    If _r < 0, then bear market, price <= sma

    use as follows:
    ts['regime'] = ts.apply(pf.Regime().apply, axis=1)
    check:
    ts['regime'] > 0:
    """
    def __init__(self, period='sma200', price='close'):
        self._period = period
        self._price = price
        self._r = 0

    def apply(self, row):
        if pd.isnull(row[self._period]):
            self._r = 0
        elif row[self._price] > row[self._period]:
            self._r = self._r + 1 if self._r > 0 else 1
        else:
            self._r = self._r -1 if self._r < 0 else -1
        return self._r
