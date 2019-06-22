import os
import shutil
import datetime
import unittest
import pandas as pd
import pinkfish as pf


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
