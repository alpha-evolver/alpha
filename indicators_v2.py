# Custom Indicators - System 1 & System 2 + Quant
# 修正版：符合我们的独有逻辑

import numpy as np
import pandas as pd
from typing import Tuple, Dict
from math import pi


# ==================== Quant CFA ====================

def calc_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().dropna()


def calc_sharpe(returns: pd.Series, risk_free: float = 0.03) -> float:
    rp = returns.mean() * 252
    sigma = returns.std() * np.sqrt(252)
    return (rp - risk_free) / sigma if sigma > 0 else 0


def calc_var(returns: pd.Series, confidence: float = 0.95) -> float:
    return returns.quantile(1 - confidence)


def calc_max_drawdown(returns: pd.Series) -> float:
    cum = (1 + returns).cumprod()
    cummax = cum.cummax()
    return (cum / cummax - 1).min()


def quant_analyze(df: pd.DataFrame) -> Dict:
    close = df['close']
    returns = calc_returns(close)
    
    if len(returns) < 10:
        return {'期间涨跌幅': '0%', '日均收益率': '0%', '日收益率标准差': '0%', 
                '年化波动率': '0%', '夏普比率': '0', '95%VaR': '0%', '最大回撤': '0%'}
    
    total = (close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100
    
    return {
        '期间涨跌幅': f"{total:.2f}%",
        '日均收益率': f"{returns.mean()*100:.4f}%",
        '日收益率标准差': f"{returns.std()*100:.4f}%",
        '年化波动率': f"{returns.std()*np.sqrt(252)*100:.2f}%",
        '夏普比率': f"{calc_sharpe(returns):.2f}",
        '95%VaR': f"{calc_var(returns)*100:.2f}%",
        '最大回撤': f"{calc_max_drawdown(returns)*100:.2f}%"
    }


# ==================== 系统1 (趋势策略) ====================

def predict_next(previous: float, current: float) -> Tuple[float, float]:
    if not isinstance(previous, (int, float)) or not isinstance(current, (int, float)):
        return np.nan, np.nan
    if pd.isna(previous) or pd.isna(current) or previous == 0:
        return np.nan, np.nan
    try:
        gr = (current - previous) / previous
        return round(current * (1 + gr), 2), round(gr, 5)
    except:
        return np.nan, np.nan


def system1_analyze(df: pd.DataFrame) -> Dict:
    """
    系统1逻辑：
    - close > 上轨 = 多头趋势
    - close < 下轨 = 空头趋势  
    - 上轨中间 = 交易范围
    - close > 上轨：上中下轨都是支撑
    - close < 下轨：上中下轨都是压力
    - 跌破上轨 = 止损/止盈
    """
    close = df['close']
    open_p = df['open']
    
    # 布林带 (1.07, period=19)
    mid = close.ewm(alpha=2/19, adjust=False).mean()
    std = close.rolling(19).std()
    upper = mid + 1.07 * std
    lower = mid - 1.07 * std
    
    # 预测
    predicted = [np.nan]
    for i in range(1, len(close)):
        p, _ = predict_next(close.iloc[i-1], close.iloc[i])
        predicted.append(p)
    
    # 趋势判断 (我们的独有逻辑)
    trend = pd.Series(index=close.index, dtype=str)
    trend.loc[close > upper] = "多头趋势"
    trend.loc[close < lower] = "空头趋势"
    trend.loc[(close <= upper) & (close >= lower)] = "交易范围"
    
    # 支撑/压力 (我们的独有逻辑)
    # close > 上轨：上中下轨都是支撑
    # close < 下轨：上中下轨都是压力
    support = pd.Series(index=close.index, dtype=float)
    pressure = pd.Series(index=close.index, dtype=float)
    
    # 多头趋势：上中下都是支撑
    support.loc[close > upper] = lower
    pressure.loc[close > upper] = np.nan  # 无压力
    
    # 空头趋势：上中下都是压力
    pressure.loc[close < lower] = upper
    support.loc[close < lower] = np.nan  # 无支撑
    
    # 交易范围
    in_range = (close <= upper) & (close >= lower)
    support.loc[in_range] = lower
    pressure.loc[in_range] = upper
    
    # 冗余位 (买入参考价)
    # 多头趋势用支撑，空头趋势用压力
    redundancy = pd.Series(index=close.index, dtype=float)
    redundancy.loc[close > upper] = support.loc[close > upper] - open_p * 0.02
    redundancy.loc[close < lower] = pressure.loc[close < lower] + open_p * 0.02
    redundancy.loc[in_range] = mid
    
    # MACD信号
    ema12 = close.ewm(alpha=2/12, adjust=False).mean()
    ema26 = close.ewm(alpha=2/26, adjust=False).mean()
    diff = ema12 - ema26
    dea = diff.ewm(alpha=2/9, adjust=False).mean()
    macd = 2 * (diff - dea)
    
    # Alpha
    alpha_space = macd.max() - macd.min()
    alphalens = close / alpha_space if alpha_space > 0 else np.nan
    fast = alphalens.rolling(1).mean()
    slow = alphalens.rolling(3).mean()
    d_value = fast - slow
    
    # Regime信号
    regime = pd.Series(index=close.index, dtype=int, data=0)
    regime.loc[(d_value > 0) & (macd < 0)] = 1  # 买入
    regime.loc[(d_value < 0) & (macd > 0)] = -1  # 卖出
    
    strategy = regime.replace({1: "买入", 0: "等待", -1: "卖出"})
    
    # 收盘价数值
    c = close.iloc[-1]
    u = upper.iloc[-1]
    l = lower.iloc[-1]
    sup = support.iloc[-1]
    pres = pressure.iloc[-1]
    red = redundancy.iloc[-1]
    
    return {
        '收盘价': round(c, 2),
        '收期价': predicted[-1],
        '支撑位': round(sup, 2) if pd.notna(sup) else None,
        '压力位': round(pres, 2) if pd.notna(pres) else None,
        '冗余位': round(red, 2) if pd.notna(red) else None,
        '量化趋势': trend.iloc[-1],
        '策略': strategy.iloc[-1]
    }


# ==================== 系统2 (投机策略) ====================

def system2_analyze(df: pd.DataFrame) -> Dict:
    """
    系统2逻辑：
    - 布林带+ATR
    - 短买：突破上轨+角度为负
    - 中买：跌破下轨+超卖
    - 卖出：突破上轨+角度过高
    """
    close = df['close']
    
    # 布林带 (标准+MA平滑)
    mid = close.rolling(19).mean()
    std = close.rolling(19).std()
    upper_raw = mid + 1.07 * std
    lower_raw = mid - 1.07 * std
    upper = upper_raw.rolling(7).mean()
    lower = lower_raw.rolling(7).mean()
    
    # ATR
    high = df['high']
    low = df['low']
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    
    # 预测
    predicted = [np.nan]
    for i in range(1, len(close)):
        p, _ = predict_next(close.iloc[i-1], close.iloc[i])
        predicted.append(p)
    
    # 信号
    angle_u = (upper / upper.shift(1) - 1) * 100
    angle_l = (lower / lower.shift(1) - 1) * 100
    
    pos_u = angle_u[angle_u > 0]
    neg_l = angle_l[angle_l < 0]
    um_q = pos_u.quantile(0.88) if len(pos_u) > 0 else 30
    lm_q = neg_l.quantile(0.12) if len(neg_l) > 0 else -30
    
    buy_short = (close > upper) & (angle_u < 0)
    buy_medium = (close < lower) & (angle_l < lm_q)
    sell = (close > upper) & (angle_u > um_q)
    
    strategy = pd.Series(index=close.index, dtype=str, data='等待')
    strategy.loc[buy_short] = '短买'
    strategy.loc[buy_medium] = '中买'
    strategy.loc[sell] = '卖出'
    
    c = close.iloc[-1]
    u = upper.iloc[-1]
    l = lower.iloc[-1]
    
    return {
        '收盘价': round(c, 2),
        '收期价': predicted[-1],
        '支撑位': round(l, 2),
        '压力位': round(u, 2),
        '冗余位': None,
        '量化趋势': '交易范围',
        '策略': strategy.iloc[-1]
    }


# ==================== 回测 ====================

def calc_fee(price, shares=100):
    return max(price * shares * 0.0003, 5)


def calc_net(gross, price, shares=100):
    return (price * shares * gross - calc_fee(price, shares) * 2) / (price * shares)


def run_backtest(df, system=1, profit_target=0.02, shares=100):
    close = df['close']
    high = df['high']
    low = df['low']
    
    # 系统1
    if system == 1:
        mid = close.ewm(alpha=2/19, adjust=False).mean()
        std = close.rolling(19).std()
        upper = mid + 1.07 * std
        lower = mid - 1.07 * std
        
        ema12 = close.ewm(alpha=2/12, adjust=False).mean()
        ema26 = close.ewm(alpha=2/26, adjust=False).mean()
        diff = ema12 - ema26
        dea = diff.ewm(alpha=2/9, adjust=False).mean()
        macd = 2 * (diff - dea)
        
        alpha_space = macd.max() - macd.min()
        alphalens = close / alpha_space if alpha_space > 0 else np.nan
        fast = alphalens.rolling(1).mean()
        slow = alphalens.rolling(3).mean()
        d_value = fast - slow
        
        regime = pd.Series(index=close.index, dtype=int, data=0)
        regime.loc[(d_value > 0) & (macd < 0)] = 1
        regime.loc[(d_value < 0) & (macd > 0)] = -1
    else:
        mid = close.rolling(19).mean()
        std = close.rolling(19).std()
        upper_raw = mid + 1.07 * std
        lower_raw = mid - 1.07 * std
        upper = upper_raw.rolling(7).mean()
        lower = lower_raw.rolling(7).mean()
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
    
    trades = []
    position = None
    
    for i in range(31, len(df)):
        signal = regime.iloc[i-1] if system == 1 else 0
        curr = close.iloc[i]
        
        if position is None and signal == 1:
            position = {'price': curr, 'shares': shares}
            continue
        if position is None:
            continue
        
        # 次日2%止盈
        if i + 1 < len(close):
            ret = (close.iloc[i+1] - position['price']) / position['price']
            if calc_net(ret, position['price'], shares) >= profit_target:
                position['ret'] = calc_net(ret, position['price'], shares)
                trades.append(position)
                position = None
                continue
        
        # 止损：跌破上轨 (系统1)
        if system == 1:
            if curr <= upper.iloc[i]:
                position['ret'] = calc_net((curr - position['price']) / position['price'], position['price'], shares)
                trades.append(position)
                position = None
        else:
            if curr <= position['price'] - 2 * atr.iloc[i]:
                position['ret'] = calc_net((curr - position['price']) / position['price'], position['price'], shares)
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


def analyze_with_systems(df, ts_code=None):
    return {
        '量化分析': quant_analyze(df),
        '系统1': system1_analyze(df),
        '系统2': system2_analyze(df)
    }


def run_full_backtest(df, profit_target=0.02, shares=100):
    return {
        '系统1': run_backtest(df, 1, profit_target, shares),
        '系统2': run_backtest(df, 2, profit_target, shares)
    }
