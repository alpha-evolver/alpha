# Custom Indicators - System 1 & System 2 + Quant
# 两个独立指标系统 + CFA定量分析

import numpy as np
import pandas as pd
from typing import Tuple, Dict
from math import pi


# ==================== Quant CFA 分析 ====================

def calc_returns(prices: pd.Series) -> pd.Series:
    """计算收益率"""
    return prices.pct_change().dropna()


def calc_sharpe(returns: pd.Series, risk_free: float = 0.03) -> float:
    """夏普比率"""
    rp = returns.mean() * 252
    sigma = returns.std() * np.sqrt(252)
    return (rp - risk_free) / sigma if sigma > 0 else 0


def calc_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """VaR - 风险价值"""
    return returns.quantile(1 - confidence)


def calc_max_drawdown(returns: pd.Series) -> float:
    """最大回撤"""
    cum = (1 + returns).cumprod()
    cummax = cum.cummax()
    drawdown = cum / cummax - 1
    return drawdown.min()


def calc_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    """Beta系数"""
    if len(stock_returns) < 2 or len(market_returns) < 2:
        return 1.0
    cov = np.cov(stock_returns, market_returns)[0, 1]
    var = np.var(market_returns)
    return cov / var if var > 0 else 1.0


def calc_volatility(returns: pd.Series) -> float:
    """年化波动率"""
    return returns.std() * np.sqrt(252)


def quant_analyze(df: pd.DataFrame) -> Dict:
    """CFA定量分析"""
    close = df['close']
    returns = calc_returns(close)
    
    if len(returns) < 10:
        return {
            '期间涨跌幅': 0,
            '日均收益率': 0,
            '日收益率标准差': 0,
            '年化波动率': 0,
            '夏普比率': 0,
            '95%VaR': 0,
            '最大回撤': 0,
            'Beta': 1.0,
        }
    
    # 计算涨跌幅
    start_price = close.iloc[0]
    end_price = close.iloc[-1]
    total_return = (end_price - start_price) / start_price * 100
    
    # 简化Beta (假设市场收益为0)
    beta = 1.0
    
    result = {
        '期间涨跌幅': f"{total_return:.2f}%",
        '日均收益率': f"{returns.mean()*100:.4f}%",
        '日收益率标准差': f"{returns.std()*100:.4f}%",
        '年化波动率': f"{calc_volatility(returns)*100:.2f}%",
        '夏普比率': f"{calc_sharpe(returns):.2f}",
        '95%VaR': f"{calc_var(returns)*100:.2f}%",
        '最大回撤': f"{calc_max_drawdown(returns)*100:.2f}%",
        'Beta': f"{beta:.2f}",
    }
    
    return result


# ==================== 系统1 ====================

def predict_next_price(previous_price: float, current_price: float) -> Tuple[float, float]:
    if not isinstance(previous_price, (int, float)) or not isinstance(current_price, (int, float)):
        return np.nan, np.nan
    if pd.isna(previous_price) or pd.isna(current_price) or previous_price == 0:
        return np.nan, np.nan
    try:
        growth_rate = (current_price - previous_price) / previous_price
        next_price = current_price * (1 + growth_rate)
        return round(next_price, 2), round(growth_rate, 5)
    except:
        return np.nan, np.nan


