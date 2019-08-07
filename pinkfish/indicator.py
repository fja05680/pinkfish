"""
indicator
---------
Custom indicators
"""

# Use future imports for python 3.0 forward compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# Other imports
import numpy as np
import pandas as pd
from talib.abstract import *


class IndicatorError(Exception):
    """ Base indicator exception """

#####################################################################
# CROSSOVER

class TradeCrossOverError(IndicatorError):
    """ Invalid timeperiod specified """

class _CrossOver(object):
    """
    This indicator is used to represent regime, i.e. Bull or Bear market
    Or more generally as a crossover indicator for two moving averages
    _r is incremented(decremented) each day a bull(bear) market persists
    _r indicates the number of trading days a trend has persisted
    _r is nan, then sma_slow is nan
    _r > 0, then bull market, price > sma
    _r < 0, then bear market, price <= sma
    """
    def __init__(self):
        self._r = 0

    def apply(self, row):
        if pd.isnull(row['__sma_slow__']):
            self._r = np.nan
        elif row['__sma_fast__'] > row['__sma_slow__']:
            self._r = self._r + 1 if self._r > 0 else 1
        else:
            self._r = self._r -1 if self._r < 0 else -1
        return self._r

def CROSSOVER(ts, timeperiod_fast=50, timeperiod_slow=200,
              func_fast=SMA, func_slow=SMA,
              price='close', prevday=False):
    """
    ts: dataframe with 'open', 'high', 'low', 'close', 'volume'
    timeperiod_fast: timeperiod for fast moving average
    timeperiod_slow: timeperiod for slow moving average
    func_fast: talib func for fast moving average
    func_slow: talib func for slow moving average
      'DEMA', 'EMA', 'KAMA', SMA', 'T3', 'TEMA', 'TRIMA', 'WMA'
      ('MAMA' not compatible)
    price: input_array column to use
    prevday: True will shift the series forward; unless you are buying
      on the close, you'll likely want to set this to True.
      It gives you the previous day's CrossOver

    ex:
    ts['crossover'] = \
        CROSSOVER(ts, timeperiod_fast=1, timeperiod_slow=50, prevday=True)
    """
    if (timeperiod_fast < 1 or timeperiod_slow < 2
        or timeperiod_fast >= timeperiod_slow):
        raise TradeCrossOverError

    ts['__sma_fast__'] = ts[price] if timeperiod_fast == 1 else \
        func_fast(ts, timeperiod=timeperiod_fast, price=price)

    ts['__sma_slow__'] = \
        func_slow(ts, timeperiod=timeperiod_slow, price=price)

    func = _CrossOver().apply
    s = ts.apply(func, axis=1)
    if prevday:
        s = s.shift()
    ts.drop(['__sma_fast__', '__sma_slow__'], axis=1, inplace=True)
    return s

#####################################################################
#
