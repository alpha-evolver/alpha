# Alpha - A-Share Market Data API + Quantitative Analysis
# Broker market protocol interface package developed by Alpha
#
# Main modules:
# - hq: Market data interface
# - reader: Data readers
# - config: Server configuration
# - params: Parameter definitions
# - quant: CFA quantitative analysis
# - indicators_v2: Dual-system indicators + Take-profit/Stop-loss

# Export main classes
from .hq import AlfeHq_API
from .reader import AlfeDailyBarReader, AlfeMinBarReader
from .params import *

# Quantitative analysis module
from .quant import QuantAnalyzer

# Dual-system indicators + Take-profit/Stop-loss
from .indicators_v2 import (
    # Fee calculation
    calc_fee,
    calc_net_return,
    # System 1
    system1_analyze,
    # System 2
    system2_analyze,
    # Backtesting
    run_backtest_with_stops,
    run_full_backtest,
    analyze_with_systems,
)

# Compatibility aliases
TdxHq_API = AlfeHq_API
TdxDailyBarReader = AlfeDailyBarReader
TdxMinBarReader = AlfeMinBarReader

# Version
__version__ = "1.3.0"

__all__ = [
    "AlfeHq_API",
    "TdxHq_API",
    "AlfeDailyBarReader",
    "AlfeMinBarReader",
    "TdxDailyBarReader",
    "TdxMinBarReader",
    "QuantAnalyzer",
    # Dual-system + Take-profit/Stop-loss
    "calc_fee",
    "calc_net_return",
    "system1_analyze",
    "system2_analyze",
    "run_backtest_with_stops",
    "run_full_backtest",
    "analyze_with_systems",
]
