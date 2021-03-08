"""
statistics
---------
Calculate trading statistics
"""

import pandas as pd
import numpy as np
import operator
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
from numpy.lib.stride_tricks import as_strided
import pinkfish as pf


#####################################################################
# CONSTANTS

TRADING_DAYS_PER_YEAR = 252
TRADING_DAYS_PER_MONTH = 20
TRADING_DAYS_PER_WEEK = 5

SP500_BEGIN = '1957-03-04'

#####################################################################
# HELPER FUNCTIONS

def _difference_in_years(start, end):
    """ calculate the number of years between two dates """
    diff  = abs(start - end)
    diff_in_years = (diff.days + diff.seconds/86400)/365.2425
    return diff_in_years

def _get_trade_bars(ts, tlog, op):
    l = []
    for row in tlog.itertuples():
        if op(row.pl_cash, 0):
            l.append(len(ts[row.entry_date:row.exit_date].index))
    return l

def currency(amount):
    if amount >= 0:
        return '${:,.2f}'.format(amount)
    else:
        return '-${:,.2f}'.format(-amount)

#####################################################################
# OVERALL RESULTS

def beginning_balance(capital):
    return capital

def ending_balance(dbal):
    return dbal.iloc[-1]['close']

def total_net_profit(tlog):
    return tlog.iloc[-1]['cumul_total']

def gross_profit(tlog):
    return tlog[tlog['pl_cash'] > 0].sum()['pl_cash']

def gross_loss(tlog):
    return tlog[tlog['pl_cash'] < 0].sum()['pl_cash']

def profit_factor(tlog):
    if gross_profit(tlog) == 0: return 0
    if gross_loss(tlog) == 0: return 1000
    return gross_profit(tlog) / gross_loss(tlog) * -1

def return_on_initial_capital(tlog, capital):
    return total_net_profit(tlog) / capital * 100

def _cagr(B, A, n):
    """ calculate compound annual growth rate """
    if B < 0: B = 0
    return (math.pow(B / A, 1 / n) - 1) * 100

def annual_return_rate(end_balance, capital, start, end):
    B = end_balance
    A = capital
    n = _difference_in_years(start, end)
    return _cagr(B, A, n)

def trading_period(start, end):
    diff = relativedelta(end, start)
    return '{} years {} months {} days'.format(diff.years, diff.months, diff.days)

def _total_days_in_market(dbal):
    n = (dbal['shares'] > 0).sum()
    if dbal.iloc[-2]['shares'] > 0:
        n += 1
    return n

def pct_time_in_market(dbal):
    return _total_days_in_market(dbal) / len(dbal) * 100

#####################################################################
# LEVERAGE

def margin():
    return pf.TradeLog.margin

def avg_leverage(dbal):
    return dbal['leverage'].mean()

def max_leverage(dbal):
    return dbal['leverage'].max()

def min_leverage(dbal):
    return dbal['leverage'].min()

#####################################################################
# SUMS

def total_num_trades(tlog):
    return len(tlog)

def trades_per_year(tlog, start, end):
    diff = relativedelta(end, start)
    years = diff.years + diff.months/12 + diff.days/365
    return total_num_trades(tlog) / years

def num_winning_trades(tlog):
    return (tlog['pl_cash'] > 0).sum()

def num_losing_trades(tlog):
    return (tlog['pl_cash'] < 0).sum()

def num_even_trades(tlog):
    return (tlog['pl_cash'] == 0).sum()

def pct_profitable_trades(tlog):
    if total_num_trades(tlog) == 0: return 0
    return num_winning_trades(tlog) / total_num_trades(tlog) * 100

#####################################################################
# CASH PROFITS AND LOSSES

def avg_profit_per_trade(tlog):
    if total_num_trades(tlog) == 0: return 0
    return total_net_profit(tlog) / total_num_trades(tlog)

def avg_profit_per_winning_trade(tlog):
    if num_winning_trades(tlog) == 0: return 0
    return gross_profit(tlog) / num_winning_trades(tlog)

