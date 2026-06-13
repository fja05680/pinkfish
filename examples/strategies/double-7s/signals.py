"""
Double-7s daily trading signals.

Companion to strategy.py / strategy.ipynb: backtest the rules there, then run
this script after the close for today's action.

Rules:
  - BUY pattern: close hits a new X-day low while the regime filter allows buys
  - SELL pattern: close hits a new X-day high
  - Regime filter: close above the 200-day MA, or after dropping below the
    200-day MA restart buys once close crosses back above the 70-day MA
  - FLAT + BUY pattern  -> action BUY
  - LONG + BUY pattern  -> action HOLD
  - LONG + SELL pattern -> action SELL
  - FLAT + no trade     -> action PASS
  - LONG + close below stop loss -> action SELL
  - FLAT + SELL pattern -> action PASS

Optional notifications: copy secrets.env.example to secrets.env, or use
``pinkfish.signals.notify`` env vars directly.
"""

import argparse
import datetime
import webbrowser
from pathlib import Path

import pandas as pd

import pinkfish as pf
import pinkfish.itable as itable
import pinkfish.signals as ps
from pinkfish.signals import notify
from strategy import default_options

pd.options.display.float_format = '{:0.2f}'.format

SIGNAL_SYMBOL = 'SPY'
TRADE_INSTRUMENT = SIGNAL_SYMBOL
BROKER = 'your broker'
SYMBOL_PERIOD = {'SPY': 7, 'QQQ': 10, 'TLT': 10, 'GLD': 8}
DEFAULT_SYMBOL = SIGNAL_SYMBOL
DEFAULT_START = datetime.datetime(1900, 1, 1)
DEFAULT_VIEW_START = '2026-01-01'
RESTART_SMA = 70
REGIME_SMA = default_options['sma']
STOP_LOSS_PCT = 0.15


def indicator_lines(period):
    """Return strategy-specific indicator lines for output."""
    return [
        f'Period: {period}',
        f'Regime: {REGIME_SMA}-day MA  Restart: {RESTART_SMA}-day MA',
    ]


def format_signal_message(symbol, period, latest, signal_date, prior_position,
                          quote):
    """Build the notification body."""
    return ps.build_signal_message(
        f'Double-7s → {TRADE_INSTRUMENT} ({BROKER})',
        symbol, signal_date, latest, prior_position, quote,
        indicator_lines(period), STOP_LOSS_PCT)


def buy_allowed(regime, close, sma_restart):
    """Return True when a new buy is permitted by the regime filter."""
    return regime > 0 or close > sma_restart


def add_trade_signals(df, period_high, period_low, start_position=0):
    """
    Add pattern, buy_ok, action, and position columns.

    Walk the timeseries in date order so position state is correct.
    """
    df = df.copy()
    at_high = df['close'] == df[period_high]
    at_low = df['close'] == df[period_low]

    df['pattern'] = ''
    df.loc[at_low, 'pattern'] = 'BUY'
    df.loc[at_high, 'pattern'] = 'SELL'
    df.loc[at_high & at_low, 'pattern'] = 'SELL'

    df['buy_ok'] = [
        buy_allowed(regime, close, sma_restart)
        for regime, close, sma_restart in zip(df['regime'], df['close'], df['sma70'])
    ]

    position = 1 if start_position == 'long' else 0
    entry_date = None
    entry_price = None
    positions = []
    actions = []
    entry_dates = []
    entry_prices = []
    stop_losses = []
    sell_reasons = []

    for row in df.itertuples():
        action = ''
        sell_reason = ''
        stop_loss = None
        sell_entry = (None, None, None)
        if position == 1:
            stop_loss = (ps.stop_loss_price(entry_price, STOP_LOSS_PCT)
                         if entry_price is not None else None)
            if stop_loss is not None and row.close < stop_loss:
                action = 'SELL'
                sell_reason = 'stop loss'
                sell_entry = (entry_date, entry_price, stop_loss)
                position = 0
                entry_date = None
                entry_price = None
                stop_loss = None
            elif row.pattern == 'SELL':
                action = 'SELL'
                sell_reason = 'pattern'
                sell_entry = (entry_date, entry_price, stop_loss)
                position = 0
                entry_date = None
                entry_price = None
                stop_loss = None
        elif row.pattern == 'BUY' and row.buy_ok:
            action = 'BUY'
            position = 1
            entry_date = row.Index
            entry_price = row.close
            stop_loss = ps.stop_loss_price(entry_price, STOP_LOSS_PCT)

        if not action:
            action = ps.idle_action('LONG' if position else 'FLAT')
        row_entry = ps.row_entry_fields(
            action, entry_date, entry_price, stop_loss, sell_entry)
        actions.append(action)
        positions.append('LONG' if position else 'FLAT')
        entry_dates.append(row_entry[0])
        entry_prices.append(row_entry[1])
        stop_losses.append(row_entry[2])
        sell_reasons.append(sell_reason)

    df['action'] = actions
    df['position'] = positions
    df['entry_date'] = entry_dates
    df['entry_price'] = entry_prices
    df['stop_loss'] = stop_losses
    df['sell_reason'] = sell_reasons
    return df


