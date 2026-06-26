"""
Shared formatting for strategy signal scripts.

Keeps notification and terminal output in a consistent order:
  strategy → contract → signal → date → close → indicators → pattern
  → buy allowed → position in → action → position out → entry → stop loss
  → roll → quote
"""

import pandas as pd

from pinkfish.signals.futures import futures_lines


def stop_loss_price(entry_price, stop_loss_pct):
    """
    Return the stop loss price for a given entry.

    Parameters
    ----------
    entry_price : float
        The entry price per share.
    stop_loss_pct : float
        The stop loss percent below entry (e.g. 0.15 for 15%).

    Returns
    -------
    float
        The stop loss price.
    """
    return (1 - stop_loss_pct) * entry_price


def row_entry_fields(action, entry_date, entry_price, stop_loss, sell_entry):
    """
    Return entry columns for one signal row.

    Keeps entry date, price, and stop loss visible on SELL so the
    closing notification still shows the open trade.

    Parameters
    ----------
    action : str
        The signal action: BUY, SELL, HOLD, or PASS.
    entry_date : datetime.datetime or None
        The entry date for a new or open trade.
    entry_price : float or None
        The entry price for a new or open trade.
    stop_loss : float or None
        The stop loss price for a new or open trade.
    sell_entry : tuple
        ``(entry_date, entry_price, stop_loss)`` to use when action
        is SELL.

    Returns
    -------
    tuple
        ``(entry_date, entry_price, stop_loss)`` for the row, or
        ``(None, None, None)`` when flat with no trade.
    """
    if action == 'SELL':
        return sell_entry
    if action in ('BUY', 'HOLD'):
        return entry_date, entry_price, stop_loss
    return None, None, None


def format_entry(latest):
    """
    Return the entry line for signal output.

    Parameters
    ----------
    latest : pd.Series
        The latest signal row.  Uses ``entry_price``, ``entry_date``,
        and ``action``.

    Returns
    -------
    str or None
        Formatted entry line, or None when not long and not closing.
    """
    if pd.isna(latest.entry_price):
        return None
    if latest.action not in ('BUY', 'HOLD', 'SELL'):
        return None
    entry_date = latest.entry_date
    if hasattr(entry_date, 'date'):
        entry_date = entry_date.date()
    return f'Entry: {entry_date} @ {latest.entry_price:.2f}'


def format_stop_loss(latest, stop_loss_pct):
    """
    Return the stop loss line for signal output.

    Parameters
    ----------
    latest : pd.Series
        The latest signal row.  Uses ``stop_loss`` and ``action``.
    stop_loss_pct : float
        The stop loss percent below entry (e.g. 0.15 for 15%).

    Returns
    -------
    str or None
        Formatted stop loss line, or None when not long and not closing.
    """
    if pd.isna(latest.stop_loss):
        return None
    if latest.action not in ('BUY', 'HOLD', 'SELL'):
        return None
    return f'Stop loss: {latest.stop_loss:.2f} ({stop_loss_pct:.0%})'


def idle_action(position):
    """
    Return the action when no pattern fired today.

    Parameters
    ----------
    position : str
        Position at end of day: LONG or FLAT.

    Returns
    -------
    str
        HOLD when long, PASS when flat.
    """
    return 'HOLD' if position == 'LONG' else 'PASS'


def display_action(latest):
    """
    Return the action to show in signal output.

    Parameters
    ----------
    latest : pd.Series
        The latest signal row.  Uses ``action`` and ``position``.

    Returns
    -------
    str
        BUY, SELL, HOLD (stay long), or PASS (stay flat).
    """
    action = latest.action
    if action:
        return action
    return idle_action(latest.position)


def format_action(latest):
    """
    Return the action line for signal output.

    Parameters
    ----------
    latest : pd.Series
        The latest signal row.  Uses ``action``, ``position``, and
        optionally ``sell_reason``.

    Returns
    -------
    str
        Formatted action line, with sell reason when applicable.
    """
    action = display_action(latest)
    if action == 'SELL' and getattr(latest, 'sell_reason', ''):
        return f'Action: {action} ({latest.sell_reason})'
    return f'Action: {action}'


