# Custom Indicators - System 1 & System 2 + Quant
# Corrected version: following our unique logic

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
        return {'Period Return': '0%', 'Daily Mean Return': '0%', 'Daily Return Std Dev': '0%',
                'Annualized Volatility': '0%', 'Sharpe Ratio': '0', '95% VaR': '0%', 'Max Drawdown': '0%'}

    total = (close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100

    return {
        'Period Return': f"{total:.2f}%",
        'Daily Mean Return': f"{returns.mean()*100:.4f}%",
        'Daily Return Std Dev': f"{returns.std()*100:.4f}%",
        'Annualized Volatility': f"{returns.std()*np.sqrt(252)*100:.2f}%",
        'Sharpe Ratio': f"{calc_sharpe(returns):.2f}",
        '95% VaR': f"{calc_var(returns)*100:.2f}%",
        'Max Drawdown': f"{calc_max_drawdown(returns)*100:.2f}%"
    }


# ==================== System 1 (Trend Strategy) ====================

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
    System 1 logic:
    - close > upper band = bullish trend
    - close < lower band = bearish trend
    - between bands = trading range
    - close > upper: all bands are support
    - close < lower: all bands are resistance
    - break below upper = stop-loss/take-profit
    """
    close = df['close']
    open_p = df['open']

    # Bollinger Bands (1.07, period=19)
    mid = close.ewm(alpha=2/19, adjust=False).mean()
    std = close.rolling(19).std()
    upper = mid + 1.07 * std
    lower = mid - 1.07 * std

    # Prediction
    predicted = [np.nan]
    for i in range(1, len(close)):
        p, _ = predict_next(close.iloc[i-1], close.iloc[i])
        predicted.append(p)

    # Trend determination (our unique logic)
    trend = pd.Series(index=close.index, dtype=str)
    trend.loc[close > upper] = "Bullish Trend"
    trend.loc[close < lower] = "Bearish Trend"
    trend.loc[(close <= upper) & (close >= lower)] = "Trading Range"

    # Support/Resistance (our unique logic)
    # close > upper: all bands are support
    # close < lower: all bands are resistance
    support = pd.Series(index=close.index, dtype=float)
    pressure = pd.Series(index=close.index, dtype=float)

    # Bullish trend: upper, mid, lower are all support
    support.loc[close > upper] = lower
    pressure.loc[close > upper] = np.nan  # No resistance

    # Bearish trend: upper, mid, lower are all resistance
    pressure.loc[close < lower] = upper
    support.loc[close < lower] = np.nan  # No support

    # Trading range
    in_range = (close <= upper) & (close >= lower)
    support.loc[in_range] = lower
    pressure.loc[in_range] = upper

    # Redundancy level (buy reference price)
    # Bullish trend uses support, bearish trend uses resistance
    redundancy = pd.Series(index=close.index, dtype=float)
    redundancy.loc[close > upper] = support.loc[close > upper] - open_p * 0.02
    redundancy.loc[close < lower] = pressure.loc[close < lower] + open_p * 0.02
    redundancy.loc[in_range] = mid

    # MACD signal
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

    # Regime signal
    regime = pd.Series(index=close.index, dtype=int, data=0)
    regime.loc[(d_value > 0) & (macd < 0)] = 1  # Buy
    regime.loc[(d_value < 0) & (macd > 0)] = -1  # Sell

    strategy = regime.replace({1: "Buy", 0: "Wait", -1: "Sell"})

    # Closing price values
    c = close.iloc[-1]
    u = upper.iloc[-1]
    l = lower.iloc[-1]
    sup = support.iloc[-1]
    pres = pressure.iloc[-1]
    red = redundancy.iloc[-1]

    return {
        'Close Price': round(c, 2),
        'Predicted Price': predicted[-1],
        'Support Level': round(sup, 2) if pd.notna(sup) else None,
        'Resistance Level': round(pres, 2) if pd.notna(pres) else None,
        'Redundancy Level': round(red, 2) if pd.notna(red) else None,
        'Trend': trend.iloc[-1],
        'Strategy': strategy.iloc[-1]
    }


# ==================== System 2 (Speculative Strategy) ====================

def system2_analyze(df: pd.DataFrame) -> Dict:
    """
    System 2 logic:
    - Bollinger Bands + ATR
    - Short-term buy: break above upper band + negative angle
    - Medium-term buy: break below lower band + oversold
    - Sell: break above upper band + angle too high
    """
    close = df['close']

    # Bollinger Bands (standard + MA smoothing)
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

    # Prediction
    predicted = [np.nan]
    for i in range(1, len(close)):
        p, _ = predict_next(close.iloc[i-1], close.iloc[i])
        predicted.append(p)

    # Signals
    angle_u = (upper / upper.shift(1) - 1) * 100
    angle_l = (lower / lower.shift(1) - 1) * 100

    pos_u = angle_u[angle_u > 0]
    neg_l = angle_l[angle_l < 0]
    um_q = pos_u.quantile(0.88) if len(pos_u) > 0 else 30
    lm_q = neg_l.quantile(0.12) if len(neg_l) > 0 else -30

    buy_short = (close > upper) & (angle_u < 0)
    buy_medium = (close < lower) & (angle_l < lm_q)
    sell = (close > upper) & (angle_u > um_q)

    strategy = pd.Series(index=close.index, dtype=str, data='Wait')
    strategy.loc[buy_short] = 'Short-term Buy'
    strategy.loc[buy_medium] = 'Medium-term Buy'
    strategy.loc[sell] = 'Sell'

    c = close.iloc[-1]
    u = upper.iloc[-1]
    l = lower.iloc[-1]

    return {
        'Close Price': round(c, 2),
        'Predicted Price': predicted[-1],
        'Support Level': round(l, 2),
        'Resistance Level': round(u, 2),
        'Redundancy Level': None,
        'Trend': 'Trading Range',
        'Strategy': strategy.iloc[-1]
    }


# ==================== Backtesting ====================

def calc_fee(price, shares=100):
    return max(price * shares * 0.0003, 5)


def calc_net_return(gross, price, shares=100):
    """Calculate net return percentage"""
    return (gross - 1) * 100


def calc_net(gross, price, shares=100):
    return (price * shares * gross - calc_fee(price, shares) * 2) / (price * shares)


def run_backtest(df, system=1, profit_target=0.02, shares=100):
    close = df['close']
    high = df['high']
    low = df['low']

    # System 1
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

        # Next day 2% take-profit
        if i + 1 < len(close):
            ret = (close.iloc[i+1] - position['price']) / position['price']
            if calc_net(ret, position['price'], shares) >= profit_target:
                position['ret'] = calc_net(ret, position['price'], shares)
                trades.append(position)
                position = None
                continue

        # Stop-loss: break below upper band (System 1)
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
        return {'Total Trades': 0, 'Win Rate': '0%', 'Total Return': '0%'}

    wins = sum(1 for t in trades if t.get('ret', 0) > 0)
    total = sum(t.get('ret', 0) for t in trades)

    return {
        'Total Trades': len(trades),
        'Win Rate': f"{wins}/{len(trades)} ({wins/len(trades)*100:.1f}%)",
        'Total Return': f"{total*100:.2f}%"
    }


def analyze_with_systems(df, ts_code=None):
    return {
        'Quant Analysis': quant_analyze(df),
        'System 1': system1_analyze(df),
        'System 2': system2_analyze(df)
    }


def run_full_backtest(df, profit_target=0.02, shares=100):
    return {
        'System 1': run_backtest(df, 1, profit_target, shares),
        'System 2': run_backtest(df, 2, profit_target, shares)
    }


def run_backtest_with_stops(df, system=1, profit_target=0.02, shares=100):
    """Backtest with take-profit/stop-loss - alias for run_backtest"""
    return run_backtest(df, system, profit_target, shares)
