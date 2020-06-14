import os
from configparser import ConfigParser
import unittest
import six
if six.PY3:
    from unittest import mock
    print_location = "builtins.print"
else:
    import mock
    print_location = "__builtin__.print"
import pandas as pd
import numpy as np
import pinkfish as pf
from . test_config import get_test_config_path


class TestUtility(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        ''' Ensure we delete the test .pinkfish file if it exists. '''
        config_path = get_test_config_path()
        if os.path.isfile(config_path):
            os.remove(config_path)

    @mock.patch(print_location)
    def test_print_full(self, mocker):
        ''' Check that our data frame is printed. '''
        df = pd.DataFrame(np.random.randn(20, 4), columns=list("ABCD"))
        pf.print_full(df)
        mocker.assert_called_once_with(df)

    @mock.patch("os.path.expanduser", side_effect=get_test_config_path)
    def test_read_config(self, mocker):
        ''' Check that the config file is read correctly. '''
        config_path = get_test_config_path()
        config = ConfigParser()

        config["global"] = {}
        config["global"]["global1"] = "1"
        config["global"]["base_dir"] = "some_directory"
        config["global"]["global3"] = "3"

        with open(config_path, "w") as config_file:
            config.write(config_file)

        conf_dict = pf.read_config()
        self.assertTrue(config["global"]["base_dir"] == conf_dict["base_dir"])
