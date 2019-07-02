import os
import shutil
import datetime
import unittest
import six
if six.PY3:
    from unittest import mock
else:
    import mock
import pandas as pd
import pinkfish as pf
from . test_config import read_config_for_tests


class TestFetch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir_path = os.path.dirname(os.path.abspath(__file__))
        cls.dir_name = os.path.join(cls.dir_path, "test_data")
        cls.symbol = "AAPL"
        cls.from_year = 1990
        cls.file_path = os.path.join(cls.dir_name, cls.symbol + ".csv")

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(cls.dir_name):
            shutil.rmtree(cls.dir_name)

    def test_cache_dir_created(self):
        """ Check that a cache directory has been created. """
        df = pf.fetch_timeseries(
            self.symbol, dir_name=self.dir_name, from_year=self.from_year
        )
        file_path = os.path.join(self.dir_name, self.symbol + ".csv")
        self.assertTrue(os.path.isfile(file_path))

    def test_returns_pd_data_frame(self):
        """ Check that a pandas data frame is returned. """
        df = pf.fetch_timeseries(
            self.symbol, dir_name=self.dir_name, from_year=self.from_year
        )
        assert isinstance(df, pd.DataFrame)

    def test_select_tradeperiod(self):
        """ Check the correct period is selected. """
        start = datetime.datetime(2000, 6, 30)
        end = datetime.datetime(2000, 12, 29)
        ts = pf.fetch_timeseries(
            self.symbol, dir_name=self.dir_name, from_year=self.from_year
        )
        ts = pf.select_tradeperiod(ts, start, end)
        dates = sorted(ts.index.values.tolist())

        ts_start_date = pd.Timestamp(dates[0]).to_pydatetime()
        start -= datetime.timedelta(365)  # back dating by one year
        self.assertTrue(start == ts_start_date)

        ts_end_date = pd.Timestamp(dates[-1]).to_pydatetime()
        self.assertTrue(end == ts_end_date)

    def test_select_tradeperiod_without_pad(self):
        """ Check the time period selection when pad=False. """
        start = datetime.datetime(2000, 6, 30)
        end = datetime.datetime(2000, 12, 29)
        ts = pf.fetch_timeseries(
            self.symbol, dir_name=self.dir_name, from_year=self.from_year
        )
        ts = pf.select_tradeperiod(ts, start, end, pad=False)
        dates = sorted(ts.index.values.tolist())

        ts_start_date = pd.Timestamp(dates[0]).to_pydatetime()
        self.assertTrue(start == ts_start_date)

        ts_end_date = pd.Timestamp(dates[-1]).to_pydatetime()
        self.assertTrue(end == ts_end_date)

    def test_basic_fetch(self):
        ''' Fetch all of the data we can. '''
        df = pf.fetch_timeseries(
            self.symbol, dir_name=self.dir_name
        )

    @mock.patch("pinkfish.fetch._adj_prices")
    def test_fetch_with_adj_prices(self, mocker):
        ''' Check that the _adj_prices method gets called. '''
        ts = pf.fetch_timeseries(
            self.symbol, dir_name=self.dir_name
        )

        start = datetime.datetime(2000, 6, 30)
        end = datetime.datetime(2000, 12, 29)
        ts = pf.select_tradeperiod(ts, start, end, use_adj=True)
        mocker.assert_called_once()

    def test_adj_prices(self):
        ''' Check the price adjustments. '''
        prices = {"open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15, "adj_close": 1.17}
        ts = pd.DataFrame(
            index = [datetime.datetime.now().date()],
            data = [list(prices.values())],
            columns = list(prices.keys())
        )
        ts = pf.fetch._adj_prices(ts)
    
        open_ts = round(ts["open"].values[0], 4)
        open_ex = round(prices["open"] * prices["adj_close"] / prices["close"], 4)
        self.assertEqual(open_ts, open_ex)

        high_ts = round(ts["high"].values[0], 4)
        high_ex = round(prices["high"] * prices["adj_close"] / prices["close"], 4)
        self.assertEqual(high_ts, high_ex)
    
        low_ts = round(ts["low"].values[0], 4)
        low_ex = round(prices["low"] * prices["adj_close"] / prices["close"], 4)
        self.assertEqual(low_ts, low_ex)

    @mock.patch("pinkfish.read_config", side_effect=read_config_for_tests)
    def test_fetch_with_config(self, *args):
        ''' Check the data fetch where we have a config file. '''
        file_path = os.path.join(self.dir_path, "test_data", self.symbol + ".csv")
        if os.path.isfile(file_path):
            os.remove(file_path)

        df = pf.fetch_timeseries(
            self.symbol, dir_name="test_data"
        )

        file_exists = os.path.isfile(file_path)
        self.assertTrue(file_exists)

