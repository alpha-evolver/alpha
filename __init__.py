# Alpha - A股行情数据接口 + 定量分析
# Alpha 开发的券商行情协议接口包
#
# 主要模块：
# - hq: 行情数据接口
# - reader: 数据读取器
# - config: 服务器配置
# - params: 参数定义
# - quant: CFA定量分析 (新增)

# 导出主要类
from .hq import AlfeHq_API
from .reader import AlfeDailyBarReader, AlfeMinBarReader
from .params import *

# 定量分析模块
from .quant import QuantAnalyzer

# 保持兼容性别名
TdxHq_API = AlfeHq_API
TdxDailyBarReader = AlfeDailyBarReader
TdxMinBarReader = AlfeMinBarReader

# 版本
__version__ = "1.1.0"

__all__ = [
    "AlfeHq_API",
    "TdxHq_API",  # 兼容性别名
    "AlfeDailyBarReader", 
    "AlfeMinBarReader",
    "TdxDailyBarReader",  # 兼容性别名
    "TdxMinBarReader",  # 兼容性别名
    "QuantAnalyzer",  # 定量分析
]
