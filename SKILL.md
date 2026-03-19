---
name: alfe
description: >
  A股量化分析完整系统。触发场景：
  - 获取A股数据（实时行情、K线、财务数据）
  - 执行量化分析（统计、风险、回测）
  - AI策略生成与机器学习
  - 分布式回测（Ray + vectorbt）
  - 组合优化与绩效评估
  - 构建Dashboard可视化
tags: [finance, quantitative, stock, china, ai, backtest]
permissions: [network]
metadata:
  version: "2.0.0"
  author: "Alpha"
  python_version: "3.10+"
---

# Alfe - A股量化分析完整系统

**Version 2.0.0 | Author: Alpha**

---

## 系统架构 (System Architecture)

### 数据流
```
Market Data → Factor → Signal → Backtest → Portfolio → Evaluation → Visualization
```

### 模块分层
```
┌─────────────────────────────────────────────────────────────┐
│                    Visualization Layer                      │
│                    (plotly + dash)                        │
├─────────────────────────────────────────────────────────────┤
│                   Analytics Layer                          │
│                   (quantstats)                             │
├─────────────────────────────────────────────────────────────┤
│                  Portfolio Layer                           │
│                  (PyPortfolioOpt)                          │
├─────────────────────────────────────────────────────────────┤
│                  Backtest Layer                           │
│         (vectorbt / backtrader / Qlib)                    │
├─────────────────────────────────────────────────────────────┤
│                  Signal Layer                              │
│                  (TA-Lib + Custom)                        │
├─────────────────────────────────────────────────────────────┤
│                   Data Layer                              │
│              (alfe.data + yfinance + Qlib)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 边界定义 (Boundary Definition)

### 激活边界
| 触发条件 | 行为 |
|----------|------|
| 询问A股数据/行情/价格 | 执行数据获取 (alfe.data) |
| 量化分析/统计/风险指标 | 执行 analytics (quantstats) |
| 技术指标/RSI/MACD/布林带 | 执行 factor (TA-Lib) |
| 回测/模拟交易 | 执行 backtest (vectorbt/backtrader) |
| 组合优化/权重分配 | 执行 portfolio (PyPortfolioOpt) |
| AI策略/机器学习 | 执行 AI Layer (PyTorch/LightGBM) |
| Dashboard/可视化 | 执行 visualization (dash/plotly) |
| 分布式回测/参数搜索 | 执行 Ray + vectorbt |

### 权限边界
```
✅ 允许:
  - 网络: 券商行情服务器 (端口 7709, 80)
  - 网络: PyPI (pip安装)
  - 网络: GitHub (代码获取)
  - 磁盘: 工作目录读写

❌ 禁止:
  - 实盘交易指令 (仅分析，不执行)
  - 访问非声明的外部端点
  - 修改系统Python环境
```

---

## 环境规范 (Environment Specification)

### Python版本
```
Python: 3.10+
```

### 核心依赖
| 包名 | 版本 | 用途 |
|------|------|------|
| `numpy` | `1.26.x` | 数值计算 (vectorbt兼容关键) |
| `pandas` | ≥2.0 | 数据处理 |
| `scipy` | ≥1.10 | 统计分析 |
| `ta-lib` | 最新 | 技术指标计算 |
| `vectorbt` | ≥0.25 | 高速回测引擎 |
| `backtrader` | 最新 | 事件驱动回测 |
| `quantstats` | 最新 | 绩效分析 |
| `pyportfolioopt` | 最新 | 组合优化 |
| `plotly` | ≥5.0 | 可视化 |
| `dash` | ≥2.0 | Dashboard |

### 可选依赖
| 包名 | 版本 | 用途 |
|------|------|------|
| `ray` | ≥2.0 | 分布式计算 |
| `qlib` | 最新 | AI量化平台 |
| `torch` | ≥2.0 | 深度学习 |
| `lightgbm` | 最新 | 梯度提升 |
| `xgboost` | 最新 | 梯度提升 |

### 环境规则
```
✅ 强制规则:
  - 所有库必须安装在同一Python环境
  - 禁止system Python与venv混用
  - 使用Docker固化环境

✅ 版本锁定:
  - numpy==1.26.x (vectorbt兼容性)
  - setuptools==81.0.0 (避免pkg_resources问题)
  - torch + CUDA版本必须匹配

