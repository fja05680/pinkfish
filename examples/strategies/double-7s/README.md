# Double-7s

Connors/Alvarez mean-reversion on ETFs. Backtest the rules in `[strategy.ipynb](strategy.ipynb)` (or `[strategy.py](strategy.py)`), use `[optimize.ipynb](optimize.ipynb)` to compare settings and pick what works for your symbol, then run `[signals.py](signals.py)` after the close for today's action.

Default signal symbol is **SPY**. Other presets in `signals.py`: QQQ, TLT, GLD. Carry your optimized settings into `signals.py` before you run daily signals.

## Strategy rules

- **BUY pattern** — close hits a new X-day low while the regime filter allows buys
- **SELL pattern** — close hits a new X-day high
- **Regime filter** — close above the 200-day MA, or after dropping below the 200-day MA, restart buys once close crosses back above the 70-day MA
- **Stop loss** — 15% below entry while long


| Position | Pattern / condition   | Action   |
| -------- | --------------------- | -------- |
| FLAT     | BUY pattern           | **BUY**  |
| LONG     | BUY pattern           | **HOLD** |
| LONG     | SELL pattern          | **SELL** |
| LONG     | close below stop loss | **SELL** |
| FLAT     | no trade              | **PASS** |
| FLAT     | SELL pattern          | **PASS** |


## Daily signals

From the pinkfish repo root (with your virtual environment active):

```bash
cd examples/strategies/double-7s
./run-signals.sh
```

`run-signals.sh` activates `venv` at the repo root if it exists, sources local secrets (see below), and runs `signals.py` without opening a browser.

Every run:

1. Fetches fresh daily data (never uses the local cache)
2. Prints a terminal summary for today
3. Writes `[signals.html](signals.html)` — a formatted signal table you can open in a browser
4. Optionally sends Pushover and/or email when credentials are configured

Without notification credentials, output is terminal + HTML only.

### Command-line options

```bash
python signals.py --help
```

Useful flags:


| Flag                        | Purpose                                               |
| --------------------------- | ----------------------------------------------------- |
| `-s SPY`                    | Signal symbol (default SPY)                           |
| `-p 7`                      | Rolling window (overrides symbol default)             |
| `--view-start 2026-01-01`   | First date shown in the HTML table                    |
| `--position flat` or `long` | Override opening position before the view window      |
| `--no-open`                 | Do not open the HTML file in a browser                |
| `--notify`                  | Send notifications even if you only set some env vars |
| `--no-notify`               | Skip all notifications                                |
| `--no-notify-hold`          | Skip Pushover for HOLD and PASS (email still sends)   |


## Notifications

Delivery is handled by `[pinkfish.signals.notify](../../pinkfish/signals/notify.py)`. You can use Pushover, email, or both. Channels are independent — if one fails, the other still runs.

### When each channel fires


| Channel            | BUY / SELL               | HOLD / PASS                                    |
| ------------------ | ------------------------ | ---------------------------------------------- |
| **Pushover**       | Always (when configured) | Yes by default; use `--no-notify-hold` to skip |
| **Email (Resend)** | Always (when configured) | Always (when configured)                       |


Notifications run automatically when the required environment variables are set. Use `--no-notify` to disable them for a single run.

### Configure credentials

**Recommended:** copy the example secrets file and edit it locally.

```bash
cp secrets.env.example secrets.env
# edit secrets.env with your keys — do not commit this file
```

`run-signals.sh` sources `secrets.env` from this folder. You can also add `secrets.env.local` for machine-specific overrides (same `export` syntax); it is loaded after `secrets.env`.

Alternatively, export the variables in your shell or cron job — `signals.py` reads them from the environment directly.

---

## Pushover (phone push notifications)

