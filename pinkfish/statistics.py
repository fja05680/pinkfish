"""
Calculate trading statistics.

The stats() function returns the following metrics in a pd.Series.

 - `start` : str  
   The date when trading begins formatted as YY-MM-DD.

 - `end` : str  
   The date when trading ends formatted as YY-MM-DD.

 - `beginning_balance` : int  
    The initial capital.

 - `ending_balance` : float  
    The ending capital.

 - `total_net_profit` : float  
    Total value of all profitable trades minus all losing trades.

 - `gross_profit` : float  
    Total value of all profitable trades.

 - `gross_loss` : float  
    Total value of all losing trades.

 - `profit_factor` : float  
    The Ratio of the total profits from profitable trades divided by
    the total loses from losing trades.  A break-even system has a
    profit factor of 1.

 - `return_on_initial_capital` : float  
    The ratio of gross profit divided by the initial capital and
    multiplied by 100.

 - `annual_return_rate` : float  
    The compound annual growth rate of the strategy.

 - `trading_period` : str  
    The trading time frame expressed as years, monthe, and days.

 - `pct_time_in_market` : float  
    The percentage of days in which the strategy is not completely
    holding cash.

 - `margin` : float  
    The buying power in dollars divided by the capital.  For example,
    if the margin is 2 and the capital is $10,000, then the buying
    power is $20,000.

 - `avg_leverage` : float  
    Leverage is the total value of securities held plus any cash,
    divided by the total value of securities held plus cash minus
    loans.  The average leverage is just the average daily leverage
    over the life of the strategy.

 - `max_leverage` : float  
    The maximum daily leverage over the life of the strategy.

 - `min_leverage` : float  
    The minimum daily leverage over the life of the strategy.

 - `total_num_trades` : int  
    The number of closed trades.

 - `trades_per_year` : float  
    The average number of closed trades per year.

 - `num_winning_trades` : int  
    The number of profitable trades.

 - `num_losing_trades` : int  
    The number of losing trades.

 - `num_even_trades` : int  
    The number of break even trades.

 - `pct_profitable_trades` : float  
    The number of winning trades divided by the total number of closed
    trades and multiplied by 100.

 - `avg_profit_per_trade` : float  
    The total net profit divided by the total number of closed trades
    and multiplied by 100.

 - `avg_profit_per_winning_trade` : float  
    The gross profit divided by the number of winning trades.

 - `avg_loss_per_losing_trade` : float  
    The gross loss divided by the number of losing trades.  This
    quantity is negative.

 - `ratio_avg_profit_win_loss` : float  
    The absolute value of the average profit per winning trade divided
    by the average loss per losing trade.

 - `largest_profit_winning_trade` : float  
    The single largest profit for all winning trades.

 - `largest_loss_losing_trade` : float  
    The single largest loss for all losing trades.

 - `num_winning_points` : float  
    The sum of the increase in points from all winning trades.

 - `num_losing_points` : float  
    The sum of the decrease in points from all losing trades.  This
    quantity is negative.

 - `total_net_points` : float  
    The mathematical difference between winning points and
    losing points.

 - `avg_points` : float  
    The total net points divided by the total number of trades.

 - `largest_points_winning_trade` : float  
    The single largest point increase for all winning trades.

 - `largest_points_losing_trade` : float  
    The single largest point decrease for all losing trades.

 - `avg_pct_gain_per_trade` : float  
    The average percentage gain for all trades.

 - `largest_pct_winning_trade` : float  
    The single largest percent increase for all winning trades.

 - `largest_pct_losing_trade` : float  
    The single largest percent decrease for all losing trades.

 - `expected_shortfall` : float  
    The expected shortfall is calculated by taking the average of
    returns in the worst 5% of cases.  In other words, it is the
    average percent loss of the worst 5% of losing trades.

 - `max_consecutive_winning_trades` : int  
    The longest winning streak in trades.

 - `max_consecutive_losing_trades` : int  
    The longest losing streak in trades.

 - `avg_bars_winning_trades` : float  
    On average, how long a winning trade takes in market days.

 - `avg_bars_losing_trades` : float  
    On average, how long a losing trade takes in market days.

 - `max_closed_out_drawdown` : float  
    Worst peak minus trough balance based on closing prices.

 - `max_closed_out_drawdown_peak_date` : str  
    The beginning and peak date of the largest drawdown formatted
    as YY-MM-DD.  The balance hit it's highest point on this date.

 - `max_closed_out_drawdown_trough_date` : str  
    The trough date of the largest drawdown.  The balance hit it's
    lowest point on this date.

 - `max_closed_out_drawdown_recovery_date` : str  
    The end date of the largest drawdown.  The date in which the
    balance has equaled the peak value again.

 - `drawdown_loss_period` : int  
    The number of calendar days from peak to trough.

 - `drawdown_recovery_period` : int  
    The number of calendar days from trough to recovery.

 - `annualized_return_over_max_drawdown` : float  
    Annual return rate divided by the max drawdown.

 - `max_intra_day_drawdown` : float  
    Worst peak minus trough balance based on intraday values.

 - `avg_yearly_closed_out_drawdown` :float  
    The average yearly drawdown calculated using every available
    market year period.  In other words, every rollowing window of 252
    market days is taken as a different year in the calculation.

 - `max_yearly_closed_out_drawdown` : float  
    Worst peak minus trough balance based on closing prices during any
    252 market day period.

 - `avg_monthly_closed_out_drawdown` : float  
    The average monthly drawdown calculated using every available
    market month period.  In other words, every rollowing window of 20
    market days is taken as a different month in the calculation.

 - `max_monthly_closed_out_drawdown` : float  
    Worst peak minus trough balance based on closing prices during any
    20 market day period.

 - `avg_weekly_closed_out_drawdown` : float  
    The average weekly drawdown calculated using every available
    market week period.  In other words, every rollowing window of 5
    market days is taken as a different week in the calculation.

 - `max_weekly_closed_out_drawdown` : float  
    Worst peak minus trough balance based on closing prices during any
    5 market day period.

 - `avg_yearly_closed_out_runup` : float  
    The average yearly runup calculated using every available
    market year period.  In other words, every rollowing window of 252
    market days is taken as a different year in the calculation.

 - `max_yearly_closed_out_runup` : float  
    Best peak minus trough balance based on closing prices during any
    252 market day period.

 - `avg_monthly_closed_out_runup` : float  
    The average monthly runup calculated using every available
    market month period.  In other words, every rollowing window of 20
    market days is taken as a different month in the calculation.

 - `max_monthly_closed_out_runup` : float  
    Best peak minus trough balance based on closing prices during any
    20 market day period.

 - `avg_weekly_closed_out_runup` : float  
    The average weekly runup calculated using every available
    market week period.  In other words, every rollowing window of 5
    market days is taken as a different week in the calculation.

 - `max_weekly_closed_out_runup` : float  
    Best peak minus trough balance based on closing prices during any
    5 market day period.

 - `pct_profitable_years` : float  
    The percentage of all years that were profitable.  In other words,
    the percentage of 252 market day periods that were profitable.

 - `best_year` : float  
    The percentage increase in balance of the best year.

 - `worst_year` : float  
    The percentage decrease in balance of the worst year.

 - `avg_year` : float  
    The percentage change per year on average.

 - `annual_std` : float  
    The yearly standard deviation over the entire trading period.

 - `pct_profitable_months` : float  
    The percentage of all months that were profitable.  In other words,
    the percentage of 20 market day periods that were profitable.

 - `best_month` : float  
    The percentage increase in balance of the best month.

 - `worst_month` : float  
    The percentage decrease in balance of the worst month.

 - `avg_month` : float  
    The percentage change per month on average.

 - `monthly_std` : float  
    The monthly standard deviation over the entire trading period.

 - `pct_profitable_weeks` : float  
    The percentage of all weeks that were profitable.  In other words,
    the percentage of 5 market day periods that were profitable.

 - `best_week` : float  
    The percentage increase in balance of the best week.

 - `worst_week` : float  
    The percentage decrease in balance of the worst week.

 - `avg_week` : float  
    The percentage change per week on average.

 - `weekly_std` : float  
    The weekly standard deviation over the entire trading period.

 - `pct_profitable_weeks` : float  
    The percentage of all weeks that were profitable.  In other words,
    the percentage of 5 market day periods that were profitable.

 - `weekly_std` : float  
    The weekly standard deviation over the entire trading period.

 - `pct_profitable_days` : float  
    The percentage of all days that were profitable.

 - `best_day` : float  
    The percentage increase in balance of the best day.

 - `worst_day` : float  
    The percentage decrease in balance of the worst day.

 - `avg_day` : float  
    The percentage change per day on average.

 - `daily_std` : float  
    The daily standard deviation over the entire trading period.

 - `sharpe_ratio` : float  
    A measure of risk adjusted return.  The ratio is the average return
    per unit of volatility, i.e. standard deviation.

 - `sharpe_ratio_max` : float  
    The maximum expected sharpe ratio. It is the sharpe ratio plus
    3 standard deviations of the sharpe ratio.  99.73% of sharpe ratios
    are theoretically below this value.

 - `sharpe_ratio_min` : float  
    The mimimum expected sharpe ratio. It is the sharpe ratio minus
    3 standard deviations of the sharpe ratio.  99.73% of sharpe ratios
    are theoretically above this value.

 - `sortino_ratio` : float  
    A variation of the Sharpe ratio that differentiates harmful
    volatility from overall volatility by using the asset's standard
    deviation of negative portfolio returns (downside deviation)
    instead of the total standard deviation.
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta
import math
import operator

import numpy as np
from numpy.lib.stride_tricks import as_strided
import pandas as pd

import pinkfish as pf


########################################################################
# CONSTANTS

TRADING_DAYS_PER_YEAR = 252
"""
int : The number of trading days per year.
"""
TRADING_DAYS_PER_MONTH = 20
"""
int : The number of trading days per month.
"""
TRADING_DAYS_PER_WEEK = 5
"""
int : The number of trading days per week.
"""
ALPHA_BEGIN = (1900, 1, 1)
"""
tuple : Use with `select_timeseries`, beginning data for any timeseries.
"""
SP500_BEGIN = (1957, 3, 4)
"""
tuple : Use with `select_timeseries`, date the S&P500 began.
"""


########################################################################
# OVERALL RESULTS

def _beginning_balance(capital):
    return capital

def _ending_balance(dbal):
    return dbal.iloc[-1]['close']

def _total_net_profit(tlog):
    return tlog.iloc[-1]['cumul_total']

def _gross_profit(tlog):
    return tlog[tlog['pl_cash'] > 0].sum()['pl_cash']

def _gross_loss(tlog):
    return tlog[tlog['pl_cash'] < 0].sum()['pl_cash']

def _profit_factor(tlog):
    if _gross_profit(tlog) == 0: return 0
    if _gross_loss(tlog) == 0: return 1000
    return _gross_profit(tlog) / _gross_loss(tlog) * -1

def _return_on_initial_capital(tlog, capital):
    return _total_net_profit(tlog) / capital * 100

def _difference_in_years(start, end):
    diff  = abs(start - end)
    diff_in_years = (diff.days + diff.seconds/86400)/365.2425
    return diff_in_years

def _cagr(B, A, n):
    if B < 0: B = 0
    return (math.pow(B / A, 1 / n) - 1) * 100

def _annual_return_rate(end_balance, capital, start, end):
    B = end_balance
    A = capital
    n = _difference_in_years(start, end)
    return _cagr(B, A, n)

def _trading_period(start, end):
    diff = relativedelta(end, start)
    return '{} years {} months {} days'.format(diff.years, diff.months, diff.days)

def _total_days_in_market(dbal):
    n = (dbal['shares'] > 0).sum()
    if dbal.iloc[-2]['shares'] > 0:
        n += 1
    return n

def _pct_time_in_market(dbal):
    return _total_days_in_market(dbal) / len(dbal) * 100


########################################################################
# LEVERAGE

def _margin():
    return pf.TradeLog.margin

def _avg_leverage(dbal):
    return dbal['leverage'].mean()

def _max_leverage(dbal):
    return dbal['leverage'].max()

def _min_leverage(dbal):
    return dbal['leverage'].min()


########################################################################
# SUMS

def _total_num_trades(tlog):
    return len(tlog)

def _trades_per_year(tlog, start, end):
    diff = relativedelta(end, start)
    years = diff.years + diff.months/12 + diff.days/365
    return _total_num_trades(tlog) / years

def _num_winning_trades(tlog):
    return (tlog['pl_cash'] > 0).sum()

def _num_losing_trades(tlog):
    return (tlog['pl_cash'] < 0).sum()

def _num_even_trades(tlog):
    return (tlog['pl_cash'] == 0).sum()

def _pct_profitable_trades(tlog):
    if _total_num_trades(tlog) == 0: return 0
    return _num_winning_trades(tlog) / _total_num_trades(tlog) * 100


########################################################################
# CASH PROFITS AND LOSSES

def _avg_profit_per_trade(tlog):
    if _total_num_trades(tlog) == 0: return 0
    return _total_net_profit(tlog) / _total_num_trades(tlog)

def _avg_profit_per_winning_trade(tlog):
    if _num_winning_trades(tlog) == 0: return 0
    return _gross_profit(tlog) / _num_winning_trades(tlog)

def _avg_loss_per_losing_trade(tlog):
    if _num_losing_trades(tlog) == 0: return 0
    return _gross_loss(tlog) / _num_losing_trades(tlog)

def _ratio_avg_profit_win_loss(tlog):
    if _avg_profit_per_winning_trade(tlog) == 0: return 0
    if _avg_loss_per_losing_trade(tlog) == 0: return 1000
    return (_avg_profit_per_winning_trade(tlog) /
            _avg_loss_per_losing_trade(tlog) * -1)

def _largest_profit_winning_trade(tlog):
    if _num_winning_trades(tlog) == 0: return 0
    return tlog[tlog['pl_cash'] > 0].max()['pl_cash']

def _largest_loss_losing_trade(tlog):
    if _num_losing_trades(tlog) == 0: return 0
    return tlog[tlog['pl_cash'] < 0].min()['pl_cash']


########################################################################
# POINTS

def _num_winning_points(tlog):
    if _num_winning_trades(tlog) == 0: return 0
    return tlog[tlog['pl_points'] > 0].sum()['pl_points']

def _num_losing_points(tlog):
    if _num_losing_trades(tlog) == 0: return 0
    return tlog[tlog['pl_points'] < 0].sum()['pl_points']

def _total_net_points(tlog):
    return _num_winning_points(tlog) + _num_losing_points(tlog)

def _avg_points(tlog):
    if _total_num_trades(tlog) == 0: return 0
    return tlog['pl_points'].sum() / len(tlog.index)

def _largest_points_winning_trade(tlog):
    if _num_winning_trades(tlog) == 0: return 0
    return tlog[tlog['pl_points'] > 0].max()['pl_points']

def _largest_points_losing_trade(tlog):
    if _num_losing_trades(tlog) == 0: return 0
    return tlog[tlog['pl_points'] < 0].min()['pl_points']

def _avg_pct_gain_per_trade(tlog):
    if _total_num_trades(tlog) == 0: return 0
    s = tlog['pl_points'] / tlog['entry_price']
    return np.average(s) * 100

def _largest_pct_winning_trade(tlog):
    if _num_winning_trades(tlog) == 0: return 0
    df = tlog[tlog['pl_points'] > 0]
    s = df['pl_points'] / df['entry_price']
    return s.max() * 100

def _largest_pct_losing_trade(tlog):
    if _num_losing_trades(tlog) == 0: return 0
    df = tlog[tlog['pl_points'] < 0]
    s = df['pl_points'] / df['entry_price']
    return s.min() * 100

def _expected_shortfall(tlog):
    if _total_num_trades(tlog) == 0: return 0
    df = tlog[tlog['pl_points'] < 0]
    s = df['pl_points'] / df['entry_price']
    l = sorted(s)
    end = int(len(l) * .05)
    avg = np.mean(l[:end]) *100 if end > 0 else 0
    return avg


########################################################################
# STREAKS

def _subsequence(s, c):
    """
    Calculate the length of a subsequence

    Takes as parameter list like object `s` and returns the length of
    the longest subsequence of `s` constituted only by consecutive
    character `c`s.

    Example: If the string passed as parameter is "001000111100",
    and `c` is '0', then the longest subsequence of only '0's has
    length 3.
    """
    count = 0
    maxlen = 0

    for bit in s:
        if bit == c:
            count += 1
            if count > maxlen:
                maxlen = count
        else:
            count = 0
    return maxlen

def _max_consecutive_winning_trades(tlog):
    if _num_winning_trades(tlog) == 0: return 0
    return _subsequence(tlog['pl_cash'] > 0, True)

def _max_consecutive_losing_trades(tlog):
    if _num_losing_trades(tlog) == 0: return 0
    return _subsequence(tlog['pl_cash'] > 0, False)

def _get_trade_bars(ts, tlog, op):
    l = []
    for row in tlog.itertuples():
        if op(row.pl_cash, 0):
            l.append(len(ts[row.entry_date:row.exit_date].index))
    return l

def _avg_bars_winning_trades(ts, tlog):
    if _num_winning_trades(tlog) == 0: return 0
    return np.average(_get_trade_bars(ts, tlog, operator.gt))

def _avg_bars_losing_trades(ts, tlog):
    if _num_losing_trades(tlog) == 0: return 0
    return np.average(_get_trade_bars(ts, tlog, operator.lt))


########################################################################
# DRAWDOWN AND RUNUP

def _max_closed_out_drawdown(close):
    """
    Only compare each point to the previous running peak O(N).
    """
    running_max = pd.Series(close).expanding(min_periods=1).max()
    cur_dd = (close - running_max) / running_max * 100
    dd_max = min(0, cur_dd.min())
    idx = cur_dd.idxmin()

    dd = pd.Series(dtype='object')
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

def _max_intra_day_drawdown(high, low):
    """
    Only compare each point to the previous running peak O(N).
    """
    running_max = pd.Series(high).expanding(min_periods=1).max()
    cur_dd = (low - running_max) / running_max * 100
    dd_max = min(0, cur_dd.min())
    idx = cur_dd.idxmin()

    dd = pd.Series(dtype='object')
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

def _drawdown_loss_recovery_period(peak_date, trough_date , recovery_date):
    if recovery_date == 'Not Recovered Yet':
        loss_period = recovery_period = recovery_date
    else:
        peak_date = datetime.strptime(peak_date, '%Y-%m-%d')
        trough_date = datetime.strptime(trough_date, '%Y-%m-%d')
        recovery_date = datetime.strptime(recovery_date, '%Y-%m-%d')
        loss_period = abs(peak_date - trough_date).days
        recovery_period = abs(trough_date-recovery_date).days
    return loss_period, recovery_period

def _windowed_view(x, window_size):
    """
    Create a 2d windowed view of a 1d array.

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

