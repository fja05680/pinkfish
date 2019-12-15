"""
calendar
---------
Adds calendar columns to a dataframe

dotw: day of the week with Monday=0, Sunday=6
dotm: day of the month as 1,2,...
doty: day of the year as 1,2, ...
month: month as January=1,...,December=12
first_dotw: first trading day of the week
last_dotw: last trading day of the week
first_dotm: first trading day of the month
last_dotm: last trading day of the month
first_doty: first trading day of the year
last_doty: last trading day of the year

"""

# Use future imports for python 3.0 forward compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

# other imports
import pandas as pd
from itertools import izip
import pinkfish as pf

def _first_day(row):
    first_dotw = row['dotw'] < row['__prev_dotw__']
    first_dotm = row['dotm'] < row['__prev_dotm__']
    first_doty = row['doty'] < row['__prev_doty__']

    return first_dotw, first_dotm, first_doty

def calendar(ts):
    """ returns timeseries with calendar columns added """

    # day of the week with Monday=0, Sunday=6
    ts['dotw'] = ts.index.dayofweek

    # day of the month
    ts['dotm'] = ts.index.day

    # day of the year
    ts['doty'] = ts.index.dayofyear

    # month as January=1, December=12
    ts['month'] = ts.index.month

    # Temporarily add __prev_dotw__, __prev_dotm__, __prev_doty__
    # for convenience; drop them later
    ts['__prev_dotw__'] = ts['dotw'].shift()
    ts['__prev_dotw__'].fillna(0, inplace=True)

    ts['__prev_dotm__'] = ts['dotm'].shift()
    ts['__prev_dotm__'].fillna(0, inplace=True)

    ts['__prev_doty__'] = ts['doty'].shift()
    ts['__prev_doty__'].fillna(0, inplace=True)

    # First and last day of the week, month, and year
    ts['first_dotw'], ts['first_dotm'], ts['first_doty'] = \
        izip(*ts.apply(_first_day, axis=1))

    ts['last_dotw'] = ts['first_dotw'].shift(-1)
    ts['last_dotw'].fillna(False, inplace=True)

    ts['last_dotm'] = ts['first_dotm'].shift(-1)
    ts['last_dotm'].fillna(False, inplace=True)

    ts['last_doty'] = ts['first_doty'].shift(-1)
    ts['last_doty'].fillna(False, inplace=True)

    # Drop temporary columns
    ts.drop(columns=['__prev_dotw__', '__prev_dotm__', '__prev_doty__'], inplace=True)

    return ts

