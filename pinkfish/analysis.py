"""
Analysis of results.

This module contains some functions that were copied or derived
from the book "Trading Evolved" by Andreas F. Clenow.
Below is a correspondance I had with the author:

------------------------------------------------------------------------
Farrell
October 25, 2019 at 15:49
Hi Andreas,

I just finished reading the book. Awesome one of a kind! Thanks so much.
I also enjoyed your other two. Question: what is the copyright (if any)
on the source code you have in the book. I want to incorporate some of
it into my open source backtester, Pinkfish. How should I credit your
work if no copyright.  I could add a comment at the beginning of each
derived function or module at a minimum.

Farrell
------------------------------------------------------------------------

Andreas Clenow
October 25, 2019 at 17:29
Hi Farrell,

I can be paid in reviews and/or beer. :)

For an open source project, use the code as you see fit. A credit in the
comments somewhere would be nice, but I won't sue you if you forget it.

ac
------------------------------------------------------------------------
"""

import matplotlib.pyplot as plt
import pandas as pd

import pinkfish.indicator as indicator


########################################################################
# PRETTIER GRAPHS

def _calc_corr(dbal, benchmark_dbal, window):
    """
    Calculate the rollowing correlation between two returns.

    Parameters
    ----------
    dbal : pd.Series
        Strategy daily closing balance indexed by date.
    benchmark_dbal : pd.Series
        Benchmark daily closing balance indexed by date.
    window : int
        Size of the moving window. This is the number of observations
        used for calculating the statistic.

    Returns
    -------
    corr : pd.DataFrame
        Window size rollowing correlation between `dbal` and
        `benchmark_dbal`.
    """
    ret = dbal.pct_change()
    benchmark_ret = benchmark_dbal.pct_change()
    corr = ret.rolling(window).corr(benchmark_ret)
    return corr


def prettier_graphs(dbal, benchmark_dbal, dbal_label='Strategy',
                    benchmark_label='Benchmark', points_to_plot=None):
    """
    Plot 3 subplots.

    The first subplot will show a rebased comparison of the returns to
    the benchmark returns, recalculated with the same starting value
    of 1.  This will be shown on a semi logarithmic scale.  The second
    subplot will show relative strength of the returns to the benchmark
    returns, and the third the correlation between the two.

    Parameters
    ----------
    dbal : pd.Series
        Strategy daily closing balance indexed by date.
    benchmark_dbal : pd.Series
        Benchmark daily closing balance indexed by date.
    label : str, optional
        Label to use in graph for strategy (default is 'Strategy').
    benchmark_label : str, optional
        Label to use in graph for benchmark (default is 'Benchmark').
    points_to_plot : int, optional
        Define how many points (trading days) we intend to plot
        (default is None, which implies plot all points or days).

    Returns
    -------
    None

    Examples
    --------
    >>> prettier_graphs(dbal['close'], benchmark_dbal['close'],
                        points_to_plot=5000)
    """
    if points_to_plot is None:
        points_to_plot = 0

    data = pd.DataFrame(dbal)
    data['benchmark_dbal'] = pd.DataFrame(benchmark_dbal)
    data.columns = ['dbal', 'benchmark_dbal']
    data.head()

    # Rebase the two series to the same point in time;
    # starting where the plot will start.
    for col in data:
        data[col + '_rebased'] = \
            (data[-points_to_plot:][col].pct_change() + 1).cumprod()

    # Relative strength, strategy to benchmark.
    data['relative_strength'] = data['dbal'] / data['benchmark_dbal']

    # Calculate 100 day rolling correlation.
    data['corr'] = _calc_corr(data['dbal'], data['benchmark_dbal'], 100)

    # After this, we slice the data, effectively discarding all but
    # the last points_to_plot data points, using the slicing logic from
    # before.  Slice the data, cut points we don't intend to plot.
    plot_data = data[-points_to_plot:]

    # Make new figure and set the size.
    fig = plt.figure(figsize=(12, 8))

    # The first subplot, planning for 3 plots high, 1 plot wide,
    # this being the first.
    ax = fig.add_subplot(311)
    ax.set_title('Comparison')
    ax.semilogy(plot_data['dbal_rebased'], linestyle='-',
                label=dbal_label, linewidth=3.0)
    ax.semilogy(plot_data['benchmark_dbal_rebased'], linestyle='--',
                label=benchmark_label, linewidth=3.0)
    ax.legend()
    ax.grid(False)

    # Second sub plot.
    ax = fig.add_subplot(312)
    label = f'Relative Strength, {dbal_label} to {benchmark_label}'
    ax.plot(plot_data['relative_strength'], label=label, linestyle=':', linewidth=3.0)
    ax.legend()
    ax.grid(True)

    # Third subplot.
    ax = fig.add_subplot(313)
    label = f'Correlation between {dbal_label} and {benchmark_label}'
    ax.plot(plot_data['corr'], label=label, linestyle='-.', linewidth=3.0)
    ax.legend()
    ax.grid(True)