def build_timeseries(symbol, period, start, end):
    """Fetch data, add indicators, and finalize the timeseries."""
    period_high = f'high{period}'
    period_low = f'low{period}'

    ts = pf.fetch_timeseries(symbol, use_cache=False)
    ts = pf.select_tradeperiod(ts, start, end)

    ts['regime'] = pf.CROSSOVER(
        ts, timeperiod_fast=1, timeperiod_slow=REGIME_SMA)
    ts['sma70'] = pf.SMA(ts, timeperiod=RESTART_SMA)
    ts['sma200'] = pf.SMA(ts, timeperiod=REGIME_SMA)
    ts[period_high] = pd.Series(ts.close).rolling(window=period).max()
    ts[period_low] = pd.Series(ts.close).rolling(window=period).min()

    ts, start = pf.finalize_timeseries(ts, start, dropna=True)
    return ts, period_high, period_low


def build_pretty_table(df, period_high, period_low):
    """Format the signal table with highlights for patterns and actions."""
    pt = itable.PrettyTable(
        df, tstyle=itable.TableStyle(theme='theme1'), center=True,
        header_row=True, rpt_header=20)

    pt.update_col_header_style(
        format_function=lambda x: x.upper(), text_align='right')
    pt.update_row_header_style(
        format_function=lambda x: pd.to_datetime(str(x)).strftime('%Y/%m/%d'),
        text_align='right')

    text_cols = {'pattern', 'action', 'position', 'buy_ok', 'entry_date',
                 'sell_reason'}

    for col in range(pt.num_cols):
        col_name = pt.df.columns[col]
        if col_name == 'volume':
            pt.update_cell_style(
                cols=[col], format_function=lambda x: format(x, '.0f'),
                text_align='right')
        elif col_name == 'entry_date':
            pt.update_cell_style(
                cols=[col],
                format_function=lambda x: (
                    pd.to_datetime(x).strftime('%Y/%m/%d')
                    if pd.notna(x) else ''),
                text_align='center')
        elif col_name in text_cols:
            pt.update_cell_style(cols=[col], text_align='center')
        else:
            pt.update_cell_style(
                cols=[col], format_function=lambda x: format(x, '.2f'),
                text_align='right')

    pattern_col = df.columns.get_loc('pattern')
    action_col = df.columns.get_loc('action')
    for row in range(pt.num_rows):
        if row == 0:
            continue
        if pt.df['close'].iloc[row] == pt.df[period_high].iloc[row]:
            col = df.columns.get_loc(period_high)
            pt.update_cell_style(rows=[row], cols=[col], color='blue')
        if pt.df['close'].iloc[row] == pt.df[period_low].iloc[row]:
            col = df.columns.get_loc(period_low)
            pt.update_cell_style(rows=[row], cols=[col], color='maroon')
        if pt.df['pattern'].iloc[row] == 'BUY':
            pt.update_cell_style(rows=[row], cols=[pattern_col], color='maroon')
        elif pt.df['pattern'].iloc[row] == 'SELL':
            pt.update_cell_style(rows=[row], cols=[pattern_col], color='blue')
        if pt.df['action'].iloc[row] == 'BUY':
            pt.update_cell_style(rows=[row], cols=[action_col], color='maroon')
        elif pt.df['action'].iloc[row] == 'SELL':
            pt.update_cell_style(rows=[row], cols=[action_col], color='blue')

    return pt


