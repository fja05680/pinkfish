"""
Fetch time series data.
"""

import datetime
import os
from pathlib import Path
import sys
import warnings

import pandas as pd
import requests
import yfinance as yf

from pinkfish.pfstatistics import (
    select_trading_days
)
from pinkfish.stock_market_calendar import (
    stock_market_calendar
)
import pinkfish.utility as utility


########################################################################
# TIMESERIES (fetch, select, finalize)

FXMACRODATA_API_ROOT = 'https://fxmacrodata.com/api/v1'
TIINGO_API_ROOT = 'https://api.tiingo.com/tiingo/daily'
TIINGO_API_KEY_PATH = Path('~/.tiingo').expanduser()

_TIMESERIES_SOURCES = {
    'yahoo': 'symbol-cache',
    'tiingo': 'tiingo-cache',
}

_FX_TIMESERIES_SOURCES = {
    'fxmacrodata': 'fxmacrodata-cache',
}

def _get_cache_dir(dir_name):
    """
    Get the data dir path.

    Parameters
    ----------
    dir_name : Path
        The leaf data dir name.

    Returns
    -------
    str
        Path to the data dir.
    """
    base_dir = utility.ROOT
    try:
        conf = utility.read_config()
        base_dir = conf['base_dir']
    except Exception as e:
        pass
    finally:
        dir_path = Path(base_dir) / dir_name

    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)

    return dir_path


def _normalize_symbol(symbol):
    """
    Make symbol names uppercase and strip pinkfish suffixes.
    """
    symbol = symbol.upper()
    # pinkfish allows the use of a suffix starting with a '_',
    # like SPY_SHRT, so extract the symbol.
    return symbol.split('_')[0]


def _default_from_year():
    """
    Return the default start year for timeseries retrieval.
    """
    return 1900 if not sys.platform.startswith('win') else 1971


def _read_tiingo_api_key(path=None):
    """
    Read a Tiingo API key from a file.

    The file should contain the API key on the first non-empty line.
    Lines beginning with ``#`` are ignored.
    """
    if path is None:
        path = TIINGO_API_KEY_PATH
    if not path.is_file():
        return None

    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        return line
    return None


def _get_tiingo_api_key(api_key=None):
    """
    Resolve a Tiingo API key from a parameter, ``~/.tiingo``, or env var.
    """
    if api_key:
        return api_key

    api_key = _read_tiingo_api_key()
    if api_key:
        return api_key

    return os.environ.get('TIINGO_API_KEY')


def _load_timeseries_cache(timeseries_cache):
    """
    Read a cached timeseries CSV in pinkfish format.
    """
    ts = pd.read_csv(timeseries_cache, index_col='Date', parse_dates=True)
    ts = _adj_column_names(ts)
    ts = ts[~ts.index.duplicated(keep='first')]
    return ts


def _adj_column_names(ts):
    """
    Make all column names lower case.

    ta-lib expects columns to be lower case. To be consistent,
    make date index lowercase also.  Replace spaces with underscores.

    Parameters
    ----------
    ts : pd.DataFrame
        The timeseries of a symbol.

    Returns
    -------
    pd.DataFrame
        The timeseries with adjusted column names.
    """
    ts.columns = [col.lower().replace(' ','_') for col in ts.columns]
    ts.index.names = ['date']
    return ts


def _split_fx_pair(pair):
    pair = pair.upper().replace('/', '').replace('-', '').replace('_', '')
    if len(pair) != 6:
        raise ValueError("FX pair must be formatted like 'EURUSD' or 'EUR/USD'")
    return pair[:3], pair[3:]


