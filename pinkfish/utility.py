"""
Utility functions.
"""

from configparser import ConfigParser
import os

import pandas as pd

import pinkfish as pf


def print_full(x):
    """
    Print every row of list-like object.
    """
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')


def read_config():
    """
    Read pinkfish configuration.
    """
    conf = {}
    parser = ConfigParser()
    parser.read(os.path.expanduser('~/.pinkfish'))
    conf['base_dir'] = parser.get('global', 'base_dir')
    return conf


def is_last_row(ts, index):
    """
    Return True for last row, False otherwise.
    """
    return True if (index == len(ts) - 1) else False

def sort_dict(d, reverse=False):
    """
    Return sorted dict; optionally reverse sort.
    """
    return dict(sorted(d.items(), key=lambda x: x[1], reverse=reverse))

def set_dict_values(d, value):
    """
    Return dict with same keys as `d` and all values equal to `value'.
    """
    return dict.fromkeys(d, value)
