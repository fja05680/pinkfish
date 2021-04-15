"""
Custom indicators.
"""

import numpy as np
import pandas as pd
from talib.abstract import *

import pinkfish as pf


class IndicatorError(Exception):
    """
    Base indicator exception.
    """


########################################################################
# CROSSOVER

class TradeCrossOverError(IndicatorError):
    """
    Invalid timeperiod specified.
    """


class _CrossOver:
    """
    This is a helper class to implement the CROSSOVER function.

     The class provides the apply callback for pd.DataFrame.apply()
     in CROSSOVER.  It also keeps track of _r, explained below.

    _r indicates regime direction and duration, i.e. 50 means a bull
       market that has persisted for 50 days, whereas -20 means a bear
       market that has persisted for 20 days.
    _r is incremented(decremented) each day a bull(bear) market persists
    _r remains unchanged when fast_ma within band of slow_ma
    _r indicates the number of trading days a trend has persisted
    _r is nan, then sma_slow is nan
    _r > 0, then bull market, fast_ma > slow_ma
    _r < 0, then bear market, fast_ma < slow_ma
    _r == 0, no trend established yet
    """
    def __init__(self):
        """
        Initialize instance variables.

        Attributes
        ----------
        _r : int
            Indicates regime direction and duration.
        """
        self._r = 0

    def apply(self, row, band=0):
        """
        Implements the regime change logic.

        Parameters
        ----------
        row : pd.Series
            A row of data from the dataframe.
        band : int {0-100}
            Percent band (default is 0, which is no band).

        Returns
        -------
        _r : int
            Indicates regime direction and duration.
        """
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
    This indicator is used to represent regime direction and duration.

    For example, an indicator value of 50 means a bull market that has
    persisted for 50 days, whereas -20 means a bear market that has
    persisted for 20 days.

    More generally, this is a crossover indicator for two moving
    averages.  The indicator is positive when the fast moving average
    is above the slow moving arverage, and negative when the fast
    moving average is below the slow moving average.

    Parameters
    ----------
    ts : pd.DateFrame
        A dataframe with 'open', 'high', 'low', 'close', 'volume'.
    timeperiod_fast : int, optional
        The timeperiod for the fast moving average (default is 50).
    timeperiod_slow : int
        The timeperiod for the slow moving average (default is 200).
    func_fast : ta_lib.Function,
        {SMA, DEMA, EMA, KAMA, T3, TEMA, TRIMA, WMA}
        The talib function for fast moving average (default is SMA).
        MAMA not compatible.
    func_slow : ta_lib.Function,
        {SMA, DEMA, EMA, KAMA, T3, TEMA, TRIMA, WMA}
        The talib function for slow moving average. (default is SMA).
        MAMA not compatible.
    band : int, {0-100)
        Percent band around the slow moving average.
        (default is 0, which implies no band is used).
    price : str, {'close', 'open', 'high', 'low'}
        Input_array column to use for price (default is 'close').
    prevday : bool, optional
        True will shift the series forward.  Unless you are buying
        on the close, you'll likely want to set this to True.
        It gives you the previous day's CrossOver (default is False).

    Returns
    -------
    s : pd.Series
        A new column that contains the regime indicator values.

    Raises
    ------
    TradeCrossOverError
        If one of the timeperiods specified is invalid.

    Examples
    --------
    >>> ts['regime'] = pf.CROSSOVER(ts, timeperiod_fast=50,
                                    timeperiod_slow=200)

    >>> ts['crossover'] = CROSSOVER(ts, timeperiod_fast=1,
                                    timeperiod_slow=50, prevday=True)
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


########################################################################
# MOMENTUM

