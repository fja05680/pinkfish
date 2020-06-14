"""
plot
---------
Functions for plotting
"""

# Other imports
import matplotlib.pyplot as plt
import pinkfish as pf

# Register matplotlib converters
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

def plot_equity_curve(strategy, benchmark=None):
    """
    Plot Equity Curves: Strategy vs (optionally) Benchmark
    Both arguements are daily balance.
    """
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel='Portfolio value in $')
    axes.plot(strategy['close'], label='strategy')
    if benchmark is not None:
        axes.plot(benchmark['close'], label='benchmark')
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

    #buy
    buy = benchmark[strategy['state'] == pf.TradeState.OPEN]
    axes.plot(buy.index, buy['close'], '^', markersize=10, color='k')
    #sell
    sell = benchmark[strategy['state'] == pf.TradeState.CLOSE]
    axes.plot(sell.index, sell['close'], 'v', markersize=10, color='r')
    plt.legend(loc='best')

def plot_bar_graph(stats, benchmark_stats, *metrics):
    """ Plot Bar Graph: Strategy vs Benchmark """
    df = pf.summary2(stats, benchmark_stats, *metrics)
    fig = plt.figure()
    axes = fig.add_subplot(111, ylabel='Trading Metrix')
    df.plot(kind='bar', ax=axes, color=['g', 'r'])
    axes.set_xticklabels(df.index, rotation=60)
    plt.legend(loc='best')
    return df