def save_html(pt, path):
    """Write the formatted table to an HTML file."""
    path = Path(path)
    html = pt._repr_html_()
    path.write_text(
        f'<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<title>Double-7s Signals</title></head>'
        f'<body>{html}</body></html>',
        encoding='utf-8')
    return path


def parse_args():
    parser = argparse.ArgumentParser(
        description='Double-7s daily trading signals')
    parser.add_argument('-s', '--symbol', default=DEFAULT_SYMBOL,
                        help='Signal symbol (default: SPY)')
    parser.add_argument('-p', '--period', type=int, default=None,
                        help='Rolling window (default: symbol-specific)')
    parser.add_argument('--view-start', default=DEFAULT_VIEW_START,
                        help='Start date for the displayed table')
    parser.add_argument('--end', default=None,
                        help='End date (default: today)')
    parser.add_argument('--position', choices=('flat', 'long'), default=None,
                        help='Override opening position before the view window')
    parser.add_argument('-o', '--output',
                        default='signals.html',
                        help='HTML output path')
    parser.add_argument('--no-open', action='store_true',
                        help='Do not open the HTML file in a browser')
    notify_group = parser.add_mutually_exclusive_group()
    notify_group.add_argument('--notify', action='store_true',
                              help='Send notifications (default when configured)')
    notify_group.add_argument('--no-notify', action='store_true',
                              help='Skip push and email notifications')
    parser.add_argument('--no-notify-hold', action='store_true',
                        help='Skip Pushover (not email) when action is HOLD or PASS')
    return parser.parse_args()


def opening_position(ts, view_start, override):
    """
    Return the position carried into view_start.

    Walk the full history up to (but not including) view_start unless the
    caller overrides the opening position.
    """
    if override is not None:
        return override

    history = ts[:view_start]
    if history.empty:
        return 'flat'
    return history.iloc[-1]['position'].lower()


def main():
    args = parse_args()
    symbol = args.symbol
    period = args.period or SYMBOL_PERIOD.get(symbol, default_options['period'])
    start = DEFAULT_START
    end = (datetime.datetime.fromisoformat(args.end)
           if args.end else datetime.datetime.now())

    ts, period_high, period_low = build_timeseries(
        symbol, period, start, end)

    ts = add_trade_signals(ts, period_high, period_low, start_position=0)
    opening = opening_position(ts, args.view_start, args.position)
    if args.position is not None:
        view_ts = ts[args.view_start:].copy()
        view_ts = add_trade_signals(
            view_ts, period_high, period_low, start_position=opening)
        df = view_ts
    else:
        df = ts[args.view_start:]

    pt = build_pretty_table(df, period_high, period_low)
    output_path = save_html(pt, args.output)

    quote = pf.get_quote([symbol])
    latest = df.iloc[-1]
    if latest.action == 'BUY':
        prior_position = 'FLAT'
    elif latest.action == 'SELL':
        prior_position = 'LONG'
    else:
        prior_position = latest.position

    signal_date = df.index[-1].date()
    ps.print_signal_summary(
        symbol, TRADE_INSTRUMENT, BROKER, signal_date, latest,
        prior_position, quote, indicator_lines(period), STOP_LOSS_PCT,
        output_path)

    should_notify = (
        not args.no_notify and (args.notify or notify.configured())
    )
    if should_notify:
        action = ps.display_action(latest)
        message = format_signal_message(
            symbol, period, latest, signal_date, prior_position, quote)
        title = f'Double-7s: {action} {TRADE_INSTRUMENT}'
        sent = notify.send(
            title, message, action, notify_hold=not args.no_notify_hold)
        if sent:
            print(f'Notifications sent: {", ".join(sent)}')
        else:
            print('Notifications not sent: configure PUSHOVER_USER_KEY and '
                  'PUSHOVER_API_TOKEN, or RESEND_API_KEY with '
                  'NOTIFY_EMAIL_FROM and NOTIFY_EMAIL_TO')

    if not args.no_open:
        webbrowser.open(output_path.resolve().as_uri())


if __name__ == '__main__':
    main()
