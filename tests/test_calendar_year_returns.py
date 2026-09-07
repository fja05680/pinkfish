import unittest
from unittest.mock import MagicMock

import pandas as pd

from pinkfish.pfstatistics import calendar_year_returns


def _make_dbal(date_values):
    dates, values = zip(*date_values)
    return pd.DataFrame(
        {
            'high': values,
            'low': values,
            'close': values,
            'shares': 100,
            'cash': 0.0,
            'leverage': 1.0,
        },
        index=pd.to_datetime(dates),
    )


class TestCalendarYearReturns(unittest.TestCase):

    def test_calendar_year_returns_single_symbol(self):
        dbal = _make_dbal([
            ('2019-01-02', 100),
            ('2019-12-31', 110),
            ('2020-01-02', 120),
            ('2020-12-31', 132),
        ])

        returns = calendar_year_returns(dbal)

        self.assertEqual(returns.index.tolist(), [2019, 2020])
        self.assertAlmostEqual(returns.loc[2019], 10.0)
        self.assertAlmostEqual(returns.loc[2020], 10.0)

    def test_calendar_year_returns_accepts_get_logs_tuple(self):
        dbal = _make_dbal([
            ('2019-01-02', 100),
            ('2019-12-31', 110),
            ('2020-01-02', 110),
            ('2020-12-31', 120),
        ])
        logs = (pd.DataFrame(), pd.DataFrame(), dbal)

        returns = calendar_year_returns(logs)

        self.assertEqual(returns.index.tolist(), [2019, 2020])
        self.assertAlmostEqual(returns.loc[2019], 10.0)
        self.assertAlmostEqual(returns.loc[2020], 9.09090909090909)

    def test_calendar_year_returns_accepts_portfolio_object(self):
        dbal = _make_dbal([
            ('2020-01-02', 100),
            ('2020-12-31', 105),
        ])
        portfolio = MagicMock()
        portfolio.get_logs.return_value = (pd.DataFrame(), pd.DataFrame(), dbal)

        returns = calendar_year_returns(portfolio)

        portfolio.get_logs.assert_called_once_with()
        self.assertAlmostEqual(returns.loc[2020], 5.0)

    def test_calendar_year_returns_with_benchmark(self):
        strategy_dbal = _make_dbal([
            ('2019-01-02', 100),
            ('2019-12-31', 120),
            ('2020-01-02', 120),
            ('2020-12-31', 144),
        ])
        benchmark_dbal = _make_dbal([
            ('2019-01-02', 100),
            ('2019-12-31', 110),
            ('2020-01-02', 110),
            ('2020-12-31', 121),
        ])

        returns = calendar_year_returns(strategy_dbal, benchmark_dbal)

        self.assertEqual(list(returns.columns), ['strategy', 'benchmark', 'diff'])
        self.assertAlmostEqual(returns.loc[2019, 'strategy'], 20.0)
        self.assertAlmostEqual(returns.loc[2020, 'strategy'], 20.0)
        self.assertAlmostEqual(returns.loc[2019, 'benchmark'], 10.0)
        self.assertAlmostEqual(returns.loc[2020, 'benchmark'], 10.0)
        self.assertEqual(returns.loc[2019, 'diff'], '+10.00')
        self.assertEqual(returns.loc[2020, 'diff'], '+10.00')

    def test_calendar_year_returns_diff_shows_negative_sign(self):
        strategy_dbal = _make_dbal([
            ('2019-01-02', 100),
            ('2019-12-31', 105),
        ])
        benchmark_dbal = _make_dbal([
            ('2019-01-02', 100),
            ('2019-12-31', 110),
        ])

        returns = calendar_year_returns(strategy_dbal, benchmark_dbal)

        self.assertEqual(returns.loc[2019, 'diff'], '-5.00')


if __name__ == '__main__':
    unittest.main()
