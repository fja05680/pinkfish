"""
Plotting functions.
"""

import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
# Register matplotlib converters.
register_matplotlib_converters()

import pinkfish.pfstatistics as pfstatistics
import pinkfish.trade as trade


def plot_equity_curve(strategy, benchmark=None, yscale='linear', fname=None):
    """
    Plot Equity Curve: Strategy and (optionally) Benchmark.

    Parameters
    ----------
    strategy : pd.DataFrame
        Daily balance for the strategy.
    benchmark: pd.DataFrame, optional
        Daily balance for the benchmark (default is None, which implies
        that a benchmark is not being used).
    yscale: str, {'linear', 'log', 'symlog', 'logit'}
        The axis scale type to apply (default is 'linear')
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
    axes.set_yscale(yscale)
    if benchmark is not None:
        axes.plot(benchmark['close'], label='benchmark')
    plt.legend(loc='best')
    if fname:
        plt.savefig(fname, bbox_inches='tight')

def plot_equity_curves(strategies, labels=None, yscale='linear', fname=None):
    """
    Plot one or more equity curves on the same plot.

    Parameters
    ----------
    strategies : pd.Series of pd.Dataframe
        Container of strategy daily balance for each symbol.
    labels : list of str, optional
        List of labels for each strategy (default is None, which implies
        that `strategy.symbol` is used as the label.
    yscale: str, {'linear', 'log', 'symlog', 'logit'}
        The axis scale type to apply (default is 'linear')
    fname: str or path-like or file-like, optional
        Save the current figure to fname (default is None, which
        implies to not output the figure to a file).

    Returns
    -------
    None
    """
    fig = plt.figure(figsize=(16,12))
    axes = fig.add_subplot(111, ylabel='Portfolio value in $')
    for i, strategy in enumerate(strategies):
        if labels is None:
            label = strategy.symbol
        else:
            label = labels[i]
        axes.plot(strategy.dbal['close'], label=label)
        axes.set_yscale(yscale)
    plt.legend(loc='best')
    if fname:
        plt.savefig(fname, bbox_inches='tight')

def plot_trades(strategy, benchmark=None, yscale='linear', fname=None):
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
    yscale: str, {'linear', 'log', 'symlog', 'logit'}
        The axis scale type to apply (default is 'linear')
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
    axes.set_yscale(yscale)

    # Buy trades.
    s = strategy['state'] == trade.TradeState.OPEN
    s = s.reindex_like(benchmark)
    buy = benchmark[s]
    axes.plot(buy.index, buy['close'], '^', markersize=10, color='k')
    axes.set_yscale(yscale)

    # Sell trades.
    s = strategy['state'] == trade.TradeState.CLOSE
    s = s.reindex_like(benchmark)
    sell = benchmark[s]
    axes.plot(sell.index, sell['close'], 'v', markersize=10, color='r')
    axes.set_yscale(yscale)
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
    if extras is None:
        extras = ()
    metrics += extras

    df = pfstatistics.summary(stats, benchmark_stats, metrics)
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel='Trading Metrix')
    df.plot(kind='bar', ax=axes, color=['g', 'r'])
    axes.set_xticklabels(df.index, rotation=60)
    plt.legend(loc='best')
    if fname:
        plt.savefig(fname, bbox_inches='tight')
    return df


def optimizer_plot_bar_graph(df, metric):
    """
    Plot Bar Graph of a metric for a set of strategies.

    This function is designed to be used in analysis of an
    optimization of some parameter.  First call optimizer_summary()
    to generate the dataframe required by this function.

    Parameters
    ----------
    df : pd.DataFrame
        Summary of strategies vs metrics.
    metric : str
        The metric to be used in the summary.
    """
    df = df.loc[[metric]]
    df = df.transpose()
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel=metric)
    df.plot(kind='bar', ax=axes, legend=False)
    axes.set_xticklabels(df.index, rotation=0)
