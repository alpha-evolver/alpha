---
name: alfe
description: >
  A股市场数据获取与量化分析技能。触发场景：
  - 用户查询A股股票数据（实时行情、K线、财务数据）
  - 执行量化分析（统计、风险指标、回测）
  - 双系统交易信号分析（趋势策略/投机策略）
  - 运行回测验证交易策略
  - 批量获取多只股票数据
tags: [finance, quantitative, stock, china, api]
permissions: [network]
metadata:
  version: "1.3.0"
  author: "Alpha"
---

# Alfe - A股量化分析系统

**Version 1.3.0 | Author: Alpha**

## 边界定义 (Boundary Definition)

### 激活边界
| 触发条件 | 行为 |
|----------|------|
| 询问股票数据/行情/价格 | 执行数据获取 |
| 量化分析/统计/回测 | 执行分析模块 |
| 双系统/交易信号/Bollinger | 执行指标系统 |
| K线/分钟线/日线 | 执行K线获取 |

### 数据边界
```
✅ 允许:
  - 网络: 券商行情服务器 (IP段 60-218.*, 123.*, 180.*)
  - 端口: 7709, 80
  - 数据: A股上市公司 (沪深主板、科创板、创业板)
  - 频率: 批量请求间隔 ≥ 0.5s

❌ 禁止:
  - 访问非声明的外部端点
  - 存储用户账户信息
  - 发送交易指令 (仅分析，不执行)
  - 获取港股/美股/加密货币数据
```

---

## 环境规范 (Environment Specification)

### 依赖清单
| 包名 | 版本 | 用途 |
|------|------|------|
| `numpy` | ≥1.20 | 数值计算 |
| `pandas` | ≥1.3 | 数据处理 |
| `scipy` | ≥1.7 | 统计分析 |
| `Cython` | ≥0.29 | 编译加速 |

### 服务器配置
```python
# 优先使用已验证服务器 (延迟 < 100ms)
hq_hosts = [
    ("杭州电信J1", "60.191.117.167", 7709),   # 高优先级
    ("杭州电信J2", "115.238.56.198", 7709),   # 高优先级
    ("上海电信Z1", "180.153.18.170", 7709),   # 高优先级
    # 备用端口80
    ("上海电信Z80", "180.153.18.172", 80),
]
```

### 服务器健康检查
```bash
# 连接测试 (端口7709)
nc -zv 60.191.117.167 7709 -w 3

# 响应时间阈值: < 100ms 为健康
# 连续失败3次: 切换备用服务器
```

---

## 输入规范 (Input Specification)

### 股票代码格式
| 市场 | 格式 | 示例 |
|------|------|------|
| 上海 | `XXXXXX.SH` 或 `SH:XXXXXX` | `600519.SH`, `SH:600519` |
| 深圳 | `XXXXXX.SZ` 或 `SZ:XXXXXX` | `000001.SZ`, `SZ:000001` |
| 创业板 | `XXXXXX.SZ` | `300750.SZ` |
| 科创板 | `XXXXXX.SH` | `688xxx.SH` |

### K线类型枚举
| 类型码 | 周期 | 最大数据点 |
|--------|------|-----------|
| `0` | 5分钟 | 800 |
| `1` | 15分钟 | 800 |
| `2` | 30分钟 | 800 |
| `3` | 1小时 | 800 |
| `4` | 日线 | 800 |
| `5` | 周线 | 800 |
| `6` | 月线 | 800 |
| `8` | 1分钟 | 800 |
| `9` | 日线(等效) | 800 |

### API参数规范
```python
# 获取K线
api.get_security_bars(
    period: int,      # K线类型 (0-11)
    market: int,       # 0=深圳, 1=上海
    code: str,         # 6位股票代码
    start: int,        # 起始索引
    count: int         # 获取数量 (max=800)
) -> pd.DataFrame

# 获取分时
api.get_transaction_list(
    market: int,
    code: str,
    start: int,
    count: int         # max=2000
) -> pd.DataFrame
```

---

## 输出规范 (Output Specification)

### 标准成功响应
```json
{
  "status": "success",
  "data": {
    "code": "600519.SH",
    "name": "贵州茅台",
    "timestamp": "2026-03-19T15:00:00",
    "fields": ["date", "open", "high", "low", "close", "volume", "turnover"]
  },
  "meta": {
    "count": 60,
    "server": "杭州电信J1",
    "latency_ms": 45
  }
}
```

### 标准错误响应
```json
{
  "status": "error",
  "code": "ERR_ALFE_001",
  "message": "连接服务器失败",
  "details": {
    "host": "60.191.117.167",
    "port": 7709,
    "reason": "Connection timeout"
  },
  "recovery": "retry_alternative_server"
}
```

