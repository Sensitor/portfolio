"""
📊 PORTFOLIO OPTIMIZER PRO v2.0
The Ultimate Portfolio Analysis & Optimization Platform

New Features:
- Portfolio Health Score (0-100)
- AI-Powered Recommendations
- Interactive Portfolio Builder
- What-If Scenarios
- Learning Center
- Beautiful Modern UI
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

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Portfolio Optimizer Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Cards */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
    
    /* Health score */
    .health-score {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }
    
    .health-score h1 {
        font-size: 4rem;
        margin: 0;
        font-weight: 700;
    }
    
    .health-score p {
        font-size: 1.2rem;
        margin: 10px 0 0 0;
        opacity: 0.9;
    }
    
    /* Recommendations */
    .recommendation {
        background: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .recommendation.warning {
        border-left-color: #FFA000;
    }
    
    .recommendation.success {
        border-left-color: #00C851;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True  # Auto-login for demo
        st.session_state.user_email = "demo@portfoliooptimizer.io"
        st.session_state.user_tier = "pro"  # Give Pro access for demo
    
    if 'current_portfolio' not in st.session_state:
        st.session_state.current_portfolio = None
    
    if 'what_if_mode' not in st.session_state:
        st.session_state.what_if_mode = False

# =============================================================================
# PORTFOLIO ANALYSIS ENGINE
# =============================================================================

class PortfolioAnalyzer:
    def __init__(self, tickers, weights, start_date='2021-01-01', initial_value=100000):
        self.tickers = tickers
        self.weights = weights
        self.start_date = start_date
        self.initial_value = initial_value
        self.data = None
        
    def fetch_data(self):
        """Download market data."""
        all_data = []
        for ticker in self.tickers:
            try:
                data = yf.Ticker(ticker).history(start=self.start_date)
                data = data[['Close']].rename(columns={'Close': ticker})
                all_data.append(data)
            except:
                st.warning(f"Could not fetch {ticker}")
        
        if not all_data:
            return False
        
        self.data = pd.concat(all_data, axis=1)
        self.data = self.data.fillna(method='ffill').fillna(method='bfill')
        
        # Calculate returns
        self.returns = self.data.pct_change().dropna()
        
        # Portfolio returns
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
        
        # Sortino
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252)
        sortino = annual_return / downside_vol if downside_vol > 0 else 0
        
        # Drawdown
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
        """Calculate portfolio health score (0-100)."""
        metrics = self.calculate_metrics()
        
        # 1. Diversification Score (0-25)
        n_assets = len(self.tickers)
        diversification_score = min(25, n_assets * 5)  # Max at 5+ assets
        
        # Penalize concentration
        max_weight = max(self.weights.values())
        if max_weight > 0.4:
            diversification_score *= 0.7
        elif max_weight > 0.3:
            diversification_score *= 0.85
        
        # 2. Risk-Adjusted Return (0-30)
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
        
        # 3. Volatility Score (0-20)
        vol = metrics['volatility']
        if vol < 0.15:
            vol_score = 20
        elif vol < 0.20:
            vol_score = 15
        elif vol < 0.30:
            vol_score = 10
        else:
            vol_score = 5
        
        # 4. Drawdown Score (0-15)
        max_dd = abs(metrics['max_drawdown'])
        if max_dd < 0.15:
            dd_score = 15
        elif max_dd < 0.25:
            dd_score = 12
        elif max_dd < 0.35:
            dd_score = 8
        else:
            dd_score = 4
        
        # 5. Correlation Score (0-10)
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
    
    def generate_recommendations(self):
        """Generate AI-powered recommendations."""
        metrics = self.calculate_metrics()
        health = self.calculate_health_score()
        recommendations = []
        
        # Check concentration
        max_weight = max(self.weights.values())
        max_ticker = max(self.weights, key=self.weights.get)
        
        if max_weight > 0.35:
            recommendations.append({
                'type': 'warning',
                'icon': '⚠️',
                'title': 'High Concentration Risk',
                'description': f'{max_ticker} represents {max_weight*100:.1f}% of your portfolio. Consider reducing to below 30%.',
                'impact': '+5 points',
                'priority': 'high'
            })
        
        # Check Sharpe Ratio
        if metrics['sharpe'] < 1.0:
            recommendations.append({
                'type': 'warning',
                'icon': '📉',
                'title': 'Low Risk-Adjusted Returns',
                'description': f'Sharpe Ratio of {metrics["sharpe"]:.2f} is below optimal. Consider rebalancing.',
                'impact': '+8 points',
                'priority': 'high'
            })
        
        # Check diversification
        if len(self.tickers) < 5:
            recommendations.append({
                'type': 'warning',
                'icon': '🎯',
                'title': 'Improve Diversification',
                'description': f'Only {len(self.tickers)} assets. Add 2-3 more for better diversification.',
                'impact': '+10 points',
                'priority': 'medium'
            })
        
        # Check correlation
        corr_matrix = self.returns.corr()
        high_corr_pairs = []
        for i in range(len(corr_matrix)):
            for j in range(i+1, len(corr_matrix)):
                if abs(corr_matrix.iloc[i, j]) > 0.8:
                    high_corr_pairs.append((corr_matrix.index[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
        
        if high_corr_pairs:
            pair = high_corr_pairs[0]
            recommendations.append({
                'type': 'info',
                'icon': '🔗',
                'title': 'High Correlation Detected',
                'description': f'{pair[0]} and {pair[1]} move together ({pair[2]:.2f}). Consider replacing one.',
                'impact': '+6 points',
                'priority': 'medium'
            })
        
        # Positive feedback
        if metrics['sharpe'] > 1.5:
            recommendations.append({
                'type': 'success',
                'icon': '✅',
                'title': 'Excellent Risk-Adjusted Returns',
                'description': f'Sharpe Ratio of {metrics["sharpe"]:.2f} is outstanding!',
                'impact': 'Keep it up!',
                'priority': 'low'
            })
        
        if health['total'] > 80:
            recommendations.append({
                'type': 'success',
                'icon': '🎉',
                'title': 'Healthy Portfolio',
                'description': f'Your portfolio scores {health["total"]}/100. Well diversified and balanced!',
                'impact': 'Maintain',
                'priority': 'low'
            })
        
        return recommendations
    
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

def render_health_score(score_data):
    """Render health score card."""
    total = score_data['total']
    
    # Determine color and emoji
    if total >= 80:
        color = "#00C851"
        emoji = "🎉"
        status = "Excellent"
    elif total >= 60:
        color = "#2BBBAD"
        emoji = "✅"
        status = "Good"
    elif total >= 40:
        color = "#FFA000"
        emoji = "⚠️"
        status = "Fair"
    else:
        color = "#FF4444"
        emoji = "🔴"
        status = "Needs Improvement"
    
    st.markdown(f"""
    <div style='background: {color}; color: white; padding: 40px; border-radius: 20px; 
         text-align: center; box-shadow: 0 8px 16px rgba(0,0,0,0.2); margin: 20px 0;'>
        <h1 style='font-size: 5rem; margin: 0; font-weight: 700;'>{emoji} {total}/100</h1>
        <p style='font-size: 1.5rem; margin: 10px 0 0 0; opacity: 0.95;'>
            Portfolio Health: {status}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Breakdown
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