def fetch_fxmacrodata_timeseries(pair, start, end, api_key=None,
                                 api_root=FXMACRODATA_API_ROOT,
                                 dir_name='fxmacrodata-cache',
                                 use_cache=True):
    """
    Read daily FX reference rates from FXMacroData.

    FXMacroData returns one official reference value per date. Pinkfish expects
    OHLCV-style bars, so the reference value is copied into open, high, low,
    close, and adj_close with zero volume.
    """
    base, quote = _split_fx_pair(pair)
    symbol = base + quote
    timeseries_cache = _get_cache_dir(dir_name) / f'{symbol}.csv'

    if not (timeseries_cache.is_file() and use_cache):
        params = {
            'start_date': start,
            'end_date': end,
            'limit': 5000,
        }
        if api_key:
            params['api_key'] = api_key

        url = f"{api_root.rstrip('/')}/forex/{base}/{quote}"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        rows = response.json().get('data', [])

        records = []
        for row in rows:
            value = float(row['val'])
            records.append({
                'Date': row['date'],
                'Open': value,
                'High': value,
                'Low': value,
                'Close': value,
                'Adj Close': value,
                'Volume': 0.0,
            })

        ts = pd.DataFrame.from_records(records)
        if ts.empty:
            print(f'No FXMacroData data for {base}/{quote}')
            return None
        ts = ts.sort_values('Date')
        ts.to_csv(timeseries_cache, index=False, encoding='utf-8')

    return _load_timeseries_cache(timeseries_cache)


def fetch_fx_timeseries(pair, start, end, dir_name=None, use_cache=True,
                        source='fxmacrodata', **kwargs):
    """
    Read daily FX timeseries data.

    Parameters
    ----------
    pair : str
        The FX pair, e.g. ``'EUR/USD'`` or ``'EURUSD'``.
    start : str
        The start date (``'YYYY-MM-DD'``).
    end : str
        The end date (``'YYYY-MM-DD'``).
    dir_name : str, optional
        The leaf data dir name.  Defaults to ``fxmacrodata-cache`` for
        FXMacroData.
    use_cache : bool, optional
        True to use data cache.  False to retrieve from the internet
        (default is True).
    source : {'fxmacrodata'}, optional
        The data vendor to use (default is ``'fxmacrodata'``).
    **kwargs
        Additional keyword arguments passed to the vendor fetcher.

    Returns
    -------
    pd.DataFrame
        The timeseries of an FX pair.
    """
    try:
        default_dir_name = _FX_TIMESERIES_SOURCES[source]
    except KeyError as exc:
        raise ValueError(
            f"Unknown FX data source: {source!r}. "
            f"Choose from {sorted(_FX_TIMESERIES_SOURCES)}."
        ) from exc

    if dir_name is None:
        dir_name = default_dir_name

    fetchers = {
        'fxmacrodata': fetch_fxmacrodata_timeseries,
    }
    return fetchers[source](
        pair,
        start,
        end,
        dir_name=dir_name,
        use_cache=use_cache,
        **kwargs,
    )


def fetch_yahoo_finance_timeseries(symbol, dir_name='symbol-cache',
                                   use_cache=True, from_year=None):
    """
    Read daily OHLCV data from Yahoo Finance.

    Use cached version if it exists and use_cache is True, otherwise
    retrieve, cache, then read.
    """
    symbol = _normalize_symbol(symbol)
    if from_year is None:
        from_year = _default_from_year()

    timeseries_cache = _get_cache_dir(dir_name) / f'{symbol}.csv'

    if not (timeseries_cache.is_file() and use_cache):
        try:
            ts = yf.download(symbol, start=datetime.datetime(from_year, 1, 1),
                             progress=False, auto_adjust=False,
                             multi_level_index=False)
            if ts.empty:
                print(f'No Data for {symbol}')
                return None
        except Exception as e:
            print(f'\n{e}')
            return None
        else:
            column_order = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
            ts = ts[column_order]
            ts.to_csv(timeseries_cache, encoding='utf-8')

    return _load_timeseries_cache(timeseries_cache)