########################################################################
# VOLATILITY

def volatility_graphs(dbals, labels, points_to_plot=None):
    """
    Plot volatility graphs.

    The first graph is a boxplot showing the differences between
    2 or more returns.  The second graph shows the volatility plotted
    for 2 or more returns.

    Parameters
    ----------
    dbals : list of pd.DataFrame
        A list of daily closing balances (or daily instrument closing
        prices) indexed by date.
    labels : list of str
        A list of labels.
    points_to_plot : int, optional
        Define how many points (trading days) we intend to plot
        (default is None, which implies plot all points or days).

    Returns
    -------
    pf.DataFrame
        Statistics comparing the `dbals`.

    Examples
    --------
    >>> df = pf.volatility_graph([ts, dbal], ['SPY', 'Strategy'],
                                 points_to_plot=5000)
    >>> df
    """
    def _boxplot(volas, labels):
        """
        Plot a volatility boxplot.
        """
        fig = plt.figure(figsize=(12, 8))
        fig.add_subplot(111, ylabel='Volatility')
        plt.ylim(0, 1)
        plt.boxplot(volas, labels=labels)


    def _volas_plot(volas, labels):
        """
        Plot volatility.
        """
        fig = plt.figure(figsize=(14, 10))
        axes = fig.add_subplot(111, ylabel='Volatility')
        for i, vola in enumerate(volas):
            axes.plot(vola, label=labels[i])
        plt.legend(loc='best')

    if points_to_plot is None:
        points_to_plot = 0

    # Get volatility for each dbal set.
    volas = []
    for dbal in dbals:
        volas.append(indicator.VOLATILITY(dbal[-points_to_plot:]).dropna())

    # Build metrics dataframe.
    index = []
    columns = labels
    data = []
    # Add metrics.
    metrics = ['avg', 'median', 'min', 'max', 'std', 'last']
    for metric in metrics:
        index.append(metric)
        if   metric == 'avg':    data.append(vola.mean() for vola in volas)
        elif metric == 'median': data.append(vola.median() for vola in volas)
        elif metric == 'min':    data.append(vola.min() for vola in volas)
        elif metric == 'max':    data.append(vola.max() for vola in volas)
        elif metric == 'std':    data.append(vola.std() for vola in volas)
        elif metric == 'last':   data.append(vola.iloc[-1] for vola in volas)

    df = pd.DataFrame(data, columns=columns, index=index)
    _boxplot(volas, labels)
    _volas_plot(volas, labels)
    return df


########################################################################
# KELLY CRITERION

def kelly_criterion(stats, benchmark_stats=None):
    """
    Use this function to help with sizing of leverage.

    This function uses ideas based on the Kelly Criterion.

    Parameters
    ----------
    stats : pd.Series
        Statistics for the strategy.
    bbenchmark_stats : pd.Series, optimal
        Statistics for the benchmark (default is None, which implies
        that a benchmark is not being used).

    Returns
    -------
    s : pf.Series
        Leverage statistics.

         - `sharpe_ratio` is a measure of risk adjusted return.

         - `sharpe_ratio_max` is the maximum expected sharpe ratio.

         - `sharpe_ratio_min` is the minimum expected sharpe ratio.

         - `strategy risk` is a measure of how risky a trading strategy
            is, calculated as an annual standard deviation of returns.

         - `instrument_risk` is a measure of how risky an instrument is
            before any leverage is applied, calculated as an annual
            standard deviation of returns.

         - `optimal target risk` is equal to the expected sharpe ratio,
            according to the Kelly criterion.  Target risk is the amount
            of risk you expect to see when trading, calculated as an
            annual standard deviation of returns.

         - `half kelly criterion` is equal to half the expected
            sharpe ratio.  It uses a conservative version of the
            Kelly criterion known as half Kelly.

         - `aggressive leverage` is the optimal target risk divided by
            the instrument risk.  This is an aggressive form of the
            leverage factor, which is the cash value of a position
            divided by your capital.

         - `moderate leverage` is the leverage factor calculated using
            half Kelly.

         - `conservative leverage` is the leverage factor calculated
            using half of the minimum sharpe ratio divided by 2.
    """
    s = pd.Series(dtype='object')

    s['sharpe_ratio']           = stats['sharpe_ratio']
    s['sharpe_ratio_max']       = stats['sharpe_ratio_max']
    s['sharpe_ratio_min']       = stats['sharpe_ratio_min']
    s['strategy risk']          = stats['annual_std'] / 100
    if benchmark_stats is not None:
        s['instrument risk']    = benchmark_stats['annual_std'] / 100
    s['optimal target risk']    = s['sharpe_ratio']
    s['half kelly criterion']   = s['sharpe_ratio'] / 2
    s['aggressive leverage']    = s['optimal target risk'] / s['instrument risk']
    s['moderate leverage']      = s['half kelly criterion'] / s['instrument risk']
    s['conservative leverage']  = (s['sharpe_ratio_min'] / 2) / s['instrument risk']
    return s
