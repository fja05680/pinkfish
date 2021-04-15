from .fetch import (
    fetch_timeseries,
    select_tradeperiod,
    finalize_timeseries,
    remove_cache_symbols,
    update_cache_symbols,
    get_symbol_metadata
)

from .trade import (
    Direction,
    Margin,
    TradeLog,
    TradeState,
    DailyBal
)

from .statistics import (
    SP500_BEGIN,
    TRADING_DAYS_PER_YEAR,
    TRADING_DAYS_PER_MONTH,
    TRADING_DAYS_PER_WEEK,
    stats,
    currency,
    summary,
    default_metrics,
    currency_metrics
)

from .plot import (
    plot_equity_curve,
    plot_equity_curves,
    plot_trades,
    plot_bar_graph
)

from .benchmark import (
    Benchmark
)

from .portfolio import (
    Portfolio
)

from .indicator import (
    CROSSOVER,
    MOMENTUM,
    VOLATILITY
)

from .pfcalendar import (
    calendar
)

from .analysis import (
    monthly_returns_map,
    holding_period_map,
    prettier_graphs,
    volatility_graphs,
    kelly_criterian
)

from .utility import (
    print_full,
    read_config,
    is_last_row
)

DEBUG = False
"""
bool : True to enable DBG() output.
"""
def DBG(s):
    """
    Debug print.  Enable by setting pf.DEBUG=True.
    """
    if DEBUG: print(s)
    else:     pass