def fetch_tiingo_timeseries(symbol, dir_name='tiingo-cache', use_cache=True,
                            from_year=None, api_key=None,
                            api_root=TIINGO_API_ROOT):
    """
    Read daily OHLCV data from Tiingo.

    Use cached version if it exists and use_cache is True, otherwise
    retrieve, cache, then read.

    The API key is read from ``api_key``, then ``~/.tiingo``, then the
    ``TIINGO_API_KEY`` environment variable.
    """
    symbol = _normalize_symbol(symbol)
    if from_year is None:
        from_year = _default_from_year()

    timeseries_cache = _get_cache_dir(dir_name) / f'{symbol}.csv'

    if not (timeseries_cache.is_file() and use_cache):
        api_key = _get_tiingo_api_key(api_key)
        if not api_key:
            raise ValueError(
                'Tiingo API key required: pass api_key, create ~/.tiingo, '
                'or set TIINGO_API_KEY'
            )

        url = f"{api_root.rstrip('/')}/{symbol}/prices"
        params = {'startDate': f'{from_year}-01-01'}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {api_key}',
        }
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        rows = response.json()

        records = []
        for row in rows:
            records.append({
                'Date': row['date'][:10],
                'Open': row['open'],
                'High': row['high'],
                'Low': row['low'],
                'Close': row['close'],
                'Adj Close': row['adjClose'],
                'Volume': row['volume'],
            })

        ts = pd.DataFrame.from_records(records)
        if ts.empty:
            print(f'No Tiingo data for {symbol}')
            return None
        ts = ts.sort_values('Date')
        ts.to_csv(timeseries_cache, index=False, encoding='utf-8')

    return _load_timeseries_cache(timeseries_cache)


def fetch_timeseries(symbol, dir_name=None, use_cache=True, from_year=None,
                     source='yahoo', **kwargs):
    """
    Read time series data.

    Use cached version if it exists and use_cache is True, otherwise
    retrive, cache, then read.

    Parameters
    ----------
    symbol : str
        The symbol for a security.
    dir_name : str, optional
        The leaf data dir name.  Defaults to ``symbol-cache`` for Yahoo
        Finance and ``tiingo-cache`` for Tiingo.
    use_cache: bool, optional
        True to use data cache.  False to retrieve from the internet
        (default is True).
    from_year: int, optional
        The start year for timeseries retrieval (default is None,
        which implies that all the available data is retrieved).
    source : {'yahoo', 'tiingo'}, optional
        The data vendor to use (default is ``'yahoo'``).
    **kwargs
        Additional keyword arguments passed to the vendor fetcher.

    Returns
    -------
    pd.DataFrame
        The timeseries of a symbol.
    """
    try:
        default_dir_name = _TIMESERIES_SOURCES[source]
    except KeyError as exc:
        raise ValueError(
            f"Unknown data source: {source!r}. "
            f"Choose from {sorted(_TIMESERIES_SOURCES)}."
        ) from exc

    if dir_name is None:
        dir_name = default_dir_name

    fetchers = {
        'yahoo': fetch_yahoo_finance_timeseries,
        'tiingo': fetch_tiingo_timeseries,
    }
    return fetchers[source](
        symbol,
        dir_name=dir_name,
        use_cache=use_cache,
        from_year=from_year,
        **kwargs,
    )


def _adj_prices(ts):
    """
    Back adjust prices relative to adj_close for dividends and splits.

    Parameters
    ----------
    ts : pd.DataFrame
        The timeseries of a symbol.

    Returns
    -------
    pd.DataFrame
        The timeseries with adjusted prices.
    """
    ts['open'] = ts['open'] * ts['adj_close'] / ts['close']
    ts['high'] = ts['high'] * ts['adj_close'] / ts['close']
    ts['low'] = ts['low'] * ts['adj_close'] / ts['close']
    ts['close'] = ts['close'] * ts['adj_close'] / ts['close']
    return ts


