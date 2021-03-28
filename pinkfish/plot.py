"""
Plotting functions.
"""

import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
# Register matplotlib converters.
register_matplotlib_converters()

import pinkfish as pf


def plot_equity_curve(strategy, benchmark=None, fname=None):
    """
    Plot Equity Curve: Strategy vs (optionally) Benchmark.

    Parameters
    ----------
    strategy : pd.DataFrame
        Daily balance for the strategy.
    benchmark: pd.DataFrame, optional
        Daily balance for the benchmark (default is None, which implies
        that a benchmark is not being used).
    fname: str or path-like or file-like, optional
        Save the current figure to fname (default is None, which
        implies to not output the figure to a file).

    Returns
    -------
    None
    """
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel='Portfolio value in $')
    axes.plot(strategy['close'], label='strategy')
    if benchmark is not None:
        axes.plot(benchmark['close'], label='benchmark')
    plt.legend(loc='best')
    if fname:
        plt.savefig(fname, bbox_inches='tight')

def plot_equity_curves(strategies, fname=None):
    """
    Plot Equity Curve: multiple equity curves on same plot.

    Parameters
    ----------
    strategies : pd.Series
        Container of strategy Daily balance (pd.Dataframe) for each
        symbol.
    fname: str or path-like or file-like, optional
        Save the current figure to fname (default is None, which
        implies to not output the figure to a file).

    Returns
    -------
    None
    """
    fig = plt.figure(figsize=(16,12))
    axes = fig.add_subplot(111, ylabel='Portfolio value in $')
    for strategy in strategies:
        axes.plot(strategy.dbal['close'], label=strategy.symbol)
    plt.legend(loc='best')
    if fname:
        plt.savefig(fname, bbox_inches='tight')

def plot_trades(strategy, benchmark=None, fname=None):
    """
    Plot Trades.

    Benchmark is the equity curve that the trades get plotted on.
    If not provided, strategy equity curve is used.

    Parameters
    ----------
    strategy : pd.DataFrame
        Daily balance for the strategy.
    benchmark: pd.DataFrame, optional
        Daily balance for the benchmark.
    fname: str or path-like or file-like, optional
        Save the current figure to fname (default is None, which
        implies to not output the figure to a file).

    Returns
    -------
    None
    """
    if benchmark is None or strategy is benchmark:
        benchmark = strategy
        label = 'strategy'
    else:
        label = 'benchmark'

    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel='Portfolio value in $')
    axes.plot(benchmark.index, benchmark['close'], label=label)

    # Buy trades.
    s = strategy['state'] == pf.TradeState.OPEN
    s = s.reindex_like(benchmark)
    buy = benchmark[s]
    axes.plot(buy.index, buy['close'], '^', markersize=10, color='k')

    # Sell trades.
    s = strategy['state'] == pf.TradeState.CLOSE
    s = s.reindex_like(benchmark)
    sell = benchmark[s]
    axes.plot(sell.index, sell['close'], 'v', markersize=10, color='r')
    plt.legend(loc='best')
    if fname:
        plt.savefig(fname, bbox_inches='tight')


default_metrics = (
    'annual_return_rate',
    'max_closed_out_drawdown',
    'annualized_return_over_max_drawdown',
    'best_month',
    'worst_month',
    'sharpe_ratio',
    'sortino_ratio',
    'monthly_std',
    'annual_std')
"""
tuple : Default metrics for plot_bar_graph().

The metrics are:

    'annual_return_rate'  
    'max_closed_out_drawdown'  
    'annualized_return_over_max_drawdown'  
    'best_month'  
    'worst_month'  
    'sharpe_ratio'  
    'sortino_ratio'  
    'monthly_std'  
    'annual_std'
"""


def plot_bar_graph(stats, benchmark_stats=None, metrics=default_metrics,
                   extras=None, fname=None):
    """
    Plot Bar Graph: Strategy vs Benchmark (optional).

    Parameters
    ----------
    stats : pd.Series
        Statistics from the strategy.
    benchmark_stats : pd.Series, optional
        Statistics from the benchmark (default is None, which implies
        that a benchmark is not being used).
    metrics: tuple, optional
        The metrics to be plotted (default is `default_metrics`).
    extras: tuple, optional
        The additional metrics to be plotted (default is None, which
        implies no extra metrics should be added).
    fname: str or path-like or file-like, optional
        Save the current figure to fname (default is None, which
        implies to not output the figure to a file).

    Returns
    -------
    pd.DataFrame
        Summary metrics.
    """
    if extras is None: extras = ()
    metrics += extras

    df = pf.summary(stats, benchmark_stats, metrics)
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel='Trading Metrix')
    df.plot(kind='bar', ax=axes, color=['g', 'r'])
    axes.set_xticklabels(df.index, rotation=60)
    plt.legend(loc='best')
    if fname:
        plt.savefig(fname, bbox_inches='tight')
    return df