def system1_bollinger(close: pd.Series, period: int = 19, std_dev: float = 1.07):
    mid = close.ewm(alpha=2/period, adjust=False).mean()
    std = close.rolling(window=period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    return mid, upper, lower


def system1_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = close.ewm(alpha=2/fast, adjust=False).mean()
    ema_slow = close.ewm(alpha=2/slow, adjust=False).mean()
    diff = ema_fast - ema_slow
    dea = diff.ewm(alpha=2/signal, adjust=False).mean()
    macd = 2 * (diff - dea)
    return diff, dea, macd


def system1_analyze(df: pd.DataFrame) -> Dict:
    close = df['close']
    open_price = df['open']
    
    # 预测
    predicted = []
    for i in range(1, len(close)):
        pred, _ = predict_next_price(close.iloc[i-1], close.iloc[i])
        predicted.append(pred)
    predicted = [np.nan] + predicted
    
    # 布林带
    mid, upper, lower = system1_bollinger(close)
    
    # MACD
    diff, dea, macd = system1_macd(close)
    
    # 趋势
    trend = pd.Series(index=close.index, dtype=str)
    trend.loc[close > upper] = "多头趋势"
    trend.loc[close < lower] = "空头趋势"
    trend.loc[(close <= upper) & (close >= lower)] = "交易范围"
    
    # 支撑/压力
    support = pd.Series(index=close.index, dtype=float)
    pressure = pd.Series(index=close.index, dtype=float)
    support.loc[close > upper] = upper
    pressure.loc[close < lower] = lower
    in_range = (close <= upper) & (close >= lower)
    support.loc[in_range & (close < mid)] = lower
    support.loc[in_range & (close >= mid)] = mid
    pressure.loc[in_range & (close < mid)] = mid
    pressure.loc[in_range & (close >= mid)] = upper
    
    # 冗余位
    redundancy = pd.Series(index=close.index, dtype=float)
    redundancy.loc[close > upper] = upper + open_price * 0.02
    redundancy.loc[close < lower] = lower - open_price * 0.02
    redundancy.loc[(close <= upper) & (close >= lower)] = mid
    
    # Regime
    alpha_space = macd.max() - macd.min()
    alphalens = close / alpha_space if alpha_space > 0 else np.nan
    fast = alphalens.rolling(1).mean()
    slow = alphalens.rolling(3).mean()
    d_value = fast - slow
    
    regime = pd.Series(index=close.index, dtype=int, data=0)
    regime.loc[(d_value > 0) & (macd < 0)] = 1
    regime.loc[(d_value < 0) & (macd > 0)] = -1
    
    strategy = regime.replace({1: "买入", 0: "等待", -1: "卖出"})
    
    return {
        '收盘价': close.iloc[-1],
        '收期价': predicted[-1],
        '支撑位': round(support.iloc[-1], 2) if pd.notna(support.iloc[-1]) else None,
        '压力位': round(pressure.iloc[-1], 2) if pd.notna(pressure.iloc[-1]) else None,
        '冗余位': round(redundancy.iloc[-1], 2) if pd.notna(redundancy.iloc[-1]) else None,
        '量化趋势': trend.iloc[-1],
        '策略': strategy.iloc[-1],
    }


# ==================== 系统2 ====================

def system2_bollinger(close: pd.Series, period: int = 19):
    mid = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper_raw = mid + 1.07 * std
    lower_raw = mid - 1.07 * std
    upper = upper_raw.rolling(window=7).mean()
    lower = lower_raw.rolling(window=7).mean()
    return upper, lower


def system2_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def system2_analyze(df: pd.DataFrame) -> Dict:
    close = df['close']
    
    upper, lower = system2_bollinger(close)
    
    # 预测
    predicted = []
    for i in range(1, len(close)):
        pred, _ = predict_next_price(close.iloc[i-1], close.iloc[i])
        predicted.append(pred)
    predicted = [np.nan] + predicted
    
    # 信号
    upper_angle = (upper / upper.shift(1) - 1) * 100
    lower_angle = (lower / lower.shift(1) - 1) * 100
    
    upper_pos = upper_angle[upper_angle > 0]
    lower_neg = lower_angle[lower_angle < 0]
    um_q = upper_pos.quantile(0.88) if len(upper_pos) > 0 else 30
    lm_q = lower_neg.quantile(0.12) if len(lower_neg) > 0 else -30
    
    buy_short = (close > upper) & (upper_angle < 0)
    buy_medium = (close < lower) & (lower_angle < lm_q)
    sell = (close > upper) & (upper_angle > um_q)
    
    strategy = pd.Series(index=close.index, dtype=str, data='等待')
    strategy.loc[buy_short] = '短买'
    strategy.loc[buy_medium] = '中买'
    strategy.loc[sell] = '卖出'
    
    return {
        '收盘价': close.iloc[-1],
        '收期价': predicted[-1],
        '支撑位': round(lower.iloc[-1], 2),
        '压力位': round(upper.iloc[-1], 2),
        '冗余位': None,
        '量化趋势': '交易范围',
        '策略': strategy.iloc[-1],
    }


# ==================== 回测 ====================

def calc_fee(price: float, shares: int = 100) -> float:
    fee = price * shares * 0.0003
    return max(fee, 5)


def calc_net_return(gross_return: float, price: float, shares: int = 100) -> float:
    fee = calc_fee(price, shares) * 2
    return (price * shares * gross_return - fee) / (price * shares)


def run_backtest(df: pd.DataFrame, system: int = 1, profit_target: float = 0.02, shares: int = 100) -> Dict:
    close = df['close']
    high = df['high']
    low = df['low']
    
    if system == 1:
        mid, upper, lower = system1_bollinger(close)
        diff, dea, macd = system1_macd(close)
        alpha_space = macd.max() - macd.min()
        alphalens = close / alpha_space if alpha_space > 0 else np.nan
        fast = alphalens.rolling(1).mean()
        slow = alphalens.rolling(3).mean()
        d_value = fast - slow
        regime = pd.Series(index=close.index, dtype=int, data=0)
        regime.loc[(d_value > 0) & (macd < 0)] = 1
        regime.loc[(d_value < 0) & (macd > 0)] = -1
    else:
        upper, lower = system2_bollinger(close)
        atr = system2_atr(high, low, close)
    
    trades = []
    position = None
    
    for i in range(31, len(df)):
        signal = regime.iloc[i-1] if system == 1 else 0
        current = close.iloc[i]
        
        if position is None and signal == 1:
            position = {'price': current, 'shares': shares}
            continue
        
        if position is None:
            continue
        
        # 次日止盈
        if i + 1 < len(close):
            ret = (close.iloc[i+1] - position['price']) / position['price']
            if calc_net_return(ret, position['price'], shares) >= profit_target:
                position['ret'] = calc_net_return(ret, position['price'], shares)
                trades.append(position)
                position = None
                continue
        
        # 止损
        if system == 1:
            if current <= lower.iloc[i]:
                position['ret'] = calc_net_return((current - position['price']) / position['price'], position['price'], shares)
                trades.append(position)
                position = None
        else:
            if current <= position['price'] - 2 * atr.iloc[i]:
                position['ret'] = calc_net_return((current - position['price']) / position['price'], position['price'], shares)
                trades.append(position)
                position = None
    
    if not trades:
        return {'交易次数': 0, '胜率': '0%', '总收益': '0%'}
    
    wins = sum(1 for t in trades if t.get('ret', 0) > 0)
    total = sum(t.get('ret', 0) for t in trades)
    
    return {
        '交易次数': len(trades),
        '胜率': f"{wins}/{len(trades)} ({wins/len(trades)*100:.1f}%)",
        '总收益': f"{total*100:.2f}%"
    }


def analyze_with_systems(df: pd.DataFrame, ts_code: str = None) -> Dict:
    """完整分析 + Quant"""
    quant = quant_analyze(df)
    
    return {
        '量化分析': quant,
        '系统1': system1_analyze(df),
        '系统2': system2_analyze(df)
    }


def run_full_backtest(df: pd.DataFrame, profit_target: float = 0.02, shares: int = 100) -> Dict:
    return {
        '系统1': run_backtest(df, system=1, profit_target=profit_target, shares=shares),
        '系统2': run_backtest(df, system=2, profit_target=profit_target, shares=shares)
    }
