from .fetch import (
    fetch_timeseries,
    select_tradeperiod,
    finalize_timeseries,
    remove_cache_symbols,
    update_cache_symbols
)

from .trade import (
    Direction,
    Margin,
    TradeLog,
    TradeState,
    DailyBal
)

from .statistics import (
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
    CROSSOVER
)

from .calendar import (
    calendar
)

from .evolved import (
    monthly_returns_map,
    holding_period_map,
    prettier_graphs
)

from .utility import (
    print_full,
    read_config,
    is_last_row
)

DEBUG = False
def DBG(s):
    if DEBUG: print(s)
    else:     pass

SP500_BEGIN = '1957-03-04'