def select_tradeperiod(ts, start, end, use_adj=False,
                       use_continuous_calendar=False,
                       force_stock_market_calendar=False,
                       check_fields=['close']):
    """
    Select the trade period.

    First, remove rows that have zero values in price columns. Then,
    select a time slice of the data to trade from ts.  Back date a year
    to allow time for long term indicators, e.g. 200sma is become valid.

    Parameters
    ----------
    ts : pd.DataFrame
        The timeseries of a symbol.
    start : datetime.datetime
        The desired start date for the strategy.
    end : datetime.datetime
        The desired end date for the strategy.
    use_adj : bool, optional
        True to adjust prices for dividends and splits
        (default is False).
    use_continuous_calendar: bool, optional
        True if your timeseries has data for all seven days a week,
        and you want to backtest trading every day, including weekends.
        If this value is True, then `force_stock_market_calendar`
        is set to False (default is False).
    force_stock_market_calendar : bool, optional
        True forces use of stock market calendar on timeseries.
        Normally, you don't need to do this.  This setting is intended
        to transform a continuous timeseries into a weekday timeseries.
        If this value is True, then `use_continuous_calendar` is set
        to False (default is False).
    check_fields : list of str, optional {'open', 'high', 'low',
        'close', 'adj_close'}
        Fields to check for for NaN values.  If a NaN value is found
        for one of these fields, that row is dropped
        (default is ['close']).

    Returns
    -------
    pd.DataFrame
        The timeseries for specified start:end, optionally with prices
        adjusted.

    Notes
    -----
    You should only set one of `use_continuous_calendar`=True or
    `force_stock_market_calendar`=True for a continuous timeseries.
    You should set neither of these to True if your timeseries is based
    on the stock market.
    """
    columns = ['open', 'high', 'low', 'close']
    if use_adj:
        columns.append('adj_close')

    # Replace 0 value columns with NaN.
    ts[columns] = ts[ts[columns] > 0][columns]

    if use_continuous_calendar:
        force_stock_market_calendar = False
    if force_stock_market_calendar:
        use_continuous_calendar = False

    if use_continuous_calendar:
        select_trading_days(use_stock_market_calendar=False)

    if force_stock_market_calendar:
        index = pd.to_datetime(stock_market_calendar)
        ts = ts.reindex(index=index)

    ts.dropna(subset=check_fields, inplace=True)

    if use_adj:
        _adj_prices(ts)

    if start < ts.index[0]:
        start = ts.index[0]
    if end > ts.index[-1]:
        end = ts.index[-1]
    ts = ts[start - datetime.timedelta(365):end]

    return ts


def finalize_timeseries(ts, start, dropna=False, drop_columns=None):
    """
    Finalize timeseries.

    Drop all rows that have nan column values.  Set timeseries to begin
    at start.

    Parameters
    ----------
    ts : pd.DataFrame
        The timeseries of a symbol.
    start : datetime.datetime
        The start date for backtest.
    dropna : bool, optional
        Drop rows that have a NaN value in one of it's columns
        (default is False).
    drop_columns : list of str, optional
        List of columns to drop from `ts` (default is None, which
        implies that no columns should be dropped).

    Returns
    -------
    datetime.datetime
        The start date.
    pd.DataFrame
        The timeseries of a symbol.
    """
    if drop_columns:
        ts.drop(columns=drop_columns, inplace=True)
    if dropna:
        ts.dropna(inplace=True)
    elif ts.isnull().values.any():
        warnings.warn("NaN value(s) detected in timeseries")
    ts = ts[start:]
    start = ts.index[0]
    return ts, start


#####################################################################
# CACHE SYMBOLS (remove, update, get_symbol_metadata)

def _difference_in_years(start, end):
    """
    Calculate the number of years between two dates.

    Parameters
    ----------
    start : datetime.datetime
        The start date.
    end : datetime.datetime
        The end date.

    Returns
    -------
    float
        The difference in years between start and end dates.
    """
    diff = end - start
    diff_in_years = (diff.days + diff.seconds/86400)/365.2425
    return diff_in_years


def remove_cache_symbols(symbols=None, dir_name='symbol-cache'):
    """
    Remove cached timeseries for list of symbols.

    Filter out any symbols prefixed with '__'.

    Parameters
    ----------
    symbols : str or list of str, optional
        The symbol(s) for which to remove cached timeseries (default
        is None, which implies remove timeseries for all symbols).
    dir_name : str, optional
        The leaf data dir name (default is 'symbol-cache').

    Returns
    -------
    None
    """
    cache_dir = _get_cache_dir(dir_name)

    if symbols:
        # If symbols is not a list, cast it to a list.
        if not isinstance(symbols, list):
            symbols = [symbols]
        filenames = [symbol.upper() + '.csv' for symbol in symbols]
    else:
        filenames = [f.name for f in cache_dir.iterdir() if f.suffix == '.csv']

    # Filter out any filename prefixed with '__'.
    filenames = [f for f in filenames if not f.startswith('__')]

    print('removing symbols:')
    for i, f in enumerate(filenames):
        symbol = Path(f).stem
        print(symbol + ' ', end='')
        if i % 10 == 0 and i != 0:
            print()

        filepath = cache_dir / f
        if filepath.exists():
            filepath.unlink()
        else:
            print(f'\n({f} not found)')
    print()


