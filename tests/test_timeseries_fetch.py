import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from pinkfish.fetch import (
    fetch_timeseries,
    fetch_tiingo_timeseries,
    fetch_yahoo_finance_timeseries,
)


class TestTimeseriesFetch(unittest.TestCase):

    def test_fetch_timeseries_defaults_to_yahoo(self):
        with patch('pinkfish.fetch.fetch_yahoo_finance_timeseries') as mock_fetch:
            mock_fetch.return_value = pd.DataFrame()
            fetch_timeseries('spy')
            mock_fetch.assert_called_once_with(
                'spy',
                dir_name='symbol-cache',
                use_cache=True,
                from_year=None,
            )

    def test_fetch_timeseries_dispatches_to_tiingo(self):
        with patch('pinkfish.fetch.fetch_tiingo_timeseries') as mock_fetch:
            mock_fetch.return_value = pd.DataFrame()
            fetch_timeseries('SPY', source='tiingo', api_key='test-key')
            mock_fetch.assert_called_once_with(
                'SPY',
                dir_name='tiingo-cache',
                use_cache=True,
                from_year=None,
                api_key='test-key',
            )

    def test_fetch_timeseries_unknown_source(self):
        with self.assertRaises(ValueError):
            fetch_timeseries('SPY', source='unknown')

    def test_fetch_tiingo_timeseries(self):
        class MockResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return [
                    {
                        'date': '2026-01-02T00:00:00.000Z',
                        'open': 101.0,
                        'high': 102.0,
                        'low': 100.0,
                        'close': 101.5,
                        'adjClose': 101.5,
                        'volume': 1000,
                    },
                    {
                        'date': '2026-01-01T00:00:00.000Z',
                        'open': 100.0,
                        'high': 101.0,
                        'low': 99.0,
                        'close': 100.5,
                        'adjClose': 100.5,
                        'volume': 900,
                    },
                ]

        calls = {}

        def mock_get(url, params, headers, timeout):
            calls['url'] = url
            calls['params'] = params
            calls['headers'] = headers
            calls['timeout'] = timeout
            return MockResponse()

        import pinkfish.fetch as fetch

        original_get = fetch.requests.get
        original_cache_dir = fetch._get_cache_dir
        try:
            fetch.requests.get = mock_get
            with tempfile.TemporaryDirectory() as cache_dir:
                fetch._get_cache_dir = lambda dir_name: Path(cache_dir)
                ts = fetch_tiingo_timeseries(
                    'SPY',
                    api_key='test-key',
                    api_root='https://example.test/tiingo/daily',
                    use_cache=False,
                )
        finally:
            fetch.requests.get = original_get
            fetch._get_cache_dir = original_cache_dir

        self.assertEqual(calls['url'], 'https://example.test/tiingo/daily/SPY/prices')
        self.assertEqual(calls['params']['startDate'], '1900-01-01')
        self.assertEqual(calls['headers']['Authorization'], 'Token test-key')
        self.assertIsInstance(ts, pd.DataFrame)
        self.assertEqual(list(ts['close']), [100.5, 101.5])
        self.assertEqual(list(ts.columns),
                         ['open', 'high', 'low', 'close', 'adj_close', 'volume'])

    def test_fetch_tiingo_reads_api_key_from_file(self):
        class MockResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return []

        calls = {}

        def mock_get(url, params, headers, timeout):
            calls['headers'] = headers
            return MockResponse()

        import pinkfish.fetch as fetch

        original_get = fetch.requests.get
        original_cache_dir = fetch._get_cache_dir
        key_path = Path(tempfile.mkstemp()[1])
        try:
            key_path.write_text('file-token\n', encoding='utf-8')
            fetch.requests.get = mock_get
            with tempfile.TemporaryDirectory() as cache_dir:
                fetch._get_cache_dir = lambda dir_name: Path(cache_dir)
                with patch('pinkfish.fetch.TIINGO_API_KEY_PATH', key_path):
                    fetch_tiingo_timeseries(
                        'SPY',
                        api_root='https://example.test/tiingo/daily',
                        use_cache=False,
                    )
        finally:
            fetch.requests.get = original_get
            fetch._get_cache_dir = original_cache_dir
            key_path.unlink(missing_ok=True)

        self.assertEqual(calls['headers']['Authorization'], 'Token file-token')

    def test_fetch_yahoo_finance_timeseries_strips_suffix(self):
        with patch('pinkfish.fetch.yf.download') as mock_download:
            mock_ts = pd.DataFrame(
                {
                    'Open': [100.0],
                    'High': [101.0],
                    'Low': [99.0],
                    'Close': [100.5],
                    'Adj Close': [100.5],
                    'Volume': [1000],
                },
                index=pd.to_datetime(['2026-01-01']),
            )
            mock_ts.index.name = 'Date'
            mock_download.return_value = mock_ts
            import pinkfish.fetch as fetch

            original_cache_dir = fetch._get_cache_dir
            try:
                with tempfile.TemporaryDirectory() as cache_dir:
                    fetch._get_cache_dir = lambda dir_name: Path(cache_dir)
                    ts = fetch_yahoo_finance_timeseries(
                        'SPY_SHRT',
                        use_cache=False,
                    )
            finally:
                fetch._get_cache_dir = original_cache_dir

        mock_download.assert_called_once()
        self.assertEqual(mock_download.call_args.args[0], 'SPY')
        self.assertIsInstance(ts, pd.DataFrame)
        self.assertEqual(ts.index[0].strftime('%Y-%m-%d'), '2026-01-01')


if __name__ == '__main__':
    unittest.main()
