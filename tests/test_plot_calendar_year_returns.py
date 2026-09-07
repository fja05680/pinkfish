import unittest

import matplotlib
import pandas as pd

matplotlib.use('Agg')

from pinkfish.plot import plot_calendar_year_returns


class TestPlotCalendarYearReturns(unittest.TestCase):

    def test_plot_calendar_year_returns_single_series(self):
        returns = pd.Series([10.0, -5.0], index=[2019, 2020], name='strategy')

        result = plot_calendar_year_returns(returns)

        self.assertIs(result, returns)

    def test_plot_calendar_year_returns_with_benchmark(self):
        returns = pd.DataFrame(
            {
                'strategy': [20.0, 10.0],
                'benchmark': [10.0, 5.0],
                'diff': [10.0, 5.0],
            },
            index=[2019, 2020],
        )

        result = plot_calendar_year_returns(returns)

        self.assertIs(result, returns)


if __name__ == '__main__':
    unittest.main()
