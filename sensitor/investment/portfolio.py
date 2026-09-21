"""
Portfolio analyzer — the engine behind the original Sensitor dashboards.

Downloads prices for a set of tickers, derives the return and value series, and
computes the metrics, robustness and health scores, improvement suggestions,
crisis stress results and Markowitz optimisation the legacy pages render.

Extracted verbatim from the Streamlit entry point in V2 Phase 2. The calculations
are unchanged; the only edit is that `fetch_data` reports progress through
callbacks instead of calling `st.progress` and `st.warning`, so the class runs
from a test, a script, a scheduled job or the future API with no Streamlit
runtime present.

Note on overlap: several methods here compute quantities that `investment.
analytics`, `health`, `stress` and `optimize` also compute — by different
methods, with different thresholds and over different windows. That duplication
is deliberate for now: the legacy pages render these versions, and converging
them would change what users see. See docs/ARCHITECTURE.md section 3.

The lint warnings this file carries (unused locals, f-strings without
placeholders) came with the code. They are left alone on purpose: Phase 2 changes
structure, not behaviour, and tidying code while moving it is how a move becomes
a regression.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize

from .assets import ASSET_INFO, GEOGRAPHY_MAPPING, SECTOR_MAPPING

class PortfolioAnalyzer:
    def __init__(self, tickers, weights, start_date='2021-01-01', initial_value=100000, user_profile="balanced"):
        self.tickers = tickers
        self.weights = weights
        self.start_date = start_date
        self.initial_value = initial_value
        self.user_profile = user_profile
        self.data = None
        
    def fetch_data(self, *, progress=None, on_error=None):
        """
        Download prices and derive the return and value series.

        `progress(fraction, label)` and `on_error(ticker, message)` are optional
        callbacks. They exist so this method can report what it is doing without
        knowing what it reports to: the Streamlit app passes callbacks driving a
        progress bar and a warning, a test passes none, and a scheduled job or the
        future API can pass a logger. Before the V2 extraction this called
        `st.progress` and `st.warning` directly, which meant the entire analyzer
        needed a Streamlit runtime to run at all.

        Tickers that fail to download are skipped and their weight redistributed
        across the survivors, so one dead symbol does not lose the portfolio.
        """
        all_data = []
        total = len(self.tickers) or 1

        for i, ticker in enumerate(self.tickers):
            try:
                if progress:
                    progress(i / total, f"Loading {ticker}...")
                data = yf.Ticker(ticker).history(start=self.start_date)
                data = data[['Close']].rename(columns={'Close': ticker})
                all_data.append(data)
                if progress:
                    progress((i + 1) / total, f"Loading {ticker}...")
            except Exception as e:
                if on_error:
                    on_error(ticker, str(e)[:80])
        
        if not all_data:
            return False

        self.data = pd.concat(all_data, axis=1)
        # Only keep tickers that actually downloaded successfully
        available = [t for t in self.tickers if t in self.data.columns]
        if not available:
            return False
        self.data = self.data[available].ffill().bfill()

        # Sync tickers and weights to available data
        self.tickers = available
        total_w = sum(self.weights[t] for t in available)
        self.weights = {t: self.weights[t] / total_w for t in available}

        self.returns = self.data.pct_change().dropna()
        weights_array = np.array([self.weights[t] for t in self.tickers])
        self.portfolio_returns = self.returns @ weights_array
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
    
    def calculate_health_score(self):
        """
        Global Portfolio Health Score (0-100).
        Combines three dimensions:
          - Structure (40%): Robustness Index
          - Performance Quality (35%): Sharpe + Annual Return
          - Liquidity (25%): weighted average liquidity of assets
        """
        robustness = self.calculate_robustness_index()
        metrics = self.calculate_metrics()

        # ── 1. Structure (directly from Robustness Index) ──────────────────
        structure = robustness['total']  # 0-100

        # ── 2. Performance Quality ─────────────────────────────────────────
        sharpe = metrics['sharpe']
        annual_ret = metrics['annual_return']

        if sharpe >= 2.0:   sharpe_s = 100
        elif sharpe >= 1.5: sharpe_s = 84
        elif sharpe >= 1.0: sharpe_s = 68
        elif sharpe >= 0.5: sharpe_s = 50
        elif sharpe >= 0:   sharpe_s = 30
        else:               sharpe_s = 10

        if annual_ret >= 0.15:   ret_s = 100
        elif annual_ret >= 0.10: ret_s = 84
        elif annual_ret >= 0.07: ret_s = 68
        elif annual_ret >= 0.04: ret_s = 50
        elif annual_ret >= 0:    ret_s = 30
        else:                    ret_s = 10

        performance = (sharpe_s * 0.55 + ret_s * 0.45)  # 0-100

        # ── 3. Liquidity ───────────────────────────────────────────────────
        weighted_liq = 0.0
        for ticker in self.tickers:
            info = ASSET_INFO.get(ticker, {})
            liq = info.get('liquidity', 70)
            weighted_liq += liq * self.weights[ticker]
        liquidity = weighted_liq  # 0-100

        # ── Overall ────────────────────────────────────────────────────────
        total = structure * 0.40 + performance * 0.35 + liquidity * 0.25
        total = round(min(100, max(0, total)))

        if total >= 85:
            grade, color = "Excellent", "#10b981"
        elif total >= 70:
            grade, color = "Good", "#4f46e5"
        elif total >= 55:
            grade, color = "Fair", "#f59e0b"
        elif total >= 40:
            grade, color = "Weak", "#f97316"
        else:
            grade, color = "Critical", "#ef4444"

        grade_fr = {"Excellent": "Excellent", "Good": "Bon", "Fair": "Passable",
                    "Weak": "Faible", "Critical": "Critique"}

        return {
            'total': total,
            'structure': round(structure),
            'performance': round(performance),
            'liquidity': round(liquidity),
            'grade': grade,
            'grade_fr': grade_fr[grade],
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
                'impact': 'Robustness +15 pts' if lang == 'en' else 'Robustesse +15 pts',
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
                    'issue': f'{exposure*100:.0f}% in {sector}' if lang == 'en' else f'{exposure*100:.0f}% dans {sector}',
                    'solution': f'Add international ETF (VXUS) or bonds (AGG)' if lang == 'en'
                               else f'Ajouter ETF international (VXUS) ou obligations (AGG)',
                    'impact': 'Robustness +10 pts' if lang == 'en' else 'Robustesse +10 pts',
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
                'issue': f'{usa_exposure*100:.0f}% USA exposure' if lang == 'en' else f'{usa_exposure*100:.0f}% exposition USA',
                'solution': 'Add VXUS (international) for global diversification' if lang == 'en'
                           else 'Ajouter VXUS (international) pour diversification mondiale',
                'impact': 'Robustness +8 pts' if lang == 'en' else 'Robustesse +8 pts',
            })
        
        # Lack of bonds/hedges
        has_bonds = any(ticker in ['AGG', 'BND', 'TLT'] for ticker in self.tickers)
        has_gold = any(ticker in ['GLD', 'IAU'] for ticker in self.tickers)
        
        if not has_bonds and not has_gold:
            suggestions.append({
                'priority': 'MEDIUM',
                'type': 'info',
                'title': 'Missing Hedges' if lang == 'en' else 'Absence de Couverture',
                'issue': 'No bonds or gold in portfolio' if lang == 'en' else 'Aucune obligation ni or dans le portefeuille',
                'solution': 'Add 10-20% AGG (bonds) and 5-10% GLD (gold) for stability' if lang == 'en'
                           else 'Ajouter 10-20% AGG (obligations) et 5-10% GLD (or)',
                'impact': 'Robustness +6 pts' if lang == 'en' else 'Robustesse +6 pts',
            })
        
        # Low diversification
        if len(self.tickers) < 5:
            suggestions.append({
                'priority': 'HIGH',
                'type': 'warning',
                'title': 'Low Diversification' if lang == 'en' else 'Faible Diversification',
                'issue': f'Only {len(self.tickers)} assets' if lang == 'en' else f'Seulement {len(self.tickers)} actifs',
                'solution': 'Add 3-5 more assets from different sectors/geographies' if lang == 'en'
                           else 'Ajouter 3-5 actifs de secteurs/géographies différents',
                'impact': 'Robustness +12 pts' if lang == 'en' else 'Robustesse +12 pts',
            })
        
        # High volatility
        if metrics['volatility'] > 0.25:
            suggestions.append({
                'priority': 'MEDIUM',
                'type': 'warning',
                'title': 'High Volatility' if lang == 'en' else 'Volatilité Élevée',
                'issue': f'{metrics["volatility"]*100:.0f}% annual volatility' if lang == 'en' else f'{metrics["volatility"]*100:.0f}% de volatilité annuelle',
                'solution': 'Reduce high-vol assets. Add AGG (bonds) for stability' if lang == 'en'
                           else 'Réduire actifs volatils. Ajouter AGG (obligations)',
                'impact': 'Robustness +7 pts' if lang == 'en' else 'Robustesse +7 pts',
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
                    'issue': f'Volatility {vol*100:.0f}% > recommended 12%' if lang == 'en' else f'Volatilité {vol*100:.0f}% > recommandé 12%',
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
                    'issue': 'Missing safe-haven assets' if lang == 'en' else 'Actifs refuge absents',
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
                    'issue': f'{stock_exposure*100:.0f}% stocks (target 60%)' if lang == 'en' else f'{stock_exposure*100:.0f}% actions (cible 60%)',
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
                    'issue': 'Missing high-growth exposure' if lang == 'en' else 'Exposition croissance insuffisante',
                    'solution': 'Consider QQQ (Nasdaq), NVDA, or 5-10% BTC-USD' if lang == 'en'
                               else 'Considérer QQQ (Nasdaq), NVDA, ou 5-10% BTC-USD',
                    'recommended': ['QQQ', 'NVDA', 'BTC-USD', 'TSLA'],
                })
        
        return suggestions
    
    def stress_test_scenarios(self):
        """Simulate historical crisis scenarios using independent yfinance downloads."""
        scenarios = {
            "2008 Crisis": {
                "start": "2008-09-01", "end": "2009-03-01",
                "market_drop": -0.40,
                "description": "Financial crisis, market -40%",
            },
            "COVID-2020": {
                "start": "2020-02-01", "end": "2020-04-30",
                "market_drop": -0.30,
                "description": "Pandemic crash, market -30%",
            },
            "Inflation 2022": {
                "start": "2022-01-01", "end": "2022-10-01",
                "market_drop": -0.20,
                "description": "Rate hikes, market -20%",
            },
        }

        results = {}
        for name, scenario in scenarios.items():
            try:
                raw = yf.download(
                    self.tickers,
                    start=scenario["start"],
                    end=scenario["end"],
                    auto_adjust=True,
                    progress=False,
                )
                if raw.empty:
                    continue
                prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
                # Keep only tickers that actually downloaded
                available = [t for t in self.tickers if t in prices.columns]
                if not available:
                    continue
                prices = prices[available].dropna(how="all")
                if len(prices) < 5:
                    continue
                weights_arr = np.array([self.weights[t] for t in available])
                weights_arr /= weights_arr.sum()  # renormalise for missing tickers
                rets = prices.pct_change().dropna()
                port_rets = rets @ weights_arr
                total_ret = (1 + port_rets).prod() - 1
                results[name] = {
                    'portfolio_loss': total_ret,
                    'market_loss': scenario['market_drop'],
                    'resilience': 1 - abs(total_ret / scenario['market_drop']),
                    'recovery_days': len(prices),
                    'description': scenario['description'],
                }
            except Exception:
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
            interp_fr = {
                "Very Robust": "Très Robuste", "Robust": "Robuste",
                "Fragile": "Fragile", "High Risk": "Risque Élevé",
            }
            interp_display = interp_fr.get(robustness['interpretation'], robustness['interpretation'])
            summary = f"""
            Votre portefeuille est **fortement exposé au secteur {dominant_sector}** ({sector_exposure*100:.0f}%)
            et aux marchés **{dominant_geo}** ({geo_exposure*100:.0f}%).
            La diversification est **{div_status}** sur {len(self.tickers)} actifs.
            La volatilité est **{risk_level}** ({vol*100:.0f}% annuelle).
            Score de robustesse: **{robustness['total']}/100 ({interp_display})**.
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


# The name the legacy entry point and any saved user code still use.
UltimatePortfolioAnalyzer = PortfolioAnalyzer
