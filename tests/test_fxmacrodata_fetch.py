import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from pinkfish.fetch import (
    fetch_fx_timeseries,
    fetch_fxmacrodata_timeseries,
)


class TestFXMacroDataFetch(unittest.TestCase):

    def test_fetch_fx_timeseries_defaults_to_fxmacrodata(self):
        with patch('pinkfish.fetch.fetch_fxmacrodata_timeseries') as mock_fetch:
            mock_fetch.return_value = pd.DataFrame()
            fetch_fx_timeseries('EUR/USD', '2026-01-01', '2026-01-02')
            mock_fetch.assert_called_once_with(
                'EUR/USD',
                '2026-01-01',
                '2026-01-02',
                dir_name='fxmacrodata-cache',
                use_cache=True,
            )

    def test_fetch_fx_timeseries_unknown_source(self):
        with self.assertRaises(ValueError):
            fetch_fx_timeseries('EUR/USD', '2026-01-01', '2026-01-02',
                                source='unknown')

    def test_fetch_fxmacrodata_timeseries(self):
        class MockResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    'data': [
                        {'date': '2026-01-02', 'val': 1.2},
                        {'date': '2026-01-01', 'val': 1.1},
                    ]
                }

        calls = {}

        def mock_get(url, params, timeout):
            calls['url'] = url
            calls['params'] = params
            calls['timeout'] = timeout
            return MockResponse()

        import pinkfish.fetch as fetch

        original_get = fetch.requests.get
        original_cache_dir = fetch._get_cache_dir
        try:
            fetch.requests.get = mock_get
            with tempfile.TemporaryDirectory() as cache_dir:
                fetch._get_cache_dir = lambda dir_name: Path(cache_dir)
                ts = fetch_fxmacrodata_timeseries(
                    'EUR/USD',
                    '2026-01-01',
                    '2026-01-02',
                    api_key='test-key',
                    api_root='https://example.test/api/v1',
                    use_cache=False,
                )
        finally:
            fetch.requests.get = original_get
            fetch._get_cache_dir = original_cache_dir

        self.assertEqual(calls['url'], 'https://example.test/api/v1/forex/EUR/USD')
        self.assertEqual(calls['params']['api_key'], 'test-key')
        self.assertIsInstance(ts, pd.DataFrame)
        self.assertEqual(list(ts['close']), [1.1, 1.2])
        self.assertEqual(list(ts.columns),
                         ['open', 'high', 'low', 'close', 'adj_close', 'volume'])


if __name__ == '__main__':
    unittest.main()
