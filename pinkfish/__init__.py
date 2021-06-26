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
    ALPHA_BEGIN,
    SP500_BEGIN,
    currency_metrics,
    stats,
    currency,
    summary,
    optimizer_summary
)

from .plot import (
    plot_equity_curve,
    plot_equity_curves,
    plot_trades,
    plot_bar_graph,
    optimizer_plot_bar_graph
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
    VOLATILITY,
    ANNUALIZED_RETURNS,
    ANNUALIZED_STANDARD_DEVIATION,
    ANNUALIZED_SHARPE_RATIO
)

from .pfcalendar import (
    calendar
)

from .stock_market_calendar import (
    stock_market_calendar
)

from .analysis import (
    monthly_returns_map,
    holding_period_map,
    prettier_graphs,
    volatility_graphs,
    kelly_criterian
)

from .utility import (
    ROOT,
    import_strategy,
    print_full,
    read_config,
    is_last_row,
    sort_dict,
    set_dict_values
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
