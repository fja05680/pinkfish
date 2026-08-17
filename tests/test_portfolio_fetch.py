import datetime
import unittest
from io import StringIO
from unittest.mock import patch

import pandas as pd

from pinkfish.fetch import print_symbol_timeseries_starts, symbol_timeseries_metadata
from pinkfish.portfolio import Portfolio


def _sample_timeseries(start='2020-01-01', periods=400):
    dates = pd.bdate_range(start, periods=periods)
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
                print_starts=False,
            )

        self.assertEqual(mock_fetch.call_count, 2)
        for call in mock_fetch.call_args_list:
            self.assertEqual(call.kwargs['source'], 'tiingo')
            self.assertEqual(call.kwargs['api_key'], 'test-key')
            self.assertIsNone(call.kwargs['dir_name'])

    def test_fetch_timeseries_prints_symbol_starts(self):
        portfolio = Portfolio()
        start = datetime.datetime(2015, 1, 1)
        end = datetime.datetime(2021, 12, 31)

        def mock_fetch(symbol, **kwargs):
            if symbol == 'SPY':
                return _sample_timeseries('2010-01-01', 3000)
            return _sample_timeseries('2019-01-01', 700)

        with patch('pinkfish.portfolio.fetch_timeseries', side_effect=mock_fetch):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                portfolio.fetch_timeseries(
                    ['SPY', 'DBMF'],
                    start,
                    end,
                    print_starts=True,
                )
                output = mock_stdout.getvalue()

        self.assertIn('Symbol timeseries availability:', output)
        self.assertIn('DBMF', output)
        self.assertIn('limits portfolio', output)
        self.assertIn('Portfolio effective start', output)


class TestSymbolTimeseriesMetadata(unittest.TestCase):

    def test_symbol_timeseries_metadata_marks_limiting_symbol(self):
        pairs = [
            ('SPY', _sample_timeseries('2010-01-01', 3000)),
            ('DBMF', _sample_timeseries('2019-01-01', 700)),
        ]
        metadata = symbol_timeseries_metadata(pairs)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_symbol_timeseries_starts(metadata, portfolio_start='2019-01-02')
            output = mock_stdout.getvalue()

        self.assertEqual(metadata.loc[metadata['symbol'] == 'DBMF', 'start_date'].iloc[0],
                         '2019-01-01')
        self.assertIn('limits portfolio', output)
        self.assertIn('Limited by: DBMF', output)


if __name__ == '__main__':
    unittest.main()