def avg_loss_per_losing_trade(tlog):
    if num_losing_trades(tlog) == 0: return 0
    return gross_loss(tlog) / num_losing_trades(tlog)

def ratio_avg_profit_win_loss(tlog):
    if avg_profit_per_winning_trade(tlog) == 0: return 0
    if avg_loss_per_losing_trade(tlog) == 0: return 1000
    return (avg_profit_per_winning_trade(tlog) /
            avg_loss_per_losing_trade(tlog) * -1)

def largest_profit_winning_trade(tlog):
    if num_winning_trades(tlog) == 0: return 0
    return tlog[tlog['pl_cash'] > 0].max()['pl_cash']

def largest_loss_losing_trade(tlog):
    if num_losing_trades(tlog) == 0: return 0
    return tlog[tlog['pl_cash'] < 0].min()['pl_cash']

#####################################################################
# POINTS

def num_winning_points(tlog):
    if num_winning_trades(tlog) == 0: return 0
    return tlog[tlog['pl_points'] > 0].sum()['pl_points']

def num_losing_points(tlog):
    if num_losing_trades(tlog) == 0: return 0
    return tlog[tlog['pl_points'] < 0].sum()['pl_points']

def total_net_points(tlog):
    return num_winning_points(tlog) + num_losing_points(tlog)

def avg_points(tlog):
    if total_num_trades(tlog) == 0: return 0
    return tlog['pl_points'].sum() / len(tlog.index)

def largest_points_winning_trade(tlog):
    if num_winning_trades(tlog) == 0: return 0
    return tlog[tlog['pl_points'] > 0].max()['pl_points']

def largest_points_losing_trade(tlog):
    if num_losing_trades(tlog) == 0: return 0
    return tlog[tlog['pl_points'] < 0].min()['pl_points']

def avg_pct_gain_per_trade(tlog):
    if total_num_trades(tlog) == 0: return 0
    s = tlog['pl_points'] / tlog['entry_price']
    return np.average(s) * 100

def largest_pct_winning_trade(tlog):
    if num_winning_trades(tlog) == 0: return 0
    df = tlog[tlog['pl_points'] > 0]
    s = df['pl_points'] / df['entry_price']
    return s.max() * 100

def largest_pct_losing_trade(tlog):
    if num_losing_trades(tlog) == 0: return 0
    df = tlog[tlog['pl_points'] < 0]
    s = df['pl_points'] / df['entry_price']
    return s.min() * 100

def expected_shortfall(tlog):
    if total_num_trades(tlog) == 0: return 0
    df = tlog[tlog['pl_points'] < 0]
    s = df['pl_points'] / df['entry_price']
    l = sorted(s)
    end = int(len(l) * .05)
    avg = np.mean(l[:end]) *100 if end > 0 else 0
    return avg

#####################################################################
# STREAKS

def _subsequence(s, c):
    """
    Takes as parameter list like object s and returns the length of the longest
    subsequence of s constituted only by consecutive character 'c's.
    Example: If the string passed as parameter is "001000111100", and c is '0',
    then the longest subsequence of only '0's has length 3.
    """

    count = 0      # current length of the sequence of zeros
    maxlen = 0     # temporary value of the maximum length

    for bit in s:
        if bit == c:            # we have read a new '0'
            count += 1          # update the length of the current sequence
            if count > maxlen:  # if necessary, update the temporary maximum
                maxlen = count
        else:                   # we have read a 1
            count = 0           # reset the length of the current sequence
    return maxlen

def max_consecutive_winning_trades(tlog):
    if num_winning_trades(tlog) == 0: return 0
    return _subsequence(tlog['pl_cash'] > 0, True)

def max_consecutive_losing_trades(tlog):
    if num_losing_trades(tlog) == 0: return 0
    return _subsequence(tlog['pl_cash'] > 0, False)

def avg_bars_winning_trades(ts, tlog):
    if num_winning_trades(tlog) == 0: return 0
    return np.average(_get_trade_bars(ts, tlog, operator.gt))

