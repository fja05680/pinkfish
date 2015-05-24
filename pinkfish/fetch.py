"""
fetch
---------
Retrive time series data
"""

# Use future imports for python 3.0 forward compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# Other imports
import pandas as pd
from pandas.io.data import DataReader
import datetime
import os

def _adj_column_names(ts):
    """
    ta-lib expects columns to be lower case; to be consistent,
    change date index
    """
    ts.columns = [col.lower().replace(' ','_') for col in ts.columns]
    ts.index.names = ['date']
    return ts

def fetch_timeseries(symbol, dir_name='data', use_cache=True):
    """
    Read time series data. Use cached version if it exists and
    use_cache is True, otherwise retrive, cache, then read.
    """
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)    

    timeseries_cache = os.path.join(dir_name, symbol + '.' + '.csv')
    
    if os.path.isfile(timeseries_cache) and use_cache:
        pass
    else:
        ts = DataReader(symbol, 'yahoo', start=datetime.datetime(1900, 1, 1))
        ts.to_csv(timeseries_cache, encoding='utf-8')
    
    ts = pd.read_csv(timeseries_cache, index_col='Date', parse_dates=True)
    ts = _adj_column_names(ts)
    return ts

def _adj_prices(ts):
    """
    Back adjust prices relative to adj_close for dividends and splits
    """
    ts.is_copy = False  # prevents SettingWithCopyWarning
    ts['open'] = ts['open'] * ts['close'] / ts['adj_close']
    ts['high'] = ts['high'] * ts['close'] / ts['adj_close']
    ts['low'] = ts['low'] * ts['close'] / ts['adj_close']
    ts['close'] = ts['close'] * ts['close'] / ts['adj_close']
    return ts

def select_tradeperiod(ts, start, end, use_adj=False, pad=True):
    """
    Select a time slice of the data to trade from ts.  If pad=True,
    back date a year to allow time for long term indicators,
    e.g. 200sma is become valid
    """
    if start < ts.index[0]: start = ts.index[0]
    if end > ts.index[-1]: end = ts.index[-1]
    if pad:    
        ts = ts[start - datetime.timedelta(365):end]
    else:
        ts = ts[start:end]
    if use_adj:
        ts = _adj_prices(ts)
    return ts

