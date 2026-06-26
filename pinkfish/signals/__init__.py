"""
Daily trading signal helpers: formatted output and optional notifications.

Use :mod:`pinkfish.signals` for message formatting and
:mod:`pinkfish.signals.notify` for Pushover and Resend delivery.
"""

from pinkfish.signals.format import (
    build_signal_message,
    buy_allowed_text,
    display_action,
    format_action,
    format_entry,
    format_stop_loss,
    idle_action,
    print_signal_summary,
    row_entry_fields,
    stop_loss_price,
)
from pinkfish.signals.futures import (
    format_contract,
    futures_lines,
    parse_root,
    trade_contract,
)

__all__ = [
    'build_signal_message',
    'buy_allowed_text',
    'display_action',
    'format_action',
    'format_contract',
    'format_entry',
    'format_stop_loss',
    'futures_lines',
    'idle_action',
    'parse_root',
    'print_signal_summary',
    'row_entry_fields',
    'stop_loss_price',
    'trade_contract',
]
