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

    def _run_fetch(self, pages, **kwargs):
        class MockResponse:
            def __init__(self, payload):
                self.payload = payload
                self.status_code = 200
                if isinstance(payload, tuple):
                    self.status_code, self.payload = payload

            def raise_for_status(self):
                pass

            def json(self):
                if isinstance(self.payload, Exception):
                    raise self.payload
                return self.payload

        calls = []

        def mock_get(url, params, headers, timeout, allow_redirects=True):
            calls.append({
                'url': url,
                'params': dict(params),
                'headers': dict(headers),
                'timeout': timeout,
                'allow_redirects': allow_redirects,
            })
            return MockResponse(pages[len(calls) - 1])

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
                    api_root='https://example.test/v1',
                    use_cache=False,
                    **kwargs,
                )
        finally:
            fetch.requests.get = original_get
            fetch._get_cache_dir = original_cache_dir
        return ts, calls

    def test_fetch_fxmacrodata_timeseries(self):
        pages = [{
            'data': [
                {'date': '2026-01-02', 'val': 1.2},
                {'date': '2026-01-01', 'val': 1.1},
            ],
            'pagination': {'has_more': False},
        }]
        ts, calls = self._run_fetch(pages, api_key='test-key')

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['url'], 'https://example.test/v1/forex/EUR/USD')
        self.assertEqual(calls[0]['headers'], {'X-API-Key': 'test-key'})
        self.assertNotIn('api_key', calls[0]['params'])
        self.assertLessEqual(calls[0]['params']['limit'], 100)
        self.assertFalse(calls[0]['allow_redirects'])
        self.assertIsInstance(ts, pd.DataFrame)
        self.assertEqual(list(ts['close']), [1.1, 1.2])
        self.assertEqual(list(ts.columns),
                         ['open', 'high', 'low', 'close', 'adj_close', 'volume'])

    def test_fetch_fxmacrodata_timeseries_reads_every_page(self):
        pages = [
            {
                'data': [{'date': '2026-01-01', 'val': 1.1}],
                'pagination': {'has_more': True, 'next_offset': 1},
            },
            {
                'data': [{'date': '2026-01-02', 'val': 1.2}],
                'pagination': {'has_more': False},
            },
        ]
        ts, calls = self._run_fetch(pages, api_key='test-key')

        self.assertEqual([c['params']['offset'] for c in calls], [0, 1])
        self.assertEqual(list(ts['close']), [1.1, 1.2])

    def test_fetch_fxmacrodata_timeseries_key_from_env(self):
        pages = [{'data': [{'date': '2026-01-01', 'val': 1.1}]}]
        with patch.dict('os.environ', {'FXMACRODATA_API_KEY': 'env-key'}):
            _, calls = self._run_fetch(pages)
        self.assertEqual(calls[0]['headers'], {'X-API-Key': 'env-key'})

    def test_fetch_fxmacrodata_timeseries_refuses_redirect(self):
        with self.assertRaises(ValueError) as ctx:
            self._run_fetch([(302, {})], api_key='secret-key')
        self.assertIn('redirect', str(ctx.exception))
        self.assertNotIn('secret-key', str(ctx.exception))

    def test_fetch_fxmacrodata_timeseries_bad_key_not_echoed(self):
        for bad in (' secret-key x', 'secret\nkey', 'sec ret'):
            with self.assertRaises(ValueError) as ctx:
                self._run_fetch([], api_key=bad)
            self.assertNotIn('secret', str(ctx.exception))

    def test_fetch_fxmacrodata_timeseries_strips_key(self):
        pages = [{'data': [{'date': '2026-01-01', 'val': 1.1}]}]
        _, calls = self._run_fetch(pages, api_key='test-key\n')
        self.assertEqual(calls[0]['headers'], {'X-API-Key': 'test-key'})

    def test_fetch_fxmacrodata_timeseries_error_body_with_200(self):
        pages = [{'detail': 'Unknown currency pair'}]
        with self.assertRaises(ValueError) as ctx:
            self._run_fetch(pages, api_key='test-key')
        self.assertIn('Unknown currency pair', str(ctx.exception))

    def test_fetch_fxmacrodata_timeseries_malformed_payloads(self):
        for pages in (
            [['not', 'a', 'dict']],
            [{'data': 'nope'}],
            [ValueError('not json')],
            [{'data': [{'val': 1.1}]}],
            [{'data': [{'date': '2026-01-01', 'val': 'abc'}]}],
            [{'data': [{'date': '2026-01-01', 'val': 1.1}],
              'pagination': {'has_more': True, 'next_offset': 0}}],
        ):
            with self.assertRaises(ValueError):
                self._run_fetch(pages, api_key='test-key')

    def test_fetch_fxmacrodata_timeseries_requires_key(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                self._run_fetch([])


if __name__ == '__main__':
    unittest.main()
