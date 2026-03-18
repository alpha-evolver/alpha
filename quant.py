# Quant-Skill Quantitative Analysis Core Module
# Based on CFA quantitative analysis framework

import sys
import os
import math
from collections import OrderedDict

# Add alfe path
sys.path.insert(0, '/home/node/.openclaw/workspace/evolve/skills')

try:
    from alfe.hq import AlfeHq_API
    from alfe.config.hosts import hq_hosts
    ALFE_AVAILABLE = True
except ImportError:
    ALFE_AVAILABLE = False
    print("Warning: alfe module not available")

import numpy as np
import pandas as pd
from scipy import stats


class QuantAnalyzer:
    """CFA-style Quantitative Analyzer"""

    def __init__(self):
        self.api = None
        self.connected = False

    def connect(self, server_idx=0):
        """Connect to market data server"""
        if not ALFE_AVAILABLE:
            raise Exception("alfe module not available")

        self.api = AlfeHq_API()
        host = hq_hosts[server_idx]
        ip, port = host[1], host[2]

        result = self.api.connect(ip, port)
        if result:
            self.connected = True
            print(f"Connected: {host[0]}")
        return result

    def connect_auto(self, max_servers=10):
        """Auto-connect to available server

        Args:
            max_servers: Maximum number of servers to try

        Returns:
            bool: Whether connection is successful
        """
        if not ALFE_AVAILABLE:
            raise Exception("alfe module not available")

        self.api = AlfeHq_API()

        for i in range(min(max_servers, len(hq_hosts))):
            host = hq_hosts[i]
            ip, port = host[1], host[2]
            try:
                print(f"Trying to connect: {host[0]} ({ip}:{port})...")
                result = self.api.connect(ip, port)
                if result:
                    self.connected = True
                    print(f"✓ Successfully connected: {host[0]}")
                    return True
            except Exception as e:
                print(f"✗ Failed: {host[0]} - {e}")
                try:
                    self.api.disconnect()
                except:
                    pass
                continue

        print("Unable to find available market data server")
        return False

    def disconnect(self):
        """Disconnect"""
        if self.api and self.connected:
            self.api.disconnect()
            self.connected = False

    # ==================== CFA L1: Basic Statistics ====================

    def mean(self, data):
        """Calculate mean (expected value)"""
        return np.mean(data)

    def median(self, data):
        """Calculate median"""
        return np.median(data)

    def variance(self, data, population=True):
        """Calculate variance"""
        if population:
            return np.var(data, ddof=0)
        return np.var(data, ddof=1)

    def std_dev(self, data, population=True):
        """Calculate standard deviation"""
        if population:
            return np.std(data, ddof=0)
        return np.std(data, ddof=1)

    def covariance(self, x, y):
        """Calculate covariance"""
        return np.cov(x, y)[0, 1]

    def correlation(self, x, y):
        """Calculate correlation coefficient (Pearson)"""
        return np.corrcoef(x, y)[0, 1]

    def correlation_matrix(self, data_dict):
        """Calculate correlation matrix"""
        df = pd.DataFrame(data_dict)
        return df.corr()

    def skewness(self, data):
        """Skewness (CFA L1)"""
        return stats.skew(data)

    def kurtosis(self, data):
        """Kurtosis (CFA L1)"""
        return stats.kurtosis(data)

    def normal_test(self, data):
        """Normal distribution test (Jarque-Bera)"""
        stat, p_value = stats.jarque_bera(data)
        return {'statistic': stat, 'p_value': p_value, 'is_normal': p_value > 0.05}

    # ==================== CFA L1: Probability Theory ====================

    def expected_value(self, values, probabilities):
        """Expected value E(X) = Σxi*Pi"""
        return np.average(values, weights=probabilities)

    def variance_prob(self, values, probabilities):
        """Variance of probability distribution Var(X) = E(X²) - [E(X)]²"""
        ev = self.expected_value(values, probabilities)
        ev2 = np.average([v**2 for v in values], weights=probabilities)
        return ev2 - ev**2

    def bayes_theorem(self, p_a_b, p_b, p_a):
        """Bayes' theorem P(A|B) = P(B|A) * P(A) / P(B)"""
        return p_a_b * p_a / p_b

    # ==================== CFA L1: Time Value of Money ====================

    def fv(self, pv, r, n, m=1):
        """Future value FV = PV × (1 + r/m)^(m×n)"""
        return pv * (1 + r/m) ** (m*n)

    def pv(self, fv, r, n, m=1):
        """Present value PV = FV / (1 + r/m)^(m×n)"""
        return fv / (1 + r/m) ** (m*n)

    def annuity_pv(self, pmt, r, n, m=1, due=False):
        """Annuity present value"""
        if r == 0:
            return pmt * n
        i = r / m
        if due:
            return pmt * ((1 - (1 + i)**(-n)) / i) * (1 + i)
        return pmt * (1 - (1 + i)**(-n)) / i

    def annuity_fv(self, pmt, r, n, m=1, due=False):
        """Annuity future value"""
        if r == 0:
            return pmt * n
        i = r / m
        if due:
            return pmt * (((1 + i)**n - 1) / i) * (1 + i)
        return pmt * ((1 + i)**n - 1) / i

    def npv(self, cash_flows, r):
        """Net present value NPV = ΣCFt/(1+r)^t"""
        return sum(cf / (1 + r)**t for t, cf in enumerate(cash_flows))

    def irr(self, cash_flows, guess=0.1):
        """Internal rate of return IRR"""
        return np.irr(cash_flows)

    # ==================== CFA L1-L2: Regression Analysis ====================

    def linear_regression(self, y, x):
        """Simple linear regression y = a + bx"""
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
        """Multiple linear regression (requires pandas)"""
        from scipy.stats import t
        X = np.array(X)
        y = np.array(y)

        # Add constant column
        X = np.column_stack([np.ones(len(y)), X])

        # OLS
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        y_pred = X @ beta

        # Calculate statistics
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

    # ==================== CFA L2: Time Series ====================

    def moving_average(self, data, window):
        """Moving average"""
        return pd.Series(data).rolling(window=window).mean().tolist()

    def exponential_smoothing(self, data, alpha=0.3):
        """Exponential smoothing"""
        return pd.Series(data).ewm(alpha=alpha).mean().tolist()

    # ==================== CFA L1: Financial Ratios ====================

    def get_finance_data(self, market, code):
        """Get financial data"""
        if not self.connected:
            raise Exception("Not connected to server")
        return self.api.get_finance_info(market, code)

    def calc_financial_ratios(self, finance_data):
        """Calculate financial ratios"""
        ratios = {}

        # Valuation ratios
        if 'zongguben' in finance_data and 'jinglirun' in finance_data:
            total_shares = finance_data.get('zongguben', 0)
            net_profit = finance_data.get('jinglirun', 0)
            if total_shares > 0:
                eps = net_profit / total_shares
                ratios['EPS'] = eps

        # Book value per share
        if 'meigujingzichan' in finance_data:
            ratios['BVPS'] = finance_data['meigujingzichan']

        # Equity/Total assets
        if 'jingzichan' in finance_data and 'zongzichan' in finance_data:
            if finance_data['zongzichan'] > 0:
                ratios['Equity_Asset_Ratio'] = finance_data['jingzichan'] / finance_data['zongzichan']

        # Current assets/Current liabilities (if data available)
        if 'liudongzichan' in finance_data and 'liudongfuzhai' in finance_data:
            if finance_data['liudongfuzhai'] > 0:
                ratios['Current_Ratio'] = finance_data['liudongzichan'] / finance_data['liudongfuzhai']

        return ratios

    # ==================== CFA L2-L3: Risk Analysis ====================

    def returns(self, prices):
        """Calculate returns"""
        return pd.Series(prices).pct_change().dropna().tolist()

    def value_at_risk(self, returns, confidence=0.95):
        """VaR (Value at Risk) - Parametric method"""
        mu = np.mean(returns)
        sigma = np.std(returns, ddof=1)
        z = stats.norm.ppf(1 - confidence)
        return mu + z * sigma

    def conditional_var(self, returns, confidence=0.95):
        """CVaR / Expected Shortfall"""
        var = self.value_at_risk(returns, confidence)
        return np.mean(returns[returns <= var])

    def sharpe_ratio(self, returns, risk_free=0.03):
        """Sharpe ratio"""
        rp = np.mean(returns)
        rf = risk_free / 252  # Daily
        sigma = np.std(returns, ddof=1)
        if sigma == 0:
            return 0
        return (rp - rf) / sigma * np.sqrt(252)

    def beta(self, stock_returns, market_returns):
        """Beta coefficient"""
        covariance = np.cov(stock_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        return covariance / market_variance if market_variance > 0 else 1.0

    def volatility(self, returns, annualize=True):
        """Volatility"""
        vol = np.std(returns, ddof=1)
        if annualize:
            return vol * np.sqrt(252)  # Annualized volatility
        return vol

    # ==================== CFA L1: Discounted Cash Flow ====================

    def dcf_value(self, cash_flows, growth_rate, discount_rate, terminal_growth, years=5):
        """DCF valuation"""
        # Forecast period cash flows
        pv_cfs = []
        cf = cash_flows[0] if cash_flows else 0
        for i in range(years):
            cf = cf * (1 + growth_rate)
            pv_cfs.append(cf / (1 + discount_rate)**(i+1))

        # Terminal value
        terminal_value = (cf * (1 + terminal_growth)) / (discount_rate - terminal_growth)
        terminal_pv = terminal_value / (1 + discount_rate)**years

        return {
            'pv_cash_flows': sum(pv_cfs),
            'terminal_value': terminal_value,
            'terminal_pv': terminal_pv,
            'enterprise_value': sum(pv_cfs) + terminal_pv
        }


# Quick functions
def correlation(x, y):
    """Correlation coefficient"""
    return np.corrcoef(x, y)[0, 1]

def std_dev(data):
    """Standard deviation"""
    return np.std(data, ddof=1)

def variance(data):
    """Variance"""
    return np.var(data, ddof=1)


# ==================== Monte Carlo Simulation ====================

def sim(steps=2000, bins=10, seed=2026):
    """
    Monte Carlo stock price path simulator

    Simulate stock price fluctuation paths based on probability distribution

    Args:
        steps: Number of simulation steps (days)
        bins: Number of price intervals
        seed: Random seed

    Returns:
        list: Simulated price time series
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
    Monte Carlo option pricing simulation

    Args:
        current_price: Current price
        volatility: Annualized volatility (default 20%)
        days: Number of simulation days (default 252 trading days)
        simulations: Number of simulations
        seed: Random seed

    Returns:
        array: Simulated final price distribution
    """
    np.random.seed(seed)

    # Generate random returns
    returns = np.random.normal(0, volatility / np.sqrt(days), (simulations, days))

    # Calculate price paths
    price_paths = current_price * np.exp(np.cumsum(returns, axis=1))

    return price_paths[:, -1]  # Return final prices


def black_scholes_call(S, K, T, r, sigma):
    """
    Black-Scholes call option pricing

    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (years)
        r: Risk-free rate
        sigma: Volatility

    Returns:
        float: Option price
    """
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)

    call_price = S * stats.norm.cdf(d1) - K * np.exp(-r*T) * stats.norm.cdf(d2)
    return call_price