❌ 常见错误:
  - vectorbt[full] 未加引号
  - numpy 2.x 导致vectorbt崩溃
  - tornado/telegram依赖冲突
```

---

## 数据规范 (Data Specification)

### A股数据源 (alfe.data)
```python
from alfe import QuantAnalyzer

qa = QuantAnalyzer()
qa.connect_auto()

# 获取日K线
bars = qa.api.get_security_bars(
    period=9,      # 日线
    market=1,      # 1=上海, 0=深圳
    code='600519', # 6位股票代码
    start=0,
    count=60
)

qa.disconnect()
```

### 标准数据结构
```python
# OHLCV DataFrame
{
    'datetime': np.datetime64,
    'open': float,     # 开盘价
    'high': float,     # 最高价
    'low': float,      # 最低价
    'close': float,    # 收盘价
    'volume': float    # 成交量
}
```

### 数据验证规则
| 字段 | 校验规则 |
|------|----------|
| `close` | > 0 且 < 10000 |
| `high` | >= `low` |
| `high` | >= `close` |
| `volume` | >= 0 |
| `datetime` | 递增，不重复 |

---

## 技术指标 (Factor Layer)

### TA-Lib 使用
```python
import talib
import numpy as np

# 假设 data['close'] 是numpy数组
close = data['close'].values

# RSI
rsi = talib.RSI(close, timeperiod=14)

# MACD
macd, signal, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

# 布林带
upper, middle, lower = talib.BOLLBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)

# SMA/EMA
sma = talib.SMA(close, timeperiod=20)
ema = talib.EMA(close, timeperiod=20)

# ATR
high = data['high'].values
low = data['low'].values
atr = talib.ATR(high, low, close, timeperiod=14)
```

### 常用指标速查
| 指标 | 函数 | 参数 |
|------|------|------|
| RSI | `talib.RSI` | timeperiod=14 |
| MACD | `talib.MACD` | fast=12, slow=26, signal=9 |
| 布林带 | `talib.BOLLBANDS` | period=20, nbdev=2 |
| SMA | `talib.SMA` | timeperiod |
| EMA | `talib.EMA` | timeperiod |
| ATR | `talib.ATR` | timeperiod=14 |
| ADX | `talib.ADX` | timeperiod=14 |
| OBV | `talib.OBV` | - |
| CCI | `talib.CCI` | timeperiod=14 |
| Stochastic | `talib.STOCH` | fastk=14, slowk=3 |

---

## 信号生成 (Signal Layer)

### 双系统交易信号

**系统1: 趋势策略**
```
输入: df (OHLCV)
处理:
  1. Bollinger Bands (20, 2)
  2. MACD (12, 26, 9)
  3. 信号:
     - Buy: price > upper_band AND MACD > signal
     - Sell: price < middle_band
     - Hold: 其他
输出: {advice, signals, indicators}
```

**系统2: 投机策略**
```
输入: df (OHLCV)
处理:
  1. Bollinger Bands (20, 2)
  2. ATR (14)
  3. 信号:
     - Buy: price > upper_band AND volume > avg_volume
     - Stop-loss: price < entry - 2*ATR
     - Take-profit: price > entry + 3*ATR
输出: {advice, signals, atr_value, sl, tp}
```

### AI策略生成
```python
import pandas as pd
import talib
from sklearn.ensemble import RandomForestClassifier

# 特征工程
df['rsi'] = talib.RSI(df['close'])
df['ma20'] = talib.SMA(df['close'], timeperiod=20)
df['ma50'] = talib.SMA(df['close'], timeperiod=50)

# 标签: 未来N日上涨=1
N = 5
df['label'] = (df['close'].shift(-N) > df['close']).astype(int)

df = df.dropna()
X = df[['rsi', 'ma20', 'ma50', 'volume']]
y = df['label']

# 模型训练
model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# 预测信号
df['signal'] = model.predict(X)
```

---

## 回测引擎 (Backtest Layer)

### 三种执行模式

| 模式 | 工具链 | 特点 |
|------|--------|------|
| **Research** | TA-Lib → vectorbt → quantstats → plotly | 快速验证、大规模参数搜索 |
| **Production** | TA-Lib → backtrader → quantstats → dash | 结构稳定、接近实盘 |
| **AI Mode** | Qlib → Feature → Model → Backtest | 因子挖掘、ML驱动 |

### vectorbt 高速回测
```python
import vectorbt as vbt
import pandas as pd

