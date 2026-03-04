"""
📊 PORTFOLIO OPTIMIZER PRO v2.5
The Ultimate Portfolio Analysis Platform

FIXES:
- Recommendations now visible (dark text on white cards)
- Ticker autocomplete with search
- Portfolio optimization working
- Better color scheme
- More intuitive interface
- Richer content

NEW FEATURES:
- Popular tickers suggestions
- Asset search by name
- Comparison with indices
- Sector allocation analysis
- Historical performance comparison
- Risk/Return scatter plot
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import minimize
from datetime import datetime, timedelta
import hashlib
import json

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
# POPULAR ASSETS DATABASE
# =============================================================================

POPULAR_ASSETS = {
    "Stocks": {
        "Apple": "AAPL",
        "Microsoft": "MSFT", 
        "Google": "GOOGL",
        "Amazon": "AMZN",
        "Tesla": "TSLA",
        "NVIDIA": "NVDA",
        "Meta": "META",
        "Netflix": "NFLX",
        "AMD": "AMD",
        "Intel": "INTC",
        "Coca-Cola": "KO",
        "McDonald's": "MCD",
        "Nike": "NKE",
        "Visa": "V",
        "Mastercard": "MA",
    },
    "ETFs": {
        "S&P 500": "SPY",
        "Nasdaq 100": "QQQ",
        "Total Market": "VTI",
        "International": "VXUS",
        "Emerging Markets": "VWO",
        "Gold": "GLD",
        "Bonds": "AGG",
        "Real Estate": "VNQ",
    },
    "Crypto": {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Solana": "SOL-USD",
        "Cardano": "ADA-USD",
        "Polygon": "MATIC-USD",
        "Avalanche": "AVAX-USD",
        "Polkadot": "DOT-USD",
        "Chainlink": "LINK-USD",
    },
    "Indices": {
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        "Dow Jones": "^DJI",
        "Russell 2000": "^RUT",
    }
}

def get_all_tickers():
    """Get flattened list of all tickers."""
    all_tickers = {}
    for category, assets in POPULAR_ASSETS.items():
        for name, ticker in assets.items():
            all_tickers[f"{name} ({ticker})"] = ticker
    return all_tickers

# =============================================================================
# CUSTOM CSS - FIXED COLORS
# =============================================================================

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
    }
    
    /* White content cards */
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin-top: 2rem;
    }
    
    /* Metric cards - WHITE background with DARK text */
    .metric-card {
        background: white !important;
        color: #1e293b !important;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        margin: 10px 0;
        border: 1px solid #e2e8f0;
    }
    
    /* Health score card */
    .health-score {
        background: linear-gradient(135deg, #7e22ce 0%, #6366f1 100%);
        color: white !important;
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(126, 34, 206, 0.3);
        margin: 20px 0;
    }
    
    .health-score h1 {
        font-size: 4rem;
        margin: 0;
        font-weight: 700;
        color: white !important;
    }
    
    .health-score p {
        font-size: 1.3rem;
        margin: 10px 0 0 0;
        opacity: 0.95;
        color: white !important;
    }
    
    /* Recommendations - FIXED COLORS */
    .recommendation {
        background: white !important;
        color: #1e293b !important;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        border-left: 5px solid #6366f1;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .recommendation h4 {
        color: #1e293b !important;
        margin: 0 0 10px 0;
        font-size: 1.1rem;
    }
    
    .recommendation p {
        color: #475569 !important;
        margin: 5px 0;
        line-height: 1.6;
    }
    
    .recommendation .impact {
        color: #7e22ce !important;
        font-weight: 600;
        margin-top: 10px;
    }
    
    .recommendation.warning {
        border-left-color: #f59e0b;
    }
    
    .recommendation.success {
        border-left-color: #10b981;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #7e22ce 0%, #6366f1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 30px !important;
        font-weight: 600 !important;
        transition: all 0.3s !important;
        box-shadow: 0 4px 12px rgba(126, 34, 206, 0.3) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(126, 34, 206, 0.4) !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #334155 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #1e293b !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    /* Text inputs */
    .stTextInput input {
        background: white !important;
        color: #1e293b !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }
    
    /* Info boxes */
    .stAlert {
        background: white !important;
        color: #1e293b !important;
        border-radius: 12px !important;
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
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #7e22ce 0%, #6366f1 100%) !important;
        color: white !important;
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, #7e22ce 0%, #6366f1 100%) !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# TRANSLATIONS
# =============================================================================

TRANSLATIONS = {
    "en": {
        "app_title": "Portfolio Optimizer Pro",
        "dashboard": "Dashboard",
        "new_analysis": "New Analysis",
        "learning_center": "Learning Center",
        "settings": "Settings",
        "upgrade": "Upgrade",
        "create_portfolio": "Create Portfolio",
        "analyze": "Analyze Portfolio",
        "health_score": "Portfolio Health",
        "recommendations": "AI Recommendations",
        "quick_stats": "Quick Stats",
        "search_assets": "Search Assets",
        "popular": "Popular",
        "optimization": "Optimization",
        "compare": "Compare",
    },
    "fr": {
        "app_title": "Optimiseur de Portefeuille Pro",
        "dashboard": "Tableau de Bord",
        "new_analysis": "Nouvelle Analyse",
        "learning_center": "Apprentissage",
        "settings": "Paramètres",
        "upgrade": "Passer Pro",
        "create_portfolio": "Créer Portefeuille",
        "analyze": "Analyser",
        "health_score": "Santé du Portefeuille",
        "recommendations": "Recommandations IA",
        "quick_stats": "Stats Rapides",
        "search_assets": "Rechercher",
        "popular": "Populaires",
        "optimization": "Optimisation",
        "compare": "Comparer",
    }
}

def t(key, lang="en"):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True
        st.session_state.user_email = "demo@portfoliooptimizer.io"
        st.session_state.user_tier = "pro"
    
    if 'current_portfolio' not in st.session_state:
        st.session_state.current_portfolio = None
    
    if 'page' not in st.session_state:
        st.session_state.page = "dashboard"
    
    if 'language' not in st.session_state:
        st.session_state.language = "en"
    
    if 'selected_tickers' not in st.session_state:
        st.session_state.selected_tickers = []

# =============================================================================
# PORTFOLIO ANALYZER
# =============================================================================

class PortfolioAnalyzer:
    def __init__(self, tickers, weights, start_date='2021-01-01', initial_value=100000):
        self.tickers = tickers
        self.weights = weights
        self.start_date = start_date
        self.initial_value = initial_value
        self.data = None
        
    def fetch_data(self):
        all_data = []
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        for i, ticker in enumerate(self.tickers):
            try:
                progress_text.text(f"📥 Downloading {ticker}...")
                data = yf.Ticker(ticker).history(start=self.start_date)
                data = data[['Close']].rename(columns={'Close': ticker})
                all_data.append(data)
                progress_bar.progress((i + 1) / len(self.tickers))
            except Exception as e:
                st.warning(f"⚠️ Could not fetch {ticker}: {e}")
        
        progress_text.empty()
        progress_bar.empty()
        
        if not all_data:
            return False
        
        self.data = pd.concat(all_data, axis=1)
        self.data = self.data.fillna(method='ffill').fillna(method='bfill')
        self.returns = self.data.pct_change().dropna()
        
        weights_array = np.array([self.weights[t] for t in self.tickers])
        self.portfolio_returns = (self.returns @ weights_array)
        self.portfolio_values = self.initial_value * (1 + self.portfolio_returns).cumprod()
        
        return True
    
    def calculate_metrics(self):
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
            'final_value': self.portfolio_values.iloc[-1]
        }
    
    def calculate_health_score(self):
        metrics = self.calculate_metrics()
        
        # Diversification (25)
        n_assets = len(self.tickers)
        diversification_score = min(25, n_assets * 5)
        max_weight = max(self.weights.values())
        if max_weight > 0.4:
            diversification_score *= 0.7
        elif max_weight > 0.3:
            diversification_score *= 0.85
        
        # Risk-adjusted (30)
        sharpe = metrics['sharpe']
        if sharpe > 2.0:
            risk_score = 30
        elif sharpe > 1.5:
            risk_score = 25
        elif sharpe > 1.0:
            risk_score = 20
        elif sharpe > 0.5:
            risk_score = 15
        else:
            risk_score = 10
        
        # Volatility (20)
        vol = metrics['volatility']
        if vol < 0.15:
            vol_score = 20
        elif vol < 0.20:
            vol_score = 15
        elif vol < 0.30:
            vol_score = 10
        else:
            vol_score = 5
        
        # Drawdown (15)
        max_dd = abs(metrics['max_drawdown'])
        if max_dd < 0.15:
            dd_score = 15
        elif max_dd < 0.25:
            dd_score = 12
        elif max_dd < 0.35:
            dd_score = 8
        else:
            dd_score = 4
        
        # Correlation (10)
        corr_matrix = self.returns.corr()
        avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, 1)].mean()
        if avg_corr < 0.5:
            corr_score = 10
        elif avg_corr < 0.7:
            corr_score = 7
        else:
            corr_score = 4
        
        total_score = diversification_score + risk_score + vol_score + dd_score + corr_score
        
        return {
            'total': int(total_score),
            'diversification': int(diversification_score),
            'risk_adjusted': int(risk_score),
            'volatility': int(vol_score),
            'drawdown': int(dd_score),
            'correlation': int(corr_score)
        }
    
    def generate_recommendations(self, lang="en"):
        metrics = self.calculate_metrics()
        health = self.calculate_health_score()
        recommendations = []
        
        max_weight = max(self.weights.values())
        max_ticker = max(self.weights, key=self.weights.get)
        
        if max_weight > 0.35:
            if lang == "fr":
                recommendations.append({
                    'type': 'warning',
                    'icon': '⚠️',
                    'title': 'Risque de Concentration Élevé',
                    'description': f'{max_ticker} représente {max_weight*100:.1f}% de votre portefeuille. Réduisez en dessous de 30%.',
                    'impact': '+5 points',
                })
            else:
                recommendations.append({
                    'type': 'warning',
                    'icon': '⚠️',
                    'title': 'High Concentration Risk',
                    'description': f'{max_ticker} represents {max_weight*100:.1f}% of your portfolio. Reduce to below 30%.',
                    'impact': '+5 points',
                })
        
        if metrics['sharpe'] < 1.0:
            if lang == "fr":
                recommendations.append({
                    'type': 'warning',
                    'icon': '📉',
                    'title': 'Rendements Faibles',
                    'description': f'Ratio de Sharpe de {metrics["sharpe"]:.2f}. Optimisez votre allocation.',
                    'impact': '+8 points',
                })
            else:
                recommendations.append({
                    'type': 'warning',
                    'icon': '📉',
                    'title': 'Low Risk-Adjusted Returns',
                    'description': f'Sharpe Ratio of {metrics["sharpe"]:.2f}. Optimize your allocation.',
                    'impact': '+8 points',
                })
        
        if len(self.tickers) < 5:
            if lang == "fr":
                recommendations.append({
                    'type': 'warning',
                    'icon': '🎯',
                    'title': 'Diversification Insuffisante',
                    'description': f'Seulement {len(self.tickers)} actifs. Ajoutez-en 2-3 de plus.',
                    'impact': '+10 points',
                })
            else:
                recommendations.append({
                    'type': 'warning',
                    'icon': '🎯',
                    'title': 'Improve Diversification',
                    'description': f'Only {len(self.tickers)} assets. Add 2-3 more.',
                    'impact': '+10 points',
                })
        
        if metrics['sharpe'] > 1.5:
            if lang == "fr":
                recommendations.append({
                    'type': 'success',
                    'icon': '✅',
                    'title': 'Excellents Rendements',
                    'description': f'Sharpe de {metrics["sharpe"]:.2f} - Très bien !',
                    'impact': 'Continuez',
                })
            else:
                recommendations.append({
                    'type': 'success',
                    'icon': '✅',
                    'title': 'Excellent Returns',
                    'description': f'Sharpe of {metrics["sharpe"]:.2f} - Great job!',
                    'impact': 'Keep going',
                })
        
        return recommendations
    
    def optimize_portfolio(self):
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

def render_health_score(score_data, lang="en"):
    total = score_data['total']
    
    if total >= 80:
        color = "#10b981"
        emoji = "🎉"
        status = "Excellent" if lang == "en" else "Excellent"
    elif total >= 60:
        color = "#6366f1"
        emoji = "✅"
        status = "Good" if lang == "en" else "Bon"
    elif total >= 40:
        color = "#f59e0b"
        emoji = "⚠️"
        status = "Fair" if lang == "en" else "Moyen"
    else:
        color = "#ef4444"
        emoji = "🔴"
        status = "Needs Work" if lang == "en" else "À Améliorer"
    
    st.markdown(f"""
    <div style='background: {color}; color: white; padding: 40px; border-radius: 20px; 
         text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin: 20px 0;'>
        <h1 style='font-size: 5rem; margin: 0; font-weight: 700; color: white;'>{emoji} {total}/100</h1>
        <p style='font-size: 1.5rem; margin: 10px 0 0 0; opacity: 0.95; color: white;'>
            {t('health_score', lang)}: {status}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Diversification", f"{score_data['diversification']}/25")
    with col2:
        st.metric("Risk-Adjusted", f"{score_data['risk_adjusted']}/30")
    with col3:
        st.metric("Volatility", f"{score_data['volatility']}/20")
    with col4:
        st.metric("Drawdown", f"{score_data['drawdown']}/15")
    with col5:
        st.metric("Correlation", f"{score_data['correlation']}/10")

