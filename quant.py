# Quant-Skill 定量分析核心模块
# 基于CFA定量分析框架

import sys
import os
import math
from collections import OrderedDict

# 添加alfe路径
sys.path.insert(0, '/home/node/.openclaw/workspace/evolve/skills')

try:
    from alfe.hq import AlfeHq_API
    from alfe.config.hosts import hq_hosts
    ALFE_AVAILABLE = True
except ImportError:
    ALFE_AVAILABLE = False
    print("警告: alfe模块不可用")

import numpy as np
import pandas as pd
from scipy import stats


class QuantAnalyzer:
    """CFA风格定量分析器"""
    
    def __init__(self):
        self.api = None
        self.connected = False
        
    def connect(self, server_idx=0):
        """连接行情服务器"""
        if not ALFE_AVAILABLE:
            raise Exception("alfe模块不可用")
        
        self.api = AlfeHq_API()
        host = hq_hosts[server_idx]
        ip, port = host[1], host[2]
        
        result = self.api.connect(ip, port)
        if result:
            self.connected = True
            print(f"已连接: {host[0]}")
        return result
    
    def disconnect(self):
        """断开连接"""
        if self.api and self.connected:
            self.api.disconnect()
            self.connected = False
    
    # ==================== CFA L1: 基础统计 ====================
    
    def mean(self, data):
        """计算均值 (期望值)"""
        return np.mean(data)
    
    def median(self, data):
        """计算中位数"""
        return np.median(data)
    
    def variance(self, data, population=True):
        """计算方差"""
        if population:
            return np.var(data, ddof=0)
        return np.var(data, ddof=1)
    
    def std_dev(self, data, population=True):
        """计算标准差"""
        if population:
            return np.std(data, ddof=0)
        return np.std(data, ddof=1)
    
    def covariance(self, x, y):
        """计算协方差"""
        return np.cov(x, y)[0, 1]
    
    def correlation(self, x, y):
        """计算相关系数 (Pearson)"""
        return np.corrcoef(x, y)[0, 1]
    
    def correlation_matrix(self, data_dict):
        """计算相关系数矩阵"""
        df = pd.DataFrame(data_dict)
        return df.corr()
    
    def skewness(self, data):
        """偏度 (CFA L1)"""
        return stats.skew(data)
    
    def kurtosis(self, data):
        """峰度 (CFA L1)"""
        return stats.kurtosis(data)
    
    def normal_test(self, data):
        """正态分布检验 (Jarque-Bera)"""
        stat, p_value = stats.jarque_bera(data)
        return {'statistic': stat, 'p_value': p_value, 'is_normal': p_value > 0.05}
    
    # ==================== CFA L1: 概率论 ====================
    
    def expected_value(self, values, probabilities):
        """期望值 E(X) = Σxi*Pi"""
        return np.average(values, weights=probabilities)
    
    def variance_prob(self, values, probabilities):
        """概率分布的方差 Var(X) = E(X²) - [E(X)]²"""
        ev = self.expected_value(values, probabilities)
        ev2 = np.average([v**2 for v in values], weights=probabilities)
        return ev2 - ev**2
    
    def bayes_theorem(self, p_a_b, p_b, p_a):
        """贝叶斯定理 P(A|B) = P(B|A) * P(A) / P(B)"""
        return p_a_b * p_a / p_b
    
    # ==================== CFA L1: 货币时间价值 ====================
    
    def fv(self, pv, r, n, m=1):
        """未来值 FV = PV × (1 + r/m)^(m×n)"""
        return pv * (1 + r/m) ** (m*n)
    
    def pv(self, fv, r, n, m=1):
        """现值 PV = FV / (1 + r/m)^(m×n)"""
        return fv / (1 + r/m) ** (m*n)
    
    def annuity_pv(self, pmt, r, n, m=1, due=False):
        """年金现值"""
        if r == 0:
            return pmt * n
        i = r / m
        if due:
            return pmt * ((1 - (1 + i)**(-n)) / i) * (1 + i)
        return pmt * (1 - (1 + i)**(-n)) / i
    
    def annuity_fv(self, pmt, r, n, m=1, due=False):
        """年金未来值"""
        if r == 0:
            return pmt * n
        i = r / m
        if due:
            return pmt * (((1 + i)**n - 1) / i) * (1 + i)
        return pmt * ((1 + i)**n - 1) / i
    
    def npv(self, cash_flows, r):
        """净现值 NPV = ΣCFt/(1+r)^t"""
        return sum(cf / (1 + r)**t for t, cf in enumerate(cash_flows))
    
    def irr(self, cash_flows, guess=0.1):
        """内部收益率 IRR"""
        return np.irr(cash_flows)
    
    # ==================== CFA L1-L2: 回归分析 ====================
    
    def linear_regression(self, y, x):
        """简单线性回归 y = a + bx"""
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value ** 2,
            'r': r_value,
            'p_value': p_value,
            'std_error': std_err,
            'formula': f'y = {intercept:.4f} + {slope:.4f}x'
        }
    
    def multi_regression(self, y, X):
        """多元线性回归 (需要pandas)"""
        from scipy.stats import t
        X = np.array(X)
        y = np.array(y)
        
        # 添加常数列
        X = np.column_stack([np.ones(len(y)), X])
        
        # OLS
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        y_pred = X @ beta
        
        # 计算统计量
        n, k = X.shape
        residuals = y - y_pred
        mse = np.sum(residuals**2) / (n - k)
        
        var_beta = mse * np.linalg.inv(X.T @ X)
        se = np.sqrt(np.diag(var_beta))
        t_stats = beta / se
        p_values = 2 * (1 - t.cdf(np.abs(t_stats), n - k))
        
        ssr = np.sum((y_pred - np.mean(y))**2)
        sst = np.sum((y - np.mean(y))**2)
        r_squared = ssr / sst
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1)
        
        return {
            'coefficients': beta,
            'std_errors': se,
            't_stats': t_stats,
            'p_values': p_values,
            'r_squared': r_squared,
            'adj_r_squared': adj_r_squared,
            'mse': mse
        }
    
    # ==================== CFA L2: 时间序列 ====================
    
    def moving_average(self, data, window):
        """移动平均"""
        return pd.Series(data).rolling(window=window).mean().tolist()
    
    def exponential_smoothing(self, data, alpha=0.3):
        """指数平滑"""
        return pd.Series(data).ewm(alpha=alpha).mean().tolist()
    
    # ==================== CFA L1: 财务比率 ====================
    
    def get_finance_data(self, market, code):
        """获取财务数据"""
        if not self.connected:
            raise Exception("未连接服务器")
        return self.api.get_finance_info(market, code)
    
    def calc_financial_ratios(self, finance_data):
        """计算财务比率"""
        ratios = {}
        
        # 估值比率
        if 'zongguben' in finance_data and 'jinglirun' in finance_data:
            total_shares = finance_data.get('zongguben', 0)
            net_profit = finance_data.get('jinglirun', 0)
            if total_shares > 0:
                eps = net_profit / total_shares
                ratios['EPS'] = eps
        
        # 每股净资产
        if 'meigujingzichan' in finance_data:
            ratios['BVPS'] = finance_data['meigujingzichan']
        
        # 股东权益/总资产
        if 'jingzichan' in finance_data and 'zongzichan' in finance_data:
            if finance_data['zongzichan'] > 0:
                ratios['Equity_Asset_Ratio'] = finance_data['jingzichan'] / finance_data['zongzichan']
        
        # 流动资产/流动负债 (如数据有)
        if 'liudongzichan' in finance_data and 'liudongfuzhai' in finance_data:
            if finance_data['liudongfuzhai'] > 0:
                ratios['Current_Ratio'] = finance_data['liudongzichan'] / finance_data['liudongfuzhai']
        
        return ratios
    
    # ==================== CFA L2-L3: 风险分析 ====================
    
    def returns(self, prices):
        """计算收益率"""
        return pd.Series(prices).pct_change().dropna().tolist()
    
    def value_at_risk(self, returns, confidence=0.95):
        """VaR (Value at Risk) - 参数法"""
        mu = np.mean(returns)
        sigma = np.std(returns, ddof=1)
        z = stats.norm.ppf(1 - confidence)
        return mu + z * sigma
    
    def conditional_var(self, returns, confidence=0.95):
        """CVaR / Expected Shortfall"""
        var = self.value_at_risk(returns, confidence)
        return np.mean(returns[returns <= var])
    
    def sharpe_ratio(self, returns, risk_free=0.03):
        """夏普比率"""
        rp = np.mean(returns)
        rf = risk_free / 252  # 日化
        sigma = np.std(returns, ddof=1)
        if sigma == 0:
            return 0
        return (rp - rf) / sigma * np.sqrt(252)
    
    def beta(self, stock_returns, market_returns):
        """Beta系数"""
        covariance = np.cov(stock_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        return covariance / market_variance if market_variance > 0 else 1.0
    
    def volatility(self, returns, annualize=True):
        """波动率"""
        vol = np.std(returns, ddof=1)
        if annualize:
            return vol * np.sqrt(252)  # 年化波动率
        return vol
    
    # ==================== CFA L1: 折现现金流 ====================
    
    def dcf_value(self, cash_flows, growth_rate, discount_rate, terminal_growth, years=5):
        """DCF估值"""
        # 预测期现金流
        pv_cfs = []
        cf = cash_flows[0] if cash_flows else 0
        for i in range(years):
            cf = cf * (1 + growth_rate)
            pv_cfs.append(cf / (1 + discount_rate)**(i+1))
        
        # 终值
        terminal_value = (cf * (1 + terminal_growth)) / (discount_rate - terminal_growth)
        terminal_pv = terminal_value / (1 + discount_rate)**years
        
        return {
            'pv_cash_flows': sum(pv_cfs),
            'terminal_value': terminal_value,
            'terminal_pv': terminal_pv,
            'enterprise_value': sum(pv_cfs) + terminal_pv
        }


# 快捷函数
def correlation(x, y):
    """相关系数"""
    return np.corrcoef(x, y)[0, 1]

def std_dev(data):
    """标准差"""
    return np.std(data, ddof=1)

def variance(data):
    """方差"""
    return np.var(data, ddof=1)


# ==================== 蒙特卡洛模拟 ====================

def sim(steps=2000, bins=10, seed=2026):
    """
    蒙特卡洛股价路径模拟器
    
    基于概率分布模拟股价波动路径
    
    参数:
        steps: 模拟步数 (天数)
        bins: 价格区间数量
        seed: 随机种子
    
    返回:
        list: 模拟的价格时间序列
    """
    import random as random_module
    random_module.seed(seed)
    np.random.seed(seed)
    
    c = np.linspace(725, 1175, bins)          # Bin center
    p = np.full(bins, 1.0 / bins)             # Initial uniform distribution
    h = []                                      # Historical expected price
    
    for _ in range(steps):
        r = random_module.random()
        x = np.arange(bins)
        
        if   r < 0.28: cen = random_module.randint(0,bins-1); s = random_module.uniform(1.4,2.6); b = np.exp(-((x-cen)**2)/(2*s*s))
        elif r < 0.52: b = np.exp(-((x - (bins-1)/2)**2) / 18)
        elif r < 0.66: b = np.linspace(0.4, 3.2, bins)**1.3
        elif r < 0.80: b = np.linspace(3.2, 0.4, bins)**1.3
        elif r < 0.92: cen = bins * (1 - (950-700)/500); b = np.exp(-((x-cen)**2)/10)
        else:          b = np.random.exponential(bins) if r < 0.96 else np.ones(bins)
        
        b += np.random.normal(0, 0.015, bins)
        b = np.clip(b, 1e-5, None)
        b /= b.sum() + 1e-12
        
        w = random_module.uniform(0.004, 0.035)
        p = (1-w)*p + w*b
        p /= p.sum() + 1e-12
        
        h.append(np.dot(p, c))
    
    return h


def monte_carlo_price(current_price, volatility=0.2, days=252, simulations=1000, seed=42):
    """
    蒙特卡洛期权定价模拟
    
    参数:
        current_price: 当前价格
        volatility: 年化波动率 (默认20%)
        days: 模拟天数 (默认252个交易日)
        simulations: 模拟次数
        seed: 随机种子
    
    返回:
        array: 模拟的最终价格分布
    """
    np.random.seed(seed)
    
    # 生成随机收益率
    returns = np.random.normal(0, volatility / np.sqrt(days), (simulations, days))
    
    # 计算价格路径
    price_paths = current_price * np.exp(np.cumsum(returns, axis=1))
    
    return price_paths[:, -1]  # 返回最终价格


def black_scholes_call(S, K, T, r, sigma):
    """
    Black-Scholes 看涨期权定价
    
    参数:
        S: 当前股价
        K: 行权价
        T: 到期时间 (年)
        r: 无风险利率
        sigma: 波动率
    
    返回:
        float: 期权价格
    """
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    
    call_price = S * stats.norm.cdf(d1) - K * np.exp(-r*T) * stats.norm.cdf(d2)
    return call_price
