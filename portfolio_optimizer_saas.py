"""
📊 PORTFOLIO OPTIMIZER - SaaS Application
Version: 1.0.0
Author: Finance Masters Student - IUM

Professional portfolio analysis and optimization platform.
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
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Portfolio Optimizer Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Pricing tiers
TIERS = {
    "free": {
        "name": "Free",
        "price": 0,
        "max_portfolios": 1,
        "max_assets": 5,
        "features": ["Basic metrics", "1 portfolio/day", "5 assets max"],
        "stripe_link": None
    },
    "pro": {
        "name": "Pro",
        "price": 9.99,
        "max_portfolios": 999,
        "max_assets": 50,
        "features": ["Unlimited portfolios", "Up to 50 assets", "Markowitz optimization", 
                    "VaR analysis", "Monte Carlo", "PDF reports", "Priority support"],
        "stripe_link": "https://buy.stripe.com/test_XXXXX"  # À remplacer
    },
    "business": {
        "name": "Business",
        "price": 49,
        "max_portfolios": 9999,
        "max_assets": 200,
        "features": ["Everything in Pro", "Unlimited assets", "API access", 
                    "White label reports", "Team collaboration", "Dedicated support"],
        "stripe_link": "https://buy.stripe.com/test_YYYYY"  # À remplacer
    }
}

# =============================================================================
# AUTHENTICATION (Simple - Production : utilise Streamlit Auth ou Auth0)
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_tier' not in st.session_state:
        st.session_state.user_tier = "free"
    if 'portfolios_today' not in st.session_state:
        st.session_state.portfolios_today = 0
    if 'current_portfolio' not in st.session_state:
        st.session_state.current_portfolio = None

def hash_password(password):
    """Simple password hashing."""
    return hashlib.sha256(password.encode()).hexdigest()

def login_page():
    """Login/Signup page."""
    st.title("📊 Portfolio Optimizer Pro")
    st.markdown("### Professional Portfolio Analysis & Optimization")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Welcome Back!")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary"):
            # Simple demo login (Production : use real database)
            if email and password:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_tier = "free"  # Default
                st.rerun()
            else:
                st.error("Please enter email and password")
    
    with tab2:
        st.subheader("Start Free Today!")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        st.markdown("**What you get for FREE:**")
        for feature in TIERS["free"]["features"]:
            st.markdown(f"✅ {feature}")
        
        if st.button("Create Account", type="primary"):
            if new_email and new_password and new_password == confirm_password:
                st.session_state.authenticated = True
                st.session_state.user_email = new_email
                st.session_state.user_tier = "free"
                st.success("✅ Account created! Welcome!")
                st.rerun()
            else:
                st.error("Please check your inputs")

def logout():
    """Logout user."""
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_tier = "free"
    st.rerun()

# =============================================================================
# PORTFOLIO ANALYSIS ENGINE
# =============================================================================

class PortfolioAnalyzer:
    """Core portfolio analysis engine."""
    
    def __init__(self, tickers, weights, start_date, initial_value=100000):
        self.tickers = tickers
        self.weights = weights
        self.start_date = start_date
        self.initial_value = initial_value
        self.prices = None
        self.returns = None
        
    def fetch_data(self):
        """Download market data."""
        all_prices = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ticker in enumerate(self.tickers):
            try:
                status_text.text(f"Downloading {ticker}...")
                data = yf.Ticker(ticker).history(start=self.start_date)
                prices = data['Close']
                prices.name = ticker
                all_prices.append(prices)
                progress_bar.progress((i + 1) / len(self.tickers))
            except Exception as e:
                st.warning(f"⚠️ Could not fetch {ticker}: {e}")
        
        status_text.empty()
        progress_bar.empty()
        
        if not all_prices:
            raise ValueError("No data could be downloaded")
        
        self.prices = pd.concat(all_prices, axis=1)
        self.prices = self.prices.fillna(method='ffill').fillna(method='bfill')
        self.returns = self.prices.pct_change().dropna()
        
        weights_array = np.array([self.weights[t] for t in self.tickers])
        self.portfolio_returns = (self.returns @ weights_array)
        self.portfolio_values = self.initial_value * (1 + self.portfolio_returns).cumprod()
        
        return True
    
    def calculate_metrics(self):
        """Calculate performance metrics."""
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
        
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252)
        sortino = annual_return / downside_vol if downside_vol > 0 else 0
        
        return {
            'Total Return': total_return,
            'Annual Return': annual_return,
            'Volatility': volatility,
            'Sharpe Ratio': sharpe,
            'Sortino Ratio': sortino,
            'Max Drawdown': max_dd,
            'Final Value': self.portfolio_values.iloc[-1]
        }
    
    def calculate_var(self, confidence=0.95):
        """Calculate Value at Risk."""
        var_hist = -np.percentile(self.portfolio_returns, (1 - confidence) * 100)
        
        mu = self.portfolio_returns.mean()
        sigma = self.portfolio_returns.std()
        from scipy import stats
        z = stats.norm.ppf(1 - confidence)
        var_param = -(mu + sigma * z)
        
        tail_losses = self.portfolio_returns[self.portfolio_returns <= -var_hist]
        es = -tail_losses.mean() if len(tail_losses) > 0 else var_hist
        
        return {
            'VaR Historical': var_hist,
            'VaR Parametric': var_param,
            'Expected Shortfall': es
        }
    
    def optimize_portfolio(self):
        """Markowitz optimization."""
        n_assets = len(self.tickers)
        expected_returns = self.returns.mean() * 252
        cov_matrix = self.returns.cov() * 252
        
        def negative_sharpe(weights):
            port_return = np.dot(weights, expected_returns)
            port_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            return -(port_return - 0.04) / port_vol
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = tuple((0.05, 0.40) for _ in range(n_assets))
        initial = np.array([1/n_assets] * n_assets)
        
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
# MAIN APP
# =============================================================================

def main_app():
    """Main application after login."""
    
    # Sidebar
    with st.sidebar:
        st.title("📊 Portfolio Optimizer")
        st.markdown(f"**Logged in as:** {st.session_state.user_email}")
        
        tier_info = TIERS[st.session_state.user_tier]
        st.markdown(f"**Plan:** {tier_info['name']}")
        
        if st.session_state.user_tier != "business":
            st.markdown("---")
            st.markdown("### 🚀 Upgrade to unlock more!")
            
            if st.session_state.user_tier == "free":
                st.markdown("**Pro Plan - $9.99/month**")
                for feature in TIERS["pro"]["features"][:4]:
                    st.markdown(f"✅ {feature}")
                if TIERS["pro"]["stripe_link"]:
                    st.link_button("Upgrade to Pro", TIERS["pro"]["stripe_link"])
            
            st.markdown("**Business Plan - $49/month**")
            for feature in TIERS["business"]["features"][:3]:
                st.markdown(f"✅ {feature}")
            if TIERS["business"]["stripe_link"]:
                st.link_button("Upgrade to Business", TIERS["business"]["stripe_link"])
        
        st.markdown("---")
        if st.button("Logout"):
            logout()
    
    # Main content
    st.title("📊 Portfolio Analysis Dashboard")
    
    # Check limits
    tier_info = TIERS[st.session_state.user_tier]
    
    if st.session_state.user_tier == "free" and st.session_state.portfolios_today >= tier_info["max_portfolios"]:
        st.error("🚫 You've reached your daily limit (1 portfolio). Upgrade to Pro for unlimited access!")
        st.stop()
    
    # Portfolio input
    st.markdown("### 1️⃣ Configure Your Portfolio")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        tickers_input = st.text_input(
            "Enter tickers (comma-separated)",
            placeholder="AAPL, MSFT, GOOGL, AMZN",
            help=f"Maximum {tier_info['max_assets']} assets for {tier_info['name']} plan"
        )
    
    with col2:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=365*2),
            max_value=datetime.now()
        )
    
    if tickers_input:
        tickers = [t.strip().upper() for t in tickers_input.split(',')]
        
        if len(tickers) > tier_info["max_assets"]:
            st.error(f"🚫 Your plan allows max {tier_info['max_assets']} assets. You entered {len(tickers)}.")
            st.info("💎 Upgrade to Pro for up to 50 assets!")
            st.stop()
        
        st.markdown("### 2️⃣ Set Weights")
        
        weights = {}
        cols = st.columns(min(len(tickers), 4))
        
        for i, ticker in enumerate(tickers):
            with cols[i % 4]:
                weight = st.slider(
                    ticker,
                    min_value=0.0,
                    max_value=100.0,
                    value=100.0 / len(tickers),
                    step=1.0
                )
                weights[ticker] = weight / 100
        
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            st.warning(f"⚠️ Weights sum to {total_weight*100:.1f}%. Should be 100%.")
        
        # Analyze button
        if st.button("🚀 Analyze Portfolio", type="primary"):
            
            with st.spinner("Analyzing your portfolio..."):
                try:
                    # Create analyzer
                    analyzer = PortfolioAnalyzer(
                        tickers=tickers,
                        weights=weights,
                        start_date=start_date.strftime('%Y-%m-%d')
                    )
                    
                    # Fetch data
                    analyzer.fetch_data()
                    
                    # Calculate metrics
                    metrics = analyzer.calculate_metrics()
                    
                    # Increment counter
                    st.session_state.portfolios_today += 1
                    st.session_state.current_portfolio = {
                        'analyzer': analyzer,
                        'metrics': metrics
                    }
                    
                    st.success("✅ Analysis complete!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    st.stop()
            
            # Display results
            st.markdown("---")
            st.markdown("### 📊 Results")
            
            # Metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Return", f"{metrics['Total Return']*100:.2f}%")
            with col2:
                st.metric("Annual Return", f"{metrics['Annual Return']*100:.2f}%")
            with col3:
                st.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
            with col4:
                st.metric("Volatility", f"{metrics['Volatility']*100:.2f}%")
            with col5:
                st.metric("Max Drawdown", f"{metrics['Max Drawdown']*100:.2f}%")
            
            # Performance chart
            st.markdown("#### 📈 Performance Over Time")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=analyzer.portfolio_values.index,
                y=analyzer.portfolio_values.values,
                mode='lines',
                name='Portfolio',
                line=dict(color='#2E86AB', width=3)
            ))
            fig.update_layout(
                xaxis_title='Date',
                yaxis_title='Value ($)',
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Allocation
            st.markdown("#### 🥧 Current Allocation")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=list(weights.keys()),
                    values=list(weights.values()),
                    hole=.3
                )])
                fig_pie.update_layout(height=350)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                weights_df = pd.DataFrame({
                    'Asset': list(weights.keys()),
                    'Weight': [f"{w*100:.1f}%" for w in weights.values()]
                })
                st.dataframe(weights_df, hide_index=True, use_container_width=True)
            
            # PRO FEATURES
            if st.session_state.user_tier in ["pro", "business"]:
                
                st.markdown("---")
                st.markdown("### 💎 PRO FEATURES")
                
                tab1, tab2, tab3 = st.tabs(["Optimization", "Risk Analysis", "Monte Carlo"])
                
                with tab1:
                    st.markdown("#### 🎯 Portfolio Optimization (Markowitz)")
                    
                    if st.button("Optimize Portfolio"):
                        with st.spinner("Optimizing..."):
                            optimal = analyzer.optimize_portfolio()
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Current Portfolio:**")
                            current_sharpe = metrics['Sharpe Ratio']
                            st.metric("Sharpe Ratio", f"{current_sharpe:.2f}")
                        
                        with col2:
                            st.markdown("**Optimized Portfolio:**")
                            improvement = ((optimal['sharpe'] / current_sharpe) - 1) * 100
                            st.metric("Sharpe Ratio", f"{optimal['sharpe']:.2f}", 
                                     delta=f"+{improvement:.1f}%")
                        
                        st.markdown("**Optimal Weights:**")
                        optimal_df = pd.DataFrame({
                            'Asset': list(optimal['weights'].keys()),
                            'Current': [f"{weights[t]*100:.1f}%" for t in optimal['weights'].keys()],
                            'Optimal': [f"{optimal['weights'][t]*100:.1f}%" for t in optimal['weights'].keys()]
                        })
                        st.dataframe(optimal_df, hide_index=True, use_container_width=True)
                
                with tab2:
                    st.markdown("#### 🔬 Value at Risk Analysis")
                    
                    var_results = analyzer.calculate_var()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("VaR Historical (95%)", 
                                 f"${var_results['VaR Historical']*100000:,.0f}")
                    with col2:
                        st.metric("VaR Parametric (95%)", 
                                 f"${var_results['VaR Parametric']*100000:,.0f}")
                    with col3:
                        st.metric("Expected Shortfall", 
                                 f"${var_results['Expected Shortfall']*100000:,.0f}")
                    
                    st.info("💡 VaR = Maximum expected loss with 95% confidence on a $100k portfolio")
                
                with tab3:
                    st.markdown("#### 🎲 Monte Carlo Simulation")
                    st.info("🚧 Coming soon in next update!")
            
            else:
                # Upgrade prompt
                st.markdown("---")
                st.markdown("### 🔒 Unlock More Features")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**✨ With Pro you get:**")
                    st.markdown("- 🎯 Markowitz Optimization")
                    st.markdown("- 🔬 Value at Risk Analysis")
                    st.markdown("- 🎲 Monte Carlo Simulations")
                    st.markdown("- 📄 PDF Reports")
                    st.markdown("- ⚡ Priority Support")
                
                with col2:
                    st.markdown("**💎 Just $9.99/month**")
                    if TIERS["pro"]["stripe_link"]:
                        st.link_button("Upgrade Now →", TIERS["pro"]["stripe_link"], 
                                      type="primary")

# =============================================================================
# APP ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    init_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