def buy_allowed_text(latest):
    """
    Return yes/no for whether a new buy is allowed today.

    Parameters
    ----------
    latest : pd.Series
        The latest signal row.  Uses ``buy_ok`` when present.

    Returns
    -------
    str
        ``'yes'`` or ``'no'``.
    """
    if hasattr(latest, 'buy_ok'):
        return 'yes' if latest.buy_ok else 'no'
    return 'yes'


def _signal_date(signal_date):
    """Return a ``datetime.date`` from a signal timestamp."""
    if hasattr(signal_date, 'date'):
        return signal_date.date()
    return signal_date


def _append_futures_lines(lines, trade_instrument, signal_date, position):
    if not trade_instrument:
        return
    lines.extend(futures_lines(
        trade_instrument, _signal_date(signal_date), position))


def build_signal_message(strategy_line, symbol, signal_date, latest,
                         prior_position, quote, indicator_lines,
                         stop_loss_pct, trade_instrument=None):
    """
    Build the notification body in standard order.

    Parameters
    ----------
    strategy_line : str
        Strategy name and trade routing (e.g. broker or instrument).
    symbol : str
        The signal symbol.
    signal_date : datetime.date or datetime.datetime
        The signal date.
    latest : pd.Series
        The latest signal row.
    prior_position : str
        Position at the start of the signal day (LONG or FLAT).
    quote : str
        The after-hours or latest quote string.
    indicator_lines : list of str
        Strategy-specific indicator lines to insert after close.
    stop_loss_pct : float
        The stop loss percent below entry (e.g. 0.15 for 15%).
    trade_instrument : str, optional
        Futures root (e.g. ``/MES``) for contract and roll lines.

    Returns
    -------
    str
        The full message body, one field per line.
    """
    lines = [
        strategy_line,
    ]
    _append_futures_lines(lines, trade_instrument, signal_date, latest.position)
    lines.extend([
        f'Signal: {symbol}',
        f'Date: {signal_date}',
        f'Close: {latest.close:.2f}',
    ])
    lines.extend(indicator_lines)
    lines.extend([
        f'Pattern: {latest.pattern or "none"}',
        f'Buy allowed: {buy_allowed_text(latest)}',
        f'Position in: {prior_position}',
        format_action(latest),
        f'Position out: {latest.position}',
    ])
    entry = format_entry(latest)
    if entry:
        lines.append(entry)
    stop = format_stop_loss(latest, stop_loss_pct)
    if stop:
        lines.append(stop)
    lines.append(f'Quote: {quote}')
    return '\n'.join(lines)


def print_signal_summary(symbol, trade_instrument, broker, signal_date, latest,
                         prior_position, quote, indicator_lines, stop_loss_pct,
                         output_path):
    """
    Print the terminal summary in standard order.

    Parameters
    ----------
    symbol : str
        The signal symbol.
    trade_instrument : str
        The instrument to trade (may differ from the signal symbol).
    broker : str
        The broker or account label.
    signal_date : datetime.date or datetime.datetime
        The signal date.
    latest : pd.Series
        The latest signal row.
    prior_position : str
        Position at the start of the signal day (LONG or FLAT).
    quote : str
        The after-hours or latest quote string.
    indicator_lines : list of str
        Strategy-specific indicator lines to print after close.
    stop_loss_pct : float
        The stop loss percent below entry (e.g. 0.15 for 15%).
    output_path : pathlib.Path
        Path to the HTML signals file (printed at end of summary).

    Returns
    -------
    None
    """
    print(f'Signal symbol: {symbol}  Trade: {trade_instrument} via {broker}')
    futures = futures_lines(
        trade_instrument, _signal_date(signal_date), latest.position)
    for line in futures:
        print(line)
    print(f'Date: {signal_date}')
    print(f'Close: {latest.close:.2f}')
    for line in indicator_lines:
        print(line)
    print(f'Pattern: {latest.pattern or "none"}')
    print(f'Buy allowed: {buy_allowed_text(latest)}')
    print(f'Position entering day: {prior_position}')
    print(format_action(latest).replace('Action: ', 'Action today: '))
    print(f'Position after day: {latest.position}')
    entry = format_entry(latest)
    if entry:
        print(entry)
    stop = format_stop_loss(latest, stop_loss_pct)
    if stop:
        print(stop)
    print(f'Quote: {quote}')
    print(f'Signals saved to {output_path.resolve()}')
