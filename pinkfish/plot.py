"""
plot
---------
Functions for plotting
"""

import matplotlib.pyplot as plt
import pinkfish as pf

# Register matplotlib converters
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


def plot_equity_curve(strategy, benchmark=None):
    """
    Plot Equity Curve: Strategy vs (optionally) Benchmark
    Both arguements are daily balance.
    """
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel='Portfolio value in $')
    axes.plot(strategy['close'], label='strategy')
    if benchmark is not None:
        axes.plot(benchmark['close'], label='benchmark')
    plt.legend(loc='best')

def plot_equity_curves(strategies):
    """
    Plot Equity Curve: multiple equity curves on same plot
    Arguement is daily balance.
    """
    fig = plt.figure(figsize=(16,12))
    axes = fig.add_subplot(111, ylabel='Portfolio value in $')
    for strategy in strategies:
        axes.plot(strategy.dbal['close'], label=strategy._symbol)

    plt.legend(loc='best')

def plot_trades(strategy, benchmark=None):
    """
    Plot Trades: benchmark is the equity curve that the trades get plotted on.
    If not provided, strategy equity curve is used.
    Both arguements are daily balance.
    """
    if benchmark is None or strategy is benchmark:
        benchmark = strategy
        label = 'strategy'
    else:
        label = 'benchmark'

    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel='Portfolio value in $')
    axes.plot(benchmark.index, benchmark['close'], label=label)

    # buy trades
    buy = benchmark[strategy['state'] == pf.TradeState.OPEN]
    axes.plot(buy.index, buy['close'], '^', markersize=10, color='k')

    #sell trades
    sell = benchmark[strategy['state'] == pf.TradeState.CLOSE]
    axes.plot(sell.index, sell['close'], 'v', markersize=10, color='r')
    plt.legend(loc='best')

default_metrics = (
    'annual_return_rate',
    'max_closed_out_drawdown',
    'drawdown_annualized_return',
    'drawdown_recovery',
    'best_month',
    'worst_month',
    'sharpe_ratio',
    'sortino_ratio',
    'monthly_std')

def plot_bar_graph(stats, benchmark_stats=None, metrics=default_metrics, extras=None):
    """ Plot Bar Graph: Strategy vs Benchmark """
    if extras is None: extras = ()
    metrics += extras

    df = pf.summary(stats, benchmark_stats, metrics)
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel='Trading Metrix')
    df.plot(kind='bar', ax=axes, color=['g', 'r'])
    axes.set_xticklabels(df.index, rotation=60)
    plt.legend(loc='best')
    return df

