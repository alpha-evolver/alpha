---
name: alfe
description: Alpha 开发的 A股股票行情数据接口技能 + CFA定量分析。基于券商行情协议，支持获取实时行情、K线数据、公司信息、财务数据，以及完整的CFA定量分析功能。
---

# Alfe 技能

Alpha 开发的 A 股股票数据接口技能 + 定量分析工具。

## 功能列表

### 行情数据
1. **实时行情** - 获取股票实时涨跌幅、成交量等
2. **K线数据** - 日/周/月/分钟K线
3. **分时数据** - 当日分时走势
4. **历史分笔** - 历史逐笔成交

### 公司与财务
5. **公司信息** - 上市公司基本信息
6. **财务数据** - 财务指标查询
7. **除权除息** - 分红送股信息

### 定量分析 (CFA L1-L3)
8. **基础统计** - 均值、方差、标准差、偏度、峰度
9. **相关性分析** - 相关系数、协方差
10. **回归分析** - 线性回归、R²、t检验
11. **时间序列** - 移动平均、指数平滑
12. **财务比率** - PE, PB, ROE, ROA, 毛利率等
13. **风险分析** - VaR, CVaR, 夏普比率, Beta
14. **估值模型** - NPV, IRR, DCF估值

## 数据源

使用券商行情服务器协议，无需 Token，直接连接券商服务器获取数据。

## 使用方法

```python
from alfe import AlfeHq_API, QuantAnalyzer

# 行情数据
api = AlfeHq_API()
api.connect(ip='服务器IP', port=7709)
quotes = api.get_security_quotes([(0, '000001')])
api.disconnect()

# 定量分析
qa = QuantAnalyzer()
qa.connect(0)  # 连接服务器
finance = qa.get_finance_data(0, '000001')
ratios = qa.calc_financial_ratios(finance)
qa.disconnect()
```

## 服务器列表

内置多个券商服务器（详见 config/hosts.py）

## 注意事项

- 需要能访问券商服务器网络
- 遵守券商使用协议

## 版本

Alpha 开发
版本号: 1.1.0
