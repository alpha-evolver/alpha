# Alfe - A-Share Stock Market Data & Quantitative Analysis Skill

**Developed by Alpha**  
Alfe is a powerful, locally-run Python skill that provides **A-share (China) stock market data access**, combined with **CFA-level quantitative analysis tools** and a **dual-system trading indicator framework** (Trend + Speculative).  

It supports real-time quotes, K-line data, company fundamentals, financial metrics, and full backtesting with profit/loss controls.

Version: **1.3.0**

## Features Overview

### Market Data
1. **Real-time Quotes** — Current price, change %, volume, turnover, etc.
2. **K-Line Data** — Daily, weekly, monthly, minute-level bars
3. **Intraday Tick Data** — Today's minute-by-minute chart
4. **Historical Tick-by-Tick** — Full trade-by-trade history

### Company & Fundamentals
5. **Company Profile** — Basic information of listed companies
6. **Financial Statements** — Key financial metrics
7. **Dividend & Split History** — Ex-dividend, bonus shares, rights issues

### Quantitative Analysis (CFA L1–L3 Level)
8. **Basic Statistics** — Mean, variance, std dev, skewness, kurtosis
9. **Correlation & Covariance** — Pairwise stock relationships
10. **Regression Analysis** — Linear regression, R², t-tests
11. **Time Series** — Moving averages, exponential smoothing
12. **Financial Ratios** — PE, PB, ROE, ROA, gross margin, etc.
13. **Risk Metrics** — VaR, CVaR, Sharpe ratio, Beta
14. **Valuation Models** — NPV, IRR, DCF
15. **Monte Carlo Simulation** — Price path simulation, option pricing
16. **Black-Scholes Option Pricing**

### Dual-System Trading Indicators (v1.3+)
Both systems are compiled into `.so` binaries for source protection.

#### System 1: Trend Strategy
- Bollinger Bands + MACD for trend detection
- Next-day 2% take-profit + trailing profit protection
- Stop-loss when price breaks below upper Bollinger Band

#### System 2: Speculative (Momentum/Reversal) Strategy
- Bollinger Bands + ATR for entry signals
- Next-day 2% take-profit + trailing stop
- Stop-loss at 2× ATR / Take-profit at 3× ATR

### Backtesting Engine
- Full simulation with take-profit / stop-loss / trailing rules
- Realistic A-share commission: 0.03% per side (minimum ¥5)
- Performance metrics: Sharpe ratio, max drawdown, win rate, profit/loss ratio, etc.

## Installation

### Recommended: Automatic Installation
```bash
cd alfe/
python3 build_auto.py
```
The script automatically:
1. Detects your platform (Linux / WSL / macOS)
2. Installs dependencies (Cython, GCC, etc.)
3. Compiles the protected `.so` binary
4. Runs functionality tests
5. Deletes source files to protect intellectual property

### Manual Installation
```bash
# Install core dependencies
pip install numpy pandas scipy

# Clone the repository
git clone https://github.com/alpha-evolver/alpha.git
cd alpha/alfe
# Then run the build script or manually compile if customized
```

## Quick Start Examples

### Dual-System Analysis
```python
from alfe import analyze_with_systems
import pandas as pd

# Assume df is a DataFrame with OHLCV data for the stock
result = analyze_with_systems(df, '600519.SH')

print(result['system1']['advice'])   # e.g. "Buy", "Sell", "Hold"
print(result['system2']['advice'])   # e.g. "Short-term Buy", "Sell", "Wait"
```

### Full Backtest with Stops
```python
from alfe import run_full_backtest

result = run_full_backtest(
    df,
    profit_target=0.02,         # Initial take-profit: +2% next day
    trailing_percent=0.02,      # Trail stops after 2% drawdown from high
    shares=100
)

print(result['system1']['summary'])
# Example output:
# {'total_trades': 488, 'win_rate': 51.8%, 'total_return': 519.95%, ...}
```

### Quantitative Analysis
```python
from alfe import QuantAnalyzer

qa = QuantAnalyzer()
qa.connect_auto()  # Auto-select available broker server

# Example: fetch 60 daily bars
bars = qa.api.get_security_bars(period=9, market=0, code='600519', start=0, count=60)

# ... perform analysis ...

qa.disconnect()
```

## Standard Analysis Report Format

```
============================================================
A-Share Market Quantitative Analysis Report
Data Period: Last 60 trading days → Analysis on most recent 22 days
============================================================
```

### Single Stock Report (Table Example)

| Metric                  | Description                              |
|-------------------------|------------------------------------------|
| Closing Price           | Start → End                              |
| Period Return           | (End - Start)/Start × 100%               |
| Daily Mean Return       | Mean daily return × 100%                 |
| Daily Return Std Dev    | Standard deviation of daily returns × 100% |
| Annualized Volatility   | Daily std × √252                         |
| Sharpe Ratio            | (Daily mean / Daily std) × √252          |
| 95% VaR                 | 5% quantile of returns × 100%            |
| Period Amplitude        | (High - Low)/Low × 100%                  |

### Multi-Stock Comparison
- Correlation matrix
- Sharpe ratio ranking (highest to lowest)
- Volatility ranking (lowest to highest risk)
- Overall evaluation: Best risk-adjusted return, lowest volatility picks

## Data Pulling Rules
- Historical window: Last **60 trading days**
- Analysis window: Most recent **22 trading days**

## Data Source
Connects directly to Chinese brokerage market servers (no token/API key required).  
Multiple built-in servers (see `config/hosts.py`).

## Important Notes
- Requires network access to Chinese brokerage quote servers
- Must comply with the terms of service of the connected broker
- Core indicator logic is compiled into binary (.so) for protection
- To modify logic: edit `.py.bak` backup files and recompile

Developed by **Alpha**  
Version **1.3.0**
