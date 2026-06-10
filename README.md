pinkfish
========
A lightweight backtester and spreadsheet library for security analysis.

Pinkfish is built for a specific niche: **backtesting stocks, ETFs, portfolios, and swing-trading strategies** using free daily data. It started as a way to test simple, rule-based strategies from authors like **Larry Connors**, **Cesar Alvarez**, **Andreas Clenow**, and **Gary Antonacci** — short-term mean reversion, momentum rotation, and allocation ideas that read cleanly in a few lines of Python. It is simple, pandas-native, and stays out of your way while you test ideas.

## What pinkfish is good at

- **Single stock or ETF strategies** — Connors-style mean reversion (see `examples/080.double-7s`), golden cross, sell-in-May, and similar swing-trading ideas
- **Stock and ETF portfolios** — asset allocation, sector rotation, and momentum across a fixed basket of symbols (see `examples/220.asset-allocation-portfolio`, `examples/200.momentum-gem-portfolio`, `examples/240.double-7s-portfolio`)
- **Open and close execution with daily bars** — pinkfish's distinguishing feature (see below)
- **Short selling and margin** — included in the trade log API
- **Parameter optimization** — run a strategy with different settings and compare performance metrics side by side
- **Jupyter spreadsheets** — build formatted trading spreadsheets in a notebook: add indicators, highlight buy/sell conditions, and review signals you can execute manually

Many backtesters use an order model (market, limit, stop, etc.), not "close only." Pinkfish is different in a simpler way: you choose the fill price when you call `buy()` / `sell()` — `row.open`, `row.close`, or whatever fits the rule. No order matching; you decide the price in your loop. On one daily bar you can buy at the open and sell at the close, or act on a signal at the close and fill at that close on the same day — practical for swing rules on free daily OHLC data.

## What pinkfish is not designed for

Pinkfish is **not** aimed at large, changing stock universes — for example, screening the S&P 500 each month and holding a different set of individual stocks as constituents enter and leave the index. That workflow needs point-in-time membership data, corporate actions across many symbols, and heavier infrastructure. Pinkfish keeps a **fixed, small set of symbols** and focuses on getting trade timing right.

If you need a general-purpose event-driven engine, a live-trading framework, or a stock-picking screener with a rotating universe, look elsewhere. Pinkfish does one thing well: **test trading ideas on daily OHLC data with realistic open/close fills**.

## Why another backtesting library?

I specifically wanted to backtest simple strategies from Larry Connors and others — the kind of quantified swing rules in books like *Short Term Trading Strategies That Work* (Connors and Alvarez) and *Trading Evolved* (Clenow), or dual-momentum ETF models like Antonacci's GEM approach. Even straightforward rules — buy on the close the same day a new 20-day high is set, or buy at the open and sell at the close — were awkward in the backtesters I tried. I wanted something lightweight and to the point.

## Features

- pandas DataFrames for spreadsheet-style trading signal sheets in Jupyter
- Common technical indicators included; optional integration with [TA-Lib](https://github.com/TA-Lib/ta-lib-python) or [pandas-ta](https://github.com/twopirllc/pandas-ta)
- matplotlib for equity curves and charts
- Free daily data from Yahoo Finance (cached locally)
- Simple Python API — loop over rows, call `tlog.buy()` / `tlog.sell()` at the price you choose

## Installation

I recommend using pinkfish on Linux or in a Linux VM. It should also work on Windows and macOS.

### Basic (without TA-Lib)

```bash
# Recommended: create a new Python virtual environment first.

git clone https://github.com/fja05680/pinkfish.git
cd pinkfish
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install setuptools
python setup.py install    # or: python setup.py develop
```

### Developer (with TA-Lib)

This is how I got pinkfish working on Xubuntu 22.04:

```bash
# Make sure your system is up to date
sudo apt update
sudo apt upgrade

# Install some preliminary requirements
sudo apt install build-essential
sudo apt install git
sudo apt install python3-pip

# Clone pinkfish repo from GitHub
git clone https://github.com/fja05680/pinkfish.git
cd pinkfish

# Create virtual Python environment
python -m venv venv
source venv/bin/activate

# Install pinkfish
python setup.py develop

# Install TA-Lib (optional)
cd ~/Downloads
sudo wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzvf ta-lib-0.4.0-src.tar.gz
cd ta-lib
./configure --prefix=/usr
make
sudo make install
pip install TA-Lib

# Create shared data cache directory (optional)
mkdir $HOME/data
echo [global] > $HOME/.pinkfish
echo base_dir = $HOME >> $HOME/.pinkfish
```

## Examples

Examples in the [`examples/`](examples/) folder are ordered roughly by complexity.

- [buy-and-hold](examples/010.buy-and-hold/strategy.ipynb) — minimal strategy
- [buy-open-sell-close](examples/030.buy-open-sell-close/strategy.ipynb) — buy at the open, sell at the close on the same day
- [double-7s](examples/080.double-7s/strategy.ipynb) — Connors/Alvarez mean-reversion strategy on ETFs
- [golden-cross](examples/050.golden-cross/strategy.ipynb) — classic moving-average crossover
- [asset-allocation-portfolio](examples/220.asset-allocation-portfolio/strategy.ipynb) — multi-ETF portfolio with monthly rebalance
- [spreadsheet](examples/100.spreadsheet/spreadsheet.ipynb) — trading signal sheet in Jupyter

## Documentation

API reference: [`docs/html/pinkfish/index.html`](docs/html/pinkfish/index.html)

Generate the docs with:

```bash
cd docs
./generate-docs.sh
```

## Pinkfish on YouTube

https://www.youtube.com/channel/UCsPHH2UBn8Fz0g0MGrZ2Ihw