# 假设 price 是收盘价Series
price = pd.Series(data['close'])

# 移动平均交叉策略
fast_ma = price.rolling(10).mean()
slow_ma = price.rolling(50).mean()

entries = fast_ma > slow_ma
exits = fast_ma < slow_ma

# 向量化回测
pf = vbt.Portfolio.from_signals(
    price,
    entries,
    exits,
    init_cash=100000,
    commission=0.001,  # 0.1%
)

# 绩效指标
returns = pf returns()
sharpe = returns.mean() / returns.std() * (252 ** 0.5)
max_dd = pf.max_drawdown()

print(f"Total Return: {pf.total_return():.2%}")
print(f"Sharpe Ratio: {sharpe:.2f}")
print(f"Max Drawdown: {max_dd:.2%}")
```

### backtrader 事件回测
```python
import backtrader as bt

class MyStrategy(bt.Strategy):
    def __init__(self):
        self.ma = bt.indicators.SMA(self.data.close, period=20)
    
    def next(self):
        if self.data.close > self.ma:
            self.buy()
        elif self.data.close < self.ma:
            self.sell()

cerebro = bt.Cerebro()
cerebro.addstrategy(MyStrategy)

data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
cerebro.run()
cerebro.plot()
```

### 参数网格搜索
```python
import vectorbt as vbt

# 网格搜索最佳参数
param_grid = {
    'fast_period': [5, 10, 15, 20],
    'slow_period': [20, 30, 50, 100]
}

pf = vbt.Param(
    fast_period=param_grid['fast_period'],
    slow_period=param_grid['slow_period']
).run(
    vbt.nbfunc(lambda fast, slow: 
        (price.rolling(fast).mean() > price.rolling(slow).mean()).astype(int)
    )
)

# 找出最佳参数
best_idx = pf.total_return().idxmax()
print(f"Best params: {best_idx}")
print(f"Best return: {pf.total_return()[best_idx]:.2%}")
```

---

## 组合优化 (Portfolio Layer)

### PyPortfolioOpt
```python
from pypfolioopt import EfficientFrontier, risk_models, expected_returns

# 计算收益率矩阵
mu = expected_returns.mean_historical_return(df)
Sigma = risk_models.sample_cov(df)

# 组合优化
ef = EfficientFrontier(mu, Sigma)

# 最大夏普比率
weights = ef.max_sharpe()
clean_weights = ef.clean_weights()

print(clean_weights)

# 转换为dict
portfolio = {k: v for k, v in clean_weights.items() if v > 0.01}
```

### 优化目标
| 目标 | 方法 |
|------|------|
| 最大夏普 | `ef.max_sharpe()` |
| 最小波动 | `ef.min_volatility()` |
| 最大收益 | `ef.max_quadratic_utility()` |
| 目标收益 | `ef.efficient_return(target_return)` |
| 目标风险 | `ef.efficient_risk(target_volatility)` |

---

## 绩效分析 (Analytics Layer)

### quantstats
```python
import quantstats as qs

# 假设 returns 是日收益率序列
returns = df['close'].pct_change().dropna()

# 完整报告
qs.reports.full(returns)

# 关键指标
sharpe = qs.sharpe_ratio(returns)
sortino = qs.sortino_ratio(returns)
max_dd = qs.max_drawdown(returns)
cagr = qs.cagr(returns)

# 收益分析
qs.plots.snapshot(returns, title='Strategy Performance')

# 输出HTML报告
qs.reports.html(returns, output='report.html')
```

### 绩效指标
| 指标 | 计算方式 | 理想值 |
|------|----------|--------|
| Sharpe | (均值/标准差) × √252 | > 1.5 |
| Sortino | (均值/下行标准差) × √252 | > 1.5 |
| Calmar | CAGR / MaxDD | > 1 |
| Win Rate | 盈利交易/总交易 | > 50% |
| Profit Factor | 总盈利/总亏损 | > 1.5 |
| Max Drawdown | 最大回撤 | < 20% |
| CAGR | 年化复合增长率 | > 15% |

---

## 可视化 (Visualization Layer)

### plotly K线图
```python
import plotly.graph_objects as go