def avg_bars_losing_trades(ts, tlog):
    if num_losing_trades(tlog) == 0: return 0
    return np.average(_get_trade_bars(ts, tlog, operator.lt))

#####################################################################
# DRAWDOWN AND RUNUP

def max_closed_out_drawdown(close):
    """ only compare each point to the previous running peak O(N) """
    running_max = pd.Series(close).expanding(min_periods=1).max()
    cur_dd = (close - running_max) / running_max * 100
    dd_max = min(0, cur_dd.min())
    idx = cur_dd.idxmin()

    dd = pd.Series()
    dd['max'] = dd_max
    dd['peak'] = running_max[idx]
    dd['trough'] = close[idx]
    dd['peak_date'] = close[close == dd['peak']].index[0].strftime('%Y-%m-%d')
    dd['trough_date'] = idx.strftime('%Y-%m-%d')
    close = close[close.index > idx]

    rd_mask = close > dd['peak']
    if rd_mask.any():
        dd['recovery_date'] = close[rd_mask].index[0].strftime('%Y-%m-%d')
    else:
        dd['recovery_date'] = 'Not Recovered Yet'

    return dd

def max_intra_day_drawdown(high, low):
    """ only compare each point to the previous running peak O(N) """
    running_max = pd.Series(high).expanding(min_periods=1).max()
    cur_dd = (low - running_max) / running_max * 100
    dd_max = min(0, cur_dd.min())
    idx = cur_dd.idxmin()

    dd = pd.Series()
    dd['max'] = dd_max
    dd['peak'] = running_max[idx]
    dd['trough'] = low[idx]
    dd['peak_date'] = high[high == dd['peak']].index[0].strftime('%Y-%m-%d')
    dd['trough_date'] = idx.strftime('%Y-%m-%d')
    high = high[high.index > idx]

    rd_mask = high > dd['peak']
    if rd_mask.any():
        dd['recovery_date'] = high[rd_mask].index[0].strftime('%Y-%m-%d')
    else:
        dd['recovery_date'] = 'Not Recovered Yet'

    return dd

def drawdown_loss_recovery_period(peak_date, trough_date , recovery_date):
    if recovery_date == 'Not Recovered Yet':
        loss_period = recovery_period = recovery_date
    else:
        peak_date = datetime.strptime(peak_date, '%Y-%m-%d')
        trough_date = datetime.strptime(trough_date, '%Y-%m-%d')
        recovery_date = datetime.strptime(recovery_date, '%Y-%m-%d')
        loss_period = abs(peak_date - trough_date).days
        loss_period = str(loss_period) + ' days'
        recovery_period = abs(trough_date-recovery_date).days
        recovery_period = str(recovery_period) + ' days'
    return loss_period, recovery_period

def _windowed_view(x, window_size):
    """Create a 2d windowed view of a 1d array.

    `x` must be a 1d numpy array.

    `numpy.lib.stride_tricks.as_strided` is used to create the view.
    The data is not copied.

    Example:

    >>> x = np.array([1, 2, 3, 4, 5, 6])
    >>> _windowed_view(x, 3)
    array([[1, 2, 3],
           [2, 3, 4],
           [3, 4, 5],
           [4, 5, 6]])
    """
    y = as_strided(x, shape=(x.size - window_size + 1, window_size),
                   strides=(x.strides[0], x.strides[0]))
    return y

def rolling_max_dd(ser, period, min_periods=1):
    """Compute the rolling maximum drawdown of `ser`.

    `ser` must be a Series.
    `min_periods` should satisfy `1 <= min_periods <= window_size`.

    Returns an 1d array with length `len(x) - min_periods + 1`.
    """
    window_size = period + 1
    x = ser.values
    if min_periods < window_size:
        pad = np.empty(window_size - min_periods)
        pad.fill(x[0])
        x = np.concatenate((pad, x))
    y = _windowed_view(x, window_size)
    running_max_y = np.maximum.accumulate(y, axis=1)
    dd = (y - running_max_y) / running_max_y * 100
    rmdd = dd.min(axis=1)
    return pd.Series(data=rmdd, index=ser.index, name=ser.name)