[Pushover](https://pushover.net) sends alerts to iOS, Android, and desktop clients. Pinkfish uses the HTTP API; there is no extra Python package to install.

### 1. Create an account

Sign up at [pushover.net](https://pushover.net). Install the app on the device where you want alerts.

### 2. Get your User Key

On the Pushover dashboard, copy your **User Key** (30 characters). This identifies your account.

### 3. Create an application API token

1. Go to [Create an Application/API Token](https://pushover.net/apps/build)
2. Name it something like `pinkfish-double-7s`
3. Copy the **API Token/Key** (30 characters)

### 4. Optional: target one device

If you have multiple devices and want pushes on only one, set **Device** to the device name shown in the Pushover client (e.g. `iphone`). Leave this unset to notify all devices.

### 5. Add to `secrets.env`

```bash
export PUSHOVER_USER_KEY='your_30_char_user_key'
export PUSHOVER_API_TOKEN='your_30_char_app_api_token'
# export PUSHOVER_DEVICE='optional_device_name'
```

### 6. Test

```bash
./run-signals.sh
```

If Pushover is configured, you should see `Notifications sent: pushover` (and/or `email`) when delivery succeeds. On failure, the script prints the error and continues.

Pushover charges a one-time fee per platform (see their site). API usage for personal alerts is included with your account.

---

## Email (Resend)

[Resend](https://resend.com) sends a plain-text and HTML copy of each signal. Email is useful as a backup log even when Pushover is working.

### 1. Create an account

Sign up at [resend.com](https://resend.com).

### 2. Create an API key

In the Resend dashboard, create an API key with **Sending access**. Copy the key (starts with `re_`).

### 3. Set the From address

- **Quick test:** Resend provides `onboarding@resend.dev` for trial sends to your own verified email.
- **Production:** Add and verify your domain under **Domains**, then use an address on that domain (e.g. `signals@yourdomain.com`).

### 4. Set the To address

Use the inbox where you want daily signals (your personal email is fine).

### 5. Add to `secrets.env`

```bash
export RESEND_API_KEY='re_your_api_key'
export NOTIFY_EMAIL_FROM='onboarding@resend.dev'
export NOTIFY_EMAIL_TO='you@example.com'
```

Replace `NOTIFY_EMAIL_FROM` with your verified domain address when you move off the sandbox.

### 6. Test

```bash
./run-signals.sh
```

Email sends on **every** run when configured, including HOLD and PASS days. The subject line is the notification title plus the current time (e.g. `Double-7s: HOLD SPY 16:05:32`).

Resend has a free tier with monthly send limits; check their pricing for your volume.

---

## Example `secrets.env`

```bash
# Pushover
export PUSHOVER_USER_KEY='abc123...'
export PUSHOVER_API_TOKEN='xyz789...'

# Email backup
export RESEND_API_KEY='re_...'
export NOTIFY_EMAIL_FROM='signals@yourdomain.com'
export NOTIFY_EMAIL_TO='you@example.com'
```

You can configure Pushover only, email only, or both.

## Schedule after the close

Run once per trading day after the market closes and daily data is available (e.g. 5:00 PM US/Eastern). Example cron entry (adjust paths and timezone):

```cron
0 17 * * 1-5 cd /path/to/pinkfish/examples/strategies/double-7s && ./run-signals.sh >> signals.log 2>&1
```

`run-signals.sh` already passes `--no-open`, which suits unattended runs.

## Files in this folder


| File                  | Purpose                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------- |
| `strategy.ipynb`      | Backtest and explore the strategy: charts, stats, benchmark comparison                            |
| `strategy.py`         | `Strategy` class used by the notebook; run `python strategy.py` to backtest from the command line |
| `optimize.ipynb`      | Compare period, regime SMA, stop loss, and margin settings                                        |
| `spreadsheet.ipynb`   | Formatted signal sheet in Jupyter for developing strategies and as a manual trading aid           |
| `signals.py`          | Daily signal script: today's action, terminal summary, and `signals.html`                         |
| `run-signals.sh`      | Wrapper: load secrets, activate venv, run `signals.py`                                            |
| `secrets.env.example` | Template for API keys (copy to `secrets.env`)                                                     |
| `signals.html`        | Generated signal table (overwritten each run)                                                     |


## Customize

Edit the constants at the top of `signals.py` if needed:

- `TRADE_INSTRUMENT` / `BROKER` — shown in messages (e.g. which ETF you actually trade and where)
- `SYMBOL_PERIOD` — default rolling window per symbol
- `STOP_LOSS_PCT` — stop loss below entry

Shared formatting and notification helpers live in `[pinkfish.signals](../../pinkfish/signals/)`.