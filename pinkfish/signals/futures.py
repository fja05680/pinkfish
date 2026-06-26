"""
CME quarterly micro futures contract selection and roll warnings.

Supports /MES and /MNQ roots in Schwab format (e.g. /MESM26, /MNQH26).
"""

import datetime

QUARTER_MONTHS = (3, 6, 9, 12)
MONTH_CODE = {3: 'H', 6: 'M', 9: 'U', 12: 'Z'}
PRODUCTS = frozenset({'MES', 'MNQ'})
ROLL_DAYS_BEFORE_EXPIRY = 8


def parse_root(symbol):
    """
    Return the futures product for a Schwab root symbol, or None.

    Accepts ``/MES``, ``MES``, ``/mnq``, etc.
    """
    if not symbol:
        return None
    product = symbol.strip().upper().lstrip('/')
    if product in PRODUCTS:
        return product
    return None


def third_friday(year, month):
    """Return the third Friday of ``month`` in ``year``."""
    first = datetime.date(year, month, 1)
    first_friday = first + datetime.timedelta(days=(4 - first.weekday()) % 7)
    return first_friday + datetime.timedelta(days=14)


def _next_quarter(year, month):
    index = QUARTER_MONTHS.index(month)
    if index == len(QUARTER_MONTHS) - 1:
        return year + 1, QUARTER_MONTHS[0]
    return year, QUARTER_MONTHS[index + 1]


def _nearest_quarter_expiry(as_of):
    """
    Return ``(year, quarter_month, expiry_date)`` for the next quarterly
    contract that has not yet expired.
    """
    for year in (as_of.year, as_of.year + 1):
        for month in QUARTER_MONTHS:
            expiry = third_friday(year, month)
            if as_of <= expiry:
                return year, month, expiry
    raise RuntimeError(f'no quarterly expiry found for {as_of}')


def format_contract(product, year, quarter_month):
    """Return the Schwab contract symbol, e.g. ``/MESM26``."""
    return f'/{product.upper()}{MONTH_CODE[quarter_month]}{year % 100:02d}'


def trade_contract(product, as_of):
    """
    Return the contract to trade on ``as_of``.

    During the expiration month of a quarterly contract, skip that month
    and use the following quarter (e.g. early June → /MESU26, not /MESM26).
    """
    year, month, expiry = _nearest_quarter_expiry(as_of)
    if as_of.year == year and as_of.month == month:
        year, month = _next_quarter(year, month)
        expiry = third_friday(year, month)
    return format_contract(product, year, month), expiry


def _expiring_contract_in_roll_window(product, as_of):
    """
    Return ``(symbol, expiry, roll_start)`` when ``as_of`` is in the roll
    window for a quarterly contract, else ``None``.
    """
    for year in (as_of.year - 1, as_of.year, as_of.year + 1):
        for month in QUARTER_MONTHS:
            expiry = third_friday(year, month)
            roll_start = expiry - datetime.timedelta(days=ROLL_DAYS_BEFORE_EXPIRY)
            if roll_start <= as_of <= expiry:
                return (
                    format_contract(product, year, month),
                    expiry,
                    roll_start,
                )
    return None


def futures_lines(trade_root, as_of, position):
    """
    Return output lines for contract selection and optional roll status.

    Parameters
    ----------
    trade_root : str
        Futures root such as ``/MES`` or ``/MNQ``.
    as_of : datetime.date
        Signal date.
    position : str
        End-of-day position: ``LONG`` or ``FLAT``.

    Returns
    -------
    list of str
        Empty when ``trade_root`` is not a supported futures product.
    """
    product = parse_root(trade_root)
    if product is None:
        return []

    contract, expiry = trade_contract(product, as_of)
    lines = [f'Contract: {contract} (expires {expiry})']

    if position.upper() != 'LONG':
        return lines

    roll = _expiring_contract_in_roll_window(product, as_of)
    if roll is None:
        lines.append('Roll: OK')
        return lines

    expiring_symbol, expiring_date, roll_start = roll
    target, _ = trade_contract(product, as_of)
    if expiring_symbol == target:
        lines.append('Roll: OK')
        return lines

    lines.append(
        f'Roll: ROLL — close {expiring_symbol}, open {target} '
        f'(window opened {roll_start})'
    )
    return lines
