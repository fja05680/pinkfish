"""
util
---------
Utilities
"""

import pandas as pd
from configparser import ConfigParser
import os


def print_full(x):
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')

def read_config():
    ''' Read configuration '''
    conf = {}
    parser = ConfigParser()
    parser.read(os.path.expanduser('~/.pinkfish'))
    conf['base_dir'] = parser.get('global', 'base_dir')
    return conf

def is_last_row(timeseries, index):
    return True if (index == len(timeseries) - 1) else False