def rolling_max_ru(ser, period, min_periods=1):
    """Compute the rolling maximum runup of `ser`.

    `ser` must be a Series.
    `min_periods` should satisfy `1 <= min_periods <= window_size`.

    Returns an 1d array with length `len(x) - min_periods + 1`.
    """
    window_size = period + 1
    x = ser.values
    if min_periods < window_size:
        pad = np.empty(window_size - min_periods)
        pad.fill(x[0])
        x = np.concatenate((pad, x))
    y = _windowed_view(x, window_size)
    running_min_y = np.minimum.accumulate(y, axis=1)
    ru = (y - running_min_y) / running_min_y * 100
    rmru = ru.max(axis=1)
    return pd.Series(data=rmru, index=ser.index, name=ser.name)

#####################################################################
# PERCENT CHANGE - used to compute several stastics

def pct_change(close: pd.Series, period: int) -> pd.Series:
    diff = (close.shift(-period) - close) / close * 100
    diff.dropna(inplace=True)
    return diff

#####################################################################
# RATIOS

def sharpe_ratio(rets, risk_free=0.00, period=TRADING_DAYS_PER_YEAR):
    """
    summary Returns the daily Sharpe ratio of the returns.
    param rets: 1d numpy array or fund list of daily returns (centered on 0)
    param risk_free: risk free returns, default is 0%
    return Sharpe Ratio, computed off daily returns
    """
    dev = np.std(rets, axis=0)
    mean = np.mean(rets, axis=0)
    sharpe = (mean*period - risk_free) / (dev * np.sqrt(period))
    return sharpe

def sortino_ratio(rets, risk_free=0.00, period=TRADING_DAYS_PER_YEAR):
    """
    summary Returns the daily Sortino ratio of the returns.
    param rets: 1d numpy array or fund list of daily returns (centered on 0)
    param risk_free: risk free return, default is 0%
    return Sortino Ratio, computed off daily returns
    """
    mean = np.mean(rets, axis=0)
    negative_rets = rets[rets < 0]
    dev = np.std(negative_rets, axis=0)
    sortino = (mean*period - risk_free) / (dev * np.sqrt(period))
    return sortino

#####################################################################
# STATS - this is the primary call used to generate the results

