"""
evolved
---------
This module contains a collection of functions that were copied or derived
from the book "Trading Evolved" by Andreas F. Clenow.
Below is a correspondance I had with the author:

-------------------------------------------------------------------------------
Farrell
October 25, 2019 at 15:49
Hi Andreas,

I just finished reading the book. Awesome one of a kind! Thanks so much.
I also enjoyed your other two. Question: what is the copyright (if any) on the
source code you have in the book. I want to incorporate some of it into my open
source backtester, Pinkfish. How should I credit your work if no copyright.
I could add a comment at the beginning of each derived function or module
at a minimum.

Farrell
-------------------------------------------------------------------------------

Andreas Clenow
October 25, 2019 at 17:29
Hi Farrell,

I can be paid in reviews and/or beer. :)

For an open source project, use the code as you see fit. A credit in the
comments somewhere would be nice, but I won't sue you if you forget it.

ac
-------------------------------------------------------------------------------

"""

# Use future imports for python 3.0 forward compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# Other imports
import pandas as pd
import matplotlib.pyplot as plt
import empyrical as em
from IPython.core.display import display, HTML


def monthly_returns_map(returns):
    """ Display per month and per year returns in a table """

    monthly_data = em.aggregate_returns(returns.pct_change(),'monthly')
    yearly_data = em.aggregate_returns(returns.pct_change(),'yearly')

    table_header = """
    <table class='table table-hover table-condensed table-striped'>
    <thead>
    <tr>
    <th style="text-align:right">Year</th>
    <th style="text-align:right">Jan</th>
    <th style="text-align:right">Feb</th>
    <th style="text-align:right">Mar</th>
    <th style="text-align:right">Apr</th>
    <th style="text-align:right">May</th>
    <th style="text-align:right">Jun</th>
    <th style="text-align:right">Jul</th>
    <th style="text-align:right">Aug</th>
    <th style="text-align:right">Sep</th>
    <th style="text-align:right">Oct</th>
    <th style="text-align:right">Nov</th>
    <th style="text-align:right">Dec</th>
    <th style="text-align:right">Year</th>
    </tr>
    </thead>
    <tbody>
    <tr>"""

    first_year = True
    first_month = True
    year = 0
    month = 0
    year_count = 0
    table = ''
    for m, val in monthly_data.iteritems():
        year = m[0]
        month = m[1]

        if first_month:
            if year_count % 15 == 0:
                table += table_header
            table += "<td align='right'><b>{}</b></td>\n".format(year)
            first_month = False

        # pad empty months for first year if sim doesn't start in January
        if first_year:
            first_year = False
            if month > 1:
                for _ in range(1, month):
                    table += "<td align='right'>-</td>\n"

        table += "<td align='right'>{:.1f}</td>\n".format(val * 100)

        # check for dec, add yearly
        if month == 12:
            table += "<td align='right'><b>{:.1f}</b></td>\n".format(
                yearly_data[year] * 100)
            table += '</tr>\n <tr> \n'
            first_month = True
            year_count += 1

    # add padding for empty months and last year's value
    if month != 12:
        for i in range(month+1, 13):
            table += "<td align='right'>-</td>\n"
            if i == 12:
                table += "<td align='right'><b>{:.1f}</b></td>\n".format(
                    yearly_data[year] * 100)
                table += '</tr>\n <tr> \n'
    table += '</tr>\n </tbody> \n </table>'
    display(HTML(table))

#returns = s.dbal['close']
#monthly_returns_map(returns)

def holding_period_map(returns):
    """
    Display holding period returns in a table.
    length of returns should be 30 or less, otherwise the output
    will be jumbled
    """

    year = em.aggregate_returns(returns.pct_change(), 'yearly')
    returns = pd.DataFrame(columns=range(1, len(year)+1), index=year.index)

    year_start = 0

    table = "<table class='table table-hover table-condensed table-striped'>"
    table += "<tr><th>Years</th>"

    for i in range(len(year)):
        table += "<th>{}</th>".format(i+1)
    table += "</tr>"

    for the_year, value in year.iteritems(): # Iterates years
        table += "<tr><th>{}</th>".format(the_year) # New table row

        for years_held in (range(1, len(year)+1)): # Iterates years held
            if years_held <= len(year[year_start:year_start + years_held]):
                ret = em.annual_return(year[year_start:year_start + years_held], 'yearly' )
                table += "<td>{:.0f}</td>".format(ret * 100)
        table += "</tr>"
        year_start+=1
    display(HTML(table))

#table = holding_period_map(returns['1990':])
#display(HTML(table))

def calc_corr(ser1, ser2, window):
    """
    Calculates correlation between two series.
    """
    ret1 = ser1.pct_change()
    ret2 = ser2.pct_change()
    corr = ret1.rolling(window).corr(ret2)
    return corr

def prettier_graphs(ret1, ret2, label1='Strategy', label2='Benchmark',
                    points_to_plot=None):
    """
    Plot 3 subplots.  The first subplot will show a rebased comparison of the
    returns to the benchmark returns, recalculated with the same starting value
    of 1.  This will be shown on a semi logarithmic scale.  The second subplot
    will show relative strength of the returns to the benchmark returns, and
    the third the correlation between the two.

    points_to_plot: Define how many points (trading days) we intend to plot.
    """

    # default is to plot all points (days)
    if points_to_plot is None:
        points_to_plot = 0;

    data = pd.DataFrame(ret1)
    data['ret2'] = pd.DataFrame(ret2)
    data.columns = ['ret1', 'ret2']
    data.head()

    # Rebase the two series to the same point in time,
    # starting where the plot will start.
    for col in data:
        data[col + '_rebased'] = \
            (data[-points_to_plot:][col].pct_change() + 1).cumprod()

    # Relative strength, ret1 to ret2
    data['rel_str'] = data['ret1'] / data['ret2']

    # Calculate 50 day rolling correlation
    data['corr'] = calc_corr(data['ret1'], data['ret2'], 100)

    # After this, we slice the data, effectively discarding all but the last
    # 300 data points, using the slicing logic from before.
    # Slice the data, cut points we don't intend to plot.
    plot_data = data[-points_to_plot:]

    # Make  new figure and set the size.
    fig = plt.figure(figsize=(12, 8))

    # The first subplot, planning for 3 plots high, 1 plot wide,
    # this being the first.
    ax = fig.add_subplot(311)
    ax.set_title('Comparison')
    ax.semilogy(plot_data['ret1_rebased'], linestyle='-',
                label=label1, linewidth=3.0)
    ax.semilogy(plot_data['ret2_rebased'], linestyle='--',
                label=label2, linewidth=3.0)
    ax.legend()
    ax.grid(False)

    # Second sub plot.
    ax = fig.add_subplot(312)
    label='Relative Strength, {} to {}'.format(label1, label2)
    ax.plot(plot_data['rel_str'], label=label, linestyle=':', linewidth=3.0)
    ax.legend()
    ax.grid(True)

    # Third subplot.
    ax = fig.add_subplot(313)
    label='Correlation between {} and {}'.format(label1, label2)
    ax.plot(plot_data['corr'], label=label, linestyle='-.', linewidth=3.0)
    ax.legend()
    ax.grid(True)

