# Alpha - A股行情数据接口 + 定量分析
# Alpha 开发的券商行情协议接口包
#
# 主要模块：
# - hq: 行情数据接口
# - reader: 数据读取器
# - config: 服务器配置
# - params: 参数定义
# - quant: CFA定量分析
# - indicators_v2: 双系统指标 + 止盈止损

# 导出主要类
from .hq import AlfeHq_API
from .reader import AlfeDailyBarReader, AlfeMinBarReader
from .params import *

# 定量分析模块
from .quant import QuantAnalyzer

# 双系统指标 + 止盈止损
from .indicators_v2 import (
    # 手续费计算
    calc_fee,
    calc_net_return,
    # 系统1
    system1_analyze,
    system1_bollinger,
    system1_macd,
    system1_regime,
    # 系统2
    system2_analyze,
    system2_bollinger,
    system2_atr,
    system2_signals,
    # 回测
    run_backtest_with_stops,
    run_full_backtest,
    analyze_with_systems,
)

# 保持兼容性别名
TdxHq_API = AlfeHq_API
TdxDailyBarReader = AlfeDailyBarReader
TdxMinBarReader = AlfeMinBarReader

# 版本
__version__ = "1.3.0"

__all__ = [
    "AlfeHq_API",
    "TdxHq_API",
    "AlfeDailyBarReader", 
    "AlfeMinBarReader",
    "TdxDailyBarReader",
    "TdxMinBarReader",
    "QuantAnalyzer",
    # 双系统 + 止盈止损
    "calc_fee",
    "calc_net_return",
    "system1_analyze",
    "system2_analyze",
    "run_backtest_with_stops",
    "run_full_backtest",
    "analyze_with_systems",
]
