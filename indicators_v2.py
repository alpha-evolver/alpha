# Custom Indicators - System 1 & System 2 with Stop Loss/Profit
# 两个独立指标系统 + 止盈止损

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
from math import pi


# ==================== 手续费计算 ====================

def calc_fee(price: float, shares: int = 100) -> float:
    """
    A股手续费计算
    
    规则: 万分之三，不足5元按5元计算
    双向收费(买入+卖出)
    """
    fee = price * shares * 0.0003
    return max(fee, 5)


def calc_net_return(gross_return: float, price: float, shares: int = 100) -> float:
    """
    计算扣除手续费后的净收益
    
    Args:
        gross_return: 毛收益率 (如 0.02 = 2%)
        price: 买入价格
        shares: 股数
    
    Returns:
        float: 净收益率
    """
    fee = calc_fee(price, shares)
    # 买入+卖出 = 2倍手续费
    total_fee = fee * 2
    
    # 收益金额
    gross_profit = price * shares * gross_return
    
    # 净收益
    net_profit = gross_profit - total_fee
    
    # 净收益率
    net_return = net_profit / (price * shares)
    
    return net_return


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
    """系统1布林带 (基于EMA)"""
    mid = close.ewm(alpha=2/period, adjust=False).mean()
    std = close.rolling(window=period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    return mid, upper, lower


def system1_angles(mid: pd.Series, upper: pd.Series, lower: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """系统1角度计算"""
    mid_angle = np.arctan((mid / mid.shift(1) - 1) * 100) * 180 / pi
    upper_angle = np.arctan((upper / upper.shift(1) - 1) * 100) * 180 / pi
    lower_angle = np.arctan((lower / lower.shift(1) - 1) * 100) * 180 / pi
    return mid_angle, upper_angle, lower_angle


def system1_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """系统1 MACD"""
    ema_fast = close.ewm(alpha=2/fast, adjust=False).mean()
    ema_slow = close.ewm(alpha=2/slow, adjust=False).mean()
    diff = ema_fast - ema_slow
    dea = diff.ewm(alpha=2/signal, adjust=False).mean()
    macd = 2 * (diff - dea)
    return diff, dea, macd


def system1_trend(close: pd.Series, upper: pd.Series, lower: pd.Series) -> pd.Series:
    """系统1量化趋势"""
    trend = pd.Series(index=close.index, dtype=str)
    trend.loc[close > upper] = "多头趋势"
    trend.loc[close < lower] = "空头趋势"
    trend.loc[(close <= upper) & (close >= lower)] = "交易范围"
    return trend


def system1_regime(d_value: pd.Series, macd: pd.Series, threshold: float = 0) -> pd.Series:
    """系统1 Regime信号"""
    regime = pd.Series(index=d_value.index, dtype=int, data=0)
    regime.loc[(d_value > threshold) & (macd < threshold)] = 1   # 买入
    regime.loc[(d_value < -threshold) & (macd > threshold)] = -1  # 卖出
    return regime


def system1_kelly(total_assets: float, odds: float, price: float, win_rate: float) -> int:
    """系统1 Kelly仓位"""
    if not 0 < win_rate < 1 or odds <= 1 or total_assets <= 0 or price <= 0:
        return 0
    p, q = win_rate, 1 - win_rate
    f_star = (odds * p - q) / odds
    if f_star <= 0:
        return 0
    return int((f_star * total_assets / price) // 100)


def system1_analyze(df: pd.DataFrame, total_assets: float = 1000000, win_rate: float = 0.6) -> Dict:
    """系统1分析"""
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
    
    # 趋势
    trend = system1_trend(close, upper, lower)
    
    # Alpha因子
    alpha_space = macd.max() - macd.min()
    alphalens = close / alpha_space if alpha_space != 0 else np.nan
    fast = alphalens.rolling(1).mean()
    slow = alphalens.rolling(3).mean()
    d_value = fast - slow
    
    # Regime信号
    regime = system1_regime(d_value, macd)
    
    # Kelly仓位
    kelly_odds = [1.0382, 1.05, 1.0618, 1.10]
    kelly_positions = [system1_kelly(total_assets, odds, close.iloc[-1], win_rate) for odds in kelly_odds]
    
    latest = {
        'ts_code': df.get('ts_code', [None]*len(df)).iloc[0],
        'date': str(df.index[-1])[:10] if hasattr(df.index, '__getitem__') else str(df['trade_date'].iloc[-1]),
        'close': close.iloc[-1],
        'predicted_close': predicted_close[-1],
        'trend': trend.iloc[-1],
        'regime': '买入' if regime.iloc[-1] == 1 else ('卖出' if regime.iloc[-1] == -1 else '等待'),
        'bb_upper': upper.iloc[-1],
        'bb_lower': lower.iloc[-1],
        'macd': macd.iloc[-1],
        'kelly': kelly_positions,
        'advice': '买入' if regime.iloc[-1] == 1 else ('卖出' if regime.iloc[-1] == -1 else '观望'),
    }
    
    return latest


# ==================== 系统2: new_analysis_script 逻辑 ====================

def system2_bollinger(close: pd.Series, period: int = 19) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """系统2布林带"""
    mid = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper_raw = mid + 1.07 * std
    lower_raw = mid - 1.07 * std
    upper = upper_raw.rolling(window=7).mean()
    lower = lower_raw.rolling(window=7).mean()
    mid = mid.rolling(window=7).mean()
    return mid, upper, lower


def system2_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """系统2 ATR计算"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def system2_predict_bands(close: pd.Series, upper: pd.Series, lower: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """系统2预测布林带"""
    predicted_upper, predicted_lower, predicted_close = [], [], []
    for i in range(1, len(close)):
        pred_c, _ = predict_next_price(close.iloc[i-1], close.iloc[i])
        predicted_close.append(pred_c)
        pred_u, _ = predict_next_price(upper.iloc[i-1], upper.iloc[i])
        predicted_upper.append(pred_u)
        pred_l, _ = predict_next_price(lower.iloc[i-1], lower.iloc[i])
        predicted_lower.append(pred_l)
    return pd.Series([np.nan] + predicted_close), pd.Series([np.nan] + predicted_upper), pd.Series([np.nan] + predicted_lower)


def system2_signals(close: pd.Series, upper: pd.Series, lower: pd.Series, 
                    upper_angle: pd.Series, lower_angle: pd.Series) -> pd.Series:
    """系统2交易信号"""
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
    return strategy


def system2_analyze(df: pd.DataFrame) -> Dict:
    """系统2分析"""
    close = df['close']
    high = df['high']
    low = df['low']
    
    # 布林带
    mid, upper, lower = system2_bollinger(close)
    
    # ATR
    atr = system2_atr(high, low, close)
    
    # 预测布林带
    pred_close, pred_upper, pred_lower = system2_predict_bands(close, upper, lower)
    
    # 角度
    close_angle = (close / close.shift(1) - 1) * 100
    upper_angle = (upper / upper.shift(1) - 1) * 100
    lower_angle = (lower / lower.shift(1) - 1) * 100
    
    # 信号
    strategy = system2_signals(close, upper, lower, upper_angle, lower_angle)
    
    latest = {
        'ts_code': df.get('ts_code', [None]*len(df)).iloc[0],
        'date': str(df.index[-1])[:10] if hasattr(df.index, '__getitem__') else str(df['trade_date'].iloc[-1]),
        'close': close.iloc[-1],
        'bb_upper': upper.iloc[-1],
        'bb_mid': mid.iloc[-1],
        'bb_lower': lower.iloc[-1],
        'atr': atr.iloc[-1],
        'predicted_close': pred_close.iloc[-1],
        'strategy': strategy.iloc[-1],
    }
    
    return latest


# ==================== 回测系统 ====================

def run_backtest_with_stops(df: pd.DataFrame, system: int = 1, 
                           profit_target: float = 0.02,
                           trailing_percent: float = 0.02,
                           shares: int = 100) -> Dict:
    """
    带止盈止损的回测
    
    Args:
        df: 股票数据
        system: 1 或 2
        profit_target: 次日止盈目标 (默认2%)
        trailing_percent: 移动止盈回调比例 (默认2%)
        shares: 每次交易股数
    
    Returns:
        dict: 回测结果
    """
    close = df['close']
    high = df['high']
    low = df['low']
    
    # 预计算指标
    if system == 1:
        mid, upper, lower = system1_bollinger(close)
        diff, dea, macd = system1_macd(close)
        alpha_space = macd.max() - macd.min()
        alphalens = close / alpha_space if alpha_space > 0 else np.nan
        fast = alphalens.rolling(1).mean()
        slow = alphalens.rolling(3).mean()
        d_value = fast - slow
        regime = system1_regime(d_value, macd)
        
        signals = regime  # 1=买入, -1=卖出, 0=等待
        stop_loss_price = lower  # 跌破下轨止损
        take_profit_price = upper  # 触及上轨止盈
    else:
        mid, upper, lower = system2_bollinger(close)
        atr = system2_atr(high, low, close)
        close_angle = (close / close.shift(1) - 1) * 100
        upper_angle = (upper / upper.shift(1) - 1) * 100
        lower_angle = (lower / lower.shift(1) - 1) * 100
        signals = system2_signals(close, upper, lower, upper_angle, lower_angle)
        
        # 系统2: ATR倍数止损/止盈
        stop_loss_price = close - 2 * atr  # 跌破2倍ATR
        take_profit_price = close + 3 * atr  # 触及3倍ATR
    
    # 回测
    trades = []
    position = None  # {'entry_price': x, 'entry_date': x, 'high_price': x}
    
    for i in range(31, len(df)):
        signal = signals.iloc[i-1] if system == 1 else signals.iloc[i-1]
        
        if system == 1:
            signal_val = signal
        else:
            signal_val = 1 if signal in ['短买', '中买'] else (-1 if signal == '卖出' else 0)
        
        current_price = close.iloc[i]
        next_price = close.iloc[i+1] if i+1 < len(close) else current_price
        
        # 入场
        if position is None and signal_val == 1:
            position = {
                'entry_price': current_price,
                'entry_date': df.index[i] if hasattr(df.index, '__getitem__') else i,
                'high_price': current_price,
                'shares': shares,
                'entry_fee': calc_fee(current_price, shares)
            }
            continue
        
        if position is None:
            continue
        
        # 更新最高价
        if current_price > position['high_price']:
            position['high_price'] = current_price
        
        # 计算收益
        gross_return = (current_price - position['entry_price']) / position['entry_price']
        net_return = calc_net_return(gross_return, position['entry_price'], shares)
        
        exit_reason = None
        
        # 1. 次日2%止盈检查
        if i + 1 < len(close):
            next_return = (close.iloc[i+1] - position['entry_price']) / position['entry_price']
            next_net = calc_net_return(next_return, position['entry_price'], shares)
            if next_net >= profit_target:
                exit_reason = '次日2%止盈'
                position['exit_price'] = close.iloc[i+1]
                position['exit_date'] = df.index[i+1] if hasattr(df.index, '__getitem__') else i+1
                position['return'] = next_net
                trades.append(position)
                position = None
                continue
        
        # 2. 移动止盈/止损检查
        # 系统1: 跌破布林带上轨止损或止盈
        if system == 1:
            current_upper = upper.iloc[i]
            current_lower = lower.iloc[i]
            
            # 止损: 跌破下轨
            if current_price <= current_lower:
                exit_reason = '止损-跌破下轨'
                position['exit_price'] = current_price
                position['exit_date'] = df.index[i] if hasattr(df.index, '__getitem__') else i
                position['return'] = calc_net_return(
                    (current_price - position['entry_price']) / position['entry_price'],
                    position['entry_price'], shares
                )
                trades.append(position)
                position = None
                continue
            
            # 止盈: 触及上轨
            if current_price >= current_upper:
                exit_reason = '止盈-触及上轨'
                position['exit_price'] = current_price
                position['exit_date'] = df.index[i] if hasattr(df.index, '__getitem__') else i
                position['return'] = calc_net_return(
                    (current_price - position['entry_price']) / position['entry_price'],
                    position['entry_price'], shares
                )
                trades.append(position)
                position = None
                continue
        
        # 系统2: ATR倍数止损/止盈
        if system == 2:
            current_atr = atr.iloc[i]
            
            # 止损: 跌破2倍ATR
            stop_price = position['entry_price'] - 2 * current_atr
            if current_price <= stop_price:
                exit_reason = '止损-2倍ATR'
                position['exit_price'] = current_price
                position['exit_date'] = df.index[i] if hasattr(df.index, '__getitem__') else i
                position['return'] = calc_net_return(
                    (current_price - position['entry_price']) / position['entry_price'],
                    position['entry_price'], shares
                )
                trades.append(position)
                position = None
                continue
            
            # 止盈: 触及3倍ATR
            profit_price = position['entry_price'] + 3 * current_atr
            if current_price >= profit_price:
                exit_reason = '止盈-3倍ATR'
                position['exit_price'] = current_price
                position['exit_date'] = df.index[i] if hasattr(df.index, '__getitem__') else i
                position['return'] = calc_net_return(
                    (current_price - position['entry_price']) / position['entry_price'],
                    position['entry_price'], shares
                )
                trades.append(position)
                position = None
                continue
        
        # 移动止盈: 从高点回落2%
        if position and position['high_price'] > 0:
            trailing_stop = position['high_price'] * (1 - trailing_percent)
            if current_price <= trailing_stop and gross_return > 0.02:  # 已有2%以上收益
                exit_reason = '移动止盈-回落2%'
                position['exit_price'] = current_price
                position['exit_date'] = df.index[i] if hasattr(df.index, '__getitem__') else i
                position['return'] = calc_net_return(
                    (current_price - position['entry_price']) / position['entry_price'],
                    position['entry_price'], shares
                )
                trades.append(position)
                position = None
                continue
    
    # 统计
    if not trades:
        return {'trades': [], 'summary': {'total': 0, 'wins': 0, 'win_rate': 0, 'total_return': 0}}
    
    trades_df = pd.DataFrame(trades)
    wins = (trades_df['return'] > 0).sum()
    total_return = trades_df['return'].sum()
    avg_return = trades_df['return'].mean()
    
    # 计算夏普等指标
    returns = trades_df['return']
    if len(returns) > 1 and returns.std() > 0:
        sharpe = returns.mean() / returns.std() * np.sqrt(len(returns))
    else:
        sharpe = 0
    
    max_win = returns.max() if len(returns) > 0 else 0
    max_loss = returns.min() if len(returns) > 0 else 0
    
    # 退出原因统计
    exit_reasons = trades_df['exit_reason'].value_counts().to_dict() if 'exit_reason' in trades_df.columns else {}
    
    return {
        'trades': trades,
        'summary': {
            'total': len(trades),
            'wins': int(wins),
            'win_rate': wins / len(trades) * 100,
            'total_return': total_return * 100,
            'avg_return': avg_return * 100,
            'sharpe': sharpe,
            'max_win': max_win * 100,
            'max_loss': max_loss * 100,
            'exit_reasons': exit_reasons
        }
    }


# ==================== 统一入口 ====================

def analyze_with_systems(df: pd.DataFrame, ts_code: str = None, 
                         total_assets: float = 1000000, win_rate: float = 0.6) -> Dict:
    """完整分析 - 两个独立系统"""
    if ts_code:
        df = df.copy()
        df['ts_code'] = ts_code
    
    result = {
        'system1': system1_analyze(df, total_assets, win_rate),
        'system2': system2_analyze(df)
    }
    
    return result


def run_full_backtest(df: pd.DataFrame, profit_target: float = 0.02, 
                      trailing_percent: float = 0.02, shares: int = 100) -> Dict:
    """完整回测 - 两个系统"""
    s1_result = run_backtest_with_stops(df, system=1, profit_target=profit_target, 
                                         trailing_percent=trailing_percent, shares=shares)
    s2_result = run_backtest_with_stops(df, system=2, profit_target=profit_target,
                                         trailing_percent=trailing_percent, shares=shares)
    
    return {
        'system1': s1_result,
        'system2': s2_result
    }