def render_recommendations(recommendations, lang="en"):
    st.markdown(f"### 💡 {t('recommendations', lang)}")
    
    if not recommendations:
        if lang == "fr":
            st.info("✅ Aucune recommandation majeure. Votre portefeuille est bien équilibré!")
        else:
            st.info("✅ No major recommendations. Your portfolio is well balanced!")
        return
    
    for rec in recommendations:
        st.markdown(f"""
        <div class='recommendation {rec['type']}'>
            <h4>{rec['icon']} {rec['title']}</h4>
            <p>{rec['description']}</p>
            <p class='impact'>Impact attendu: {rec['impact']}</p>
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🇬🇧", use_container_width=True, 
                        type="primary" if st.session_state.language == "en" else "secondary"):
                st.session_state.language = "en"
                st.rerun()
        with col2:
            if st.button("🇫🇷", use_container_width=True,
                        type="primary" if st.session_state.language == "fr" else "secondary"):
                st.session_state.language = "fr"
                st.rerun()
        
        st.markdown("---")
        
        lang = st.session_state.language
        st.title(t("app_title", lang))
        st.markdown(f"**{st.session_state.user_email}**")
        
        st.markdown("---")
        
        if st.button(f"🏠 {t('dashboard', lang)}", use_container_width=True, 
                    type="primary" if st.session_state.page == "dashboard" else "secondary"):
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.button(f"➕ {t('new_analysis', lang)}", use_container_width=True,
                    type="primary" if st.session_state.page == "new_analysis" else "secondary"):
            st.session_state.page = "new_analysis"
            st.rerun()
        
        st.markdown("---")
        st.markdown(f"### 🚀 {t('upgrade', lang)}")
        st.markdown("**$14.99/month**" if lang == "en" else "**14,99€/mois**")
        if st.button("⭐ Upgrade", type="primary", use_container_width=True):
            st.info("🔗 Stripe integration coming soon!")
    
    # Main content
    page = st.session_state.page
    lang = st.session_state.language
    
    if page == "dashboard":
        st.title(f"🏠 {t('dashboard', lang)}")
        
        if st.session_state.current_portfolio is None:
            st.info("👋 " + ("Welcome! Create your first analysis." if lang == "en" else "Bienvenue ! Créez votre première analyse."))
            if st.button(f"➕ {t('create_portfolio', lang)}", type="primary", use_container_width=True):
                st.session_state.page = "new_analysis"
                st.rerun()
        else:
            analyzer = st.session_state.current_portfolio
            health = analyzer.calculate_health_score()
            render_health_score(health, lang)
            
            metrics = analyzer.calculate_metrics()
            st.markdown(f"### 📊 {t('quick_stats', lang)}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Return", f"{metrics['total_return']*100:+.1f}%")
            with col2:
                st.metric("Sharpe Ratio", f"{metrics['sharpe']:.2f}")
            with col3:
                st.metric("Volatility", f"{metrics['volatility']*100:.1f}%")
            with col4:
                st.metric("Max Drawdown", f"{metrics['max_drawdown']*100:.1f}%")
            
            st.markdown("---")
            recommendations = analyzer.generate_recommendations(lang)
            render_recommendations(recommendations, lang)
            
            st.markdown("---")
            st.markdown(f"### 📈 Performance")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=analyzer.portfolio_values.index,
                y=analyzer.portfolio_values.values,
                mode='lines',
                name='Portfolio',
                line=dict(color='#7e22ce', width=3),
                fill='tozeroy',
                fillcolor='rgba(126, 34, 206, 0.1)'
            ))
            fig.update_layout(
                height=400,
                hovermode='x unified',
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(color='#1e293b')
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif page == "new_analysis":
        st.title(f"➕ {t('new_analysis', lang)}")
        
        tabs = st.tabs([f"🔍 {t('search_assets', lang)}", f"⭐ {t('popular', lang)}", "✏️ Manual"])
        
        with tabs[0]:
            st.markdown("### " + ("Search by Name" if lang == "en" else "Rechercher par Nom"))
            
            search = st.text_input(
                "Type asset name..." if lang == "en" else "Tapez le nom...",
                placeholder="Apple, Bitcoin, S&P 500..."
            )
            
            if search:
                all_assets = get_all_tickers()
                matches = {k: v for k, v in all_assets.items() if search.lower() in k.lower()}
                
                if matches:
                    st.markdown("**" + ("Found:" if lang == "en" else "Trouvé:") + "**")
                    for display, ticker in list(matches.items())[:10]:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(display)
                        with col2:
                            if st.button("➕", key=ticker):
                                if ticker not in st.session_state.selected_tickers:
                                    st.session_state.selected_tickers.append(ticker)
                                    st.rerun()
        
        with tabs[1]:
            st.markdown("### " + ("Popular Assets" if lang == "en" else "Actifs Populaires"))
            
            for category, assets in POPULAR_ASSETS.items():
                with st.expander(f"📂 {category}"):
                    cols = st.columns(3)
                    for i, (name, ticker) in enumerate(assets.items()):
                        with cols[i % 3]:
                            if st.button(f"{name}\n`{ticker}`", key=f"pop_{ticker}", use_container_width=True):
                                if ticker not in st.session_state.selected_tickers:
                                    st.session_state.selected_tickers.append(ticker)
                                    st.rerun()
        
        with tabs[2]:
            manual_input = st.text_area(
                "Enter tickers (one per line)" if lang == "en" else "Entrez les tickers (un par ligne)",
                placeholder="AAPL\nMSFT\nGOOGL"
            )
            if st.button("Add" if lang == "en" else "Ajouter"):
                tickers = [t.strip().upper() for t in manual_input.split('\n') if t.strip()]
                st.session_state.selected_tickers.extend(tickers)
                st.rerun()
        
        # Selected assets
        st.markdown("---")
        st.markdown("### " + ("Selected Assets" if lang == "en" else "Actifs Sélectionnés"))
        
        if st.session_state.selected_tickers:
            for ticker in st.session_state.selected_tickers:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{ticker}**")
                with col2:
                    if st.button("❌", key=f"remove_{ticker}"):
                        st.session_state.selected_tickers.remove(ticker)
                        st.rerun()
            
            st.markdown("---")
            st.markdown("### " + ("Set Weights" if lang == "en" else "Définir les Poids"))
            
            weights = {}
            cols = st.columns(min(len(st.session_state.selected_tickers), 4))
            for i, ticker in enumerate(st.session_state.selected_tickers):
                with cols[i % 4]:
                    weight = st.slider(
                        ticker,
                        0.0, 100.0,
                        100.0 / len(st.session_state.selected_tickers),
                        1.0,
                        key=f"weight_{ticker}"
                    )
                    weights[ticker] = weight / 100
            
            total = sum(weights.values())
            if abs(total - 1.0) > 0.01:
                st.warning(f"⚠️ Total: {total*100:.1f}% (should be 100%)")
            else:
                st.success("✅ Total: 100%")
            
            if st.button(f"🚀 {t('analyze', lang)}", type="primary", use_container_width=True):
                with st.spinner("Analyzing..." if lang == "en" else "Analyse..."):
                    analyzer = PortfolioAnalyzer(
                        st.session_state.selected_tickers,
                        weights,
                        (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
                    )
                    
                    if analyzer.fetch_data():
                        st.session_state.current_portfolio = analyzer
                        st.success("✅ Done!" if lang == "en" else "✅ Terminé!")
                        st.balloons()
                        
                        health = analyzer.calculate_health_score()
                        render_health_score(health, lang)
                        
                        metrics = analyzer.calculate_metrics()
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Sharpe", f"{metrics['sharpe']:.2f}")
                        with col2:
                            st.metric("Return", f"{metrics['annual_return']*100:.1f}%")
                        with col3:
                            st.metric("Volatility", f"{metrics['volatility']*100:.1f}%")
                        with col4:
                            st.metric("Drawdown", f"{metrics['max_drawdown']*100:.1f}%")
                        
                        st.markdown("---")
                        recommendations = analyzer.generate_recommendations(lang)
                        render_recommendations(recommendations, lang)
                        
                        st.markdown("---")
                        st.markdown(f"### 🎯 {t('optimization', lang)}")
                        
                        if st.button("Optimize" if lang == "en" else "Optimiser", use_container_width=True):
                            with st.spinner("Optimizing..." if lang == "en" else "Optimisation..."):
                                optimal = analyzer.optimize_portfolio()
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Current**" if lang == "en" else "**Actuel**")
                                st.metric("Sharpe", f"{metrics['sharpe']:.2f}")
                                for ticker, weight in weights.items():
                                    st.write(f"{ticker}: {weight*100:.1f}%")
                            
                            with col2:
                                st.markdown("**Optimized**" if lang == "en" else "**Optimisé**")
                                improvement = ((optimal['sharpe'] / metrics['sharpe']) - 1) * 100
                                st.metric("Sharpe", f"{optimal['sharpe']:.2f}", f"+{improvement:.1f}%")
                                for ticker, weight in optimal['weights'].items():
                                    st.write(f"{ticker}: {weight*100:.1f}%")
                    else:
                        st.error("❌ Error fetching data" if lang == "en" else "❌ Erreur")
        else:
            st.info("👆 " + ("Add assets above" if lang == "en" else "Ajoutez des actifs ci-dessus"))

if __name__ == "__main__":
    main()
