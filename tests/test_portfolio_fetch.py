import datetime
import unittest
from unittest.mock import patch

import pandas as pd

from pinkfish.portfolio import Portfolio


def _sample_timeseries():
    dates = pd.bdate_range('2020-01-01', periods=400)
    return pd.DataFrame(
        {
            'open': 100.0,
            'high': 101.0,
            'low': 99.0,
            'close': 100.0,
            'adj_close': 100.0,
            'volume': 1000,
        },
        index=dates,
    )


class TestPortfolioFetch(unittest.TestCase):

    def test_fetch_timeseries_passes_source_to_all_symbols(self):
        portfolio = Portfolio()
        start = datetime.datetime(2021, 1, 1)
        end = datetime.datetime(2021, 12, 31)

        with patch('pinkfish.portfolio.fetch_timeseries') as mock_fetch:
            mock_fetch.return_value = _sample_timeseries()
            portfolio.fetch_timeseries(
                ['SPY', 'QQQ'],
                start,
                end,
                source='tiingo',
                api_key='test-key',
            )

        self.assertEqual(mock_fetch.call_count, 2)
        for call in mock_fetch.call_args_list:
            self.assertEqual(call.kwargs['source'], 'tiingo')
            self.assertEqual(call.kwargs['api_key'], 'test-key')
            self.assertIsNone(call.kwargs['dir_name'])


if __name__ == '__main__':
    unittest.main()