fig = go.Figure(data=[go.Candlestick(
    x=df['datetime'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close']
)])

fig.add_trace(go.Scatter(
    x=df['datetime'],
    y=df['ma20'],
    mode='lines',
    name='MA20'
))

fig.show()
```

### Dash Dashboard
```python
from dash import Dash, html, dcc
import plotly.express as px

app = Dash(__name__)

app.layout = html.Div([
    html.H1('量化策略 Dashboard'),
    dcc.Graph(id='equity-curve', figure=fig),
    dcc.Graph(id='drawdown', figure=dd_fig),
])

app.run_server(debug=True)
```

---

## 分布式回测 (Distributed Backtest)

### Ray + vectorbt
```python
import ray
import vectorbt as vbt
import pandas as pd

ray.init()

@ray.remote
def run_backtest(window):
    price = pd.Series(...)
    ma = price.rolling(window).mean()
    entries = price > ma
    exits = price < ma
    
    pf = vbt.Portfolio.from_signals(price, entries, exits)
    return pf.total_return()

windows = list(range(5, 200))

# 并行执行
results = ray.get([run_backtest.remote(w) for w in windows])

print(f"Best window: {windows[np.argmax(results)]}")
```

### 核心认知
```
vectorbt = 计算引擎
Ray = 分布式调度器
```

---

## 输出规范 (Output Specification)

### 标准成功响应
```json
{
  "status": "success",
  "module": "backtest",
  "data": {
    "total_return": 0.25,
    "sharpe_ratio": 1.85,
    "max_drawdown": -0.12,
    "win_rate": 0.55,
    "trades": 142
  },
  "meta": {
    "duration_ms": 1234,
    "engine": "vectorbt",
    "params": {...}
  }
}
```

### 标准错误响应
```json
{
  "status": "error",
  "code": "ERR_ALFE_001",
  "module": "data",
  "message": "连接服务器失败",
  "recovery": "retry_alternative_server"
}
```

### 错误码表
| 错误码 | 含义 | 模块 | 处理 |
|--------|------|------|------|
| `ERR_DATA_001` | 数据源连接失败 | data | retry 3x → 切换 |
| `ERR_DATA_002` | 股票代码无效 | data | 返回格式提示 |
| `ERR_DATA_003` | 数据验证失败 | data | 跳过+记录 |
| `ERR_FACTOR_001` | 指标计算异常 | factor | 返回NaN |
| `ERR_BACKTEST_001` | 回测引擎错误 | backtest | 重置+报告 |
| `ERR_PORTFOLIO_001` | 优化失败 | portfolio | 返回等权 |
| `ERR_RAY_001` | Ray集群连接失败 | distributed | 本地降级 |

---

## 工作流 (Workflow)

### Phase 1: 数据获取
**进入条件**: 请求市场数据
**步骤**:
1. 验证股票代码格式
2. 连接数据源 (alfe/yfinance/Qlib)
3. 获取OHLCV数据
4. 数据验证

**产出**: 清洗后的DataFrame

### Phase 2: 因子计算
**进入条件**: 数据可用
**步骤**:
1. 计算技术指标 (TA-Lib)
2. 生成特征
3. 异常值处理

**产出**: 包含指标的DataFrame

### Phase 3: 信号生成
**进入条件**: 因子完成
**分支**:
| 策略类型 | 工具 |
|----------|------|
| 规则策略 | 自定义条件 |
| AI策略 | ML模型预测 |

### Phase 4: 回测执行
**进入条件**: 信号可用
**分支**:
| 模式 | 工具 | 场景 |
|------|------|------|
| 快速验证 | vectorbt | 参数搜索 |
| 生产验证 | backtrader | 详细分析 |
| ML策略 | Qlib | AI策略 |

### Phase 5: 组合优化
**进入条件**: 多策略/多资产
**步骤**:
1. 计算协方差矩阵
2. 选择优化目标
3. 生成权重

### Phase 6: 绩效评估
**进入条件**: 回测完成
**步骤**:
1. 计算指标 (quantstats)
2. 生成报告
3. 可视化

### Phase 7: 部署展示
**进入条件**: 策略验证通过
**步骤**:
1. 构建Dashboard
2. 配置报警
3. 部署服务

---

## 决策矩阵 (Decision Matrix)

### 数据源选择
| 条件 | 操作 | 工具 |
|------|------|------|
| A股实时数据 | alfe.data | `QuantAnalyzer` |
| A股历史数据 | alfe.data | `get_security_bars` |
| 美股/港股数据 | yfinance | `yfinance.download` |
| 完整Pipeline | Qlib | `D.features` |

### 回测引擎选择
| 条件 | 操作 | 工具 |
|------|------|------|
| 快速验证/参数搜索 | vectorbt | `vbt.Portfolio.from_signals` |
| 详细交易逻辑 | backtrader | `Cerebro.run()` |
| ML驱动策略 | Qlib | `RLTrader` |
| 多进程参数扫描 | Ray | `@ray.remote` |

### 组合优化选择
| 条件 | 操作 | 工具 |
|------|------|------|
| 最大夏普 | `max_sharpe()` | PyPortfolioOpt |
| 最小波动 | `min_volatility()` | PyPortfolioOpt |
| 目标收益 | `efficient_return()` | PyPortfolioOpt |
| 风险预算 | `efficient_risk()` | PyPortfolioOpt |

### 信号生成选择
| 条件 | 操作 | 说明 |
|------|------|------|
| 规则策略 | TA-Lib + 自定义条件 | 确定性高 |
| AI策略 | ML模型预测 | 需训练数据 |
| 双系统 | 内置趋势+投机 | 已编译优化 |

---

## 循环控制 (Loop Control)

### 参数扫描
| 参数 | 值 | 说明 |
|------|-----|------|
| `max_combinations` | 10000 | 最大参数组合数 |
| `batch_size` | 100 | Ray批处理大小 |
| `timeout_per_run` | 60s | 单次回测超时 |
| `total_timeout` | 3600s | 整体任务超时 |

### 重试策略
| 场景 | 重试次数 | 退避策略 |
|------|----------|----------|
| 网络请求 | 3 | 1s → 2s → 4s |
| 数据获取 | 3 | 0.5s → 1s → 2s |
| 回测执行 | 1 | 不重试 |
| Ray任务 | 2 | 5s → 10s |

### 资源限制
| 资源 | 限制 | 说明 |
|------|------|------|
| CPU | 8核 | 本地并行上限 |
| GPU | 1块 | 训练使用 |
| 内存 | 16GB | 单次回测 |
| 磁盘 | 10GB | 缓存+报告 |

---

## AI执行提示 (AI Execution Hints)

```
优先使用 vectorbt 进行策略验证
需要交易逻辑时使用 backtrader
需要机器学习时使用 Qlib
所有结果必须通过 quantstats 评估
所有输出应支持 plotly 可视化
分布式回测使用 Ray + vectorbt
```

---

## 快速开始 (Quick Start)

### 最小可运行系统
```bash
pip install vectorbt[full] ta-lib quantstats plotly
```

### 完整系统
```bash
pip install vectorbt backtrader qlib ta-lib
pip install pyportfolioopt quantstats dash
pip install ray torch lightgbm
```

### 首次使用
```python
import alfe

# 获取数据
data = alfe.get_data('600519.SH', period='daily', count=60)

# 技术分析
from alfe import analyze_with_systems
result = analyze_with_systems(data, '600519.SH')

# 回测
from alfe import run_full_backtest
bt_result = run_full_backtest(data)

print(f"收益率: {bt_result['total_return']:.2%}")
```

---

## 质量检查清单 (Quality Checklist)

### 数据层面
- [ ] 股票代码格式验证
- [ ] OHLCV完整性检查
- [ ] 停牌日期处理
- [ ] 涨跌停限制

### 因子层面
- [ ] NaN值处理
- [ ] 极端值裁剪
- [ ] 前向看漏检查

### 回测层面
- [ ] 前向偏差检查
- [ ] 过拟合风险评估
- [ ] 交易成本计算
- [ ] 滑点模拟

### 系统层面
- [ ] 依赖版本兼容性
- [ ] 内存使用监控
- [ ] 执行时间预算

---

## 版本历史 (Changelog)

| 版本 | 日期 | 变更 |
|------|------|------|
| 2.0.0 | 2026-03-19 | 整合量化技术栈，添加AI/分布式能力 |
| 1.3.0 | 2026-03-18 | 双系统交易信号正式发布 |
| 1.0.0 | 2026-03-01 | 初始版本 |