def MOMENTUM(ts, lookback=1, time_frame='monthly', price='close', prevday=False):
    """
    This indicator is used to represent momentum is security prices.

    Percent price change is used to calculate momentum.  Momentum
    is positive if the price since the lookback period has increased.
    Likewise, if price has decreased since the lookback period,
    momentum is negative.  Percent change is used to normalize
    asset prices for comparison.

    Parameters
    ----------
    ts : pd.DateFrame
        A dataframe with 'open', 'high', 'low', 'close', 'volume'.
    lookback : int, optional
        The number of time frames to lookback, i.e. 2 months
        (default is 1).
    timeframe : str, {'monthly', 'daily', 'weekly', 'yearly'}
        The unit or timeframe type of lookback (default is 'monthly').
    price : str, {'close', 'open', 'high', 'low'}
        Input_array column to use for price (default is 'close').
    prevday : bool, optional
        True will shift the series forward.  Unless you are buying
        on the close, you'll likely want to set this to True.
        It gives you the previous day's Momentum (default is False).

    Returns
    -------
    s : pd.Series
        A new column that contains the momentum indicator values.

    Raises
    ------
    ValueError
        If the lookback is not positive or the time_frame is invalid.

    Examples
    --------
    >>> ts['mom'] = pf.MOMENTUM(ts, lookback=6, time_frame='monthly')
    """
    if lookback < 1:
        raise ValueError('lookback must be positive')

    if   time_frame =='daily':   factor = 1
    elif time_frame =='weekly':  factor = pf.TRADING_DAYS_PER_WEEK
    elif time_frame =='monthly': factor = pf.TRADING_DAYS_PER_MONTH
    elif time_frame =='yearly':  factor = pf.TRADING_DAYS_PER_YEAR
    else:
        raise ValueError('invalid time_frame "{}"'.format(time_frame))

    s = ts[price].pct_change(periods=lookback*factor)
    if prevday:
        s = s.shift()

    return s


########################################################################
# VOLATILITY

def VOLATILITY(ts, lookback=20, time_frame='yearly', downside=False,
               price='close', prevday=False):
    """
    This indicator is used to represent volatility in security prices.

    Volatility is represented as the standard deviation.  Volatility
    is calculated over the lookback period, then we scale to the
    time frame.  Volatility scales with the square root of time.
    For example,  if the market’s daily volatility is 0.5%, then
    volatility for two days is the square root of 2 times
    the daily volatility (0.5% * 1.414 = 0.707%).  We use the square
    root of time to scale from daily to weely, monthly, or yearly.

    Parameters
    ----------
    ts : pd.DateFrame
        A dataframe with 'open', 'high', 'low', 'close', 'volume'.
    lookback : int, optional
        The number of time frames to lookback, i.e. 2 months
        (default is 1).
    timeframe : str, {'yearly', 'daily', 'weekly', 'monthly'}
        The unit or timeframe type of lookback (default is 'yearly').
    downside : bool, optional
        True to calculate the downside volatility (default is False).
    price : str, {'close', 'open', 'high', 'low'}
        Input_array column to use for price (default is 'close').
    prevday : bool 
        True will shift the series forward.  Unless you are buying
        on the close, you'll likely want to set this to True.
        It gives you the previous day's Volatility (default is False).

    Returns
    -------
    s : pd.Series
        A new column that contains the rollowing volatility.

    Raises
    ------
    ValueError
        If the lookback is not positive or the time_frame is invalid.

    Examples
    --------
    >>> ts['vola'] = pf.MOMENTUM(ts, lookback=20, time_frame='yearly')
    """
    if lookback < 1:
        raise ValueError('lookback must be positive')

    if   time_frame == 'daily':   factor = 1
    elif time_frame == 'weekly':  factor = pf.TRADING_DAYS_PER_WEEK
    elif time_frame == 'monthly': factor = pf.TRADING_DAYS_PER_MONTH
    elif time_frame == 'yearly':  factor = pf.TRADING_DAYS_PER_YEAR
    else:
        raise ValueError('invalid time_frame "{}"'.format(time_frame))

    s = ts[price].pct_change()
    if downside:
        s[s > 0] = 0
    s = s.rolling(window=lookback).std() * np.sqrt(factor)

    if prevday:
        s = s.shift()

    return s
