# Custom Indicators - System 1 & System 2
# 两个独立指标系统 - 简洁中文输出

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
from math import pi


# ==================== 系统1: daily_data_3_14_0 逻辑 ====================

def predict_next_price(previous_price: float, current_price: float) -> Tuple[float, float]:
    """预测下一日收盘价"""
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
    """系统1分析 - 简洁中文输出"""
    close = df['close']
    open_price = df['open']
    
    # 预测收盘价
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
    
    # 支撑/压力位
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
    
    # Regime信号
    alpha_space = macd.max() - macd.min()
    alphalens = close / alpha_space if alpha_space > 0 else np.nan
    fast = alphalens.rolling(1).mean()
    slow = alphalens.rolling(3).mean()
    d_value = fast - slow
    
    regime = pd.Series(index=close.index, dtype=int, data=0)
    regime.loc[(d_value > 0) & (macd < 0)] = 1
    regime.loc[(d_value < 0) & (macd > 0)] = -1
    
    strategy = regime.replace({1: "买入", 0: "等待", -1: "卖出"})
    
    # 简洁输出
    latest = {
        '收盘价': close.iloc[-1],
        '收期价': predicted[-1],
        '支撑位': support.iloc[-1],
        '压力位': pressure.iloc[-1],
        '冗余位': redundancy.iloc[-1],
        '量化趋势': trend.iloc[-1],
        '策略': strategy.iloc[-1],
    }
    
    return latest


# ==================== 系统2: new_analysis_script 逻辑 ====================

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
    """系统2分析 - 简洁中文输出"""
    close = df['close']
    
    # 布林带
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
    
    # 简洁输出
    latest = {
        '收盘价': close.iloc[-1],
        '收期价': predicted[-1],
        '支撑位': lower.iloc[-1],
        '压力位': upper.iloc[-1],
        '冗余位': np.nan,
        '量化趋势': '交易范围',
        '策略': strategy.iloc[-1],
    }
    
    return latest


# ==================== 手续费计算 ====================

def calc_fee(price: float, shares: int = 100) -> float:
    fee = price * shares * 0.0003
    return max(fee, 5)


def calc_net_return(gross_return: float, price: float, shares: int = 100) -> float:
    fee = calc_fee(price, shares) * 2
    gross_profit = price * shares * gross_return
    return (gross_profit - fee) / (price * shares)


# ==================== 回测 ====================

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
        return {'交易次数': 0, '胜率': 0, '总收益': 0}
    
    wins = sum(1 for t in trades if t.get('ret', 0) > 0)
    total = sum(t.get('ret', 0) for t in trades)
    
    return {
        '交易次数': len(trades),
        '胜率': f"{wins}/{len(trades)} = {wins/len(trades)*100:.1f}%",
        '总收益': f"{total*100:.2f}%"
    }


def analyze_with_systems(df: pd.DataFrame, ts_code: str = None) -> Dict:
    """分析两个系统"""
    return {
        '系统1': system1_analyze(df),
        '系统2': system2_analyze(df)
    }


def run_full_backtest(df: pd.DataFrame, profit_target: float = 0.02, shares: int = 100) -> Dict:
    return {
        '系统1': run_backtest(df, system=1, profit_target=profit_target, shares=shares),
        '系统2': run_backtest(df, system=2, profit_target=profit_target, shares=shares)
    }
