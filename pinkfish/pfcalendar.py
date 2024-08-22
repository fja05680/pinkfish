"""
Adds calendar columns to a timeseries.

 - `dotw` : int, {0-6}
    Day of the week with Monday=0, Sunday=6.

 - `dotm` : int, {1,2,...}
    Day of the month as 1,2,...

 - `doty` : int, {1,2,...}
    Day of the year as 1,2,...

 - `month` : int, {1-12}
    Month as January=1,...,December=12

 - `first_dotw` : bool
    First trading day of the week.

 - `last_dotw` : bool
    Last trading day of the week.

 - `first_dotm` : bool
    First trading day of the month.

 - `last_dotm` : bool
    Last trading day of the month.

 - `first_doty` : bool
    First trading day of the year.

 - `last_doty` : bool
    Last trading day of the year.
"""

import pandas as pd
pd.set_option('future.no_silent_downcasting', True)


def _first_day(row):
    """
    Get the first trading day of week, month, year.
    """
    first_dotw = row['dotw'] < row['__prev_dotw__']
    first_dotm = row['dotm'] < row['__prev_dotm__']
    first_doty = row['doty'] < row['__prev_doty__']

    return first_dotw, first_dotm, first_doty


def calendar(ts):
    """
    Add calendar columns to a timeseries.

    Parameters
    ----------
    ts : pd.DataFrame
        The timeseries of a symbol.

    Returns
    -------
    pd.DataFrame
        The timeseries with calendar columns added.
    """

    # Day of the week with Monday=0, Sunday=6.
    ts['dotw'] = ts.index.dayofweek

    # Day of the month.
    ts['dotm'] = ts.index.day

    # Day of the year.
    ts['doty'] = ts.index.dayofyear

    # Month as January=1, December=12.
    ts['month'] = ts.index.month

    # Temporarily add __prev_dotw__, __prev_dotm__, __prev_doty__ for
    # convenience; drop them later.
    ts['__prev_dotw__'] = ts['dotw'].shift()
    ts['__prev_dotw__'] = ts['__prev_dotw__'].fillna(0)

    ts['__prev_dotm__'] = ts['dotm'].shift()
    ts['__prev_dotm__'] = ts['__prev_dotm__'].fillna(0)

    ts['__prev_doty__'] = ts['doty'].shift()
    ts['__prev_doty__'] = ts['__prev_doty__'].fillna(0)

    # First and last day of the week, month, and year.
    ts['first_dotw'], ts['first_dotm'], ts['first_doty'] = \
        zip(*ts.apply(_first_day, axis=1))

    ts['last_dotw'] = ts['first_dotw'].shift(-1)
    ts['last_dotw'] = ts['last_dotw'].fillna(False).infer_objects(copy=False)

    ts['last_dotm'] = ts['first_dotm'].shift(-1)
    ts['last_dotm'] = ts['last_dotm'].fillna(False).infer_objects(copy=False)

    ts['last_doty'] = ts['first_doty'].shift(-1)
    ts['last_doty'] = ts['last_doty'].fillna(False).infer_objects(copy=False)

    # Drop temporary columns.
    ts.drop(columns=['__prev_dotw__', '__prev_dotm__', '__prev_doty__'],
            inplace=True)

    return ts
