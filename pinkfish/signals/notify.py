"""
Pushover and Resend notifications for strategy signal scripts.

Environment variables (optional):
  Pushover: PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN, PUSHOVER_DEVICE
  Email: RESEND_API_KEY, NOTIFY_EMAIL_FROM, NOTIFY_EMAIL_TO
"""

import datetime
import html
import json
import os
from urllib import error, parse, request

USER_AGENT = 'pinkfish-signals/1.0'


def pushover_configured():
    """
    Return whether Pushover credentials are set.

    Returns
    -------
    bool
        True if ``PUSHOVER_USER_KEY`` and ``PUSHOVER_API_TOKEN`` are set.
    """
    return bool(os.environ.get('PUSHOVER_USER_KEY')
                and os.environ.get('PUSHOVER_API_TOKEN'))


def email_configured():
    """
    Return whether Resend email credentials are set.

    Returns
    -------
    bool
        True if ``RESEND_API_KEY``, ``NOTIFY_EMAIL_FROM``, and
        ``NOTIFY_EMAIL_TO`` are set.
    """
    return bool(os.environ.get('RESEND_API_KEY')
                and os.environ.get('NOTIFY_EMAIL_FROM')
                and os.environ.get('NOTIFY_EMAIL_TO'))


def configured():
    """
    Return whether any notification channel is configured.

    Returns
    -------
    bool
        True if Pushover or email credentials are set.
    """
    return pushover_configured() or email_configured()


def pushover_priority(action):
    """
    Return the Pushover message priority for an action.

    Parameters
    ----------
    action : str
        The signal action: BUY, SELL, HOLD, or PASS.

    Returns
    -------
    str
        ``'1'`` for BUY or SELL (high priority), ``'0'`` otherwise.
    """
    if action in ('BUY', 'SELL'):
        return '1'
    return '0'


def send_pushover(title, message, action):
    """
    Send a push notification through the Pushover HTTP API.

    Parameters
    ----------
    title : str
        The notification title.
    message : str
        The notification body.
    action : str
        The signal action: BUY, SELL, HOLD, or PASS.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        If Pushover returns a non-success HTTP status or API error.
    """
    fields = {
        'token': os.environ['PUSHOVER_API_TOKEN'],
        'user': os.environ['PUSHOVER_USER_KEY'],
        'title': title,
        'message': message,
        'priority': pushover_priority(action),
    }
    device = os.environ.get('PUSHOVER_DEVICE')
    if device:
        fields['device'] = device
    data = parse.urlencode(fields).encode('utf-8')
    req = request.Request(
        'https://api.pushover.net/1/messages.json',
        data=data,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': USER_AGENT,
        },
        method='POST',
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                raise RuntimeError(f'Pushover returned status {resp.status}')
            body = json.loads(resp.read().decode())
            if body.get('status') != 1:
                raise RuntimeError(f'Pushover error: {body}')
    except error.HTTPError as exc:
        body = exc.read().decode(errors='replace')
        raise RuntimeError(
            f'Pushover returned status {exc.code}: {body}') from exc


def send_email(subject, message):
    """
    Send a backup email through the Resend HTTP API.

    Parameters
    ----------
    subject : str
        The email subject.
    message : str
        The plain-text email body.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        If Resend returns a non-success HTTP status.
    """
    payload = json.dumps({
        'from': os.environ['NOTIFY_EMAIL_FROM'],
        'to': os.environ['NOTIFY_EMAIL_TO'],
        'subject': subject,
        'text': message,
        'html': (
            f'<p><strong>{html.escape(subject)}</strong></p>'
            f'<pre>{html.escape(message)}</pre>'
        ),
    }).encode('utf-8')
    req = request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {os.environ["RESEND_API_KEY"]}',
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT,
        },
        method='POST',
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError(f'Resend returned status {resp.status}')
    except error.HTTPError as exc:
        body = exc.read().decode(errors='replace')
        raise RuntimeError(
            f'Resend returned status {exc.code}: {body}') from exc


def send(title, message, action='PASS', *, notify_hold=True, email_subject=None):
    """
    Send Pushover and email notifications.

    Email sends on every run when configured.  Pushover sends on BUY and
    SELL always; HOLD and PASS too unless ``notify_hold`` is False.
    Failures are printed and do not stop other channels.

    Parameters
    ----------
    title : str
        The Pushover notification title.
    message : str
        The notification body.
    action : str, optional
        The signal action: BUY, SELL, HOLD, or PASS
        (default is 'PASS').
    notify_hold : bool, optional
        When False, skip Pushover for HOLD and PASS
        (default is True).
    email_subject : str, optional
        The email subject (default is None, which implies
        ``title`` plus the current time).

    Returns
    -------
    list of str
        Channels that succeeded: ``'pushover'`` and/or ``'email'``.
    """
    if email_subject is None:
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        email_subject = f'{title} {timestamp}'
    sent = []

    send_push_now = action in ('BUY', 'SELL') or notify_hold
    if pushover_configured() and send_push_now:
        try:
            send_pushover(title, message, action)
            sent.append('pushover')
        except (error.URLError, RuntimeError) as exc:
            print(f'Pushover notification failed: {exc}')

    if email_configured():
        try:
            print(f'Email subject: {email_subject}')
            send_email(email_subject, message)
            sent.append('email')
        except (error.URLError, RuntimeError) as exc:
            print(f'Email notification failed: {exc}')

    return sent