def update_cache_symbols(symbols=None, dir_name='symbol-cache', from_year=None):
    """
    Update cached timeseries for list of symbols.

    Filter out any filename prefixed with '__'.

    Parameters
    ----------
    symbols : str or list, optional
        The symbol(s) for which to update cached timeseries (default
        is None, which implies update timeseries for all symbols).
    dir_name : str, optional
        The leaf data dir name (default is 'symbol-cache').
    from_year: int, optional
        The start year for timeseries retrieval (default is None,
        which implies that all the available data is retrieved).

    Returns
    -------
    None
    """
    cache_dir = Path(_get_cache_dir(dir_name))

    if symbols:
        # If symbols is not a list, cast it to a list.
        if not isinstance(symbols, list):
            symbols = [symbols]
    else:
        filenames = [f for f in cache_dir.iterdir() if f.suffix == '.csv' and not f.name.startswith('__')]
        symbols = [f.stem for f in filenames]

    # Make symbol names uppercase.
    symbols = [symbol.upper() for symbol in symbols]

    print('Updating symbols:')
    for i, symbol in enumerate(symbols):
        print(f"{symbol} ", end='')
        if i % 10 == 0 and i != 0:
            print()

        try:
            fetch_timeseries(symbol, dir_name=dir_name, use_cache=False, from_year=from_year)
        except Exception as e:
            print(f'\n({e})')
    print()


from pathlib import Path
import pandas as pd

def get_symbol_metadata(symbols=None, dir_name='symbol-cache', from_year=None):
    """
    Get symbol metadata for list of symbols.

    Filter out any filename prefixed with '__'.

    Parameters
    ----------
    symbols : str or list, optional
        The symbol(s) for which to get symbol metadata (default
        is None, which implies get symbol metadata for all symbols).
    dir_name : str, optional
        The leaf data dir name (default is 'symbol-cache').
    from_year: int, optional
        The start year for timeseries retrieval (default is None,
        which implies that all the available data is retrieved).

    Returns
    -------
    pd.DataFrame
        Each row contains metadata for a symbol.
    """
    cache_dir = Path(_get_cache_dir(dir_name))

    if symbols:
        # If symbols is not a list, cast it to a list.
        if not isinstance(symbols, list):
            symbols = [symbols]
    else:
        filenames = [f for f in cache_dir.iterdir() if f.suffix == '.csv' and not f.name.startswith('__')]
        symbols = [f.stem for f in filenames]

    # Make symbol names uppercase.
    symbols = [symbol.upper() for symbol in symbols]

    metadata = []
    for i, symbol in enumerate(symbols):
        try:
            ts = fetch_timeseries(symbol, dir_name=dir_name, use_cache=True, from_year=from_year)
            start = ts.index[0].to_pydatetime()
            end = ts.index[-1].to_pydatetime()
            num_years = _difference_in_years(start, end)
            start_str = start.strftime('%Y-%m-%d')
            end_str = end.strftime('%Y-%m-%d')
            metadata.append((symbol, start_str, end_str, num_years))
        except Exception as e:
            print(f"\n({e})")

    columns = ['symbol', 'start_date', 'end_date', 'num_years']
    df = pd.DataFrame(metadata, columns=columns)
    return df


#####################################################################
# REAL TIME QUOTE

def get_quote(symbols):
    """
    Fetch the latest stock prices for a list of symbols.

    Parameters
    ----------
    symbols : list of str
        A list of stock symbols to retrieve quotes for.

    Returns
    -------
    dict
        A dictionary where keys are stock symbols and values are the latest stock prices.
        If a quote cannot be fetched, the value will be None.
    """
    d = {}
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        try:
            d[symbol] = float(ticker.fast_info['last_price'])
        except KeyError:
            print(f'Could not fetch quote for {symbol}')
            d[symbol] = None
    return d