def stats(ts, tlog, dbal, capital):
    """
    Compute trading stats
    Parameters
    ----------
    ts : Dataframe
        Time series of security prices (date, high, low, close, volume,
        adj_close)
    tlog : Dataframe
        Trade log (entry_date, entry_price, long_short, qty,
        exit_date, exit_price, pl_points, pl_cash, cumul_total)
    dbal : Dataframe
        Daily Balance (date, high, low, close)
    capital : float
        starting capital

    Examples
    --------

    Returns
    -------
    stats : Series of stats
    """

    start = ts.index[0]
    end = ts.index[-1]

    stats = pd.Series(dtype='object')

    # OVERALL RESULTS
    stats['start'] = start.strftime('%Y-%m-%d')
    stats['end'] = end.strftime('%Y-%m-%d')
    stats['beginning_balance'] = beginning_balance(capital)
    stats['ending_balance'] = ending_balance(dbal)
    stats['total_net_profit'] = total_net_profit(tlog)
    stats['gross_profit'] = gross_profit(tlog)
    stats['gross_loss'] = gross_loss(tlog)
    stats['profit_factor'] = profit_factor(tlog)
    stats['return_on_initial_capital'] = return_on_initial_capital(tlog, capital)
    cagr = annual_return_rate(dbal['close'][-1], capital, start, end)
    stats['annual_return_rate'] = cagr
    stats['trading_period'] = trading_period(start, end)
    stats['pct_time_in_market'] = pct_time_in_market(dbal)

    # LEVERAGE
    stats['margin'] = margin()
    stats['avg_leverage'] = avg_leverage(dbal)
    stats['max_leverage'] = max_leverage(dbal)
    stats['min_leverage'] = min_leverage(dbal)

    # SUMS
    stats['total_num_trades'] = total_num_trades(tlog)
    stats['trades_per_year'] = trades_per_year(tlog, start, end)
    stats['num_winning_trades'] = num_winning_trades(tlog)
    stats['num_losing_trades'] = num_losing_trades(tlog)
    stats['num_even_trades'] = num_even_trades(tlog)
    stats['pct_profitable_trades'] = pct_profitable_trades(tlog)

    # CASH PROFITS AND LOSSES
    stats['avg_profit_per_trade'] = avg_profit_per_trade(tlog)
    stats['avg_profit_per_winning_trade'] = avg_profit_per_winning_trade(tlog)
    stats['avg_loss_per_losing_trade'] = avg_loss_per_losing_trade(tlog)
    stats['ratio_avg_profit_win_loss'] = ratio_avg_profit_win_loss(tlog)
    stats['largest_profit_winning_trade'] = largest_profit_winning_trade(tlog)
    stats['largest_loss_losing_trade'] = largest_loss_losing_trade(tlog)

    # POINTS
    stats['num_winning_points'] = num_winning_points(tlog)
    stats['num_losing_points'] = num_losing_points(tlog)
    stats['total_net_points'] = total_net_points(tlog)
    stats['avg_points'] = avg_points(tlog)
    stats['largest_points_winning_trade'] = largest_points_winning_trade(tlog)
    stats['largest_points_losing_trade'] = largest_points_losing_trade(tlog)
    stats['avg_pct_gain_per_trade'] = avg_pct_gain_per_trade(tlog)
    stats['largest_pct_winning_trade'] = largest_pct_winning_trade(tlog)
    stats['largest_pct_losing_trade'] = largest_pct_losing_trade(tlog)
    stats['expected_shortfall'] = expected_shortfall(tlog)

    # STREAKS
    stats['max_consecutive_winning_trades'] = max_consecutive_winning_trades(tlog)
    stats['max_consecutive_losing_trades'] = max_consecutive_losing_trades(tlog)
    stats['avg_bars_winning_trades'] = avg_bars_winning_trades(ts, tlog)
    stats['avg_bars_losing_trades'] = avg_bars_losing_trades(ts, tlog)

    # DRAWDOWN
    dd = max_closed_out_drawdown(dbal['close'])
    stats['max_closed_out_drawdown'] = dd['max']
    stats['max_closed_out_drawdown_peak_date'] = dd['peak_date']
    stats['max_closed_out_drawdown_trough_date'] = dd['trough_date']
    stats['max_closed_out_drawdown_recovery_date'] = dd['recovery_date']
    stats['drawdown_loss_period'], stats['drawdown_recovery_period'] = \
        drawdown_loss_recovery_period(dd['peak_date'], dd['trough_date'],
                                      dd['recovery_date'])
    stats['annualized_return_over_max_drawdown'] = abs(cagr / dd['max'])
    dd = max_intra_day_drawdown(dbal['high'], dbal['low'])
    stats['max_intra_day_drawdown'] = dd['max']
    dd = rolling_max_dd(dbal['close'], TRADING_DAYS_PER_YEAR)
    stats['avg_yearly_closed_out_drawdown'] = np.average(dd)
    stats['max_yearly_closed_out_drawdown'] = min(dd)
    dd = rolling_max_dd(dbal['close'], TRADING_DAYS_PER_MONTH)
    stats['avg_monthly_closed_out_drawdown'] = np.average(dd)
    stats['max_monthly_closed_out_drawdown'] = min(dd)
    dd = rolling_max_dd(dbal['close'], TRADING_DAYS_PER_WEEK)
    stats['avg_weekly_closed_out_drawdown'] = np.average(dd)
    stats['max_weekly_closed_out_drawdown'] = min(dd)

    # RUNUP
    ru = rolling_max_ru(dbal['close'], TRADING_DAYS_PER_YEAR)
    stats['avg_yearly_closed_out_runup'] = np.average(ru)
    stats['max_yearly_closed_out_runup'] = ru.max()
    ru = rolling_max_ru(dbal['close'], TRADING_DAYS_PER_MONTH)
    stats['avg_monthly_closed_out_runup'] = np.average(ru)
    stats['max_monthly_closed_out_runup'] = max(ru)
    ru = rolling_max_ru(dbal['close'], TRADING_DAYS_PER_WEEK)
    stats['avg_weekly_closed_out_runup'] = np.average(ru)
    stats['max_weekly_closed_out_runup'] = max(ru)

    # PERCENT CHANGE
    pc = pct_change(dbal['close'], TRADING_DAYS_PER_YEAR)
    if len(pc) > 0:
        stats['pct_profitable_years'] = (pc > 0).sum() / len(pc) * 100
        stats['best_year'] = pc.max()
        stats['worst_year'] = pc.min()
        stats['avg_year'] = np.average(pc)
        stats['annual_std'] = pc.std()
    pc = pct_change(dbal['close'], TRADING_DAYS_PER_MONTH)
    if len(pc) > 0:
        stats['pct_profitable_months'] = (pc > 0).sum() / len(pc) * 100
        stats['best_month'] = pc.max()
        stats['worst_month'] = pc.min()
        stats['avg_month'] = np.average(pc)
        stats['monthly_std'] = pc.std()
    pc = pct_change(dbal['close'], TRADING_DAYS_PER_WEEK)
    if len(pc) > 0:
        stats['pct_profitable_weeks'] = (pc > 0).sum() / len(pc) * 100
        stats['best_week'] = pc.max()
        stats['worst_week'] = pc.min()
        stats['avg_week'] = np.average(pc)
        stats['weekly_std'] = pc.std()
    pc = pct_change(dbal['close'], 1)
    if len(pc) > 0:
        stats['pct_profitable_days'] = (pc > 0).sum() / len(pc) * 100
        stats['best_day'] = pc.max()
        stats['worst_day'] = pc.min()
        stats['avg_day'] = np.average(pc)
        stats['daily_std'] = pc.std()

    # RATIOS
    sr = sharpe_ratio(dbal['close'].pct_change())
    sr_std = math.sqrt((1 + 0.5*sr**2) / len(dbal))
    stats['sharpe_ratio'] = sr
    stats['sharpe_ratio_max'] = sr + 3*sr_std #3 std=>99.73%
    stats['sharpe_ratio_min'] = sr - 3*sr_std
    stats['sortino_ratio'] = sortino_ratio(dbal['close'].pct_change())
    return stats

