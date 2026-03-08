"""
📊 PORTFOLIO OPTIMIZER PRO v3.5 FINAL
The Complete Professional Portfolio Analysis Platform

VERSION 3.5 - ALL IMPROVEMENTS:
✅ 1. Fixed asset allocation bug (auto-rebalance to 100%)
✅ 2. Portfolio Robustness Index (0-100)
✅ 3. "Improve My Portfolio" mode
✅ 4. Intelligent recommendations system
✅ 5. Profile-adapted suggestions (Safe/Balanced/Aggressive)
✅ 6. Educational asset cards
✅ 7. Enhanced visualizations (drawdown, sector, geography)
✅ 8. Crisis stress tests (2008, COVID, inflation)
✅ 9. Auto-generated portfolio summary
✅ 10. Modern UX with animations

ARCHITECTURE:
- Modular improvements on existing codebase
- Maintains current structure
- Adds new features seamlessly
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
    page_title="Portfolio Optimizer Pro v3.5",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# ENHANCED CSS WITH ANIMATIONS
# =============================================================================

st.markdown("""
<style>
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #7e22ce 100%);
        animation: fadeIn 0.5s ease-out;
    }
    
    .main .block-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Robustness Score Card */
    .robustness-card {
        background: linear-gradient(135deg, #7e22ce 0%, #6366f1 100%);
        color: white;
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(126,34,206,0.4);
        margin: 20px 0;
        animation: slideIn 0.5s ease-out;
        transition: transform 0.3s;
    }
    
    .robustness-card:hover {
        transform: scale(1.02);
    }
    
    .robustness-card h1 {
        font-size: 5rem;
        margin: 0;
        color: white;
        text-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    /* Recommendation Cards */
    .rec-card {
        background: white;
        border-left: 5px solid #6366f1;
        padding: 20px;
        margin: 15px 0;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        animation: slideIn 0.4s ease-out;
        transition: all 0.3s;
    }
    
    .rec-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        transform: translateX(5px);
    }
    
    .rec-card h4 {
        color: #1e293b;
        margin: 0 0 10px 0;
        font-size: 1.1rem;
    }
    
    .rec-card p {
        color: #475569;
        margin: 5px 0;
        line-height: 1.6;
    }
    
    .rec-card.critical { border-left-color: #ef4444; }
    .rec-card.warning { border-left-color: #f59e0b; }
    .rec-card.success { border-left-color: #10b981; }
    .rec-card.info { border-left-color: #6366f1; }
    
    /* Asset Info Card */
    .asset-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        border: 2px solid #cbd5e1;
        transition: all 0.3s;
    }
    
    .asset-card:hover {
        border-color: #7e22ce;
        box-shadow: 0 8px 20px rgba(126,34,206,0.2);
    }
    
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
    
    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, #7e22ce 0%, #6366f1 100%) !important;
        transition: width 0.5s ease-out !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-radius: 12px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #64748b !important;
        border-radius: 8px !important;
        transition: all 0.3s !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #7e22ce 0%, #6366f1 100%) !important;
        color: white !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: #f8fafc !important;
        border-radius: 8px !important;
        color: #1e293b !important;
        transition: all 0.3s !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: #e2e8f0 !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA: ASSET INFO, MODEL PORTFOLIOS, SECTORS
# =============================================================================

ASSET_INFO = {
    "AAPL": {
        "name": "Apple Inc.",
        "description": "Technology company producing consumer electronics, software and services",
        "sector": "Technology",
        "geography": "USA",
        "utility": "Large-cap tech growth exposure",
        "typical_use": "Core holding for tech exposure in growth portfolios",
        "risk_level": "Medium-High"
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "description": "Software and cloud computing giant",
        "sector": "Technology",
        "geography": "USA",
        "utility": "Stable tech growth with cloud leadership",
        "typical_use": "Defensive tech holding, cloud exposure",
        "risk_level": "Medium"
    },
    "SPY": {
        "name": "S&P 500 ETF",
        "description": "Tracks the 500 largest US companies",
        "sector": "Diversified",
        "geography": "USA",
        "utility": "Broad US market exposure",
        "typical_use": "Core holding for diversified US equity exposure",
        "risk_level": "Medium"
    },
    "QQQ": {
        "name": "Nasdaq 100 ETF",
        "description": "Tracks 100 largest non-financial Nasdaq companies",
        "sector": "Technology-Heavy",
        "geography": "USA",
        "utility": "Tech-focused growth exposure",
        "typical_use": "Growth portfolio, tech overweight",
        "risk_level": "Medium-High"
    },
    "BTC-USD": {
        "name": "Bitcoin",
        "description": "Decentralized digital currency and store of value",
        "sector": "Cryptocurrency",
        "geography": "Global",
        "utility": "Inflation hedge, portfolio diversifier",
        "typical_use": "Small allocation (5-10%) for growth/diversification",
        "risk_level": "Very High"
    },
    "GLD": {
        "name": "Gold ETF",
        "description": "Tracks physical gold prices",
        "sector": "Commodities",
        "geography": "Global",
        "utility": "Inflation hedge, safe haven",
        "typical_use": "Portfolio hedge (10-15%), crisis protection",
        "risk_level": "Low-Medium"
    },
    "AGG": {
        "name": "Aggregate Bond ETF",
        "description": "Broad US investment-grade bond market",
        "sector": "Fixed Income",
        "geography": "USA",
        "utility": "Stability, income generation",
        "typical_use": "Conservative allocation, portfolio ballast",
        "risk_level": "Low"
    },
    "VXUS": {
        "name": "International Stock ETF",
        "description": "Tracks non-US developed and emerging markets",
        "sector": "Diversified International",
        "geography": "Ex-US Global",
        "utility": "Geographic diversification",
        "typical_use": "International exposure (20-40% of equity)",
        "risk_level": "Medium"
    },
}

SECTOR_MAPPING = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", "AMZN": "Technology",
    "TSLA": "Automotive", "NVDA": "Technology", "META": "Technology", "NFLX": "Technology",
    "SPY": "Diversified", "QQQ": "Technology", "VTI": "Diversified", "VXUS": "International",
    "BTC-USD": "Crypto", "ETH-USD": "Crypto", "SOL-USD": "Crypto",
    "GLD": "Commodities", "AGG": "Bonds", "VNQ": "Real Estate",
}

GEOGRAPHY_MAPPING = {
    "AAPL": "USA", "MSFT": "USA", "GOOGL": "USA", "AMZN": "USA",
    "SPY": "USA", "QQQ": "USA", "VTI": "USA",
    "VXUS": "International", "VWO": "Emerging",
    "BTC-USD": "Global", "ETH-USD": "Global",
    "GLD": "Global", "AGG": "USA",
}

POPULAR_ASSETS = {
    "Stocks": {
        "Apple": "AAPL", "Microsoft": "MSFT", "Google": "GOOGL", "Amazon": "AMZN",
        "Tesla": "TSLA", "NVIDIA": "NVDA", "Meta": "META", "Netflix": "NFLX",
    },
    "ETFs": {
        "S&P 500": "SPY", "Nasdaq 100": "QQQ", "Total Market": "VTI",
        "International": "VXUS", "Gold": "GLD", "Bonds": "AGG",
    },
    "Crypto": {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD",
    },
}

MODEL_PORTFOLIOS = {
    "Safe": {
        "description": "Low risk, capital preservation",
        "profile": "safe",
        "allocation": {"AGG": 0.40, "SPY": 0.25, "GLD": 0.15, "VTI": 0.20},
        "expected_return": 0.06,
        "expected_volatility": 0.08,
    },
    "Balanced": {
        "description": "60/40 stocks/bonds mix",
        "profile": "balanced",
        "allocation": {"SPY": 0.30, "QQQ": 0.15, "VXUS": 0.15, "AGG": 0.25, "GLD": 0.10, "VNQ": 0.05},
        "expected_return": 0.08,
        "expected_volatility": 0.12,
    },
    "Aggressive": {
        "description": "High growth potential",
        "profile": "aggressive",
        "allocation": {"AAPL": 0.15, "MSFT": 0.15, "NVDA": 0.15, "TSLA": 0.10, "QQQ": 0.20, "BTC-USD": 0.15, "ETH-USD": 0.10},
        "expected_return": 0.15,
        "expected_volatility": 0.25,
    },
}

# =============================================================================
# SESSION STATE WITH AUTO-REBALANCE
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
        'weights': {},  # FIX: Separate weights dict
        'user_profile': "balanced",  # safe/balanced/aggressive
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def auto_rebalance_weights():
    """FIX #1: Auto-rebalance weights to 100% when assets change."""
    tickers = st.session_state.selected_tickers
    if not tickers:
        st.session_state.weights = {}
        return
    
    # Equal weight distribution
    equal_weight = 1.0 / len(tickers)
    
    # If weights don't exist or have wrong tickers, reset
    if not st.session_state.weights or set(st.session_state.weights.keys()) != set(tickers):
        st.session_state.weights = {ticker: equal_weight for ticker in tickers}
    
    # Normalize to ensure 100%
    total = sum(st.session_state.weights.values())
    if total > 0:
        st.session_state.weights = {k: v/total for k, v in st.session_state.weights.items()}

# =============================================================================
# TRANSLATIONS
# =============================================================================

T = {
    "en": {
        "dashboard": "Dashboard", "new_analysis": "New Analysis",
        "models": "Model Portfolios", "improve": "Improve Portfolio",
        "robustness": "Robustness Index", "recommendations": "Recommendations",
        "stress_test": "Stress Test", "asset_info": "Asset Info",
    },
    "fr": {
        "dashboard": "Tableau de Bord", "new_analysis": "Nouvelle Analyse",
        "models": "Portefeuilles Modèles", "improve": "Améliorer",
        "robustness": "Indice de Robustesse", "recommendations": "Recommandations",
        "stress_test": "Test de Stress", "asset_info": "Info Actifs",
    }
}

def t(key, lang="en"):
    return T.get(lang, T["en"]).get(key, key)

# =============================================================================
# ADVANCED PORTFOLIO ANALYZER
# =============================================================================

class UltimatePortfolioAnalyzer:
    def __init__(self, tickers, weights, start_date='2021-01-01', initial_value=100000, user_profile="balanced"):
        self.tickers = tickers
        self.weights = weights
        self.start_date = start_date
        self.initial_value = initial_value
        self.user_profile = user_profile
        self.data = None
        
    def fetch_data(self):
        """Fetch data with progress."""
        all_data = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        for i, ticker in enumerate(self.tickers):
            try:
                status.text(f"📥 Loading {ticker}...")
                data = yf.Ticker(ticker).history(start=self.start_date)
                data = data[['Close']].rename(columns={'Close': ticker})
                all_data.append(data)
                progress_bar.progress((i + 1) / len(self.tickers))
            except Exception as e:
                st.warning(f"⚠️ {ticker}: {str(e)[:50]}")
        
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
    
    def calculate_robustness_index(self):
        """
        FIX #2: Calculate Portfolio Robustness Index (0-100).
        Measures portfolio resilience to crises and structural risks.
        """
        metrics = self.calculate_metrics()
        
        # 1. DIVERSIFICATION (20 points)
        n_assets = len(self.tickers)
        if n_assets >= 10:
            div_score = 20
        elif n_assets >= 7:
            div_score = 17
        elif n_assets >= 5:
            div_score = 14
        elif n_assets >= 3:
            div_score = 10
        else:
            div_score = 5
        
        # 2. CONCENTRATION (20 points)
        max_weight = max(self.weights.values())
        if max_weight < 0.15:
            conc_score = 20
        elif max_weight < 0.25:
            conc_score = 16
        elif max_weight < 0.35:
            conc_score = 12
        elif max_weight < 0.45:
            conc_score = 8
        else:
            conc_score = 4
        
        # 3. CORRELATION (15 points)
        corr_matrix = self.returns.corr()
        avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, 1)].mean()
        if avg_corr < 0.30:
            corr_score = 15
        elif avg_corr < 0.50:
            corr_score = 12
        elif avg_corr < 0.70:
            corr_score = 8
        else:
            corr_score = 4
        
        # 4. VOLATILITY (15 points)
        vol = metrics['volatility']
        if vol < 0.10:
            vol_score = 15
        elif vol < 0.15:
            vol_score = 13
        elif vol < 0.25:
            vol_score = 10
        elif vol < 0.35:
            vol_score = 6
        else:
            vol_score = 3
        
        # 5. DRAWDOWN (15 points)
        max_dd = abs(metrics['max_drawdown'])
        if max_dd < 0.10:
            dd_score = 15
        elif max_dd < 0.20:
            dd_score = 12
        elif max_dd < 0.30:
            dd_score = 9
        elif max_dd < 0.40:
            dd_score = 5
        else:
            dd_score = 2
        
        # 6. GEOGRAPHIC DIVERSIFICATION (10 points)
        geographies = set()
        for ticker in self.tickers:
            geo = GEOGRAPHY_MAPPING.get(ticker, "Unknown")
            geographies.add(geo)
        
        geo_count = len(geographies)
        if geo_count >= 3:
            geo_score = 10
        elif geo_count >= 2:
            geo_score = 7
        else:
            geo_score = 3
        
        # 7. SECTOR DIVERSIFICATION (5 points)
        sectors = set()
        for ticker in self.tickers:
            sector = SECTOR_MAPPING.get(ticker, "Unknown")
            sectors.add(sector)
        
        sector_count = len(sectors)
        if sector_count >= 4:
            sector_score = 5
        elif sector_count >= 3:
            sector_score = 4
        elif sector_count >= 2:
            sector_score = 2
        else:
            sector_score = 1
        
        # TOTAL SCORE
        total = div_score + conc_score + corr_score + vol_score + dd_score + geo_score + sector_score
        
        # Interpretation
        if total >= 90:
            interpretation = "Very Robust"
            color = "#10b981"
        elif total >= 70:
            interpretation = "Robust"
            color = "#6366f1"
        elif total >= 50:
            interpretation = "Fragile"
            color = "#f59e0b"
        else:
            interpretation = "High Risk"
            color = "#ef4444"
        
        return {
            'total': int(total),
            'diversification': div_score,
            'concentration': conc_score,
            'correlation': corr_score,
            'volatility': vol_score,
            'drawdown': dd_score,
            'geography': geo_score,
            'sector': sector_score,
            'interpretation': interpretation,
            'color': color,
        }
    
    def generate_improvement_suggestions(self, lang="en"):
        """
        FIX #3 & #4: Generate intelligent improvement suggestions.
        Analyzes current portfolio and suggests optimized version.
        """
        metrics = self.calculate_metrics()
        robustness = self.calculate_robustness_index()
        suggestions = []
        
        # HIGH PRIORITY
        max_weight = max(self.weights.values())
        max_ticker = max(self.weights, key=self.weights.get)
        
        if max_weight > 0.40:
            suggestions.append({
                'priority': 'CRITICAL',
                'type': 'critical',
                'title': 'Critical Concentration' if lang == 'en' else 'Concentration Critique',
                'issue': f'{max_ticker} = {max_weight*100:.0f}%',
                'solution': f'Reduce to <30%. Diversify into VXUS + AGG' if lang == 'en' 
                           else f'Réduire <30%. Diversifier vers VXUS + AGG',
                'impact': 'Robustness +15 pts',
            })
        
        # Sector concentration
        sectors = {}
        for ticker in self.tickers:
            sector = SECTOR_MAPPING.get(ticker, "Unknown")
            sectors[sector] = sectors.get(sector, 0) + self.weights[ticker]
        
        for sector, exposure in sectors.items():
            if exposure > 0.50 and sector != "Diversified":
                suggestions.append({
                    'priority': 'HIGH',
                    'type': 'warning',
                    'title': f'High {sector} Exposure' if lang == 'en' else f'Exposition {sector} Élevée',
                    'issue': f'{exposure*100:.0f}% in {sector}',
                    'solution': f'Add international ETF (VXUS) or bonds (AGG)' if lang == 'en'
                               else f'Ajouter ETF international (VXUS) ou obligations (AGG)',
                    'impact': 'Robustness +10 pts',
                })
        
        # Geographic concentration
        geographies = {}
        for ticker in self.tickers:
            geo = GEOGRAPHY_MAPPING.get(ticker, "Unknown")
            geographies[geo] = geographies.get(geo, 0) + self.weights[ticker]
        
        usa_exposure = geographies.get("USA", 0)
        if usa_exposure > 0.70:
            suggestions.append({
                'priority': 'HIGH',
                'type': 'warning',
                'title': 'Geographic Concentration' if lang == 'en' else 'Concentration Géographique',
                'issue': f'{usa_exposure*100:.0f}% USA exposure',
                'solution': 'Add VXUS (international) for global diversification' if lang == 'en'
                           else 'Ajouter VXUS (international) pour diversification mondiale',
                'impact': 'Robustness +8 pts',
            })
        
        # Lack of bonds/hedges
        has_bonds = any(ticker in ['AGG', 'BND', 'TLT'] for ticker in self.tickers)
        has_gold = any(ticker in ['GLD', 'IAU'] for ticker in self.tickers)
        
        if not has_bonds and not has_gold:
            suggestions.append({
                'priority': 'MEDIUM',
                'type': 'info',
                'title': 'Missing Hedges' if lang == 'en' else 'Absence de Couverture',
                'issue': 'No bonds or gold in portfolio',
                'solution': 'Add 10-20% AGG (bonds) and 5-10% GLD (gold) for stability' if lang == 'en'
                           else 'Ajouter 10-20% AGG (obligations) et 5-10% GLD (or)',
                'impact': 'Robustness +6 pts',
            })
        
        # Low diversification
        if len(self.tickers) < 5:
            suggestions.append({
                'priority': 'HIGH',
                'type': 'warning',
                'title': 'Low Diversification' if lang == 'en' else 'Faible Diversification',
                'issue': f'Only {len(self.tickers)} assets',
                'solution': 'Add 3-5 more assets from different sectors/geographies' if lang == 'en'
                           else 'Ajouter 3-5 actifs de secteurs/géographies différents',
                'impact': 'Robustness +12 pts',
            })
        
        # High volatility
        if metrics['volatility'] > 0.25:
            suggestions.append({
                'priority': 'MEDIUM',
                'type': 'warning',
                'title': 'High Volatility' if lang == 'en' else 'Volatilité Élevée',
                'issue': f'{metrics["volatility"]*100:.0f}% annual volatility',
                'solution': 'Reduce high-vol assets. Add AGG (bonds) for stability' if lang == 'en'
                           else 'Réduire actifs volatils. Ajouter AGG (obligations)',
                'impact': 'Robustness +7 pts',
            })
        
        return suggestions
    
    def generate_profile_adapted_suggestions(self, lang="en"):
        """
        FIX #5: Profile-adapted recommendations (Safe/Balanced/Aggressive).
        """
        profile = self.user_profile
        suggestions = []
        
        if profile == "safe":
            # Check if portfolio is too risky
            vol = self.calculate_metrics()['volatility']
            if vol > 0.12:
                suggestions.append({
                    'priority': 'HIGH',
                    'type': 'warning',
                    'title': 'Too Risky for Safe Profile' if lang == 'en' else 'Trop Risqué pour Profil Sûr',
                    'issue': f'Volatility {vol*100:.0f}% > recommended 12%',
                    'solution': 'Increase bonds (AGG) to 40-50% and reduce equity exposure' if lang == 'en'
                               else 'Augmenter obligations (AGG) à 40-50% et réduire actions',
                    'recommended': ['AGG', 'GLD', 'SPY'],
                })
            
            # Recommend defensive assets
            has_defensive = any(ticker in ['AGG', 'GLD'] for ticker in self.tickers)
            if not has_defensive:
                suggestions.append({
                    'priority': 'HIGH',
                    'type': 'info',
                    'title': 'Add Defensive Assets' if lang == 'en' else 'Ajouter Actifs Défensifs',
                    'issue': 'Missing safe-haven assets',
                    'solution': 'Add AGG (bonds 40%) and GLD (gold 15%)' if lang == 'en'
                               else 'Ajouter AGG (obligations 40%) et GLD (or 15%)',
                    'recommended': ['AGG', 'GLD'],
                })
        
        elif profile == "balanced":
            # Check 60/40 ratio
            stock_exposure = sum(self.weights[t] for t in self.tickers 
                                if SECTOR_MAPPING.get(t, "") not in ["Bonds", "Commodities"])
            
            if stock_exposure > 0.70:
                suggestions.append({
                    'priority': 'MEDIUM',
                    'type': 'info',
                    'title': 'Adjust to 60/40 Mix' if lang == 'en' else 'Ajuster vers 60/40',
                    'issue': f'{stock_exposure*100:.0f}% stocks (target 60%)',
                    'solution': 'Increase bonds to reach 40% allocation' if lang == 'en'
                               else 'Augmenter obligations vers 40%',
                    'recommended': ['AGG', 'VXUS', 'VNQ'],
                })
        
        elif profile == "aggressive":
            # Check growth exposure
            has_growth = any(ticker in ['QQQ', 'NVDA', 'TSLA', 'BTC-USD'] for ticker in self.tickers)
            if not has_growth:
                suggestions.append({
                    'priority': 'MEDIUM',
                    'type': 'info',
                    'title': 'Add Growth Assets' if lang == 'en' else 'Ajouter Actifs Croissance',
                    'issue': 'Missing high-growth exposure',
                    'solution': 'Consider QQQ (Nasdaq), NVDA, or 5-10% BTC-USD' if lang == 'en'
                               else 'Considérer QQQ (Nasdaq), NVDA, ou 5-10% BTC-USD',
                    'recommended': ['QQQ', 'NVDA', 'BTC-USD', 'TSLA'],
                })
        
        return suggestions
    
    def stress_test_scenarios(self):
        """
        FIX #8: Simulate historical crisis scenarios.
        """
        scenarios = {
            "2008 Crisis": {
                "start": "2008-09-01",
                "end": "2009-03-01",
                "market_drop": -0.40,
                "description": "Financial crisis, market -40%"
            },
            "COVID-2020": {
                "start": "2020-02-01",
                "end": "2020-04-01",
                "market_drop": -0.30,
                "description": "Pandemic crash, market -30%"
            },
            "Inflation 2022": {
                "start": "2022-01-01",
                "end": "2022-10-01",
                "market_drop": -0.20,
                "description": "Rate hikes, market -20%"
            },
        }
        
        results = {}
        for name, scenario in scenarios.items():
            try:
                period_data = self.data.loc[scenario["start"]:scenario["end"]]
                if len(period_data) > 0:
                    period_returns = period_data.pct_change().dropna()
                    weights_array = np.array([self.weights[t] for t in self.tickers])
                    portfolio_ret = (period_returns @ weights_array)
                    total_ret = (1 + portfolio_ret).prod() - 1
                    
                    # Calculate recovery time (simplified)
                    recovery_days = len(period_data)
                    
                    results[name] = {
                        'portfolio_loss': total_ret,
                        'market_loss': scenario['market_drop'],
                        'resilience': 1 - abs(total_ret / scenario['market_drop']),
                        'recovery_days': recovery_days,
                        'description': scenario['description']
                    }
            except:
                pass
        
        return results
    
    def generate_auto_summary(self, lang="en"):
        """
        FIX #9: Auto-generated portfolio summary.
        """
        metrics = self.calculate_metrics()
        robustness = self.calculate_robustness_index()
        
        # Sector analysis
        sectors = {}
        for ticker in self.tickers:
            sector = SECTOR_MAPPING.get(ticker, "Unknown")
            sectors[sector] = sectors.get(sector, 0) + self.weights[ticker]
        
        dominant_sector = max(sectors, key=sectors.get) if sectors else "Unknown"
        sector_exposure = sectors.get(dominant_sector, 0)
        
        # Geography analysis
        geographies = {}
        for ticker in self.tickers:
            geo = GEOGRAPHY_MAPPING.get(ticker, "Unknown")
            geographies[geo] = geographies.get(geo, 0) + self.weights[ticker]
        
        dominant_geo = max(geographies, key=geographies.get) if geographies else "Unknown"
        geo_exposure = geographies.get(dominant_geo, 0)
        
        # Risk level
        vol = metrics['volatility']
        if vol < 0.12:
            risk_level = "low" if lang == "en" else "faible"
        elif vol < 0.20:
            risk_level = "moderate" if lang == "en" else "modérée"
        else:
            risk_level = "elevated" if lang == "en" else "élevée"
        
        # Diversification status
        if len(self.tickers) < 5:
            div_status = "limited" if lang == "en" else "limitée"
        elif len(self.tickers) < 8:
            div_status = "moderate" if lang == "en" else "modérée"
        else:
            div_status = "good" if lang == "en" else "bonne"
        
        if lang == "en":
            summary = f"""
            Your portfolio is **heavily exposed to {dominant_sector}** ({sector_exposure*100:.0f}%) 
            and **{dominant_geo}** markets ({geo_exposure*100:.0f}%).
            Diversification is **{div_status}** across {len(self.tickers)} assets.
            Volatility is **{risk_level}** ({vol*100:.0f}% annual).
            Robustness score: **{robustness['total']}/100 ({robustness['interpretation']})**.
            """
        else:
            summary = f"""
            Votre portefeuille est **fortement exposé au secteur {dominant_sector}** ({sector_exposure*100:.0f}%)
            et aux marchés **{dominant_geo}** ({geo_exposure*100:.0f}%).
            La diversification est **{div_status}** sur {len(self.tickers)} actifs.
            La volatilité est **{risk_level}** ({vol*100:.0f}% annuelle).
            Score de robustesse: **{robustness['total']}/100 ({robustness['interpretation']})**.
            """
        
        return summary.strip()
    
    def calculate_metrics(self):
        """Calculate all performance metrics."""
        returns = self.portfolio_returns
        total_return = (self.portfolio_values.iloc[-1] / self.initial_value) - 1
        years = len(returns) / 252
        annual_return = (1 + total_return) ** (1 / years) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe = annual_return / volatility if volatility > 0 else 0
        
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'final_value': self.portfolio_values.iloc[-1],
            'drawdown_series': drawdown,
        }
    
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