def _rolling_max_dd(ser, period, min_periods=1):
    """
    Compute the rolling maximum drawdown of `ser`.

    `ser` must be a Series.
    `min_periods` should satisfy 1 <= min_periods <= window_size.

    Returns an 1d array with length len(x) - min_periods + 1.
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

def _rolling_max_ru(ser, period, min_periods=1):
    """
    Compute the rolling maximum runup of `ser`.

    `ser` must be a Series.
    `min_periods` should satisfy 1 <= min_periods <= window_size.

    Returns an 1d array with length len(x) - min_periods + 1.
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


########################################################################
# PERCENT CHANGE - used to compute several stastics

def _pct_change(close, period):
    diff = (close.shift(-period) - close) / close * 100
    diff.dropna(inplace=True)
    return diff


########################################################################
# RATIOS

def _sharpe_ratio(rets, risk_free=0.00, period=TRADING_DAYS_PER_YEAR):
    dev = np.std(rets, axis=0)
    mean = np.mean(rets, axis=0)
    sharpe = (mean*period - risk_free) / (dev * np.sqrt(period))
    return sharpe

def _sortino_ratio(rets, risk_free=0.00, period=TRADING_DAYS_PER_YEAR):
    mean = np.mean(rets, axis=0)
    negative_rets = rets[rets < 0]
    dev = np.std(negative_rets, axis=0)
    if dev == 0:
        sortino = 0
    else:
        sortino = (mean*period - risk_free) / (dev * np.sqrt(period))
    return sortino