### 错误码表
| 错误码 | 含义 | HTTP处理 |
|--------|------|----------|
| `ERR_ALFE_001` | 服务器连接失败 | retry 3x → 切换备用 |
| `ERR_ALFE_002` | 股票代码无效 | 返回格式提示 |
| `ERR_ALFE_003` | 数据请求超限 | 拆分请求 |
| `ERR_ALFE_004` | 网络超时 | retry 3x 指数退避 |
| `ERR_ALFE_005` | 服务器拒绝 | 等待10s重试 |
| `ERR_ALFE_006` | 数据解析失败 | 返回原始响应 |

---

## 工作流 (Workflow)

### Phase 1: 连接初始化 (Connection Init)
**进入条件**: 首次调用或连接断开  
**步骤**:
1. 读取 `config/hosts.py` → 服务器列表
2. 按优先级尝试连接 → 测试延迟
3. 选择延迟 < 100ms 的服务器
4. 建立Socket连接

**验证点**: `socket.connected == True`
**退出条件**: 连接成功或所有服务器失败

**备选策略**:
```python
# 依次尝试:
# 1. 高优先级服务器 (端口7709)
# 2. 备用服务器 (端口80)
# 3. 全部失败 → ERR_ALFE_001
```

### Phase 2: 数据获取 (Data Fetch)
**进入条件**: 连接已建立  
**步骤**:
1. 验证股票代码格式
2. 构建请求包 → `struct.pack`
3. 发送请求 → `socket.send`
4. 接收响应 → `socket.recv`
5. 解析数据 → `parser.parse`

**验证点**: 返回非空DataFrame
**退出条件**: 数据返回或超时

**限流控制**:
- 单次请求: 间隔 0.1s
- 批量请求: 间隔 0.5s
- 超限处理: 队列 + 延迟

### Phase 3: 数据验证 (Data Validation)
**进入条件**: 数据已获取  
**验证规则**:
| 字段 | 校验规则 |
|------|----------|
| `close` | > 0 且 < 10000 |
| `volume` | >= 0 |
| `date` | 格式 YYYY-MM-DD |
| `high` | >= `low` |
| `high` | >= `close` |

**验证点**: 所有规则通过
**失败处理**: 返回 `None` + 记录日志

### Phase 4: 量化分析 (Quantitative Analysis)
**进入条件**: 数据验证通过  
**分析流程**:
1. 计算日收益率 → `(close - prev_close) / prev_close`
2. 统计指标 → 均值、标准差、偏度、峰度
3. 风险指标 → VaR、CVaR、Sharpe、Beta
4. 生成报告 → 格式化输出

**产出**:
```python
{
    "returns": np.array,           # 日收益率序列
    "mean": float,                 # 日均收益
    "std": float,                 # 日波动率
    "sharpe": float,              # Sharpe比率
    "var_95": float,              # 95% VaR
    "max_drawdown": float,        # 最大回撤
}
```

### Phase 5: 双系统分析 (Dual-System Analysis)
**进入条件**: K线数据可用 (≥22条)  
**系统1: 趋势策略**
```
输入: df (OHLCV), code
处理:
  1. 计算 Bollinger Bands (20,2)
  2. 计算 MACD (12,26,9)
  3. 信号逻辑:
     - Buy: price > upper_band AND MACD > signal
     - Sell: price < middle_band
     - Hold: 其他
输出: {advice, signals, indicators}
```

**系统2: 投机策略**
```
输入: df (OHLCV), code
处理:
  1. 计算 Bollinger Bands (20,2)
  2. 计算 ATR (14)
  3. 信号逻辑:
     - Buy: price > upper_band AND volume > avg_volume
     - Stop-loss: price < entry - 2*ATR
     - Take-profit: price > entry + 3*ATR
输出: {advice, signals, atr_value, sl, tp}
```

**验证点**: 输出包含 `advice` 字段
**退出条件**: 策略完成

### Phase 6: 回测执行 (Backtest Execution)
**进入条件**: 策略信号可用  
**参数规范**:
```python
run_full_backtest(
    df,                    # DataFrame (必需)
    profit_target: float,  # 止盈比例 (默认0.02=2%)
    trailing_percent: float, # 追踪止损 (默认0.02=2%)
    shares: int,          # 交易股数 (默认100)
    commission: float     # 手续费 (默认0.0003=0.03%)
)
```

**佣金规则**:
- 买卖双向: 0.03%
- 最低消费: ¥5/笔
- 印花税: 0.1% (卖出时)

**产出指标**:
| 指标 | 字段名 | 计算方式 |
|------|--------|----------|
| 总交易次数 | `total_trades` | 计数 |
| 胜率 | `win_rate` | 盈利交易/总交易 |
| 总收益率 | `total_return` | (期末-期初)/期初 |
| 夏普比率 | `sharpe_ratio` | 均值/标准差×√252 |
| 最大回撤 | `max_drawdown` | 最大跌幅 |
| 盈亏比 | `profit_loss_ratio` | 均盈利/均亏损 |

---

## 决策矩阵 (Decision Matrix)

