# Pinkfish examples

Examples are grouped by purpose. The numbered prefixes are gone — use this README as the curriculum.

Open notebooks from the repo root after [installing pinkfish](../README.md#jupyter) (`jupyter nbclassic`, then browse into `examples/`).

## Layout

```
examples/
  basics/       First steps with pinkfish
  tutorials/    Library features (indicators, spreadsheets, data)
  strategies/   Single-symbol trading rules
  portfolios/   Multi-symbol portfolios and rotation
  patterns/     Cross-strategy workflows
```

### Standard files

| File | Purpose |
|------|---------|
| `strategy.py` | `Strategy` class and `default_options` (importable via `pf.import_strategy`) |
| `strategy.ipynb` | Backtest walkthrough and charts |
| `optimize.ipynb` | Optional parameter sweep |
| `signals.py` | Optional daily signal script |
| `run-signals.sh` | Optional wrapper for cron / notifications |
| `README.md` | Optional setup notes |

Import a strategy module from another notebook or script:

```python
import pinkfish as pf

double7s = pf.import_strategy(strategy_name='strategies/double-7s')
s = double7s.Strategy(symbol, capital, start, end)
s.run()
```

---

## Suggested learning path

### 1. Basics

Start here if you are new to pinkfish.

| Example | Notebook | What you learn |
|---------|----------|----------------|
| [buy-and-hold](basics/buy-and-hold/strategy.ipynb) | `strategy.ipynb` | Minimal loop: fetch data, buy, sell, stats |
| [dividends](basics/dividends/strategy.ipynb) | `strategy.ipynb` | Adjusted vs unadjusted prices |
| [buy-open-sell-close](basics/buy-open-sell-close/strategy.ipynb) | `strategy.ipynb` | Buy at the open, sell at the close on the same bar |
| [pinkfish-challenge](basics/pinkfish-challenge/strategy.ipynb) | `strategy.ipynb` | Buy on the close the same day a new 20-day high is set — a fill pattern most backtesters make awkward |

### 2. Tutorials

Pinkfish features that support strategy work — not strategies themselves.

| Example | Notebook | What you learn |
|---------|----------|----------------|
| [indicators](tutorials/indicators/indicator-tutorial.ipynb) | `indicator-tutorial.ipynb` | Built-in indicators (`SMA`, `CROSSOVER`, momentum, …) |
| [ta-lib](tutorials/ta-lib/ta-lib-tutorial.ipynb) | `ta-lib-tutorial.ipynb` | TA-Lib integration |
| [pandas-ta](tutorials/pandas-ta/pandas-ta-tutorial.ipynb) | `pandas-ta-tutorial.ipynb` | pandas-ta integration |
| [spreadsheet](tutorials/spreadsheet/spreadsheet.ipynb) | `spreadsheet.ipynb` | Jupyter signal sheets with `pinkfish.itable` |
| [merge-trades](tutorials/merge-trades/strategy.ipynb) | `strategy.ipynb` | Merge scaled entries and exits in the trade log |
| [prettier-graphs](tutorials/prettier-graphs/strategy.ipynb) | `strategy.ipynb` | `prettier_graphs()` styling |
| [update-cache-symbols](tutorials/update-cache-symbols/update-cache-symbols.ipynb) | `update-cache-symbols.ipynb` | Refresh the local symbol cache |
| [get-symbol-metadata](tutorials/get-symbol-metadata/get-symbol-metadata.ipynb) | `get-symbol-metadata.ipynb` | Inspect cached symbol metadata |
| [sp500-components-timeseries](tutorials/sp500-components-timeseries/sp500-components-timeseries.ipynb) | `sp500-components-timeseries.ipynb` | Bulk-download S&P 500 components |

### 3. Strategies

Single-symbol rules. Most folders have `strategy.py` plus `strategy.ipynb`; several include `optimize.ipynb`.

| Example | Notebook | Notes |
|---------|----------|-------|
| [golden-cross](strategies/golden-cross/strategy.ipynb) | `strategy.ipynb` | 50/200-day moving-average crossover |
| [sell-in-may](strategies/sell-in-may/strategy.ipynb) | `strategy.ipynb` | Seasonal calendar rule |
| [double-7s](strategies/double-7s/strategy.ipynb) | `strategy.ipynb` | Connors/Alvarez mean reversion; [daily signals](strategies/double-7s/README.md) |
| [sma-percent-band](strategies/sma-percent-band/strategy.ipynb) | `strategy.ipynb` | SMA envelope breakout |
| [monthly-sma](strategies/monthly-sma/strategy.ipynb) | `strategy.ipynb` | Monthly timing filter |
| [percent-allocate](strategies/percent-allocate/strategy.ipynb) | `strategy.ipynb` | Target percent allocation |
| [sell-short](strategies/sell-short/strategy.ipynb) | `strategy.ipynb` | Short selling |
| [scaling-in-out](strategies/scaling-in-out/strategy.ipynb) | `strategy.ipynb` | Scale in and out of positions |
| [follow-trend](strategies/follow-trend/strategy.ipynb) | `strategy.ipynb` | Index regime plus per-stock bands |
| [momentum](strategies/momentum/strategy.ipynb) | `strategy.ipynb` | Price lookback momentum |

**Daily signals** — [double-7s](strategies/double-7s/) includes `signals.py`, `run-signals.sh`, and optional Pushover/email via `pinkfish.signals.notify`. See [strategies/double-7s/README.md](strategies/double-7s/README.md).

### 4. Portfolios

Multi-symbol baskets, rotation, and weighting.

| Example | Notebook | Notes |
|---------|----------|-------|
| [asset-allocation-portfolio](portfolios/asset-allocation-portfolio/strategy.ipynb) | `strategy.ipynb` | Fixed-weight rebalance |
| [correlation-portfolio](portfolios/correlation-portfolio/strategy.ipynb) | `strategy.ipynb` | Correlation heatmap |
| [momentum-dmsr-portfolio](portfolios/momentum-dmsr-portfolio/strategy.ipynb) | `strategy.ipynb` | Sector dual momentum |
| [momentum-gem-portfolio](portfolios/momentum-gem-portfolio/strategy.ipynb) | `strategy.ipynb` | Antonacci GEM dual momentum |
| [weight-by-portfolio](portfolios/weight-by-portfolio/strategy.ipynb) | `strategy.ipynb` | Dynamic weighting schemes |
| [long-short-portfolio](portfolios/long-short-portfolio/strategy.ipynb) | `strategy.ipynb` | Long and short legs |
| [double-7s-portfolio](portfolios/double-7s-portfolio/strategy.ipynb) | `strategy.ipynb` | Multi-ETF double-7s |
| [double-7s-ave-portfolio](portfolios/double-7s-ave-portfolio/strategy.ipynb) | `strategy.ipynb` | Multiple lookback periods on one symbol |

### 5. Patterns

Workflows that combine other examples.

| Example | Notebook | What you learn |
|---------|----------|----------------|
| [compare-strategies](patterns/compare-strategies/strategy.ipynb) | `strategy.ipynb` | Import and compare several strategies on one symbol |

---

## Quick picks

Short list if you do not want the full path:

- **Minimal** → [basics/buy-and-hold](basics/buy-and-hold/strategy.ipynb)
- **Open/close fills** → [basics/buy-open-sell-close](basics/buy-open-sell-close/strategy.ipynb)
- **Connors mean reversion** → [strategies/double-7s](strategies/double-7s/strategy.ipynb)
- **Golden cross** → [strategies/golden-cross](strategies/golden-cross/strategy.ipynb)
- **Spreadsheet signals** → [tutorials/spreadsheet](tutorials/spreadsheet/spreadsheet.ipynb)
- **ETF portfolio** → [portfolios/asset-allocation-portfolio](portfolios/asset-allocation-portfolio/strategy.ipynb)
- **Compare strategies** → [patterns/compare-strategies](patterns/compare-strategies/strategy.ipynb)