########################################################################
# STATS - this is the primary call used to generate the results

def stats(ts, tlog, dbal, capital):
    """
    Compute trading stats.

    Parameters
    ----------
    ts : pd.DataFrame
        The timeseries of a symbol.
    tlog : pd.DataFrame
        The trade log.
    dbal : pd.DataFrame
        The daily balance.
    capital : int
        The amount of money available for trading.

    Examples
    --------
    >>> stats = pf.stats(ts, tlog, dbal, capital)

    Returns
    -------
    stats : pd.Series
        The statistics for the strategy.
    """

    start = ts.index[0]
    end = ts.index[-1]

    stats = pd.Series(dtype='object')

    # OVERALL RESULTS
    stats['start'] = start.strftime('%Y-%m-%d')
    stats['end'] = end.strftime('%Y-%m-%d')
    stats['beginning_balance'] = _beginning_balance(capital)
    stats['ending_balance'] = _ending_balance(dbal)
    stats['total_net_profit'] = _total_net_profit(tlog)
    stats['gross_profit'] = _gross_profit(tlog)
    stats['gross_loss'] = _gross_loss(tlog)
    stats['profit_factor'] = _profit_factor(tlog)
    stats['return_on_initial_capital'] = _return_on_initial_capital(tlog, capital)
    cagr = _annual_return_rate(dbal['close'][-1], capital, start, end)
    stats['annual_return_rate'] = cagr
    stats['trading_period'] = _trading_period(start, end)
    stats['pct_time_in_market'] = _pct_time_in_market(dbal)

    # LEVERAGE
    stats['margin'] = _margin()
    stats['avg_leverage'] = _avg_leverage(dbal)
    stats['max_leverage'] = _max_leverage(dbal)
    stats['min_leverage'] = _min_leverage(dbal)

    # SUMS
    stats['total_num_trades'] = _total_num_trades(tlog)
    stats['trades_per_year'] = _trades_per_year(tlog, start, end)
    stats['num_winning_trades'] = _num_winning_trades(tlog)
    stats['num_losing_trades'] = _num_losing_trades(tlog)
    stats['num_even_trades'] = _num_even_trades(tlog)
    stats['pct_profitable_trades'] = _pct_profitable_trades(tlog)

    # CASH PROFITS AND LOSSES
    stats['avg_profit_per_trade'] = _avg_profit_per_trade(tlog)
    stats['avg_profit_per_winning_trade'] = _avg_profit_per_winning_trade(tlog)
    stats['avg_loss_per_losing_trade'] = _avg_loss_per_losing_trade(tlog)
    stats['ratio_avg_profit_win_loss'] = _ratio_avg_profit_win_loss(tlog)
    stats['largest_profit_winning_trade'] = _largest_profit_winning_trade(tlog)
    stats['largest_loss_losing_trade'] = _largest_loss_losing_trade(tlog)

    # POINTS
    stats['num_winning_points'] = _num_winning_points(tlog)
    stats['num_losing_points'] = _num_losing_points(tlog)
    stats['total_net_points'] = _total_net_points(tlog)
    stats['avg_points'] = _avg_points(tlog)
    stats['largest_points_winning_trade'] = _largest_points_winning_trade(tlog)
    stats['largest_points_losing_trade'] = _largest_points_losing_trade(tlog)
    stats['avg_pct_gain_per_trade'] = _avg_pct_gain_per_trade(tlog)
    stats['largest_pct_winning_trade'] = _largest_pct_winning_trade(tlog)
    stats['largest_pct_losing_trade'] = _largest_pct_losing_trade(tlog)
    stats['expected_shortfall'] = _expected_shortfall(tlog)

    # STREAKS
    stats['max_consecutive_winning_trades'] = _max_consecutive_winning_trades(tlog)
    stats['max_consecutive_losing_trades'] = _max_consecutive_losing_trades(tlog)
    stats['avg_bars_winning_trades'] = _avg_bars_winning_trades(ts, tlog)
    stats['avg_bars_losing_trades'] = _avg_bars_losing_trades(ts, tlog)

    # DRAWDOWN
    dd = _max_closed_out_drawdown(dbal['close'])
    stats['max_closed_out_drawdown'] = dd['max']
    stats['max_closed_out_drawdown_peak_date'] = dd['peak_date']
    stats['max_closed_out_drawdown_trough_date'] = dd['trough_date']
    stats['max_closed_out_drawdown_recovery_date'] = dd['recovery_date']
    stats['drawdown_loss_period'], stats['drawdown_recovery_period'] = \
    _drawdown_loss_recovery_period(dd['peak_date'], dd['trough_date'],
                                   dd['recovery_date'])
    if dd['max'] == 0:
        stats['annualized_return_over_max_drawdown'] = 0
    else:
        stats['annualized_return_over_max_drawdown'] = abs(cagr / dd['max'])
    dd = _max_intra_day_drawdown(dbal['high'], dbal['low'])
    stats['max_intra_day_drawdown'] = dd['max']
    dd = _rolling_max_dd(dbal['close'], TRADING_DAYS_PER_YEAR)
    stats['avg_yearly_closed_out_drawdown'] = np.average(dd)
    stats['max_yearly_closed_out_drawdown'] = min(dd)
    dd = _rolling_max_dd(dbal['close'], TRADING_DAYS_PER_MONTH)
    stats['avg_monthly_closed_out_drawdown'] = np.average(dd)
    stats['max_monthly_closed_out_drawdown'] = min(dd)
    dd = _rolling_max_dd(dbal['close'], TRADING_DAYS_PER_WEEK)
    stats['avg_weekly_closed_out_drawdown'] = np.average(dd)
    stats['max_weekly_closed_out_drawdown'] = min(dd)

    # RUNUP
    ru = _rolling_max_ru(dbal['close'], TRADING_DAYS_PER_YEAR)
    stats['avg_yearly_closed_out_runup'] = np.average(ru)
    stats['max_yearly_closed_out_runup'] = ru.max()
    ru = _rolling_max_ru(dbal['close'], TRADING_DAYS_PER_MONTH)
    stats['avg_monthly_closed_out_runup'] = np.average(ru)
    stats['max_monthly_closed_out_runup'] = max(ru)
    ru = _rolling_max_ru(dbal['close'], TRADING_DAYS_PER_WEEK)
    stats['avg_weekly_closed_out_runup'] = np.average(ru)
    stats['max_weekly_closed_out_runup'] = max(ru)

    # PERCENT CHANGE
    pc = _pct_change(dbal['close'], TRADING_DAYS_PER_YEAR)
    if len(pc) > 0:
        stats['pct_profitable_years'] = (pc > 0).sum() / len(pc) * 100
        stats['best_year'] = pc.max()
        stats['worst_year'] = pc.min()
        stats['avg_year'] = np.average(pc)
        stats['annual_std'] = pc.std()
    pc = _pct_change(dbal['close'], TRADING_DAYS_PER_MONTH)
    if len(pc) > 0:
        stats['pct_profitable_months'] = (pc > 0).sum() / len(pc) * 100
        stats['best_month'] = pc.max()
        stats['worst_month'] = pc.min()
        stats['avg_month'] = np.average(pc)
        stats['monthly_std'] = pc.std()
    pc = _pct_change(dbal['close'], TRADING_DAYS_PER_WEEK)
    if len(pc) > 0:
        stats['pct_profitable_weeks'] = (pc > 0).sum() / len(pc) * 100
        stats['best_week'] = pc.max()
        stats['worst_week'] = pc.min()
        stats['avg_week'] = np.average(pc)
        stats['weekly_std'] = pc.std()
    pc = _pct_change(dbal['close'], 1)
    if len(pc) > 0:
        stats['pct_profitable_days'] = (pc > 0).sum() / len(pc) * 100
        stats['best_day'] = pc.max()
        stats['worst_day'] = pc.min()
        stats['avg_day'] = np.average(pc)
        stats['daily_std'] = pc.std()

    # RATIOS
    sr = _sharpe_ratio(dbal['close'].pct_change())
    sr_std = math.sqrt((1 + 0.5*sr**2) / len(dbal))
    stats['sharpe_ratio'] = sr
    stats['sharpe_ratio_max'] = sr + 3*sr_std #3 std=>99.73%
    stats['sharpe_ratio_min'] = sr - 3*sr_std
    stats['sortino_ratio'] = _sortino_ratio(dbal['close'].pct_change())
    return stats


