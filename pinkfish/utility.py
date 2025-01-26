"""
Utility functions.
"""

from configparser import ConfigParser
from functools import wraps
import importlib.util
import inspect
from pathlib import Path

import pandas as pd


def _get_project_top_level():
    """
    Returns the outermost pinkfish path.
    """
    current_path = Path(__file__).resolve()
    pinkfish_path = None
    for parent in current_path.parents:
        if parent.name == "pinkfish":
            pinkfish_path = parent
    if pinkfish_path:
        return pinkfish_path
    raise RuntimeError("Top-level pinkfish directory not found")


ROOT = _get_project_top_level()
"""
str: pinkfish project root dir.
"""


def import_strategy(strategy_name, top_level_dir='examples', module_name='strategy'):
    """
    Import a strategy from a python `.py` file.

    Parameters
    ----------
    strategy_name : str
        The leaf dir name that contains the strategy to import.
    top_level_dir : str, optional
        The top level dir name for the strategies
        (default is 'examples').
    module_name: str, optional
        The name of the python module (default is 'strategy').

    Returns
    -------
    module
        The imported module.

    Examples
    --------
    >>> strategy = import_strategy(strategy_name='190.momentum-dmsr-portfolio')
    """

    strategy_location = (Path(ROOT) / Path(top_level_dir)
                                    / Path(strategy_name)
                                    / Path(module_name + '.py'))
    print(strategy_location)
    spec = importlib.util.spec_from_file_location(module_name, strategy_location)
    strategy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strategy)
    return strategy


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
    parser.read(Path('~/.pinkfish').expanduser())
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


def find_nan_rows(ts):
    """
    Return a dataframe with the rows that contain NaN values.

    This function can help you track down problems with a timeseries.
    You may need to call `pd.set_option("display.max_columns", None)`
    at the top of your notebook to display all columns.

    Examples
    --------
    >>> pd.set_option("display.max_columns", None)
    >>> df = pf.find_nan_rows(ts)
    >>> df
    """
    is_NaN = ts.isnull()
    row_has_NaN = is_NaN.any(axis=1)
    rows_with_NaN = ts[row_has_NaN]
    return rows_with_NaN


def no_empty_container(container_name, default_ret_value):
    """
    Check if container is empty.  If so, return `default_ret_value`.

    Parameters
    ----------
    container_name : str
        The name of the container parameter to check.
    default_ret_value : int
        The return value the wrapped function if the container is empty.
        (default is 'examples').
    module_name: str, optional
        The name of the python module (default is 'strategy').

    Returns
    -------
    `default_ret_value` or `func` return value : type of return value
        If the container is empty, `default_ret_value` is returned,
        otherwise the return value of `func`.

    Examples
    --------
    >>> @no_empty_container('my_list', 0)
    >>> def my_func(my_list):
    >>>     return 5
    >>> my_func([])
    0
    """

    def decorator(func):
    
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                container_obj = kwargs[container_name]
            except KeyError:
                container_arg_index = inspect.getfullargspec(func).args.index(container_name)
                container_obj = args[container_arg_index]

            if len(container_obj) == 0:
                return default_ret_value

            return func(*args, **kwargs)
        return wrapper
    return decorator
