"""
util
---------
Utilities
"""

# Use future imports for python 3.0 forward compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# Other imports
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