########################################################################
# SUMMARY - stats() must be called before calling summary()

def currency(amount):
    """
    Returns the dollar amount in US currency format.
    """
    if amount >= 0:
        return '${:,.2f}'.format(amount)
    else:
        return '-${:,.2f}'.format(-amount)

default_metrics = (
    'annual_return_rate',
    'max_closed_out_drawdown',
    'best_month',
    'worst_month',
    'sharpe_ratio',
    'sortino_ratio',
    'monthly_std',
    'annual_std')
"""
tuple : Default metrics for summary().

The metrics are:

    'annual_return_rate'  
    'max_closed_out_drawdown'  
    'best_month'  
    'worst_month'  
    'sharpe_ratio'  
    'sortino_ratio'  
    'monthly_std'  
    'annual_std'
"""

currency_metrics = (
    'beginning_balance',
    'ending_balance',
    'total_net_profit',
    'gross_profit',
    'gross_loss')
"""
tuple : Currency metrics for summary().

The metrics are:

    'beginning_balance'  
    'ending_balance'  
    'total_net_profit'  
    'gross_profit'  
    'gross_loss'
"""

def _get_metric_value(s, metric):
    """
    Returns a metric in either currency or raw format.
    """
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
    Returns stats summary.

    IMPORTANT: stats() must be called before calling this function.

    Parameters
    ----------
    stats : pd.Series
        Statistics for the strategy.
    benchmark_stats : pd.Series, optimal
        Statistics for the benchmark (default is None, which implies
        that a benchmark is not being used).
    metrics : tuple, optional
        The metrics to be used in the summary (default is
        `default_metrics`).
    extras : tuple, optional
        The extra metrics to be used in the summary (default is None,
        which imples that no extra metrics are being used).
    """
    if extras is None: extras = ()
    metrics += extras

    # Columns.
    columns = ['strategy']
    if benchmark_stats is not None:
        columns.append('benchmark')

    # Index & data.
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


def optimizer_summary(strategies, metrics):
    """
    Generate summary dataframe of a set of strategies vs metrics.

    This function is designed to be used in analysis of an
    optimization of some parameter.  stats() must be called for
    each strategy before calling this function.

   Parameters
    ----------
    strategies : pd.Series
        Series of strategy objects that have the `stats` attribute.
    metrics : tuple
        The metrics to be used in the summary.

    Returns
    -------
    df : pf.DataFrame
        Summary of strategies vs metrics.
    """
    index = []
    columns = strategies.index
    data = []
    # Add metrics.
    for metric in metrics:
        index.append(metric)
        data.append([_get_metric_value(strategy.stats, metric) for strategy in strategies])

    df = pd.DataFrame(data, columns=columns, index=index)
    return df
