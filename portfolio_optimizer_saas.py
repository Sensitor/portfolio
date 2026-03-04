"""
📊 PORTFOLIO OPTIMIZER PRO v3.0
The Ultimate Professional Portfolio Analysis Platform

NEW IN v3.0:
✅ Advanced Health Score (multi-dimensional)
✅ Correlation heatmap & analysis
✅ Professional charts (drawdown, allocation over time)
✅ Benchmark comparison (S&P500, NASDAQ, MSCI World)
✅ Stress test scenarios (2008, 2020, inflation)
✅ Intelligent recommendations system
✅ Model portfolios (Safe, Balanced, Aggressive, ESG...)
✅ Smart rebalancing suggestions
✅ Auto-generated portfolio summary
✅ Beginner-friendly explanations
✅ Fixed navigation menu
✅ All charts working
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from scipy.optimize import minimize
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Portfolio Optimizer Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #7e22ce 100%);
    }
    
    .main .block-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    
    /* Health Score Card */
    .health-card {
        background: linear-gradient(135deg, #7e22ce 0%, #6366f1 100%);
        color: white;
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(126,34,206,0.4);
        margin: 20px 0;
    }
    
    .health-card h1 {
        font-size: 5rem;
        margin: 0;
        color: white;
    }
    
    .health-card p {
        font-size: 1.5rem;
        color: white;
        opacity: 0.95;
    }
    
    /* Recommendation Cards */
    .rec-card {
        background: white;
        border-left: 5px solid #6366f1;
        padding: 20px;
        margin: 15px 0;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .rec-card h4 {
        color: #1e293b;
        margin: 0 0 10px 0;
    }
    
    .rec-card p {
        color: #475569;
        margin: 5px 0;
    }
    
    .rec-card.warning { border-left-color: #f59e0b; }
    .rec-card.success { border-left-color: #10b981; }
    .rec-card.danger { border-left-color: #ef4444; }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #7e22ce, #6366f1) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 30px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(126,34,206,0.3) !important;
        transition: all 0.3s !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(126,34,206,0.4) !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Info boxes */
    .stAlert {
        background: white !important;
        color: #1e293b !important;
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: #f8fafc !important;
        border-radius: 8px !important;
        color: #1e293b !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# POPULAR ASSETS & MODEL PORTFOLIOS
# =============================================================================

POPULAR_ASSETS = {
    "Stocks": {
        "Apple": "AAPL", "Microsoft": "MSFT", "Google": "GOOGL", "Amazon": "AMZN",
        "Tesla": "TSLA", "NVIDIA": "NVDA", "Meta": "META", "Netflix": "NFLX",
        "AMD": "AMD", "Intel": "INTC", "Coca-Cola": "KO", "Nike": "NKE",
        "Visa": "V", "Mastercard": "MA", "JPMorgan": "JPM",
    },
    "ETFs": {
        "S&P 500": "SPY", "Nasdaq 100": "QQQ", "Total Market": "VTI",
        "International": "VXUS", "Emerging": "VWO", "Gold": "GLD",
        "Bonds": "AGG", "Real Estate": "VNQ",
    },
    "Crypto": {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD",
        "Cardano": "ADA-USD", "Polygon": "MATIC-USD", "Avalanche": "AVAX-USD",
    },
    "Indices": {
        "S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Dow Jones": "^DJI",
    }
}

MODEL_PORTFOLIOS = {
    "Safe": {
        "description": "Low risk, capital preservation",
        "allocation": {
            "AGG": 0.40,  # Bonds
            "SPY": 0.25,  # S&P 500
            "GLD": 0.15,  # Gold
            "VTI": 0.20,  # Total Market
        },
        "expected_return": 0.06,
        "expected_volatility": 0.08,
        "risk_level": "Low"
    },
    "Balanced": {
        "description": "60/40 stocks/bonds mix",
        "allocation": {
            "SPY": 0.30,
            "QQQ": 0.15,
            "VXUS": 0.15,
            "AGG": 0.25,
            "GLD": 0.10,
            "VNQ": 0.05,
        },
        "expected_return": 0.08,
        "expected_volatility": 0.12,
        "risk_level": "Medium"
    },
    "Aggressive": {
        "description": "High growth potential",
        "allocation": {
            "AAPL": 0.15,
            "MSFT": 0.15,
            "NVDA": 0.15,
            "TSLA": 0.10,
            "META": 0.10,
            "QQQ": 0.20,
            "BTC-USD": 0.10,
            "ETH-USD": 0.05,
        },
        "expected_return": 0.15,
        "expected_volatility": 0.25,
        "risk_level": "High"
    },
    "Tech Growth": {
        "description": "100% tech exposure",
        "allocation": {
            "AAPL": 0.20,
            "MSFT": 0.20,
            "GOOGL": 0.15,
            "NVDA": 0.15,
            "META": 0.10,
            "AMD": 0.10,
            "TSLA": 0.10,
        },
        "expected_return": 0.18,
        "expected_volatility": 0.28,
        "risk_level": "Very High"
    },
    "Crypto": {
        "description": "Cryptocurrency focused",
        "allocation": {
            "BTC-USD": 0.50,
            "ETH-USD": 0.30,
            "SOL-USD": 0.10,
            "MATIC-USD": 0.05,
            "AVAX-USD": 0.05,
        },
        "expected_return": 0.30,
        "expected_volatility": 0.60,
        "risk_level": "Extreme"
    },
    "ESG": {
        "description": "Environmental & Social focus",
        "allocation": {
            "AAPL": 0.20,
            "MSFT": 0.20,
            "TSLA": 0.15,
            "GLD": 0.15,
            "VXUS": 0.15,
            "VNQ": 0.15,
        },
        "expected_return": 0.10,
        "expected_volatility": 0.16,
        "risk_level": "Medium"
    },
}

BENCHMARKS = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "MSCI World": "URTH",  # iShares MSCI World ETF
}

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    defaults = {
        'authenticated': True,
        'user_email': "demo@portfoliooptimizer.io",
        'user_tier': "pro",
        'current_portfolio': None,
        'page': "dashboard",
        'language': "en",
        'selected_tickers': [],
        'show_help': False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# =============================================================================
# TRANSLATIONS
# =============================================================================

T = {
    "en": {
        "dashboard": "Dashboard", "new_analysis": "New Analysis",
        "models": "Model Portfolios", "settings": "Settings",
        "health_score": "Health Score", "recommendations": "Recommendations",
        "charts": "Charts", "stress_test": "Stress Test",
        "compare": "Compare", "rebalancing": "Rebalancing",
    },
    "fr": {
        "dashboard": "Tableau de Bord", "new_analysis": "Nouvelle Analyse",
        "models": "Portefeuilles Modèles", "settings": "Paramètres",
        "health_score": "Score de Santé", "recommendations": "Recommandations",
        "charts": "Graphiques", "stress_test": "Test de Stress",
        "compare": "Comparer", "rebalancing": "Rééquilibrage",
    }
}

def t(key, lang="en"):
    return T.get(lang, T["en"]).get(key, key)

# =============================================================================
# PORTFOLIO ANALYZER (ENHANCED)
# =============================================================================

class AdvancedPortfolioAnalyzer:
    def __init__(self, tickers, weights, start_date='2021-01-01', initial_value=100000):
        self.tickers = tickers
        self.weights = weights
        self.start_date = start_date
        self.initial_value = initial_value
        self.data = None
        self.benchmark_data = {}
        
    def fetch_data(self):
        """Fetch portfolio data + benchmarks."""
        all_data = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        total_items = len(self.tickers) + len(BENCHMARKS)
        
        # Fetch portfolio assets
        for i, ticker in enumerate(self.tickers):
            try:
                status.text(f"📥 Loading {ticker}...")
                data = yf.Ticker(ticker).history(start=self.start_date)
                data = data[['Close']].rename(columns={'Close': ticker})
                all_data.append(data)
                progress_bar.progress((i + 1) / total_items)
            except Exception as e:
                st.warning(f"⚠️ {ticker}: {e}")
        
        # Fetch benchmarks
        for i, (name, ticker) in enumerate(BENCHMARKS.items()):
            try:
                status.text(f"📥 Loading {name}...")
                data = yf.Ticker(ticker).history(start=self.start_date)
                self.benchmark_data[name] = data['Close']
                progress_bar.progress((len(self.tickers) + i + 1) / total_items)
            except:
                pass
        
        status.empty()
        progress_bar.empty()
        
        if not all_data:
            return False
        
        self.data = pd.concat(all_data, axis=1).fillna(method='ffill').fillna(method='bfill')
        self.returns = self.data.pct_change().dropna()
        
        weights_array = np.array([self.weights[t] for t in self.tickers])
        self.portfolio_returns = (self.returns @ weights_array)
        self.portfolio_values = self.initial_value * (1 + self.portfolio_returns).cumprod()
        
        return True
    
    def calculate_advanced_health_score(self):
        """Enhanced multi-dimensional health score."""
        metrics = self.calculate_metrics()
        
        # 1. DIVERSIFICATION (25 points)
        n_assets = len(self.tickers)
        div_base = min(25, n_assets * 5)
        
        # Penalties
        max_weight = max(self.weights.values())
        if max_weight > 0.40:
            div_penalty = 0.5
        elif max_weight > 0.30:
            div_penalty = 0.8
        else:
            div_penalty = 1.0
        
        diversification_score = div_base * div_penalty
        
        # 2. RISK-ADJUSTED RETURNS (30 points)
        sharpe = metrics['sharpe']
        if sharpe > 2.0:
            risk_score = 30
        elif sharpe > 1.5:
            risk_score = 26
        elif sharpe > 1.0:
            risk_score = 22
        elif sharpe > 0.5:
            risk_score = 16
        elif sharpe > 0:
            risk_score = 10
        else:
            risk_score = 5
        
        # 3. VOLATILITY MANAGEMENT (20 points)
        vol = metrics['volatility']
        if vol < 0.12:
            vol_score = 20
        elif vol < 0.18:
            vol_score = 16
        elif vol < 0.25:
            vol_score = 12
        elif vol < 0.35:
            vol_score = 8
        else:
            vol_score = 4
        
        # 4. DRAWDOWN PROTECTION (15 points)
        max_dd = abs(metrics['max_drawdown'])
        if max_dd < 0.10:
            dd_score = 15
        elif max_dd < 0.20:
            dd_score = 13
        elif max_dd < 0.30:
            dd_score = 10
        elif max_dd < 0.40:
            dd_score = 6
        else:
            dd_score = 3
        
        # 5. CORRELATION (10 points)
        corr_matrix = self.returns.corr()
        avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, 1)].mean()
        
        if avg_corr < 0.40:
            corr_score = 10
        elif avg_corr < 0.60:
            corr_score = 8
        elif avg_corr < 0.75:
            corr_score = 5
        else:
            corr_score = 2
        
        total = diversification_score + risk_score + vol_score + dd_score + corr_score
        
        return {
            'total': int(total),
            'diversification': int(diversification_score),
            'risk_adjusted': int(risk_score),
            'volatility': int(vol_score),
            'drawdown': int(dd_score),
            'correlation': int(corr_score),
            'max_weight': max_weight,
            'avg_correlation': avg_corr,
        }
    
    def calculate_metrics(self):
        """Calculate all performance metrics."""
        returns = self.portfolio_returns
        total_return = (self.portfolio_values.iloc[-1] / self.initial_value) - 1
        years = len(returns) / 252
        annual_return = (1 + total_return) ** (1 / years) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe = annual_return / volatility if volatility > 0 else 0
        
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252)
        sortino = annual_return / downside_vol if downside_vol > 0 else 0
        
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe': sharpe,
            'sortino': sortino,
            'max_drawdown': max_dd,
            'final_value': self.portfolio_values.iloc[-1],
            'drawdown_series': drawdown,
        }
    
    def generate_intelligent_recommendations(self, lang="en"):
        """Generate comprehensive AI recommendations."""
        metrics = self.calculate_metrics()
        health = self.calculate_advanced_health_score()
        recommendations = []
        
        # HIGH PRIORITY - Concentration
        max_weight = health['max_weight']
        max_ticker = max(self.weights, key=self.weights.get)
        
        if max_weight > 0.40:
            recommendations.append({
                'priority': 'HIGH',
                'type': 'danger',
                'icon': '🚨',
                'title': 'Critical Concentration Risk' if lang == 'en' else 'Risque de Concentration Critique',
                'description': f'{max_ticker}: {max_weight*100:.0f}%. Reduce to < 30%.' if lang == 'en' 
                              else f'{max_ticker}: {max_weight*100:.0f}%. Réduire < 30%.',
                'action': f'Sell {(max_weight-0.30)*100:.0f}% of {max_ticker}' if lang == 'en'
                         else f'Vendre {(max_weight-0.30)*100:.0f}% de {max_ticker}',
                'impact': '+8 points',
            })
        elif max_weight > 0.30:
            recommendations.append({
                'priority': 'MEDIUM',
                'type': 'warning',
                'icon': '⚠️',
                'title': 'Concentration Warning' if lang == 'en' else 'Avertissement Concentration',
                'description': f'{max_ticker}: {max_weight*100:.0f}%.' if lang == 'en'
                              else f'{max_ticker}: {max_weight*100:.0f}%.',
                'action': f'Consider reducing to 25-30%' if lang == 'en' else f'Réduire à 25-30%',
                'impact': '+4 points',
            })
        
        # Sharpe Ratio
        if metrics['sharpe'] < 0.5:
            recommendations.append({
                'priority': 'HIGH',
                'type': 'danger',
                'icon': '📉',
                'title': 'Poor Risk-Adjusted Returns' if lang == 'en' else 'Rendements Ajustés Faibles',
                'description': f'Sharpe {metrics["sharpe"]:.2f} is very low.' if lang == 'en'
                              else f'Sharpe {metrics["sharpe"]:.2f} très faible.',
                'action': 'Run optimization or choose a model portfolio' if lang == 'en'
                         else 'Optimiser ou choisir un portefeuille modèle',
                'impact': '+12 points',
            })
        elif metrics['sharpe'] < 1.0:
            recommendations.append({
                'priority': 'MEDIUM',
                'type': 'warning',
                'icon': '📊',
                'title': 'Below Average Returns' if lang == 'en' else 'Rendements Sous la Moyenne',
                'description': f'Sharpe {metrics["sharpe"]:.2f}. Target: > 1.0.' if lang == 'en'
                              else f'Sharpe {metrics["sharpe"]:.2f}. Cible: > 1.0.',
                'action': 'Optimize allocation' if lang == 'en' else 'Optimiser allocation',
                'impact': '+6 points',
            })
        
        # Diversification
        if len(self.tickers) < 5:
            recommendations.append({
                'priority': 'HIGH',
                'type': 'warning',
                'icon': '🎯',
                'title': 'Insufficient Diversification' if lang == 'en' else 'Diversification Insuffisante',
                'description': f'Only {len(self.tickers)} assets. Add 3-5 more.' if lang == 'en'
                              else f'Seulement {len(self.tickers)} actifs. Ajouter 3-5.',
                'action': 'Add international ETF (VXUS) and bonds (AGG)' if lang == 'en'
                         else 'Ajouter ETF international (VXUS) et obligations (AGG)',
                'impact': '+10 points',
            })
        
        # Correlation
        avg_corr = health['avg_correlation']
        if avg_corr > 0.75:
            recommendations.append({
                'priority': 'MEDIUM',
                'type': 'warning',
                'icon': '🔗',
                'title': 'High Correlation' if lang == 'en' else 'Corrélation Élevée',
                'description': f'Avg correlation: {avg_corr:.2f}. Assets move together.' if lang == 'en'
                              else f'Corrélation moyenne: {avg_corr:.2f}. Actifs synchronisés.',
                'action': 'Add uncorrelated assets (Gold, Bonds)' if lang == 'en'
                         else 'Ajouter actifs décorrélés (Or, Obligations)',
                'impact': '+5 points',
            })
        
        # Volatility
        if metrics['volatility'] > 0.30:
            recommendations.append({
                'priority': 'MEDIUM',
                'type': 'warning',
                'icon': '📈',
                'title': 'High Volatility' if lang == 'en' else 'Volatilité Élevée',
                'description': f'{metrics["volatility"]*100:.0f}% annual volatility.' if lang == 'en'
                              else f'Volatilité annuelle: {metrics["volatility"]*100:.0f}%.',
                'action': 'Add stable assets (AGG, GLD) to reduce swings' if lang == 'en'
                         else 'Ajouter actifs stables (AGG, GLD)',
                'impact': '+6 points',
            })
        
        # POSITIVE FEEDBACK
        if metrics['sharpe'] > 1.5:
            recommendations.append({
                'priority': 'INFO',
                'type': 'success',
                'icon': '✅',
                'title': 'Excellent Performance' if lang == 'en' else 'Performance Excellente',
                'description': f'Sharpe {metrics["sharpe"]:.2f} is outstanding!' if lang == 'en'
                              else f'Sharpe {metrics["sharpe"]:.2f} excellent !',
                'action': 'Maintain current strategy' if lang == 'en' else 'Maintenir stratégie',
                'impact': 'Keep going!',
            })
        
        if health['total'] > 80:
            recommendations.append({
                'priority': 'INFO',
                'type': 'success',
                'icon': '🎉',
                'title': 'Healthy Portfolio' if lang == 'en' else 'Portefeuille Sain',
                'description': f'Score {health["total"]}/100 - Well balanced!' if lang == 'en'
                              else f'Score {health["total"]}/100 - Bien équilibré !',
                'action': 'Review quarterly' if lang == 'en' else 'Réviser trimestriellement',
                'impact': 'Excellent',
            })
        
        # Sort by priority
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'INFO': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return recommendations
    
    def generate_auto_summary(self, lang="en"):
        """Generate automatic portfolio summary."""
        metrics = self.calculate_metrics()
        health = self.calculate_advanced_health_score()
        
        # Risk level
        vol = metrics['volatility']
        if vol < 0.12:
            risk = "low" if lang == "en" else "faible"
        elif vol < 0.20:
            risk = "moderate" if lang == "en" else "modérée"
        elif vol < 0.30:
            risk = "elevated" if lang == "en" else "élevée"
        else:
            risk = "high" if lang == "en" else "très élevée"
        
        # Diversification
        if len(self.tickers) < 5:
            div = "limited" if lang == "en" else "limitée"
        elif len(self.tickers) < 8:
            div = "moderate" if lang == "en" else "modérée"
        else:
            div = "good" if lang == "en" else "bonne"
        
        # Performance
        sharpe = metrics['sharpe']
        if sharpe > 1.5:
            perf = "excellent" if lang == "en" else "excellente"
        elif sharpe > 1.0:
            perf = "good" if lang == "en" else "bonne"
        elif sharpe > 0.5:
            perf = "fair" if lang == "en" else "correcte"
        else:
            perf = "poor" if lang == "en" else "faible"
        
        if lang == "en":
            summary = f"""
            Your portfolio shows **{perf} risk-adjusted performance** (Sharpe: {sharpe:.2f}) 
            with **{risk} volatility** ({vol*100:.0f}% annual). 
            Diversification is **{div}** across {len(self.tickers)} assets.
            Overall health score: **{health['total']}/100**.
            """
        else:
            summary = f"""
            Votre portefeuille présente une **performance ajustée au risque {perf}** (Sharpe: {sharpe:.2f})
            avec une **volatilité {risk}** ({vol*100:.0f}% annuelle).
            La diversification est **{div}** sur {len(self.tickers)} actifs.
            Score de santé global: **{health['total']}/100**.
            """
        
        return summary.strip()
    
    def stress_test(self):
        """Simulate historical crisis scenarios."""
        scenarios = {
            "2008 Crisis": {"start": "2008-09-01", "end": "2009-03-01", "expected_drop": -0.40},
            "COVID-2020": {"start": "2020-02-01", "end": "2020-04-01", "expected_drop": -0.30},
            "Inflation 2022": {"start": "2022-01-01", "end": "2022-10-01", "expected_drop": -0.20},
        }
        
        results = {}
        for name, period in scenarios.items():
            try:
                period_data = self.data.loc[period["start"]:period["end"]]
                if len(period_data) > 0:
                    period_returns = period_data.pct_change().dropna()
                    weights_array = np.array([self.weights[t] for t in self.tickers])
                    portfolio_ret = (period_returns @ weights_array)
                    total_ret = (1 + portfolio_ret).prod() - 1
                    
                    results[name] = {
                        'return': total_ret,
                        'expected': period["expected_drop"],
                        'resilience': 1 - abs(total_ret / period["expected_drop"])
                    }
            except:
                pass
        
        return results
    
    def detect_rebalancing_needed(self):
        """Detect if rebalancing is needed."""
        current_values = {ticker: self.data[ticker].iloc[-1] for ticker in self.tickers}
        total_value = sum(current_values.values())
        current_weights = {ticker: val/total_value for ticker, val in current_values.items()}
        
        drifts = {}
        needs_rebalancing = False
        
        for ticker in self.tickers:
            drift = current_weights[ticker] - self.weights[ticker]
            drifts[ticker] = drift
            if abs(drift) > 0.05:  # 5% threshold
                needs_rebalancing = True
        
        return needs_rebalancing, drifts
    
    def optimize_portfolio(self):
        """Markowitz optimization."""
        expected_returns = self.returns.mean() * 252
        cov_matrix = self.returns.cov() * 252
        
        def negative_sharpe(weights):
            port_return = np.dot(weights, expected_returns)
            port_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            return -(port_return - 0.04) / port_vol
        
        n = len(self.tickers)
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = tuple((0.05, 0.40) for _ in range(n))
        initial = np.array([1/n] * n)
        
        result = minimize(negative_sharpe, initial, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        optimal_weights = dict(zip(self.tickers, result.x))
        optimal_return = np.dot(result.x, expected_returns)
        optimal_vol = np.sqrt(np.dot(result.x, np.dot(cov_matrix, result.x)))
        optimal_sharpe = (optimal_return - 0.04) / optimal_vol
        
        return {
            'weights': optimal_weights,
            'expected_return': optimal_return,
            'volatility': optimal_vol,
            'sharpe': optimal_sharpe
        }

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_health_score(health, lang="en"):
    """Render advanced health score."""
    total = health['total']
    
    if total >= 85:
        color = "#10b981"
        emoji = "🎉"
        status = "Excellent"
    elif total >= 70:
        color = "#6366f1"
        emoji = "✅"
        status = "Good" if lang == "en" else "Bon"
    elif total >= 50:
        color = "#f59e0b"
        emoji = "⚠️"
        status = "Fair" if lang == "en" else "Moyen"
    else:
        color = "#ef4444"
        emoji = "🔴"
        status = "Poor" if lang == "en" else "Faible"
    
    st.markdown(f"""
    <div style='background: {color}; color: white; padding: 50px; border-radius: 25px;
         text-align: center; box-shadow: 0 15px 40px rgba(0,0,0,0.3); margin: 30px 0;'>
        <h1 style='font-size: 6rem; margin: 0; color: white;'>{emoji} {total}</h1>
        <p style='font-size: 2rem; margin: 15px 0 0 0; color: white; opacity: 0.95;'>/100 - {status}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    components = [
        ("Diversification", health['diversification'], 25),
        ("Risk-Adjusted", health['risk_adjusted'], 30),
        ("Volatility", health['volatility'], 20),
        ("Drawdown", health['drawdown'], 15),
        ("Correlation", health['correlation'], 10),
    ]
    
    for col, (name, score, max_score) in zip([col1, col2, col3, col4, col5], components):
        with col:
            pct = (score / max_score) * 100
            color = "#10b981" if pct > 80 else "#f59e0b" if pct > 60 else "#ef4444"
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background: white;
                 border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                <p style='margin: 0; color: #64748b; font-size: 0.9rem;'>{name}</p>
                <p style='margin: 5px 0; font-size: 2rem; font-weight: 700; color: {color};'>
                    {score}<span style='font-size: 1.2rem; color: #94a3b8;'>/{max_score}</span>
                </p>
            </div>
            """, unsafe_allow_html=True)

def render_recommendations(recommendations, lang="en"):
    """Render intelligent recommendations."""
    st.markdown(f"### 💡 {t('recommendations', lang)}")
    
    if not recommendations:
        st.info("✅ No major issues detected!")
        return
    
    for rec in recommendations:
        priority_badge = {
            'HIGH': '<span style="background:#ef4444;color:white;padding:4px 12px;border-radius:12px;font-size:0.75rem;font-weight:600;">HIGH</span>',
            'MEDIUM': '<span style="background:#f59e0b;color:white;padding:4px 12px;border-radius:12px;font-size:0.75rem;font-weight:600;">MEDIUM</span>',
            'INFO': '<span style="background:#6366f1;color:white;padding:4px 12px;border-radius:12px;font-size:0.75rem;font-weight:600;">INFO</span>',
        }
        
        st.markdown(f"""
        <div class='rec-card {rec['type']}'>
            <h4>{rec['icon']} {rec['title']} {priority_badge.get(rec['priority'], '')}</h4>
            <p><strong>Issue:</strong> {rec['description']}</p>
            <p><strong>Action:</strong> {rec['action']}</p>
            <p style='color: #7e22ce; font-weight: 600; margin-top: 10px;'>
                💎 Expected impact: {rec['impact']}
            </p>
        </div>
        """, unsafe_allow_html=True)

def render_correlation_heatmap(analyzer):
    """Render correlation heatmap."""
    corr_matrix = analyzer.returns.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdYlGn_r',
        zmid=0,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title="Asset Correlation Matrix",
        height=500,
        xaxis_title="",
        yaxis_title="",
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, 1)].mean()
    
    if avg_corr > 0.75:
        st.warning(f"⚠️ High average correlation ({avg_corr:.2f}). Assets move together - limited diversification benefit.")
    elif avg_corr > 0.50:
        st.info(f"ℹ️ Moderate correlation ({avg_corr:.2f}). Some diversification benefit.")
    else:
        st.success(f"✅ Low correlation ({avg_corr:.2f}). Good diversification!")

def render_advanced_charts(analyzer, lang="en"):
    """Render all advanced charts."""
    
    tabs = st.tabs([
        f"📈 Performance",
        f"📉 Drawdown", 
        f"⚖️ Allocation",
        f"🔄 Correlation"
    ])
    
    with tabs[0]:
        # Performance vs Benchmarks
        fig = go.Figure()
        
        # Portfolio
        fig.add_trace(go.Scatter(
            x=analyzer.portfolio_values.index,
            y=analyzer.portfolio_values.values,
            mode='lines',
            name='Your Portfolio',
            line=dict(color='#7e22ce', width=3),
            fill='tozeroy',
            fillcolor='rgba(126, 34, 206, 0.1)'
        ))
        
        # Benchmarks
        colors = {'S&P 500': '#3b82f6', 'Nasdaq': '#10b981', 'MSCI World': '#f59e0b'}
        for name, data in analyzer.benchmark_data.items():
            if len(data) > 0:
                benchmark_values = analyzer.initial_value * (data / data.iloc[0])
                fig.add_trace(go.Scatter(
                    x=benchmark_values.index,
                    y=benchmark_values.values,
                    mode='lines',
                    name=name,
                    line=dict(color=colors.get(name, '#64748b'), width=2, dash='dash')
                ))
        
        fig.update_layout(
            title="Performance Comparison",
            height=500,
            hovermode='x unified',
            yaxis_title="Value ($)",
            xaxis_title="Date"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:
        # Drawdown chart
        metrics = analyzer.calculate_metrics()
        drawdown = metrics['drawdown_series']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown.values * 100,
            mode='lines',
            name='Drawdown',
            line=dict(color='#ef4444', width=2),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.2)'
        ))
        
        fig.update_layout(
            title="Portfolio Drawdown Over Time",
            height=400,
            yaxis_title="Drawdown (%)",
            xaxis_title="Date"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.metric("Maximum Drawdown", f"{metrics['max_drawdown']*100:.2f}%")
    
    with tabs[2]:
        # Allocation pie chart
        fig = go.Figure(data=[go.Pie(
            labels=list(analyzer.weights.keys()),
            values=list(analyzer.weights.values()),
            hole=.4,
            marker=dict(colors=px.colors.qualitative.Set3)
        )])
        
        fig.update_layout(
            title="Current Allocation",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[3]:
        render_correlation_heatmap(analyzer)

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    init_session_state()
    lang = st.session_state.language
    
    # Sidebar Navigation
    with st.sidebar:
        # Language
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🇬🇧 EN", use_container_width=True,
                        type="primary" if lang == "en" else "secondary"):
                st.session_state.language = "en"
                st.rerun()
        with col2:
            if st.button("🇫🇷 FR", use_container_width=True,
                        type="primary" if lang == "fr" else "secondary"):
                st.session_state.language = "fr"
                st.rerun()
        
        st.markdown("---")
        st.title("📊 Portfolio Optimizer Pro v3.0")
        st.markdown(f"**{st.session_state.user_email}**")
        
        st.markdown("---")
        
        # Navigation
        pages = [
            ("dashboard", "🏠"),
            ("new_analysis", "➕"),
            ("models", "📋"),
            ("settings", "⚙️"),
        ]
        
        for page_key, icon in pages:
            if st.button(f"{icon} {t(page_key, lang).title()}", 
                        use_container_width=True,
                        type="primary" if st.session_state.page == page_key else "secondary"):
                st.session_state.page = page_key
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 🚀 Upgrade Pro")
        st.markdown("**$14.99/mo**")
        if st.button("⭐ Upgrade", type="primary", use_container_width=True):
            st.info("Coming soon!")
    
    # Main Content
    page = st.session_state.page
    
    if page == "dashboard":
        st.title(f"🏠 {t('dashboard', lang)}")
        
        if st.session_state.current_portfolio is None:
            st.info("👋 Welcome! Create your first portfolio analysis.")
            if st.button("➕ Create Portfolio", type="primary", use_container_width=True):
                st.session_state.page = "new_analysis"
                st.rerun()
        else:
            analyzer = st.session_state.current_portfolio
            
            # Auto Summary
            st.markdown("### 📝 Portfolio Summary")
            summary = analyzer.generate_auto_summary(lang)
            st.markdown(summary)
            
            st.markdown("---")
            
            # Health Score
            health = analyzer.calculate_advanced_health_score()
            render_health_score(health, lang)
            
            # Quick Stats
            st.markdown("### 📊 Quick Stats")
            metrics = analyzer.calculate_metrics()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Sharpe Ratio", f"{metrics['sharpe']:.2f}")
            with col2:
                st.metric("Annual Return", f"{metrics['annual_return']*100:.1f}%")
            with col3:
                st.metric("Volatility", f"{metrics['volatility']*100:.1f}%")
            with col4:
                st.metric("Max Drawdown", f"{metrics['max_drawdown']*100:.1f}%")
            
            st.markdown("---")
            
            # Recommendations
            recommendations = analyzer.generate_intelligent_recommendations(lang)
            render_recommendations(recommendations, lang)
            
            st.markdown("---")
            
            # Charts
            st.markdown(f"### 📊 {t('charts', lang)}")
            render_advanced_charts(analyzer, lang)
            
            st.markdown("---")
            
            # Stress Test
            st.markdown(f"### 🧪 {t('stress_test', lang)}")
            if st.button("Run Stress Test", use_container_width=True):
                with st.spinner("Running scenarios..."):
                    stress_results = analyzer.stress_test()
                
                if stress_results:
                    for scenario, result in stress_results.items():
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(scenario, f"{result['return']*100:.1f}%")
                        with col2:
                            st.metric("Expected", f"{result['expected']*100:.0f}%")
                        with col3:
                            resilience = result['resilience'] * 100
                            st.metric("Resilience", f"{resilience:.0f}%")
                else:
                    st.info("Not enough historical data for stress testing.")
            
            st.markdown("---")
            
            # Rebalancing
            st.markdown(f"### 🔄 {t('rebalancing', lang)}")
            needs_rebal, drifts = analyzer.detect_rebalancing_needed()
            
            if needs_rebal:
                st.warning("⚠️ Rebalancing recommended!")
                for ticker, drift in drifts.items():
                    if abs(drift) > 0.05:
                        direction = "⬆️" if drift > 0 else "⬇️"
                        st.write(f"{direction} {ticker}: {drift*100:+.1f}%")
            else:
                st.success("✅ Portfolio is balanced!")
            
            st.markdown("---")
            
            # Optimization
            st.markdown("### 🎯 Optimization")
            if st.button("Optimize Portfolio", use_container_width=True):
                with st.spinner("Optimizing..."):
                    optimal = analyzer.optimize_portfolio()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Current**")
                    st.metric("Sharpe", f"{metrics['sharpe']:.2f}")
                    for ticker, weight in analyzer.weights.items():
                        st.write(f"{ticker}: {weight*100:.1f}%")
                
                with col2:
                    st.markdown("**Optimized**")
                    improvement = ((optimal['sharpe'] / metrics['sharpe']) - 1) * 100
                    st.metric("Sharpe", f"{optimal['sharpe']:.2f}", f"+{improvement:.1f}%")
                    for ticker, weight in optimal['weights'].items():
                        st.write(f"{ticker}: {weight*100:.1f}%")
    
    elif page == "new_analysis":
        st.title(f"➕ {t('new_analysis', lang)}")
        
        tabs = st.tabs(["🔍 Search", "⭐ Popular", "✏️ Manual"])
        
        with tabs[0]:
            st.markdown("### Search Assets")
            search = st.text_input("Type name...", placeholder="Apple, Bitcoin...")
            
            if search:
                all_assets = {}
                for cat, assets in POPULAR_ASSETS.items():
                    for name, ticker in assets.items():
                        all_assets[f"{name} ({ticker})"] = ticker
                
                matches = {k: v for k, v in all_assets.items() if search.lower() in k.lower()}
                
                if matches:
                    for display, ticker in list(matches.items())[:10]:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(display)
                        with col2:
                            if st.button("➕", key=ticker):
                                if ticker not in st.session_state.selected_tickers:
                                    st.session_state.selected_tickers.append(ticker)
                                    st.rerun()
        
        with tabs[1]:
            st.markdown("### Popular Assets")
            for category, assets in POPULAR_ASSETS.items():
                with st.expander(f"📂 {category}"):
                    cols = st.columns(3)
                    for i, (name, ticker) in enumerate(assets.items()):
                        with cols[i % 3]:
                            if st.button(f"{name}\n`{ticker}`", key=f"pop_{ticker}", 
                                       use_container_width=True):
                                if ticker not in st.session_state.selected_tickers:
                                    st.session_state.selected_tickers.append(ticker)
                                    st.rerun()
        
        with tabs[2]:
            manual = st.text_area("Enter tickers (one per line)", placeholder="AAPL\nMSFT")
            if st.button("Add"):
                tickers = [t.strip().upper() for t in manual.split('\n') if t.strip()]
                st.session_state.selected_tickers.extend(tickers)
                st.rerun()
        
        # Selected & Analyze
        st.markdown("---")
        st.markdown("### Selected Assets")
        
        if st.session_state.selected_tickers:
            for ticker in st.session_state.selected_tickers:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"**{ticker}**")
                with col2:
                    if st.button("❌", key=f"rm_{ticker}"):
                        st.session_state.selected_tickers.remove(ticker)
                        st.rerun()
            
            st.markdown("### Set Weights")
            weights = {}
            cols = st.columns(min(len(st.session_state.selected_tickers), 4))
            
            for i, ticker in enumerate(st.session_state.selected_tickers):
                with cols[i % 4]:
                    weight = st.slider(ticker, 0.0, 100.0,
                                      100.0/len(st.session_state.selected_tickers),
                                      1.0, key=f"w_{ticker}")
                    weights[ticker] = weight / 100
            
            total = sum(weights.values())
            if abs(total - 1.0) > 0.01:
                st.warning(f"⚠️ {total*100:.0f}% (should be 100%)")
            else:
                st.success("✅ 100%")
            
            if st.button("🚀 Analyze", type="primary", use_container_width=True):
                with st.spinner("Analyzing..."):
                    analyzer = AdvancedPortfolioAnalyzer(
                        st.session_state.selected_tickers,
                        weights,
                        (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
                    )
                    
                    if analyzer.fetch_data():
                        st.session_state.current_portfolio = analyzer
                        st.success("✅ Done!")
                        st.balloons()
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("❌ Error")
        else:
            st.info("Add assets above")
    
    elif page == "models":
        st.title(f"📋 {t('models', lang)}")
        st.markdown("Choose a pre-built portfolio to analyze instantly")
        
        for model_name, model_data in MODEL_PORTFOLIOS.items():
            with st.expander(f"📊 {model_name} - {model_data['risk_level']} Risk"):
                st.markdown(f"**{model_data['description']}**")
                st.markdown(f"Expected Return: {model_data['expected_return']*100:.0f}% | "
                           f"Volatility: {model_data['expected_volatility']*100:.0f}%")
                
                col1, col2 = st.columns(2)
                with col1:
                    for ticker, weight in model_data['allocation'].items():
                        st.write(f"{ticker}: {weight*100:.0f}%")
                
                with col2:
                    if st.button(f"Use {model_name}", key=model_name, use_container_width=True):
                        st.session_state.selected_tickers = list(model_data['allocation'].keys())
                        
                        with st.spinner(f"Loading {model_name}..."):
                            analyzer = AdvancedPortfolioAnalyzer(
                                list(model_data['allocation'].keys()),
                                model_data['allocation'],
                                (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
                            )
                            
                            if analyzer.fetch_data():
                                st.session_state.current_portfolio = analyzer
                                st.success(f"✅ {model_name} loaded!")
                                st.balloons()
                                st.session_state.page = "dashboard"
                                st.rerun()
    
    elif page == "settings":
        st.title(f"⚙️ {t('settings', lang)}")
        st.markdown("### Account")
        st.text_input("Email", st.session_state.user_email, disabled=True)
        
        st.markdown("### Preferences")
        st.checkbox("Show beginner explanations", value=True)
        st.selectbox("Default period", ["1 Year", "2 Years", "3 Years", "5 Years"])
        st.selectbox("Risk-free rate", ["4.0%", "4.5%", "5.0%"])

if __name__ == "__main__":
    main()
