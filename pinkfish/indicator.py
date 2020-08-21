"""
indicator
---------
Custom indicators
"""

import numpy as np
import pandas as pd
from talib.abstract import *
import pinkfish as pf


class IndicatorError(Exception):
    """ Base indicator exception """

#####################################################################
# CROSSOVER

class TradeCrossOverError(IndicatorError):
    """ Invalid timeperiod specified """

class _CrossOver:
    """
    This indicator is used to represent regime, i.e. Bull or Bear market
    Or more generally as a crossover indicator for two moving averages
    _r is incremented(decremented) each day a bull(bear) market persists
    _r remains unchanged when fast_ma within band of slow_ma
    _r indicates the number of trading days a trend has persisted
    _r is nan, then sma_slow is nan
    _r > 0, then bull market, fast_ma > slow_ma
    _r < 0, then bear market, fast_ma < slow_ma
    _r == 0, no trend established yet
    """
    def __init__(self):
        self._r = 0

    def apply(self, row, band=0):
        if pd.isnull(row['__sma_slow__']):
            self._r = np.nan
        elif row['__sma_fast__'] > row['__sma_slow__']*(1+band/100):
            self._r = self._r + 1 if self._r > 0 else 1
        elif row['__sma_fast__'] < row['__sma_slow__']*(1-band/100):
            self._r = self._r -1 if self._r < 0 else -1
        else:
            pass
        return self._r

def CROSSOVER(ts, timeperiod_fast=50, timeperiod_slow=200,
              func_fast=SMA, func_slow=SMA, band=0,
              price='close', prevday=False):
    """
    ts: dataframe with 'open', 'high', 'low', 'close', 'volume'
    timeperiod_fast: timeperiod for fast moving average
    timeperiod_slow: timeperiod for slow moving average
    func_fast: talib func for fast moving average
    func_slow: talib func for slow moving average
      'DEMA', 'EMA', 'KAMA', SMA', 'T3', 'TEMA', 'TRIMA', 'WMA'
      ('MAMA' not compatible)
    band: percent band around slow_ma, band expressed in percent, i.e. *100
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
    s = ts.apply(func, band=band, axis=1)
    if prevday:
        s = s.shift()
    ts.drop(['__sma_fast__', '__sma_slow__'], axis=1, inplace=True)
    return s

#####################################################################
# MOMENTUM

def MOMENTUM(ts, lookback=1, time_frame='monthly', price='close', prevday=False):
    """
    ts: dataframe with 'open', 'high', 'low', 'close', 'volume'
    lookback: the number of time_frames to lookback, i.e. 2 months
    timeframe: daily, weekly, monthly, or yearly
    price: input_array column to use
    prevday: True will shift the series forward; unless you are buying
      on the close, you'll likely want to set this to True.
      It gives you the previous day's Momentum

    ex:
    lookback = 1
    ts['m'+str(lookback)] = MOMENTUM(ts, lookback=lookback, 
        time_frame='monthly', price='close', prevday=True)
    """

    if lookback < 1:
        raise ValueError('lookback must be positive')

    if time_frame=='daily':     factor = 1
    elif time_frame=='weekly':  factor = pf.TRADING_DAYS_PER_WEEK
    elif time_frame=='monthly': factor = pf.TRADING_DAYS_PER_MONTH
    elif time_frame=='yearly':  factor = pf.TRADING_DAYS_PER_YEAR
    else:
        raise ValueError('invalid time_frame "{}"'.format(time_frame))

    s = ts[price].pct_change(periods=lookback*factor)
    if prevday:
        s = s.shift()

    return s

#####################################################################
# VOLATILITY

def VOLATILITY(ts, lookback=20, time_frame='yearly',
               price='close', prevday=False):

    """
    ts: dataframe with 'open', 'high', 'low', 'close', 'volume'
    lookback: the number of trading days to lookback, i.e. 20 days
    timeframe: daily, weekly, monthly, or yearly
    price: input_array column to use
    prevday: True will shift the series forward; unless you are buying
      on the close, you'll likely want to set this to True.
      It gives you the previous day's Volatility

    ex:
    lookback = 20
    ts['vola'] = VOLATILITY(ts, lookback=lookback, 
        time_frame='yearly', price='close', prevday=True)
    """

    if lookback < 1:
        raise ValueError('lookback must be positive')

    if time_frame=='daily':     factor = 1
    elif time_frame=='weekly':  factor = pf.TRADING_DAYS_PER_WEEK
    elif time_frame=='monthly': factor = pf.TRADING_DAYS_PER_MONTH
    elif time_frame=='yearly':  factor = pf.TRADING_DAYS_PER_YEAR
    else:
        raise ValueError('invalid time_frame "{}"'.format(time_frame))

    s = ts[price].pct_change().rolling(window=lookback).std() * np.sqrt(factor)
    if prevday:
        s = s.shift()

    return s