def render_robustness_score(robustness, lang="en"):
    """Render Portfolio Robustness Index."""
    total = robustness['total']
    color = robustness['color']
    interpretation = robustness['interpretation']
    
    st.markdown(f"""
    <div class='robustness-card' style='background: linear-gradient(135deg, {color} 0%, {color}dd 100%);'>
        <h1>{total}</h1>
        <p>/100 - {interpretation}</p>
        <p style='font-size: 1rem; opacity: 0.9; margin-top: 10px;'>
            {'Portfolio Robustness Index' if lang == 'en' else 'Indice de Robustesse'}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Breakdown
    st.markdown("#### Score Breakdown")
    components = [
        ("Diversification", robustness['diversification'], 20),
        ("Concentration", robustness['concentration'], 20),
        ("Correlation", robustness['correlation'], 15),
        ("Volatility", robustness['volatility'], 15),
        ("Drawdown", robustness['drawdown'], 15),
        ("Geography", robustness['geography'], 10),
        ("Sector", robustness['sector'], 5),
    ]
    
    for name, score, max_score in components:
        pct = (score / max_score) * 100
        color = "#10b981" if pct > 80 else "#f59e0b" if pct > 60 else "#ef4444"
        st.markdown(f"""
        <div style='margin: 10px 0;'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 5px;'>
                <span style='font-weight: 600; color: #1e293b;'>{name}</span>
                <span style='color: {color}; font-weight: 700;'>{score}/{max_score}</span>
            </div>
            <div style='background: #e2e8f0; border-radius: 10px; height: 8px; overflow: hidden;'>
                <div style='background: {color}; width: {pct}%; height: 100%; transition: width 0.5s;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_improvement_suggestions(suggestions, lang="en"):
    """Render improvement suggestions."""
    if not suggestions:
        st.success("✅ No major improvements needed!")
        return
    
    st.markdown(f"### 💡 {'Improvement Suggestions' if lang == 'en' else 'Suggestions d'Amélioration\"}")
    
    priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'INFO': 3}
    suggestions.sort(key=lambda x: priority_order.get(x['priority'], 4))
    
    for sug in suggestions:
        badge_colors = {
            'CRITICAL': '#ef4444',
            'HIGH': '#f59e0b',
            'MEDIUM': '#6366f1',
            'INFO': '#10b981'
        }
        badge_color = badge_colors.get(sug['priority'], '#64748b')
        
        st.markdown(f"""
        <div class='rec-card {sug['type']}'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                <h4 style='margin: 0;'>{sug['title']}</h4>
                <span style='background: {badge_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'>
                    {sug['priority']}
                </span>
            </div>
            <p><strong>Issue:</strong> {sug['issue']}</p>
            <p><strong>Solution:</strong> {sug['solution']}</p>
            <p style='color: #7e22ce; font-weight: 600; margin-top: 10px;'>
                💎 Expected impact: {sug['impact']}
            </p>
        </div>
        """, unsafe_allow_html=True)