def render_recommendations(recommendations):
    """Render recommendation cards."""
    st.markdown("### 💡 AI-Powered Recommendations")
    
    # Sort by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    for rec in recommendations:
        type_class = rec['type']
        
        st.markdown(f"""
        <div class='recommendation {type_class}'>
            <h4>{rec['icon']} {rec['title']}</h4>
            <p>{rec['description']}</p>
            <p style='color: #667eea; font-weight: 600; margin-top: 10px;'>
                Expected Impact: {rec['impact']}
            </p>
        </div>
        """, unsafe_allow_html=True)

def render_what_if_simulator(analyzer):
    """Interactive what-if scenario simulator."""
    st.markdown("### 🔮 What-If Scenarios")
    st.markdown("*See how changes affect your portfolio in real-time*")
    
    # Create adjustable weights
    st.markdown("#### Adjust Weights")
    
    new_weights = {}
    cols = st.columns(min(len(analyzer.tickers), 4))
    
    for i, ticker in enumerate(analyzer.tickers):
        with cols[i % 4]:
            current_weight = analyzer.weights[ticker] * 100
            new_weight = st.slider(
                ticker,
                min_value=0.0,
                max_value=50.0,
                value=float(current_weight),
                step=1.0,
                key=f"what_if_{ticker}"
            )
            new_weights[ticker] = new_weight / 100
    
    # Normalize weights
    total = sum(new_weights.values())
    if abs(total - 1.0) > 0.01:
        st.warning(f"⚠️ Weights sum to {total*100:.1f}%. Normalizing to 100%...")
        new_weights = {k: v/total for k, v in new_weights.items()}
    
    # Calculate new metrics
    if st.button("🔄 Simulate Changes", type="primary"):
        # Create new analyzer with new weights
        sim_analyzer = PortfolioAnalyzer(
            analyzer.tickers,
            new_weights,
            analyzer.start_date,
            analyzer.initial_value
        )
        sim_analyzer.fetch_data()
        
        # Compare metrics
        original_metrics = analyzer.calculate_metrics()
        new_metrics = sim_analyzer.calculate_metrics()
        original_health = analyzer.calculate_health_score()
        new_health = sim_analyzer.calculate_health_score()
        
        st.markdown("#### 📊 Impact Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            delta_sharpe = new_metrics['sharpe'] - original_metrics['sharpe']
            st.metric(
                "Sharpe Ratio",
                f"{new_metrics['sharpe']:.2f}",
                f"{delta_sharpe:+.2f}"
            )
        
        with col2:
            delta_vol = new_metrics['volatility'] - original_metrics['volatility']
            st.metric(
                "Volatility",
                f"{new_metrics['volatility']*100:.1f}%",
                f"{delta_vol*100:+.1f}%",
                delta_color="inverse"
            )
        
        with col3:
            delta_return = new_metrics['annual_return'] - original_metrics['annual_return']
            st.metric(
                "Annual Return",
                f"{new_metrics['annual_return']*100:.1f}%",
                f"{delta_return*100:+.1f}%"
            )
        
        with col4:
            delta_health = new_health['total'] - original_health['total']
            st.metric(
                "Health Score",
                f"{new_health['total']}/100",
                f"{delta_health:+d} pts"
            )
        
        if delta_health > 0:
            st.success(f"✅ This change would improve your portfolio by {delta_health} points!")
        elif delta_health < 0:
            st.warning(f"⚠️ This change would decrease your health score by {abs(delta_health)} points.")
        else:
            st.info("➡️ This change has minimal impact on your portfolio health.")

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("📊 Portfolio Optimizer Pro")
        st.markdown(f"**{st.session_state.user_email}**")
        st.markdown(f"*{st.session_state.user_tier.title()} Plan*")
        
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "➕ New Analysis", "🎓 Learning Center", "⚙️ Settings"]
        )
        
        st.markdown("---")
        
        st.markdown("### 🚀 Upgrade")
        st.markdown("""
        **Get Pro for $14.99/mo**
        - Unlimited portfolios
        - AI recommendations
        - What-if scenarios
        - PDF reports
        """)
        st.button("Upgrade Now", type="primary")
    
    # Main content
    if page == "🏠 Dashboard":
        st.title("🏠 Portfolio Dashboard")
        
        if st.session_state.current_portfolio is None:
            st.info("👋 Welcome! Create your first portfolio analysis to get started.")
            if st.button("➕ Create Portfolio", type="primary"):
                st.session_state.page = "➕ New Analysis"
                st.rerun()
        else:
            analyzer = st.session_state.current_portfolio
            
            # Health Score
            health = analyzer.calculate_health_score()
            render_health_score(health)
            
            # Quick Stats
            metrics = analyzer.calculate_metrics()
            
            st.markdown("### 📊 Quick Stats")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Value", f"${metrics['final_value']:,.0f}")
            with col2:
                st.metric("Total Return", f"{metrics['total_return']*100:+.1f}%")
            with col3:
                st.metric("Sharpe Ratio", f"{metrics['sharpe']:.2f}")
            with col4:
                st.metric("Volatility", f"{metrics['volatility']*100:.1f}%")
            with col5:
                st.metric("Max Drawdown", f"{metrics['max_drawdown']*100:.1f}%")
            
            # Recommendations
            st.markdown("---")
            recommendations = analyzer.generate_recommendations()
            render_recommendations(recommendations)
            
            # Performance Chart
            st.markdown("---")
            st.markdown("### 📈 Performance")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=analyzer.portfolio_values.index,
                y=analyzer.portfolio_values.values,
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#667eea', width=3)
            ))
            fig.update_layout(
                height=400,
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif page == "➕ New Analysis":
        st.title("➕ Create Portfolio Analysis")
        
        # Input form
        st.markdown("### 1️⃣ Enter Your Holdings")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            tickers_input = st.text_input(
                "Tickers (comma-separated)",
                placeholder="AAPL, MSFT, GOOGL, AMZN, TSLA",
                help="Enter stock tickers separated by commas"
            )
        
        with col2:
            start_date = st.date_input(
                "Analysis Start Date",
                value=datetime.now() - timedelta(days=365*2)
            )
        
        if tickers_input:
            tickers = [t.strip().upper() for t in tickers_input.split(',')]
            
            st.markdown("### 2️⃣ Set Allocation")
            
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
            else:
                st.success("✅ Weights sum to 100%")
            
            # Analyze button
            st.markdown("---")
            
            if st.button("🚀 Analyze Portfolio", type="primary", use_container_width=True):
                with st.spinner("Analyzing your portfolio..."):
                    try:
                        analyzer = PortfolioAnalyzer(
                            tickers,
                            weights,
                            start_date.strftime('%Y-%m-%d')
                        )
                        
                        if analyzer.fetch_data():
                            st.session_state.current_portfolio = analyzer
                            st.success("✅ Analysis complete!")
                            st.balloons()
                            
                            # Show results immediately
                            st.markdown("---")
                            
                            # Health Score
                            health = analyzer.calculate_health_score()
                            render_health_score(health)
                            
                            # Quick metrics
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
                            
                            # Recommendations
                            st.markdown("---")
                            recommendations = analyzer.generate_recommendations()
                            render_recommendations(recommendations)
                            
                            # What-if
                            st.markdown("---")
                            render_what_if_simulator(analyzer)
                            
                            # Optimization
                            st.markdown("---")
                            st.markdown("### 🎯 Portfolio Optimization")
                            
                            if st.button("Optimize Allocation"):
                                with st.spinner("Optimizing..."):
                                    optimal = analyzer.optimize_portfolio()
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("#### Current Portfolio")
                                    st.metric("Sharpe Ratio", f"{metrics['sharpe']:.2f}")
                                    
                                    # Current weights
                                    for ticker, weight in weights.items():
                                        st.write(f"**{ticker}:** {weight*100:.1f}%")
                                
                                with col2:
                                    st.markdown("#### Optimized Portfolio")
                                    improvement = ((optimal['sharpe'] / metrics['sharpe']) - 1) * 100
                                    st.metric("Sharpe Ratio", f"{optimal['sharpe']:.2f}", 
                                             f"+{improvement:.1f}%")
                                    
                                    # Optimal weights
                                    for ticker, weight in optimal['weights'].items():
                                        st.write(f"**{ticker}:** {weight*100:.1f}%")
                                
                                if improvement > 5:
                                    st.success(f"✅ Optimization improves Sharpe by {improvement:.1f}%!")
                                else:
                                    st.info("Your current allocation is already well optimized!")
                        
                        else:
                            st.error("❌ Could not fetch data. Please check tickers.")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    elif page == "🎓 Learning Center":
        st.title("🎓 Learning Center")
        st.markdown("*Master portfolio management with interactive lessons*")
        
        tab1, tab2, tab3 = st.tabs(["📚 Beginner", "📊 Intermediate", "🎯 Advanced"])
        
        with tab1:
            st.markdown("### Beginner Lessons")
            
            with st.expander("📖 What is the Sharpe Ratio?"):
                st.markdown("""
                The **Sharpe Ratio** measures risk-adjusted returns.
                
                **Formula:** `(Return - Risk-Free Rate) / Volatility`
                
                **Interpretation:**
                - > 2.0 = Excellent
                - 1.0-2.0 = Good
                - 0.5-1.0 = Fair
                - < 0.5 = Poor
                
                **Example:**
                If your portfolio returns 15% with 20% volatility:
                - Sharpe = (0.15 - 0.04) / 0.20 = 0.55
                
                This means you get 0.55 units of return per unit of risk.
                """)
            
            with st.expander("🎯 How to Diversify Effectively"):
                st.markdown("""
                **Diversification** reduces risk without sacrificing returns.
                
                **Key Principles:**
                1. **5-10 assets minimum** for good diversification
                2. **Low correlation** between assets
                3. **Different sectors** (tech, healthcare, finance)
                4. **Different asset classes** (stocks, bonds, commodities)
                
                **Example:**
                ❌ Bad: 5 tech stocks (all correlated)
                ✅ Good: 2 tech, 2 healthcare, 1 finance, 1 commodities
                """)
            
            with st.expander("📉 Understanding Volatility"):
                st.markdown("""
                **Volatility** measures how much your portfolio value fluctuates.
                
                **Annual Volatility Benchmarks:**
                - < 10% = Very Low (bonds)
                - 10-15% = Low (balanced)
                - 15-25% = Medium (stocks)
                - > 25% = High (crypto)
                
                **Why it matters:**
                Higher volatility = higher risk = need higher returns to compensate
                """)
        
        with tab2:
            st.markdown("### Intermediate Lessons")
            
            with st.expander("🎯 Modern Portfolio Theory"):
                st.markdown("""
                **Markowitz Portfolio Theory** (Nobel Prize 1990)
                
                **Key Concept:**
                For any level of risk, there exists an optimal portfolio 
                that maximizes returns.
                
                **Efficient Frontier:**
                The curve of optimal portfolios.
                
                Our optimizer finds this mathematically using:
                - Expected returns
                - Covariance matrix
                - Constraints (no short selling, max 40% per asset)
                """)
            
            with st.expander("📊 Value at Risk (VaR)"):
                st.markdown("""
                **VaR** estimates maximum loss at a confidence level.
                
                **Example:**
                95% VaR of $5,000 means:
                - 95% of days, you won't lose more than $5,000
                - 5% of days (1 in 20), you might lose more
                
                **Three Methods:**
                1. **Historical:** Based on past data
                2. **Parametric:** Assumes normal distribution
                3. **Monte Carlo:** Simulates thousands of scenarios
                """)
        
        with tab3:
            st.markdown("### Advanced Lessons")
            
            with st.expander("🎯 Factor Investing"):
                st.markdown("""
                **Factor Investing** targets specific drivers of returns.
                
                **Common Factors:**
                - **Value:** Undervalued stocks
                - **Momentum:** Recent winners
                - **Size:** Small-cap premium
                - **Quality:** Profitable, stable companies
                - **Low Volatility:** Defensive stocks
                
                **Application:**
                Tilt your portfolio toward factors that historically outperform.
                """)
            
            with st.expander("💰 Tax Optimization"):
                st.markdown("""
                **Tax-Loss Harvesting:**
                Sell losing positions to offset gains.
                
                **Long-term vs Short-term:**
                - Hold > 1 year = long-term capital gains (lower tax)
                - Hold < 1 year = short-term (higher tax)
                
                **Rebalancing Timing:**
                Time rebalancing to minimize tax impact.
                """)
    
    elif page == "⚙️ Settings":
        st.title("⚙️ Settings")
        
        st.markdown("### 👤 Account")
        st.text_input("Email", value=st.session_state.user_email, disabled=True)
        st.text_input("Plan", value=st.session_state.user_tier.title(), disabled=True)
        
        st.markdown("---")
        
        st.markdown("### 🎨 Preferences")
        st.selectbox("Default Analysis Period", ["1 Year", "2 Years", "3 Years", "5 Years"])
        st.selectbox("Risk-Free Rate", ["4.0%", "4.5%", "5.0%"])
        
        st.markdown("---")
        
        st.markdown("### 🔔 Notifications")
        st.checkbox("Email alerts for portfolio changes", value=True)
        st.checkbox("Weekly performance reports", value=True)
        st.checkbox("Rebalancing reminders", value=False)

if __name__ == "__main__":
    main()