#####################################################################
# SUMMARY - stats() must be called before calling summary()

default_metrics = (
    'annual_return_rate',
    'max_closed_out_drawdown',
    'best_month',
    'worst_month',
    'sharpe_ratio',
    'sortino_ratio',
    'monthly_std',
    'annual_std')

currency_metrics = (
    'beginning_balance',
    'ending_balance',
    'total_net_profit',
    'gross_profit',
    'gross_loss')

def _get_metric_value(s, metric):
    metrics = (
        'beginning_balance',
        'ending_balance',
        'ending_balance',
        'total_net_profit',
        'gross_profit',
        'gross_loss')
    if metric in metrics:
        return currency(s[metric])
    else:
        return s[metric]

def summary(stats, benchmark_stats=None, metrics=default_metrics, extras=None):
    """
    Returns stats summary in a DataFrame.
    stats() must be called before calling this function
    """
    if extras is None: extras = ()
    metrics += extras

    # columns
    columns = ['strategy']
    if benchmark_stats is not None:
        columns.append('benchmark')

    # index & data
    index = []; data = []
    for metric in metrics:
        index.append(metric)
        if benchmark_stats is not None:
            data.append((_get_metric_value(stats, metric),
                         _get_metric_value(benchmark_stats, metric)))
        else:
            data.append(_get_metric_value(stats, metric))

    df = pd.DataFrame(data, columns=columns, index=index)
    return df

