# Custom Indicators - System 1 & System 2
# 两个独立指标系统 - 输出格式与原始脚本一致

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


def system1_bollinger(close: pd.Series, period: int = 19, std_dev: float = 1.07) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """布林带"""
    mid = close.ewm(alpha=2/period, adjust=False).mean()
    std = close.rolling(window=period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    return mid, upper, lower


def system1_angles(mid: pd.Series, upper: pd.Series, lower: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """角度计算"""
    mid_angle = np.arctan((mid / mid.shift(1) - 1) * 100) * 180 / pi
    upper_angle = np.arctan((upper / upper.shift(1) - 1) * 100) * 180 / pi
    lower_angle = np.arctan((lower / lower.shift(1) - 1) * 100) * 180 / pi
    return mid_angle, upper_angle, lower_angle


def system1_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """MACD"""
    ema_fast = close.ewm(alpha=2/fast, adjust=False).mean()
    ema_slow = close.ewm(alpha=2/slow, adjust=False).mean()
    diff = ema_fast - ema_slow
    dea = diff.ewm(alpha=2/signal, adjust=False).mean()
    macd = 2 * (diff - dea)
    return diff, dea, macd


def system1_analyze(df: pd.DataFrame, total_assets: float = 1000000, win_rate: float = 0.6) -> Dict:
    """
    系统1分析 - 输出与daily_data_3_14_0.py一致
    """
    close = df['close']
    
    # 预测收盘价
    predicted_close = []
    for i in range(1, len(close)):
        pred, _ = predict_next_price(close.iloc[i-1], close.iloc[i])
        predicted_close.append(pred)
    predicted_close = [np.nan] + predicted_close
    
    # 布林带
    mid, upper, lower = system1_bollinger(close)
    
    # 角度
    mid_angle, upper_angle, lower_angle = system1_angles(mid, upper, lower)
    
    # MACD
    diff, dea, macd = system1_macd(close)
    
    # 量化趋势
    trend = pd.Series(index=close.index, dtype=str)
    trend.loc[close > upper] = "多头趋势"
    trend.loc[close < lower] = "空头趋势"
    trend.loc[(close <= upper) & (close >= lower)] = "交易范围"
    
    # 支撑/压力位
    support_level = pd.Series(index=close.index, dtype=float)
    pressure_level = pd.Series(index=close.index, dtype=float)
    
    support_level.loc[close > upper] = upper
    pressure_level.loc[close < lower] = lower
    
    in_range = (close <= upper) & (close >= lower)
    support_level.loc[in_range & (close < mid)] = lower
    support_level.loc[in_range & (close >= mid)] = mid
    pressure_level.loc[in_range & (close < mid)] = mid
    pressure_level.loc[in_range & (close >= mid)] = upper
    
    # 冗余位 (止损位)
    redundancy = pd.Series(index=close.index, dtype=float)
    o = df['open']
    redundancy.loc[close > upper] = upper + o * 0.02
    redundancy.loc[close < lower] = lower - o * 0.02
    redundancy.loc[(close <= upper) & (close >= lower)] = mid
    
    # Alpha因子
    alpha_space = macd.max() - macd.min()
    alphalens = close / alpha_space if alpha_space > 0 else np.nan
    fast = alphalens.rolling(1).mean()
    slow = alphalens.rolling(3).mean()
    d_value = fast - slow
    
    # Regime信号
    regime = pd.Series(index=close.index, dtype=int, data=0)
    regime.loc[(d_value > 0) & (macd < 0)] = 1   # 买入
    regime.loc[(d_value < 0) & (macd > 0)] = -1  # 卖出
    
    # Regime映射
    Regime = regime.replace({1: "买入", 0: "等待", -1: "卖出"})
    
    # Kelly仓位
    odds_list = [1.0382, 1.05, 1.0618, 1.10]
    if close.iloc[-1] > 0 and win_rate > 0:
        p, q = win_rate, 1 - win_rate
        kelly_positions = []
        for odds in odds_list:
            f_star = (odds * p - q) / odds
            if f_star > 0:
                pos = int((f_star * total_assets / close.iloc[-1]) // 100)
            else:
                pos = 0
            kelly_positions.append(pos)
    else:
        kelly_positions = [0, 0, 0, 0]
    
    # 最新数据
    latest = {
        # 基础数据
        'ts_code': df.get('ts_code', [None]*len(df)).iloc[0],
        'trade_date': str(df.index[-1])[:10] if hasattr(df.index, '__getitem__') else str(df.get('trade_date', [None]*len(df)).iloc[-1]),
        'Open': df['open'].iloc[-1],
        'High': df['high'].iloc[-1],
        'Low': df['low'].iloc[-1],
        'Close': close.iloc[-1],
        
        # 预测
        'Predicted_Close': predicted_close[-1],
        
        # EMA/MACD
        'EMA12': mid.iloc[-1],
        'EMA26': close.ewm(alpha=2/26, adjust=False).mean().iloc[-1],
        'DIFF': diff.iloc[-1],
        'DEA': dea.iloc[-1],
        'MACD': macd.iloc[-1],
        
        # 布林带
        'mid': mid.iloc[-1],
        'upper': upper.iloc[-1],
        'lower': lower.iloc[-1],
        
        # 角度
        'mid_angle': mid_angle.iloc[-1],
        'upper_angle': upper_angle.iloc[-1],
        'lower_angle': lower_angle.iloc[-1],
        
        # 趋势和信号
        'quantitative_trend': trend.iloc[-1],
        'support_level': support_level.iloc[-1],
        'pressure_level': pressure_level.iloc[-1],
        'redundancy': redundancy.iloc[-1],
        'Regime': Regime.iloc[-1],
        
        # 策略 (保持与原始一致)
        'Regimes': Regime.iloc[-1],
        
        # Kelly仓位
        'Kelly': str(kelly_positions),
    }
    
    return latest


# ==================== 系统2: new_analysis_script 逻辑 ====================

def system2_bollinger(close: pd.Series, period: int = 19) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """布林带 + MA平滑"""
    mid = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper_raw = mid + 1.07 * std
    lower_raw = mid - 1.07 * std
    upper = upper_raw.rolling(window=7).mean()
    lower = lower_raw.rolling(window=7).mean()
    mid = mid.rolling(window=7).mean()
    return mid, upper, lower


def system2_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """ATR计算"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def system2_analyze(df: pd.DataFrame) -> Dict:
    """
    系统2分析 - 输出与new_analysis_script.py一致
    """
    close = df['close']
    high = df['high']
    low = df['low']
    
    # 布林带
    mid, upper, lower = system2_bollinger(close)
    
    # ATR
    atr = system2_atr(high, low, close)
    
    # 预测收盘价
    predicted_close = []
    for i in range(1, len(close)):
        pred, _ = predict_next_price(close.iloc[i-1], close.iloc[i])
        predicted_close.append(pred)
    predicted_close = [np.nan] + predicted_close
    
    # 信号
    upper_angle = (upper / upper.shift(1) - 1) * 100
    lower_angle = (lower / lower.shift(1) - 1) * 100
    
    upper_pos = upper_angle[upper_angle > 0]
    lower_neg = lower_angle[lower_angle < 0]
    um_quantile = upper_pos.quantile(0.88) if len(upper_pos) > 0 else 30
    lm_quantile = lower_neg.quantile(0.12) if len(lower_neg) > 0 else -30
    
    buy_short = (close > upper) & (upper_angle < 0)
    buy_medium = (close < lower) & (lower_angle < lm_quantile)
    sell = (close > upper) & (upper_angle > um_quantile)
    
    strategy = pd.Series(index=close.index, dtype=str, data='等待')
    strategy.loc[buy_short] = '短买'
    strategy.loc[buy_medium] = '中买'
    strategy.loc[sell] = '卖出'
    
    latest = {
        # 基础数据
        'ts_code': df.get('ts_code', [None]*len(df)).iloc[0],
        'trade_date': str(df.index[-1])[:10] if hasattr(df.index, '__getitem__') else str(df.get('trade_date', [None]*len(df)).iloc[-1]),
        'Open': df['open'].iloc[-1],
        'High': df['high'].iloc[-1],
        'Low': df['low'].iloc[-1],
        'Close': close.iloc[-1],
        
        # 预测
        'Predicted_Close': predicted_close[-1],
        
        # 布林带
        'upper_band': upper.iloc[-1],
        'mid_band': mid.iloc[-1],
        'lower_band': lower.iloc[-1],
        
        # ATR
        'ATR': atr.iloc[-1],
        
        # 策略 (与原始一致)
        'Strategy': strategy.iloc[-1],
    }
    
    return latest


# ==================== 手续费计算 ====================

def calc_fee(price: float, shares: int = 100) -> float:
    """A股手续费: 万分之三，不足5元按5元"""
    fee = price * shares * 0.0003
    return max(fee, 5)


def calc_net_return(gross_return: float, price: float, shares: int = 100) -> float:
    """净收益"""
    fee = calc_fee(price, shares)
    total_fee = fee * 2
    gross_profit = price * shares * gross_return
    net_profit = gross_profit - total_fee
    return net_profit / (price * shares)


# ==================== 回测系统 ====================

def run_backtest_with_stops(df: pd.DataFrame, system: int = 1, 
                           profit_target: float = 0.02,
                           trailing_percent: float = 0.02,
                           shares: int = 100) -> Dict:
    """带止盈止损的回测"""
    close = df['close']
    high = df['high']
    low = df['low']
    
    # 预计算
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
        mid, upper, lower = system2_bollinger(close)
        atr = system2_atr(high, low, close)
        upper_angle = (upper / upper.shift(1) - 1) * 100
        lower_angle = (lower / lower.shift(1) - 1) * 100
        upper_pos = upper_angle[upper_angle > 0]
        lower_neg = lower_angle[lower_angle < 0]
        um_quantile = upper_pos.quantile(0.88) if len(upper_pos) > 0 else 30
        lm_quantile = lower_neg.quantile(0.12) if len(lower_neg) > 0 else -30
        buy_short = (close > upper) & (upper_angle < 0)
        buy_medium = (close < lower) & (lower_angle < lm_quantile)
        strategy = pd.Series(index=close.index, dtype=str, data='等待')
        strategy.loc[buy_short] = '短买'
        strategy.loc[buy_medium] = '中买'
    
    trades = []
    position = None
    
    for i in range(31, len(df)):
        if system == 1:
            signal_val = regime.iloc[i-1] if i > 0 else 0
        else:
            sig = strategy.iloc[i-1] if i > 0 else '等待'
            signal_val = 1 if sig in ['短买', '中买'] else (-1 if sig == '卖出' else 0)
        
        current_price = close.iloc[i]
        
        if position is None and signal_val == 1:
            position = {
                'entry_price': current_price,
                'shares': shares,
            }
            continue
        
        if position is None:
            continue
        
        # 次日2%止盈
        if i + 1 < len(close):
            next_return = (close.iloc[i+1] - position['entry_price']) / position['entry_price']
            next_net = calc_net_return(next_return, position['entry_price'], shares)
            if next_net >= profit_target:
                position['exit_price'] = close.iloc[i+1]
                position['return'] = next_net
                trades.append(position)
                position = None
                continue
        
        # 止损/止盈
        if system == 1:
            if current_price <= lower.iloc[i]:
                position['exit_price'] = current_price
                position['return'] = calc_net_return(
                    (current_price - position['entry_price']) / position['entry_price'],
                    position['entry_price'], shares
                )
                trades.append(position)
                position = None
        else:
            current_atr = atr.iloc[i]
            stop_price = position['entry_price'] - 2 * current_atr
            if current_price <= stop_price:
                position['exit_price'] = current_price
                position['return'] = calc_net_return(
                    (current_price - position['entry_price']) / position['entry_price'],
                    position['entry_price'], shares
                )
                trades.append(position)
                position = None
    
    if not trades:
        return {'trades': [], 'summary': {'total': 0, 'wins': 0, 'win_rate': 0, 'total_return': 0}}
    
    trades_df = pd.DataFrame(trades)
    wins = (trades_df['return'] > 0).sum()
    total_return = trades_df['return'].sum()
    avg_return = trades_df['return'].mean()
    returns = trades_df['return']
    sharpe = returns.mean() / returns.std() * np.sqrt(len(returns)) if len(returns) > 1 and returns.std() > 0 else 0
    
    return {
        'trades': trades,
        'summary': {
            'total': len(trades),
            'wins': int(wins),
            'win_rate': wins / len(trades) * 100,
            'total_return': total_return * 100,
            'avg_return': avg_return * 100,
            'sharpe': sharpe,
        }
    }


def analyze_with_systems(df: pd.DataFrame, ts_code: str = None, 
                         total_assets: float = 1000000, win_rate: float = 0.6) -> Dict:
    """完整分析"""
    if ts_code:
        df = df.copy()
        df['ts_code'] = ts_code
    
    return {
        'system1': system1_analyze(df, total_assets, win_rate),
        'system2': system2_analyze(df)
    }


def run_full_backtest(df: pd.DataFrame, profit_target: float = 0.02, 
                      trailing_percent: float = 0.02, shares: int = 100) -> Dict:
    """完整回测"""
    s1 = run_backtest_with_stops(df, system=1, profit_target=profit_target, 
                                 trailing_percent=trailing_percent, shares=shares)
    s2 = run_backtest_with_stops(df, system=2, profit_target=profit_target,
                                 trailing_percent=trailing_percent, shares=shares)
    
    return {'system1': s1, 'system2': s2}