### 服务器选择
| 条件 | 操作 | 备选 |
|------|------|------|
| 延迟 < 50ms | 使用当前服务器 | - |
| 延迟 50-100ms | 记录警告，使用 | 监控 |
| 延迟 > 100ms | 尝试下一服务器 | 标记为低优先级 |
| 全部 > 200ms | 使用最低延迟 | 记录告警 |

### 数据获取策略
| 条件 | 操作 | 说明 |
|------|------|------|
| 单只股票 | 直接请求 | 单次调用 |
| 批量 < 10只 | 循环请求 | 间隔0.5s |
| 批量 ≥ 10只 | 异步队列 | 间隔1s，最大并发3 |
| 数据量 > 800 | 分页请求 | start参数分页 |

### K线数据选择
| 分析目的 | 推荐周期 | 数据量 |
|----------|----------|--------|
| 短期信号 | 1分钟/5分钟 | 60-100 |
| 日内交易 | 15分钟/30分钟 | 80 |
| 波段交易 | 日线 | 60-120 |
| 趋势分析 | 周线/月线 | 52/24 |

---

## 循环控制 (Loop Control)

| 参数 | 值 | 说明 |
|------|-----|------|
| `max_retries` | 3 | 单服务器重试次数 |
| `retry_delay_ms` | 1000 | 重试间隔基数 |
| `backoff_multiplier` | 2 | 退避倍数 |
| `max_backoff_ms` | 8000 | 最大退避时间 |
| `connection_timeout_ms` | 5000 | 连接超时 |
| `read_timeout_ms` | 3000 | 读取超时 |

**终止条件**:
1. 数据获取成功
2. 达到 `max_retries`
3. 手动取消 (Ctrl+C)
4. 超时 `connection_timeout_ms`

---

## 示例 (Examples)

### 基础数据获取
```python
from alfe import QuantAnalyzer

qa = QuantAnalyzer()
qa.connect_auto()

# 获取日K线
bars = qa.api.get_security_bars(
    period=9,      # 日线
    market=1,      # 上海
    code='600519', # 贵州茅台
    start=0,
    count=60
)
print(bars.tail())

qa.disconnect()
```

### 双系统分析
```python
from alfe import analyze_with_systems

# df: DataFrame with OHLCV columns
result = analyze_with_systems(df, '600519.SH')

print("趋势策略:", result['system1']['advice'])
print("投机策略:", result['system2']['advice'])
print("ATR:", result['system2']['atr_value'])
```

### 完整回测
```python
from alfe import run_full_backtest

result = run_full_backtest(
    df,
    profit_target=0.02,      # 2%止盈
    trailing_percent=0.02,   # 2%追踪止损
    shares=100
)

print(f"总交易: {result['total_trades']}")
print(f"胜率: {result['win_rate']}")
print(f"总收益: {result['total_return']}%")
```

### 批量分析
```python
from alfe import batch_analyze

stocks = ['600519.SH', '000001.SZ', '300750.SZ']
results = batch_analyze(stocks, periods=[4, 5])

for code, data in results.items():
    print(f"{code}: Sharpe={data['sharpe']:.2f}")
```

---

## 标准报告格式 (Report Format)

```
============================================================
A-Share Market Quantitative Analysis Report
============================================================
股票代码: 600519.SH (贵州茅台)
数据周期: 最近60个交易日
分析窗口: 最近22个交易日
============================================================

一、价格走势
----------------------------------------
收盘价: 1850.00 → 1920.00
期间涨幅: +3.78%

二、风险收益指标
----------------------------------------
日均收益率:  0.18%
日收益标准差: 1.52%
年化波动率:  24.14%
夏普比率:    0.75

三、风险指标
----------------------------------------
95% VaR:    -2.65%
CVaR:       -3.82%
最大回撤:   -8.45%
Beta:       0.85

四、交易信号
----------------------------------------
系统1 (趋势): Buy
系统2 (投机): Hold
  - ATR: 42.50
  - 止损位: 1805.00
  - 止盈位: 1977.50

五、回测结果
----------------------------------------
总交易次数: 488
胜率:       51.8%
总收益率:   519.95%
夏普比率:    1.42
最大回撤:   -12.3%
============================================================
```

---

## 质量检查清单 (Quality Checklist)

### 数据层面
- [ ] 股票代码格式验证
- [ ] K线数据完整性检查
- [ ] 复权处理 (前复权/后复权)
- [ ] 停牌日期处理
- [ ] 涨跌停限制

### 分析层面
- [ ] 收益率计算正确性
- [ ] 年化指标标准化
- [ ] VaR/CVaR计算方法
- [ ] 回测佣金精确

### 系统层面
- [ ] 服务器连接健康检查
- [ ] 失败重试机制
- [ ] 批量限流控制
- [ ] 超时处理

---

## 版本历史 (Changelog)

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.3.0 | 2026-03-18 | 双系统交易信号正式发布 |
| 1.2.0 | 2026-03-15 | 量化分析增强，VaR/CVaR |
| 1.1.0 | 2026-03-10 | 回测引擎完善 |
| 1.0.0 | 2026-03-01 | 初始版本 |
