import unittest
import pandas as pd
import pinkfish as pf


class TestStatistics(unittest.TestCase):
    def setUp(self):
        d = {
            "open": [1.0, 2.0, 3.0],
            "high": [1.2, 2.2, 3.2],
            "low": [0.9, 1.9, 2.9],
            "close": [1.1, 2.1, 3.1],
            "adj_close": [1.15, 2.15, 3.15],
            "cumul_total": [5, 10, 15],
        }
        self.df_test = pd.DataFrame(d)

    def test_ending_balance(self):
        result = pf.statistics.ending_balance(self.df_test)
        self.assertEqual(result, 3.1)

    def test_total_net_profit(self):
        result = pf.statistics.total_net_profit(self.df_test)
        self.assertEqual(result, 15)


if __name__ == "__main__":
    unittest.main()
