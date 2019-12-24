from .fetch import (
    fetch_timeseries,
    select_tradeperiod,
    clear_timeseries
)

from .trade import (
    TradeLog,
    TradeState,
    DailyBal
)

from .statistics import (
    stats,
    currency,
    summary,
    summary2,
    summary3,
    summary4,
    summary5
)

from .evolved import (
    monthly_returns_map,
    holding_period_map,
    prettier_graphs
)

from .benchmark import (
    Benchmark
)

from .calendar import (
    calendar
)

from .plot import (
    plot_equity_curve,
    plot_trades,
    plot_bar_graph
)

from .indicator import (
    CROSSOVER
)

from .utility import (
    print_full,
    read_config
)

DEBUG = False
def DBG(s):
    if DEBUG: print(s)
    else:     pass

SP500_BEGIN = '1957-03-04'