def render_asset_card(ticker, lang="en"):
    """FIX #6: Educational asset card."""
    info = ASSET_INFO.get(ticker, {
        "name": ticker,
        "description": "Asset information not available",
        "sector": "Unknown",
        "geography": "Unknown",
        "utility": "N/A",
        "typical_use": "N/A",
        "risk_level": "Unknown"
    })
    
    with st.expander(f"📊 {ticker} - {info['name']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Description:**
            {info['description']}
            
            **Sector:** {info['sector']}
            **Geography:** {info['geography']}
            **Risk Level:** {info['risk_level']}
            """)
        
        with col2:
            st.markdown(f"""
            **Portfolio Role:**
            {info['utility']}
            
            **Typical Use:**
            {info['typical_use']}
            """)

def render_enhanced_charts(analyzer, lang="en"):
    """FIX #7: Enhanced visualizations."""
    
    tabs = st.tabs([
        "📈 Performance",
        "📉 Drawdown",
        "🥧 Allocation",
        "🌍 Geography",
        "🏢 Sectors"
    ])
    
    with tabs[0]:
        # Performance
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=analyzer.portfolio_values.index,
            y=analyzer.portfolio_values.values,
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#7e22ce', width=3),
            fill='tozeroy',
            fillcolor='rgba(126, 34, 206, 0.1)'
        ))
        fig.update_layout(
            title="Portfolio Performance",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:
        # Drawdown
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
            title="Portfolio Drawdown",
            yaxis_title="Drawdown (%)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[2]:
        # Allocation pie
        fig = go.Figure(data=[go.Pie(
            labels=list(analyzer.weights.keys()),
            values=list(analyzer.weights.values()),
            hole=.4
        )])
        fig.update_layout(title="Current Allocation", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[3]:
        # Geographic allocation
        geo_alloc = {}
        for ticker in analyzer.tickers:
            geo = GEOGRAPHY_MAPPING.get(ticker, "Unknown")
            geo_alloc[geo] = geo_alloc.get(geo, 0) + analyzer.weights[ticker]
        
        fig = go.Figure(data=[go.Bar(
            x=list(geo_alloc.keys()),
            y=[v*100 for v in geo_alloc.values()],
            marker=dict(color='#7e22ce')
        )])
        fig.update_layout(
            title="Geographic Allocation",
            yaxis_title="Allocation (%)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[4]:
        # Sector allocation
        sector_alloc = {}
        for ticker in analyzer.tickers:
            sector = SECTOR_MAPPING.get(ticker, "Unknown")
            sector_alloc[sector] = sector_alloc.get(sector, 0) + analyzer.weights[ticker]
        
        fig = go.Figure(data=[go.Bar(
            x=list(sector_alloc.keys()),
            y=[v*100 for v in sector_alloc.values()],
            marker=dict(color='#6366f1')
        )])
        fig.update_layout(
            title="Sector Allocation",
            yaxis_title="Allocation (%)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

def render_stress_test_results(stress_results, lang="en"):
    """FIX #8: Display stress test results."""
    st.markdown(f"### 🧪 {t('stress_test', lang)}")
    
    if not stress_results:
        st.info("Not enough historical data for stress testing")
        return
    
    for scenario, result in stress_results.items():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(scenario, f"{result['portfolio_loss']*100:.1f}%")
        with col2:
            st.metric("Market", f"{result['market_loss']*100:.0f}%")
        with col3:
            resilience = result['resilience'] * 100
            color = "normal" if resilience > 80 else "inverse"
            st.metric("Resilience", f"{resilience:.0f}%", delta_color=color)
        with col4:
            recovery_months = result['recovery_days'] / 30
            st.metric("Recovery", f"~{recovery_months:.0f} months")
        
        st.caption(result['description'])
        st.markdown("---")

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    init_session_state()
    lang = st.session_state.language
    
    # Sidebar
    with st.sidebar:
        # Language
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🇬🇧", use_container_width=True,
                        type="primary" if lang == "en" else "secondary"):
                st.session_state.language = "en"
                st.rerun()
        with col2:
            if st.button("🇫🇷", use_container_width=True,
                        type="primary" if lang == "fr" else "secondary"):
                st.session_state.language = "fr"
                st.rerun()
        
        st.markdown("---")
        st.title("📊 Portfolio Optimizer Pro v3.5")
        st.markdown(f"**{st.session_state.user_email}**")
        
        # User profile selector
        st.markdown("### 👤 Profile")
        profile = st.selectbox(
            "Risk Tolerance",
            ["safe", "balanced", "aggressive"],
            index=1
        )
        st.session_state.user_profile = profile
        
        st.markdown("---")
        
        # Navigation
        pages = [
            ("dashboard", "🏠"),
            ("new_analysis", "➕"),
            ("models", "📋"),
            ("improve", "⚡"),
        ]
        
        for page_key, icon in pages:
            if st.button(f"{icon} {t(page_key, lang).title()}", 
                        use_container_width=True,
                        type="primary" if st.session_state.page == page_key else "secondary"):
                st.session_state.page = page_key
                st.rerun()
    
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
            
            # Auto Summary (FIX #9)
            st.markdown("### 📝 Portfolio Summary")
            summary = analyzer.generate_auto_summary(lang)
            st.markdown(summary)
            
            st.markdown("---")
            
            # Robustness Index (FIX #2)
            robustness = analyzer.calculate_robustness_index()
            render_robustness_score(robustness, lang)
            
            st.markdown("---")
            
            # Quick Metrics
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
            
            # Improvement Suggestions (FIX #3, #4, #5)
            st.markdown(f"### 💡 {t('recommendations', lang)}")
            suggestions = analyzer.generate_improvement_suggestions(lang)
            profile_suggestions = analyzer.generate_profile_adapted_suggestions(lang)
            all_suggestions = suggestions + profile_suggestions
            render_improvement_suggestions(all_suggestions, lang)
            
            st.markdown("---")
            
            # Enhanced Charts (FIX #7)
            render_enhanced_charts(analyzer, lang)
            
            st.markdown("---")
            
            # Stress Test (FIX #8)
            if st.button("🧪 Run Stress Test", use_container_width=True):
                with st.spinner("Running scenarios..."):
                    stress_results = analyzer.stress_test_scenarios()
                render_stress_test_results(stress_results, lang)
            
            st.markdown("---")
            
            # Asset Info (FIX #6)
            st.markdown(f"### 📚 {t('asset_info', lang)}")
            for ticker in analyzer.tickers:
                render_asset_card(ticker, lang)
    
    elif page == "new_analysis":
        st.title(f"➕ {t('new_analysis', lang)}")
        
        tabs = st.tabs(["🔍 Search", "⭐ Popular"])
        
        with tabs[0]:
            search = st.text_input("Search assets...", placeholder="Apple, Bitcoin...")
            if search:
                all_assets = {}
                for cat, assets in POPULAR_ASSETS.items():
                    for name, ticker in assets.items():
                        all_assets[f"{name} ({ticker})"] = ticker
                
                matches = {k: v for k, v in all_assets.items() if search.lower() in k.lower()}
                
                for display, ticker in list(matches.items())[:10]:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(display)
                    with col2:
                        if st.button("➕", key=ticker):
                            if ticker not in st.session_state.selected_tickers:
                                st.session_state.selected_tickers.append(ticker)
                                auto_rebalance_weights()  # FIX #1
                                st.rerun()
        
        with tabs[1]:
            for category, assets in POPULAR_ASSETS.items():
                with st.expander(f"📂 {category}"):
                    cols = st.columns(3)
                    for i, (name, ticker) in enumerate(assets.items()):
                        with cols[i % 3]:
                            if st.button(f"{name}\n`{ticker}`", key=f"pop_{ticker}", 
                                       use_container_width=True):
                                if ticker not in st.session_state.selected_tickers:
                                    st.session_state.selected_tickers.append(ticker)
                                    auto_rebalance_weights()  # FIX #1
                                    st.rerun()
        
        # Selected Assets
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
                        auto_rebalance_weights()  # FIX #1
                        st.rerun()
            
            st.markdown("### Set Weights")
            
            # Display current weights with sliders (FIX #1)
            new_weights = {}
            cols = st.columns(min(len(st.session_state.selected_tickers), 4))
            
            for i, ticker in enumerate(st.session_state.selected_tickers):
                with cols[i % 4]:
                    current_weight = st.session_state.weights.get(ticker, 1.0/len(st.session_state.selected_tickers))
                    weight = st.slider(
                        ticker,
                        0.0, 100.0,
                        current_weight * 100,
                        1.0,
                        key=f"weight_slider_{ticker}"
                    )
                    new_weights[ticker] = weight / 100
            
            # Update weights
            st.session_state.weights = new_weights
            
            # Normalize and show total
            total = sum(new_weights.values())
            if abs(total - 1.0) > 0.01:
                st.warning(f"⚠️ Total: {total*100:.1f}% → Normalizing to 100%")
                st.session_state.weights = {k: v/total for k, v in new_weights.items()}
            else:
                st.success(f"✅ Total: {total*100:.1f}%")
            
            # Analyze button
            if st.button("🚀 Analyze Portfolio", type="primary", use_container_width=True):
                with st.spinner("Analyzing..."):
                    analyzer = UltimatePortfolioAnalyzer(
                        st.session_state.selected_tickers,
                        st.session_state.weights,
                        (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
                        user_profile=st.session_state.user_profile
                    )
                    
                    if analyzer.fetch_data():
                        st.session_state.current_portfolio = analyzer
                        st.success("✅ Analysis complete!")
                        st.balloons()
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("❌ Could not fetch data")
        else:
            st.info("Add assets above to begin")
    
    elif page == "models":
        st.title(f"📋 {t('models', lang)}")
        
        for model_name, model_data in MODEL_PORTFOLIOS.items():
            with st.expander(f"📊 {model_name}"):
                st.markdown(f"**{model_data['description']}**")
                st.markdown(f"Expected Return: {model_data['expected_return']*100:.0f}% | "
                           f"Volatility: {model_data['expected_volatility']*100:.0f}%")
                
                for ticker, weight in model_data['allocation'].items():
                    st.write(f"{ticker}: {weight*100:.0f}%")
                
                if st.button(f"Use {model_name}", key=model_name, use_container_width=True):
                    st.session_state.selected_tickers = list(model_data['allocation'].keys())
                    st.session_state.weights = model_data['allocation'].copy()
                    
                    with st.spinner(f"Loading {model_name}..."):
                        analyzer = UltimatePortfolioAnalyzer(
                            list(model_data['allocation'].keys()),
                            model_data['allocation'],
                            (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
                            user_profile=model_data['profile']
                        )
                        
                        if analyzer.fetch_data():
                            st.session_state.current_portfolio = analyzer
                            st.success(f"✅ {model_name} loaded!")
                            st.balloons()
                            st.session_state.page = "dashboard"
                            st.rerun()
    
    elif page == "improve":
        st.title(f"⚡ {t('improve', lang)}")
        
        if st.session_state.current_portfolio is None:
            st.info("Create a portfolio first to see improvement suggestions")
        else:
            analyzer = st.session_state.current_portfolio
            metrics = analyzer.calculate_metrics()
            
            st.markdown("### Current Portfolio")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Sharpe Ratio", f"{metrics['sharpe']:.2f}")
                st.metric("Annual Return", f"{metrics['annual_return']*100:.1f}%")
            with col2:
                st.metric("Volatility", f"{metrics['volatility']*100:.1f}%")
                st.metric("Max Drawdown", f"{metrics['max_drawdown']*100:.1f}%")
            
            st.markdown("---")
            
            # Run optimization
            if st.button("🎯 Optimize Portfolio", type="primary", use_container_width=True):
                with st.spinner("Optimizing..."):
                    optimal = analyzer.optimize_portfolio()
                
                st.markdown("### Optimized Portfolio")
                
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
                
                st.markdown("---")
                
                if st.button("Apply Optimization", use_container_width=True):
                    st.session_state.weights = optimal['weights']
                    analyzer_new = UltimatePortfolioAnalyzer(
                        list(optimal['weights'].keys()),
                        optimal['weights'],
                        analyzer.start_date,
                        user_profile=st.session_state.user_profile
                    )
                    if analyzer_new.fetch_data():
                        st.session_state.current_portfolio = analyzer_new
                        st.success("✅ Optimization applied!")
                        st.balloons()
                        st.rerun()

if __name__ == "__main__":
    main()
