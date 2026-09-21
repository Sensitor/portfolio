"""
Bilingual strings for the Sensitor pages.

Kept separate from the legacy `T` dict in the main module so the new product
surface can be translated independently. `tr()` falls back to English, then to the
key itself, so a missing translation degrades to readable text rather than a
KeyError mid-render.

Metric definitions live here too (`DEFS`) and feed the tooltip system: every
quantitative metric on screen can be explained without leaving the app.


Two dictionaries live here, on purpose.

`STRINGS` is the Sensitor surface — the twelve Intelligence and Workspace pages.
`LEGACY_STRINGS` is the original product's dictionary, feeding the seven older
pages. They are kept apart rather than merged because merging them would mean
editing strings the legacy pages render, and Phase 2 changes where code lives,
not what users read. A later phase can converge them deliberately.
"""

from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {
    # ── Product / navigation ────────────────────────────────────────────────
    "product": {"en": "Sensitor Portfolio Intelligence", "fr": "Sensitor Portfolio Intelligence"},
    "product_short": {"en": "Sensitor", "fr": "Sensitor"},
    "nav_overview": {"en": "Overview", "fr": "Vue d'Ensemble"},
    "nav_performance": {"en": "Performance", "fr": "Performance"},
    "nav_health": {"en": "Portfolio Health", "fr": "Santé du Portefeuille"},
    "nav_xray": {"en": "Portfolio X-Ray", "fr": "Radiographie"},
    "nav_risk": {"en": "Risk Lab", "fr": "Laboratoire de Risque"},

    # ── Shared ───────────────────────────────────────────────────────────────
    "portfolio": {"en": "Portfolio", "fr": "Portefeuille"},
    "benchmark": {"en": "Benchmark", "fr": "Indice de Référence"},
    "vs": {"en": "vs", "fr": "vs"},
    "period": {"en": "Period", "fr": "Période"},
    "assets": {"en": "Assets", "fr": "Actifs"},
    "weight": {"en": "Weight", "fr": "Poids"},
    "value": {"en": "Value", "fr": "Valeur"},
    "no_data_title": {"en": "No portfolio loaded", "fr": "Aucun portefeuille chargé"},
    "no_data_body": {
        "en": "Build a portfolio or enter your real holdings to unlock the full analysis suite.",
        "fr": "Créez un portefeuille ou saisissez vos positions réelles pour débloquer l'analyse complète.",
    },
    "short_history_title": {"en": "History too short", "fr": "Historique trop court"},
    "short_history_body": {
        "en": "At least 20 trading days of shared history are needed for these statistics to mean anything.",
        "fr": "Au moins 20 jours de bourse d'historique commun sont nécessaires pour que ces statistiques aient un sens.",
    },
    "single_asset_note": {
        "en": "With a single holding there is nothing to diversify across, so correlation, risk contribution and concentration analysis are unavailable.",
        "fr": "Avec une seule position, il n'y a rien à diversifier : corrélation, contribution au risque et analyse de concentration sont indisponibles.",
    },

    # ── Overview ─────────────────────────────────────────────────────────────
    "overview_sub": {
        "en": "Everything that matters about this portfolio, on one screen.",
        "fr": "L'essentiel de ce portefeuille, sur un seul écran.",
    },
    "portfolio_value": {"en": "Portfolio Value", "fr": "Valeur du Portefeuille"},
    "total_return": {"en": "Total Return", "fr": "Rendement Total"},
    "annualized_return": {"en": "Annualized Return", "fr": "Rendement Annualisé"},
    "volatility": {"en": "Volatility", "fr": "Volatilité"},
    "sharpe_ratio": {"en": "Sharpe Ratio", "fr": "Ratio de Sharpe"},
    "max_drawdown": {"en": "Max Drawdown", "fr": "Perte Maximale"},
    "health_score": {"en": "Health Score", "fr": "Score de Santé"},
    "risk_concentration": {"en": "Risk Concentration", "fr": "Concentration du Risque"},
    "growth_of_capital": {"en": "Growth of Capital", "fr": "Évolution du Capital"},
    "things_to_review": {"en": "Things to Review", "fr": "Points à Examiner"},
    "no_signals": {"en": "No thresholds crossed", "fr": "Aucun seuil franchi"},
    "no_signals_body": {
        "en": "None of the configured concentration, correlation, exposure or drawdown thresholds were crossed for this portfolio.",
        "fr": "Aucun des seuils configurés de concentration, corrélation, exposition ou drawdown n'a été franchi pour ce portefeuille.",
    },
    "what_you_own": {"en": "What You Actually Own", "fr": "Ce Que Vous Détenez Réellement"},
    "holdings": {"en": "Holdings", "fr": "Positions"},
    "of_risk": {"en": "of risk", "fr": "du risque"},
    "top_risk_driver": {"en": "Top Risk Driver", "fr": "Principal Facteur de Risque"},

    # ── Performance ──────────────────────────────────────────────────────────
    "performance_sub": {
        "en": "How the portfolio performed, and what drove it.",
        "fr": "Comment le portefeuille a performé, et ce qui l'a porté.",
    },
    "cumulative_performance": {"en": "Cumulative Performance", "fr": "Performance Cumulée"},
    "rolling_metrics": {"en": "Rolling Metrics", "fr": "Métriques Glissantes"},
    "rolling_volatility": {"en": "Rolling Volatility", "fr": "Volatilité Glissante"},
    "rolling_sharpe": {"en": "Rolling Sharpe", "fr": "Sharpe Glissant"},
    "rolling_return": {"en": "Rolling Return", "fr": "Rendement Glissant"},
    "attribution": {"en": "Performance Attribution", "fr": "Attribution de Performance"},
    "attribution_sub": {
        "en": "Contribution of each holding to the portfolio's total return — the bars sum to the headline figure.",
        "fr": "Contribution de chaque position au rendement total — la somme des barres égale le chiffre principal.",
    },
    "benchmark_analysis": {"en": "Benchmark Analysis", "fr": "Analyse Comparative"},
    "beta": {"en": "Beta", "fr": "Bêta"},
    "alpha": {"en": "Alpha", "fr": "Alpha"},
    "r_squared": {"en": "R²", "fr": "R²"},
    "tracking_error": {"en": "Tracking Error", "fr": "Tracking Error"},
    "information_ratio": {"en": "Information Ratio", "fr": "Ratio d'Information"},
    "up_capture": {"en": "Up Capture", "fr": "Capture Hausse"},
    "down_capture": {"en": "Down Capture", "fr": "Capture Baisse"},
    "active_return": {"en": "Active Return", "fr": "Rendement Actif"},
    "benchmark_unavailable": {
        "en": "Benchmark data could not be retrieved. Portfolio figures are unaffected.",
        "fr": "Les données de l'indice n'ont pas pu être récupérées. Les chiffres du portefeuille ne sont pas affectés.",
    },
    "best_day": {"en": "Best Day", "fr": "Meilleur Jour"},
    "worst_day": {"en": "Worst Day", "fr": "Pire Jour"},
    "positive_days": {"en": "Positive Days", "fr": "Jours Positifs"},
    "monthly_returns": {"en": "Monthly Returns", "fr": "Rendements Mensuels"},

    # ── Health ───────────────────────────────────────────────────────────────
    "health_sub": {
        "en": "One score, five components, every threshold shown.",
        "fr": "Un score, cinq composantes, tous les seuils affichés.",
    },
    "score_breakdown": {"en": "Score Breakdown", "fr": "Décomposition du Score"},
    "why_this_score": {"en": "Why this score?", "fr": "Pourquoi ce score ?"},
    "c_performance": {"en": "Performance", "fr": "Performance"},
    "c_risk": {"en": "Risk", "fr": "Risque"},
    "c_diversification": {"en": "Diversification", "fr": "Diversification"},
    "c_concentration": {"en": "Concentration", "fr": "Concentration"},
    "c_liquidity": {"en": "Liquidity", "fr": "Liquidité"},
    "strongest": {"en": "Strongest component", "fr": "Composante la plus forte"},
    "weakest": {"en": "Weakest component", "fr": "Composante la plus faible"},
    "portfolio_dna": {"en": "Portfolio DNA", "fr": "ADN du Portefeuille"},
    "dna_sub": {
        "en": "The shape of this portfolio's character — a profile, not a grade.",
        "fr": "La forme du caractère de ce portefeuille — un profil, pas une note.",
    },
    "dna_growth": {"en": "Growth", "fr": "Croissance"},
    "dna_risk": {"en": "Risk Taken", "fr": "Risque Pris"},
    "dna_diversification": {"en": "Diversification", "fr": "Diversification"},
    "dna_liquidity": {"en": "Liquidity", "fr": "Liquidité"},
    "dna_income": {"en": "Income", "fr": "Revenu"},
    "dna_defensive": {"en": "Defensive", "fr": "Défensif"},
    "band_excellent": {"en": "Excellent", "fr": "Excellent"},
    "band_solid": {"en": "Solid", "fr": "Solide"},
    "band_mixed": {"en": "Mixed", "fr": "Mitigé"},
    "band_fragile": {"en": "Fragile", "fr": "Fragile"},
    "band_weak": {"en": "Weak", "fr": "Faible"},
    "measured": {"en": "Measured", "fr": "Mesuré"},
    "reference": {"en": "Reference", "fr": "Référence"},
    "health_method": {
        "en": "The score weights Performance 25, Risk 25, Diversification 20, Concentration 20 and Liquidity 10. Risk is scored against your stated profile's tolerance, so an aggressive profile is not penalised for holding volatile assets. These weights are a reasoned editorial choice, not an industry standard — the score describes the portfolio's structure over the analysed period and is not a forecast or a recommendation.",
        "fr": "Le score pondère Performance 25, Risque 25, Diversification 20, Concentration 20 et Liquidité 10. Le risque est évalué selon la tolérance de votre profil déclaré : un profil agressif n'est donc pas pénalisé pour détenir des actifs volatils. Ces pondérations sont un choix éditorial raisonné, pas un standard de marché — le score décrit la structure du portefeuille sur la période analysée ; ce n'est ni une prévision ni une recommandation.",
    },

    # ── Risk Lab ─────────────────────────────────────────────────────────────
    "risk_sub": {
        "en": "How much risk you carry, and exactly where it comes from.",
        "fr": "Combien de risque vous portez, et d'où il vient exactement.",
    },
    "risk_metrics": {"en": "Risk Metrics", "fr": "Métriques de Risque"},
    "downside_volatility": {"en": "Downside Volatility", "fr": "Volatilité Baissière"},
    "sortino_ratio": {"en": "Sortino Ratio", "fr": "Ratio de Sortino"},
    "calmar_ratio": {"en": "Calmar Ratio", "fr": "Ratio de Calmar"},
    "var_95": {"en": "VaR 95%", "fr": "VaR 95%"},
    "var_99": {"en": "VaR 99%", "fr": "VaR 99%"},
    "cvar_95": {"en": "CVaR 95%", "fr": "CVaR 95%"},
    "risk_contribution": {"en": "Risk Contribution", "fr": "Contribution au Risque"},
    "risk_contribution_sub": {
        "en": "A holding can be a small share of your capital and a large share of your risk. This is where that gap shows.",
        "fr": "Une position peut représenter une petite part de votre capital et une grande part de votre risque. C'est ici que l'écart apparaît.",
    },
    "correlation_matrix": {"en": "Correlation Matrix", "fr": "Matrice de Corrélation"},
    "avg_correlation": {"en": "Average Correlation", "fr": "Corrélation Moyenne"},
    "effective_assets": {"en": "Effective Assets", "fr": "Actifs Effectifs"},
    "diversification_efficiency": {"en": "Diversification Efficiency", "fr": "Efficacité de Diversification"},
    "diversification_ratio": {"en": "Diversification Ratio", "fr": "Ratio de Diversification"},
    "concentration_analysis": {"en": "Concentration Analysis", "fr": "Analyse de Concentration"},
    "concentration_curve": {"en": "Concentration Curve", "fr": "Courbe de Concentration"},
    "top1": {"en": "Largest Position", "fr": "Position la Plus Grande"},
    "top3": {"en": "Top 3", "fr": "Top 3"},
    "top5": {"en": "Top 5", "fr": "Top 5"},
    "hhi": {"en": "HHI", "fr": "IHH"},
    "drawdown_analysis": {"en": "Drawdown Analysis", "fr": "Analyse des Drawdowns"},
    "current_drawdown": {"en": "Current Drawdown", "fr": "Drawdown Actuel"},
    "avg_drawdown": {"en": "Average Drawdown", "fr": "Drawdown Moyen"},
    "time_underwater": {"en": "Time Underwater", "fr": "Temps Sous l'Eau"},
    "avg_recovery": {"en": "Average Recovery", "fr": "Récupération Moyenne"},
    "longest_underwater": {"en": "Longest Underwater", "fr": "Plus Longue Période Sous l'Eau"},
    "underwater_chart": {"en": "Underwater Chart", "fr": "Courbe Sous l'Eau"},
    "worst_drawdowns": {"en": "Worst Drawdowns", "fr": "Pires Drawdowns"},
    "depth": {"en": "Depth", "fr": "Profondeur"},
    "peak": {"en": "Peak", "fr": "Sommet"},
    "trough": {"en": "Trough", "fr": "Creux"},
    "recovery": {"en": "Recovery", "fr": "Récupération"},
    "ongoing": {"en": "Ongoing", "fr": "En cours"},
    "days": {"en": "days", "fr": "jours"},
    "return_distribution": {"en": "Return Distribution", "fr": "Distribution des Rendements"},
    "skewness": {"en": "Skewness", "fr": "Asymétrie"},
    "kurtosis": {"en": "Excess Kurtosis", "fr": "Kurtosis Excédentaire"},
    "median": {"en": "Median", "fr": "Médiane"},
    "historical": {"en": "Historical", "fr": "Historique"},
    "parametric": {"en": "Parametric", "fr": "Paramétrique"},
    "var_method_note": {
        "en": "Historical VaR reads the loss directly off the observed distribution. Parametric VaR assumes returns are normally distributed, which understates tail losses for assets with fat tails. Both are shown so the gap between them stays visible.",
        "fr": "La VaR historique lit la perte directement sur la distribution observée. La VaR paramétrique suppose des rendements normalement distribués, ce qui sous-estime les pertes extrêmes pour les actifs à queues épaisses. Les deux sont affichées pour que l'écart reste visible.",
    },

    # ── X-Ray ────────────────────────────────────────────────────────────────
    "xray_sub": {
        "en": "Funds unpacked into their underlying holdings — what you own, not which tickers you hold.",
        "fr": "Les fonds décomposés en leurs sous-jacents — ce que vous possédez, pas les tickers que vous détenez.",
    },
    "lookthrough": {"en": "Look-Through Exposure", "fr": "Exposition par Transparence"},
    "direct_holdings": {"en": "Direct Holdings", "fr": "Positions Directes"},
    "headline_exposures": {"en": "Headline Exposures", "fr": "Expositions Principales"},
    "xray_note": {
        "en": "Fund breakdowns are curated reference data approximating published fact sheets, not live holdings, and drift as funds rebalance. They reveal structural exposure; they are not the fund's official allocation. Individual stocks resolve to a single bucket per dimension.",
        "fr": "Les décompositions de fonds sont des données de référence approximant les fiches produits publiées, non des positions en temps réel, et évoluent au fil des rééquilibrages. Elles révèlent l'exposition structurelle ; ce n'est pas l'allocation officielle du fonds. Les actions individuelles sont affectées à un seul bucket par dimension.",
    },
    "hidden_exposure": {"en": "Hidden Exposure", "fr": "Exposition Cachée"},
    "hidden_exposure_sub": {
        "en": "Direct ticker weight versus resolved exposure, for the buckets where the two diverge most.",
        "fr": "Poids direct des tickers contre exposition résolue, pour les buckets où l'écart est le plus grand.",
    },
# ── Phase 2: Stress Lab ─────────────────────────────────────────────────
    "nav_stress": {"en": "Stress Lab", "fr": "Laboratoire de Stress"},
    "stress_sub": {
        "en": "What this allocation did in past crises, and what it would do under shocks you choose.",
        "fr": "Ce que cette allocation a fait lors des crises passées, et ce qu'elle ferait sous des chocs que vous choisissez.",
    },
    "historical_scenarios": {"en": "Historical Scenarios", "fr": "Scénarios Historiques"},
    "historical_sub": {
        "en": "Real prices over real crisis windows — arithmetic on history, not a model.",
        "fr": "Prix réels sur de vraies fenêtres de crise — de l'arithmétique sur l'historique, pas un modèle.",
    },
    "custom_stress": {"en": "Custom Stress Test", "fr": "Test de Stress Personnalisé"},
    "custom_stress_sub": {
        "en": "Set a move on each driver. Each holding responds through its estimated beta.",
        "fr": "Définissez un mouvement sur chaque facteur. Chaque position réagit via son bêta estimé.",
    },
    "portfolio_impact": {"en": "Portfolio Impact", "fr": "Impact sur le Portefeuille"},
    "benchmark_impact": {"en": "Benchmark Impact", "fr": "Impact sur l'Indice"},
    "coverage": {"en": "Coverage", "fr": "Couverture"},
    "coverage_warning": {
        "en": "Not enough of the portfolio had price history in this window for the result to describe the portfolio you hold.",
        "fr": "Une part trop faible du portefeuille disposait d'un historique sur cette fenêtre pour que le résultat décrive le portefeuille que vous détenez.",
    },
    "no_history_window": {"en": "No data in this window", "fr": "Aucune donnée sur cette fenêtre"},
    "missing_holdings": {"en": "Holdings without history", "fr": "Positions sans historique"},
    "worst_contributor": {"en": "Worst contributor", "fr": "Pire contributeur"},
    "best_contributor": {"en": "Best contributor", "fr": "Meilleur contributeur"},
    "apply_shock": {"en": "Apply shock", "fr": "Appliquer le choc"},
    "reset_shock": {"en": "Reset", "fr": "Réinitialiser"},
    "before": {"en": "Before", "fr": "Avant"},
    "after": {"en": "After", "fr": "Après"},
    "stressed": {"en": "Stressed", "fr": "Sous stress"},
    "estimated_impact": {"en": "Estimated Impact", "fr": "Impact Estimé"},
    "shock_note": {
        "en": "Each holding's response is estimated from its regression betas to the drivers above, measured over the selected period. This is a first-order linear estimate calibrated on ordinary conditions: in a real crash correlations rise toward one, so diversification typically helps less than these betas suggest. Treat the figure as an order of magnitude, not a forecast.",
        "fr": "La réaction de chaque position est estimée à partir de ses bêtas de régression sur les facteurs ci-dessus, mesurés sur la période sélectionnée. C'est une estimation linéaire du premier ordre calibrée en conditions normales : lors d'un vrai krach, les corrélations montent vers 1, et la diversification protège donc généralement moins que ne le suggèrent ces bêtas. À prendre comme un ordre de grandeur, pas comme une prévision.",
    },
    "historical_note": {
        "en": "Each scenario replays the real prices of the holdings that existed at the time. Holdings with no history in a window are excluded and the covered share of the portfolio is shown, because a crisis replayed on part of the book does not describe the whole book.",
        "fr": "Chaque scénario rejoue les prix réels des positions qui existaient à l'époque. Les positions sans historique sur une fenêtre sont exclues et la part couverte du portefeuille est affichée : une crise rejouée sur une partie du portefeuille ne décrit pas l'ensemble.",
    },
    "fit_quality": {"en": "Average fit", "fr": "Qualité d'ajustement moyenne"},

    # ── Phase 2: Optimize ───────────────────────────────────────────────────
    "nav_optimize": {"en": "Optimize", "fr": "Optimiser"},
    "optimize_sub": {
        "en": "The risk/return geometry of your holdings, and where your allocation sits on it.",
        "fr": "La géométrie risque/rendement de vos positions, et où se situe votre allocation.",
    },
    "efficient_frontier": {"en": "Efficient Frontier", "fr": "Frontière Efficiente"},
    "current_portfolio": {"en": "Current Portfolio", "fr": "Portefeuille Actuel"},
    "max_sharpe_portfolio": {"en": "Max Sharpe", "fr": "Sharpe Maximal"},
    "min_vol_portfolio": {"en": "Minimum Volatility", "fr": "Volatilité Minimale"},
    "expected_return": {"en": "Expected Return", "fr": "Rendement Attendu"},
    "allocation_change": {"en": "Allocation Change", "fr": "Changement d'Allocation"},
    "compare_portfolios": {"en": "Compare Allocations", "fr": "Comparer les Allocations"},
    "target_allocation": {"en": "Target", "fr": "Cible"},
    "max_position": {"en": "Max position size", "fr": "Taille max par position"},
    "frontier_note": {
        "en": "Expected returns and covariances are estimated from the selected window. Mean-variance optimisation is highly sensitive to the expected-return estimates — small input changes move the optimal weights a lot — and a position cap is applied by default because unconstrained solutions pile into whichever asset happened to perform best. This shows the geometry of a set of assets over one past period; it is not a recommendation and past performance does not predict future returns.",
        "fr": "Les rendements attendus et les covariances sont estimés sur la fenêtre sélectionnée. L'optimisation moyenne-variance est très sensible aux estimations de rendement attendu — de petits changements d'entrée déplacent beaucoup les poids optimaux — et un plafond par position est appliqué par défaut, car les solutions sans contrainte se concentrent sur l'actif qui a le mieux performé. Ceci montre la géométrie d'un ensemble d'actifs sur une période passée ; ce n'est pas une recommandation et les performances passées ne préjugent pas des performances futures.",
    },
    "frontier_unavailable": {
        "en": "At least two holdings and 60 trading days of shared history are needed to build a frontier.",
        "fr": "Au moins deux positions et 60 jours de bourse d'historique commun sont nécessaires pour construire une frontière.",
    },

    # ── Phase 2: Factor exposure ────────────────────────────────────────────
    "factor_exposure": {"en": "Factor Exposure", "fr": "Exposition Factorielle"},
    "factor_sub": {
        "en": "Which systematic risks this portfolio is actually taking, estimated against liquid ETF proxies.",
        "fr": "Quels risques systématiques ce portefeuille prend réellement, estimés contre des proxies ETF liquides.",
    },
    "factor_loading": {"en": "Loading", "fr": "Charge"},
    "factor_unavailable": {
        "en": "Factor proxy data could not be retrieved. Everything else on this page is unaffected.",
        "fr": "Les données des proxies factoriels n'ont pas pu être récupérées. Le reste de cette page n'est pas affecté.",
    },
    "explained_variance": {"en": "Explained Variance", "fr": "Variance Expliquée"},
    "not_significant": {"en": "not significant", "fr": "non significatif"},
    # ── Phase 3: Simulator ──────────────────────────────────────────────────
    "nav_simulator": {"en": "Simulator", "fr": "Simulateur"},
    "simulator_sub": {
        "en": "Change the allocation and watch every number move. Nothing here touches your saved portfolio.",
        "fr": "Modifiez l'allocation et voyez chaque chiffre bouger. Rien ici ne modifie votre portefeuille enregistré.",
    },
    "what_if": {"en": "What-If Allocation", "fr": "Allocation Hypothétique"},
    "what_if_sub": {
        "en": "Move a slider and the metrics below recompute on the same history.",
        "fr": "Déplacez un curseur et les métriques ci-dessous se recalculent sur le même historique.",
    },
    "reset_allocation": {"en": "Reset to current", "fr": "Revenir à l'actuel"},
    "normalise_note": {
        "en": "Weights are rescaled to 100% after every change, so the sliders show relative size rather than an absolute amount.",
        "fr": "Les poids sont ramenés à 100% après chaque modification : les curseurs indiquent donc une taille relative, pas un montant absolu.",
    },
    "simulated": {"en": "Simulated", "fr": "Simulé"},
    "current": {"en": "Current", "fr": "Actuel"},
    "impact": {"en": "Impact", "fr": "Impact"},
    "no_change_yet": {
        "en": "Move a slider to see the effect. Everything below currently matches your portfolio.",
        "fr": "Déplacez un curseur pour voir l'effet. Tout ce qui suit correspond actuellement à votre portefeuille.",
    },
    "simulation_note": {
        "en": "Every figure restates the same historical window under different weights, rebalanced daily. It shows how this allocation would have behaved over the period analysed — it is not a projection, and an allocation that looked better in the past is not thereby better.",
        "fr": "Chaque chiffre reformule la même fenêtre historique sous des poids différents, avec rééquilibrage quotidien. Cela montre comment cette allocation se serait comportée sur la période analysée — ce n'est pas une projection, et une allocation qui paraissait meilleure par le passé ne l'est pas pour autant.",
    },
    "comparison": {"en": "Allocation Comparison", "fr": "Comparaison d'Allocations"},
    "comparison_sub": {
        "en": "Your allocation against the optimiser's and a defensive alternative, on identical history.",
        "fr": "Votre allocation face à celle de l'optimiseur et à une variante défensive, sur un historique identique.",
    },
    "conservative": {"en": "Conservative", "fr": "Prudent"},
    "equal_weight": {"en": "Equal Weight", "fr": "Équipondéré"},
    "best": {"en": "best", "fr": "meilleur"},

    # ── Phase 3: Monte Carlo ────────────────────────────────────────────────
    "monte_carlo": {"en": "Monte Carlo Projection", "fr": "Projection Monte Carlo"},
    "monte_carlo_sub": {
        "en": "Thousands of possible paths drawn from this portfolio's own return history.",
        "fr": "Des milliers de trajectoires possibles tirées de l'historique de rendement de ce portefeuille.",
    },
    "horizon": {"en": "Horizon", "fr": "Horizon"},
    "simulations": {"en": "Simulations", "fr": "Simulations"},
    "annual_contribution": {"en": "Annual contribution", "fr": "Versement annuel"},
    "method": {"en": "Method", "fr": "Méthode"},
    "method_bootstrap": {"en": "Bootstrap (historical)", "fr": "Bootstrap (historique)"},
    "method_parametric": {"en": "Parametric (normal)", "fr": "Paramétrique (normale)"},
    "median_outcome": {"en": "Median Outcome", "fr": "Résultat Médian"},
    "pessimistic": {"en": "Pessimistic (P10)", "fr": "Pessimiste (P10)"},
    "optimistic": {"en": "Optimistic (P90)", "fr": "Optimiste (P90)"},
    "prob_loss": {"en": "Probability of Loss", "fr": "Probabilité de Perte"},
    "prob_targets": {"en": "Probability of Reaching", "fr": "Probabilité d'Atteindre"},
    "terminal_values": {"en": "Terminal Values", "fr": "Valeurs Finales"},
    "years_label": {"en": "years", "fr": "ans"},
    "mc_note": {
        "en": "Bootstrap resamples this portfolio's actual daily returns, inheriting their real fat tails; the parametric method draws from a fitted normal distribution and systematically understates extreme outcomes. Both assume the future return distribution resembles the window sampled — no regime change, no structural break, no valuation anchor. A long horizon projected from a short history is an extrapolation of that window, not a forecast.",
        "fr": "Le bootstrap rééchantillonne les rendements quotidiens réels de ce portefeuille, en héritant de leurs vraies queues épaisses ; la méthode paramétrique tire d'une loi normale ajustée et sous-estime systématiquement les résultats extrêmes. Les deux supposent que la distribution future des rendements ressemble à la fenêtre échantillonnée — sans changement de régime, ni rupture structurelle, ni ancrage de valorisation. Un horizon long projeté depuis un historique court est une extrapolation de cette fenêtre, pas une prévision.",
    },
    "mc_history_warning": {
        "en": "The projection horizon is much longer than the history it was drawn from, which makes the spread of outcomes less meaningful.",
        "fr": "L'horizon de projection est bien plus long que l'historique dont il est tiré, ce qui rend la dispersion des résultats moins significative.",
    },

    # ── Phase 3: Copilot ────────────────────────────────────────────────────
    "nav_copilot": {"en": "Copilot", "fr": "Copilote"},
    "copilot_sub": {
        "en": "Patterns worth examining, each paired with a change you can simulate.",
        "fr": "Des configurations à examiner, chacune associée à un changement que vous pouvez simuler.",
    },
    "nothing_flagged": {"en": "Nothing flagged", "fr": "Rien à signaler"},
    "nothing_flagged_body": {
        "en": "None of the configured thresholds were crossed by this allocation. That means it sits inside the documented limits, not that it is well suited to you.",
        "fr": "Aucun des seuils configurés n'a été franchi par cette allocation. Cela signifie qu'elle reste dans les limites documentées, pas qu'elle vous convient.",
    },
    "why_question": {"en": "Why?", "fr": "Pourquoi ?"},
    "show_me": {"en": "Show me", "fr": "Montrez-moi"},
    "simulate": {"en": "Simulate", "fr": "Simuler"},
    "ignore": {"en": "Ignore", "fr": "Ignorer"},
    "restore_ignored": {"en": "Restore ignored items", "fr": "Restaurer les éléments ignorés"},
    "ignored_count": {"en": "ignored", "fr": "ignorés"},
    "proposed_change": {"en": "Change to simulate", "fr": "Changement à simuler"},
    "evidence": {"en": "Evidence", "fr": "Constat"},
    "copilot_note": {
        "en": "These are observations against documented thresholds, not advice. Each proposed change exists so you can see its trade-off: trimming a volatile holding usually lowers both risk and past return, and the impact table shows both. No item claims the change would improve future outcomes — the simulation can only restate the past under different weights.",
        "fr": "Ce sont des observations mesurées contre des seuils documentés, pas des conseils. Chaque changement proposé existe pour que vous en voyiez l'arbitrage : réduire une position volatile diminue généralement à la fois le risque et le rendement passé, et le tableau d'impact montre les deux. Aucun élément ne prétend que le changement améliorerait les résultats futurs — la simulation ne fait que reformuler le passé sous d'autres poids.",
    },
    "apply_to_simulator": {"en": "Open in Simulator", "fr": "Ouvrir dans le Simulateur"},
    "improves": {"en": "improves", "fr": "améliore"},
    "worsens": {"en": "worsens", "fr": "dégrade"},

    # ── Phase 4: Portfolios & persistence ───────────────────────────────────
    "nav_portfolios": {"en": "Portfolios", "fr": "Portefeuilles"},
    "portfolios_sub": {
        "en": "Save an allocation, reload it later, and keep a record of how it changed.",
        "fr": "Enregistrez une allocation, rechargez-la plus tard, et gardez une trace de son évolution.",
    },
    "save_current": {"en": "Save current portfolio", "fr": "Enregistrer le portefeuille actuel"},
    "portfolio_name": {"en": "Name", "fr": "Nom"},
    "client_name": {"en": "Client (optional)", "fr": "Client (optionnel)"},
    "notes": {"en": "Notes", "fr": "Notes"},
    "save": {"en": "Save", "fr": "Enregistrer"},
    "load": {"en": "Load", "fr": "Charger"},
    "delete": {"en": "Delete", "fr": "Supprimer"},
    "confirm_delete": {"en": "Confirm delete", "fr": "Confirmer la suppression"},
    "saved_portfolios": {"en": "Saved Portfolios", "fr": "Portefeuilles Enregistrés"},
    "no_saved_portfolios": {"en": "Nothing saved yet", "fr": "Rien d'enregistré pour l'instant"},
    "no_saved_body": {
        "en": "Save the portfolio you are analysing to reload it in a later session and start building its history.",
        "fr": "Enregistrez le portefeuille que vous analysez pour le recharger lors d'une prochaine session et commencer à constituer son historique.",
    },
    "take_snapshot": {"en": "Take snapshot", "fr": "Prendre un instantané"},
    "snapshots": {"en": "History", "fr": "Historique"},
    "snapshot_taken": {"en": "Snapshot recorded", "fr": "Instantané enregistré"},
    "portfolio_saved": {"en": "Portfolio saved", "fr": "Portefeuille enregistré"},
    "portfolio_loaded": {"en": "Portfolio loaded", "fr": "Portefeuille chargé"},
    "last_updated": {"en": "Updated", "fr": "Mis à jour"},
    "taken_at": {"en": "Date", "fr": "Date"},
    "no_snapshots": {
        "en": "No snapshots yet. A snapshot records the allocation and its metrics at a moment in time — the app can always recompute today's figures, but it cannot recover what the allocation was last month unless it was written down.",
        "fr": "Aucun instantané. Un instantané enregistre l'allocation et ses métriques à un instant donné — l'application peut toujours recalculer les chiffres du jour, mais elle ne peut pas retrouver ce qu'était l'allocation le mois dernier si cela n'a pas été consigné.",
    },
    "storage_note": {
        "en": "Data is stored in a local SQLite file on whatever machine runs this app, and is never sent anywhere. On Streamlit Cloud that filesystem is ephemeral: saved portfolios are wiped whenever the app restarts, redeploys or sleeps. For durable storage, point SENSITOR_DB_PATH at a persistent volume or connect an external database.",
        "fr": "Les données sont stockées dans un fichier SQLite local sur la machine qui exécute l'application, et ne sont envoyées nulle part. Sur Streamlit Cloud ce système de fichiers est éphémère : les portefeuilles enregistrés sont effacés à chaque redémarrage, redéploiement ou mise en veille. Pour un stockage durable, pointez SENSITOR_DB_PATH vers un volume persistant ou connectez une base externe.",
    },
    "sign_in_required": {"en": "Sign in to save portfolios", "fr": "Connectez-vous pour enregistrer des portefeuilles"},
    "sign_in_body": {
        "en": "Saved portfolios are filed under your email address. Enter one on the Account page to use this feature.",
        "fr": "Les portefeuilles enregistrés sont classés sous votre adresse email. Saisissez-en une sur la page Compte pour utiliser cette fonctionnalité.",
    },

    # ── Phase 4: Reports ────────────────────────────────────────────────────
    "nav_reports": {"en": "Reports", "fr": "Rapports"},
    "reports_sub": {
        "en": "A self-contained document you can send to a client or print to PDF.",
        "fr": "Un document autonome que vous pouvez envoyer à un client ou imprimer en PDF.",
    },
    "report_title": {"en": "Report title", "fr": "Titre du rapport"},
    "prepared_by": {"en": "Prepared by", "fr": "Préparé par"},
    "include_sections": {"en": "Sections to include", "fr": "Sections à inclure"},
    "generate_report": {"en": "Generate report", "fr": "Générer le rapport"},
    "download_report": {"en": "Download report", "fr": "Télécharger le rapport"},
    "report_ready": {"en": "Report ready", "fr": "Rapport prêt"},
    "report_preview": {"en": "Preview", "fr": "Aperçu"},
    "report_format_note": {
        "en": "The report is a single self-contained HTML file: no scripts, no external requests, every chart drawn as inline SVG. It opens anywhere and works offline. To get a PDF, open it and print to PDF from your browser — the page breaks and margins are already set up for A4.",
        "fr": "Le rapport est un fichier HTML unique et autonome : aucun script, aucune requête externe, chaque graphique dessiné en SVG. Il s'ouvre partout et fonctionne hors ligne. Pour obtenir un PDF, ouvrez-le et imprimez en PDF depuis votre navigateur — les sauts de page et les marges sont déjà réglés pour l'A4.",
    },
    "s_overview": {"en": "Portfolio Overview", "fr": "Vue d'Ensemble"},
    "s_performance": {"en": "Performance", "fr": "Performance"},
    "s_risk": {"en": "Risk", "fr": "Risque"},
    "s_diversification": {"en": "Diversification", "fr": "Diversification"},
    "s_concentration": {"en": "Concentration", "fr": "Concentration"},
    "s_stress": {"en": "Stress Tests", "fr": "Tests de Résistance"},
    "s_observations": {"en": "Key Observations", "fr": "Observations Clés"},
    "s_optimization": {"en": "Optimization", "fr": "Optimisation"},
    "s_dna": {"en": "Portfolio DNA", "fr": "ADN du Portefeuille"},

    # ── Phase 4: Advisor ────────────────────────────────────────────────────
    "nav_advisor": {"en": "Advisor", "fr": "Conseiller"},
    "advisor_sub": {
        "en": "Every client book you have saved, side by side.",
        "fr": "Tous les portefeuilles clients que vous avez enregistrés, côte à côte.",
    },
    "clients": {"en": "Clients", "fr": "Clients"},
    "total_aum": {"en": "Total Assets", "fr": "Actifs Totaux"},
    "avg_health": {"en": "Average Health", "fr": "Santé Moyenne"},
    "open_client": {"en": "Open", "fr": "Ouvrir"},
    "no_clients": {"en": "No client portfolios", "fr": "Aucun portefeuille client"},
    "no_clients_body": {
        "en": "Save a portfolio with a client name on the Portfolios page and it will appear here.",
        "fr": "Enregistrez un portefeuille avec un nom de client sur la page Portefeuilles et il apparaîtra ici.",
    },
    "advisor_note": {
        "en": "Figures come from each portfolio's most recent snapshot, not from live prices. Take a snapshot to refresh a client's row.",
        "fr": "Les chiffres proviennent du dernier instantané de chaque portefeuille, pas des cours en direct. Prenez un instantané pour rafraîchir la ligne d'un client.",
    },
    "stale_snapshot": {"en": "No snapshot", "fr": "Aucun instantané"},
    "lowest_health": {"en": "Lowest Health", "fr": "Santé la Plus Faible"},
    "as_of_snapshot": {"en": "as of last snapshot", "fr": "au dernier instantané"},
    "with_snapshot": {"en": "with a snapshot", "fr": "avec instantané"},

    # ── Trading: navigation and shared ──────────────────────────────────────
    "nav_investment": {"en": "Investment", "fr": "Investissement"},
    "nav_trading": {"en": "Trading", "fr": "Trading"},
    "nav_trading_overview": {"en": "Overview", "fr": "Vue d'Ensemble"},
    "nav_trading_journal": {"en": "Journal", "fr": "Journal"},
    "nav_trading_analytics": {"en": "Analytics", "fr": "Analytique"},
    "nav_trading_risk": {"en": "Risk", "fr": "Risque"},
    "nav_trading_psychology": {"en": "Psychology", "fr": "Psychologie"},

    "trades": {"en": "Trades", "fr": "Trades"},
    "trade": {"en": "Trade", "fr": "Trade"},
    "account": {"en": "Account", "fr": "Compte"},
    "all_accounts": {"en": "All accounts", "fr": "Tous les comptes"},
    "no_trades_title": {"en": "No trades yet", "fr": "Aucun trade"},
    "no_trades_body": {
        "en": "Add a trade in the Journal, or import a history, to unlock the trading analytics.",
        "fr": "Ajoutez un trade dans le Journal, ou importez un historique, pour débloquer l'analytique de trading.",
    },
    "no_closed_trades": {
        "en": "Only open positions so far. Metrics need closed trades — an open position has no result to measure.",
        "fr": "Uniquement des positions ouvertes pour l'instant. Les métriques exigent des trades clôturés : une position ouverte n'a pas de résultat à mesurer.",
    },
    "filtered_notice": {"en": "Filtered view", "fr": "Vue filtrée"},
    "outcome": {"en": "Outcome", "fr": "Résultat"},
    "all": {"en": "All", "fr": "Tous"},
    "wins": {"en": "Wins", "fr": "Gains"},
    "losses": {"en": "Losses", "fr": "Pertes"},
    "search": {"en": "Search", "fr": "Recherche"},
    "search_placeholder": {
        "en": "symbol, note, reason, setup, mistake…",
        "fr": "instrument, note, raison, setup, erreur…",
    },
    "no_stop": {"en": "No stop", "fr": "Sans stop"},
    "per_trade": {"en": "per trade", "fr": "par trade"},
    "with_stop": {"en": "had a stop", "fr": "avec stop"},
    "from_peak": {"en": "from peak", "fr": "depuis le sommet"},
    "current_streak": {"en": "Current Streak", "fr": "Série en Cours"},
    "recent_trades": {"en": "Recent Trades", "fr": "Trades Récents"},
    "long": {"en": "Long", "fr": "Achat"},
    "short": {"en": "Short", "fr": "Vente"},
    "above_threshold": {
        "en": "above the sample threshold",
        "fr": "au-dessus du seuil d'échantillon",
    },
    "product_trading": {
        "en": "Sensitor Trading Intelligence",
        "fr": "Sensitor Trading Intelligence",
    },
    "best_bucket": {"en": "Strongest", "fr": "Le plus fort"},
    "weakest_bucket": {"en": "Weakest", "fr": "Le plus faible"},
    "currency": {"en": "Currency", "fr": "Devise"},
    "time_label": {"en": "time", "fr": "heure"},

    # ── Authentication ──────────────────────────────────────────────────────
    "sign_in": {"en": "Sign in", "fr": "Connexion"},
    "sign_out": {"en": "Sign out", "fr": "Se déconnecter"},
    "sign_out_all": {"en": "Sign out everywhere", "fr": "Déconnecter partout"},
    "signed_in_as": {"en": "Signed in as", "fr": "Connecté en tant que"},
    "create_account": {"en": "Create an account", "fr": "Créer un compte"},
    "choose_password": {"en": "Password", "fr": "Mot de passe"},
    "repeat_password": {"en": "Repeat password", "fr": "Confirmez le mot de passe"},
    "current_password": {"en": "Current password", "fr": "Mot de passe actuel"},
    "change_password": {"en": "Change password", "fr": "Changer le mot de passe"},
    "password_changed": {
        "en": "Password changed. Every other session has been signed out.",
        "fr": "Mot de passe modifié. Toutes les autres sessions ont été déconnectées.",
    },
    "single_user_intro": {
        "en": "Enter your email to open your data. If you have a Pro subscription, its features unlock automatically.",
        "fr": "Saisissez votre email pour ouvrir vos données. Si vous avez un abonnement Pro, ses fonctionnalités se débloquent automatiquement.",
    },
    "auth_mode_single": {
        "en": "Single-user mode. Your email is a label for your data, not a login — anyone who can reach this app can open any of it. That is the right setup on your own machine. Before putting this somewhere other people can reach, set SENSITOR_AUTH=multi, which requires a password and expires sessions.",
        "fr": "Mode mono-utilisateur. Votre email est une étiquette pour vos données, pas un identifiant — quiconque atteint cette application peut ouvrir n'importe quelles données. C'est la bonne configuration sur votre propre machine. Avant de la déployer là où d'autres peuvent y accéder, définissez SENSITOR_AUTH=multi, qui exige un mot de passe et fait expirer les sessions.",
    },
    "auth_mode_multi": {
        "en": "Multi-user mode. Accounts are protected by a password, sessions expire, and no account can reach another's data.",
        "fr": "Mode multi-utilisateur. Les comptes sont protégés par mot de passe, les sessions expirent, et aucun compte ne peut atteindre les données d'un autre.",
    },
    "auth_invalid_email": {
        "en": "That does not look like an email address.",
        "fr": "Cela ne ressemble pas à une adresse email.",
    },
    "auth_invalid_credentials": {
        "en": "That email and password do not match an account.",
        "fr": "Cet email et ce mot de passe ne correspondent à aucun compte.",
    },
    "auth_already_registered": {
        "en": "An account already exists for that address. Sign in instead.",
        "fr": "Un compte existe déjà pour cette adresse. Connectez-vous plutôt.",
    },
    "auth_weak_password": {"en": "That password is too weak.",
                           "fr": "Ce mot de passe est trop faible."},
    "auth_locked": {
        "en": "Too many failed attempts. Locked until",
        "fr": "Trop de tentatives échouées. Bloqué jusqu'à",
    },
    "auth_not_multi_user": {
        "en": "Passwords are only used in multi-user mode.",
        "fr": "Les mots de passe ne sont utilisés qu'en mode multi-utilisateur.",
    },
    "auth_passwords_differ": {
        "en": "The two passwords do not match.",
        "fr": "Les deux mots de passe ne correspondent pas.",
    },

    # ── Trading: broker synchronisation ─────────────────────────────────────
    "sync_broker": {"en": "Import from MetaTrader 5", "fr": "Importer depuis MetaTrader 5"},
    "sync_now": {"en": "Sync now", "fr": "Synchroniser"},
    "sync_running": {"en": "Reading the terminal…", "fr": "Lecture du terminal…"},
    "sync_done": {"en": "Sync complete", "fr": "Synchronisation terminée"},
    "sync_failed": {"en": "Sync failed", "fr": "Échec de la synchronisation"},
    "annotations_kept": {
        "en": "trades kept the setups, notes and ratings you had added",
        "fr": "trades ont conservé les setups, notes et évaluations que vous aviez ajoutés",
    },
    "mt5_login": {"en": "Account number", "fr": "Numéro de compte"},
    "mt5_password": {"en": "Password", "fr": "Mot de passe"},
    "mt5_server": {"en": "Server", "fr": "Serveur"},
    "mt5_path": {"en": "Terminal path", "fr": "Chemin du terminal"},
    "mt5_offset": {"en": "Server UTC offset (hours)", "fr": "Décalage UTC du serveur (heures)"},
    "mt5_days": {"en": "History to fetch (days)", "fr": "Historique à récupérer (jours)"},
    "mt5_platform_note": {
        "en": "Requires MetaTrader 5 running on the same machine as this app, with the MetaTrader5 Python package installed. That package is published for Windows only. Leave the credentials blank to use the account already signed in to the terminal. Re-syncing is safe: trades are matched on the broker's own position number, and anything you have written — setups, notes, emotions, ratings — is kept.",
        "fr": "Nécessite MetaTrader 5 en fonctionnement sur la même machine que cette application, avec le paquet Python MetaTrader5 installé. Ce paquet n'est publié que pour Windows. Laissez les identifiants vides pour utiliser le compte déjà connecté dans le terminal. Resynchroniser est sans risque : les trades sont appariés sur le numéro de position du courtier, et tout ce que vous avez écrit — setups, notes, émotions, évaluations — est conservé.",
    },
    "mt5_offset_note": {
        "en": "MetaTrader timestamps are the broker's server clock, and most brokers run on UTC+2 or UTC+3 rather than UTC. Enter the offset your terminal's Market Watch clock shows against UTC. Left at zero on a UTC+3 server, every trade lands three hours late and a third of them are attributed to the wrong session.",
        "fr": "Les horodatages MetaTrader sont l'heure du serveur du courtier, et la plupart des courtiers tournent en UTC+2 ou UTC+3 plutôt qu'en UTC. Saisissez le décalage qu'affiche l'horloge du Market Watch de votre terminal par rapport à UTC. Laissé à zéro sur un serveur UTC+3, chaque trade arrive avec trois heures de retard et un tiers d'entre eux est attribué à la mauvaise séance.",
    },
    "metric": {"en": "Metric", "fr": "Métrique"},
    "no_stops_at_all": {
        "en": "No trade in this view recorded a stop loss, so there is no amount risked to measure. Every R statistic in the product is empty until a stop is recorded.",
        "fr": "Aucun trade de cette vue n'a enregistré de stop, il n'y a donc pas de montant risqué à mesurer. Toutes les statistiques en R du produit restent vides tant qu'aucun stop n'est enregistré.",
    },
    "lower_is_steadier": {"en": "lower is steadier", "fr": "plus bas = plus régulier"},
    "needs_n": {"en": "needs at least", "fr": "exige au moins"},
    "without_stop": {"en": "without a stop", "fr": "sans stop"},
    "largest_vs_median": {"en": "Largest vs Median", "fr": "Plus Grand vs Médian"},
    "rolling_windows": {"en": "rolling windows", "fr": "fenêtres glissantes"},
    "drift_up": {
        "en": "Position risk is higher at the end of this window than at the start.",
        "fr": "Le risque par position est plus élevé à la fin de cette fenêtre qu'au début.",
    },
    "drift_down": {
        "en": "Position risk is lower at the end of this window than at the start.",
        "fr": "Le risque par position est plus faible à la fin de cette fenêtre qu'au début.",
    },
    "drift_stable": {
        "en": "Position risk is about where it started.",
        "fr": "Le risque par position est resté proche de son point de départ.",
    },
    "drift_note": {
        "en": "A comparison of the first and last rolling windows, not a fitted trend. Fitting a slope to a dozen points would dress a rough comparison up as something more precise than it is. Anything within ±15% is reported as stable.",
        "fr": "Une comparaison entre la première et la dernière fenêtre glissante, pas une tendance ajustée. Ajuster une pente sur une douzaine de points ferait passer une comparaison approximative pour plus précise qu'elle ne l'est. Tout écart inférieur à ±15% est indiqué comme stable.",
    },
    "of_losses": {"en": "of losses", "fr": "des pertes"},
    "worst_loss_r": {"en": "Worst Loss", "fr": "Pire Perte"},
    "avg_loss_r": {"en": "Average Loss", "fr": "Perte Moyenne"},
    "measured_gross": {"en": "gross, before costs", "fr": "brut, avant frais"},
    "exposure_note": {
        "en": "Peak simultaneous risk is found by sweeping every open and close in time order. Per-trade risk understates the real figure: three positions each risking 1%, taken at once on correlated instruments, is not three separate 1% bets.",
        "fr": "Le risque simultané maximal est trouvé en parcourant chaque ouverture et clôture dans l'ordre chronologique. Le risque par trade sous-estime le chiffre réel : trois positions risquant chacune 1%, prises simultanément sur des instruments corrélés, ne sont pas trois paris distincts à 1%.",
    },
    "max_word": {"en": "max", "fr": "max"},
    "unusual_run": {"en": "Unusual?", "fr": "Inhabituelle ?"},
    "yes": {"en": "Yes", "fr": "Oui"},
    "no": {"en": "No", "fr": "Non"},
    "threshold_1_5x": {
        "en": "flagged above 1.5x expected",
        "fr": "signalé au-delà de 1,5x l'attendu",
    },
    "run_within_expectation": {
        "en": "The worst run is within what chance produces",
        "fr": "La pire série reste dans ce que le hasard produit",
    },
    "run_within_expectation_body": {
        "en": "Your longest losing run is {observed}. A win rate like yours produces a run of about {expected} by chance alone over this many trades.",
        "fr": "Votre plus longue série perdante est de {observed}. Un taux de réussite comme le vôtre produit une série d'environ {expected} par simple hasard sur autant de trades.",
    },
    "run_beyond_expectation": {
        "en": "The worst run is longer than chance alone explains",
        "fr": "La pire série dépasse ce que le hasard seul explique",
    },
    "run_beyond_expectation_body": {
        "en": "Your longest losing run is {observed}, against about {expected} expected by chance. That is a reason to look at the trades in the run, not a conclusion about them — trades are not perfectly independent, and a trader's state carries over.",
        "fr": "Votre plus longue série perdante est de {observed}, contre environ {expected} attendus par hasard. C'est une raison de regarder les trades de la série, pas une conclusion à leur sujet — les trades ne sont pas parfaitement indépendants, et l'état du trader se reporte d'un trade à l'autre.",
    },
    "median_word": {"en": "median", "fr": "médiane"},
    "median_holding": {"en": "Median Holding", "fr": "Durée Médiane"},
    "instrument_one": {"en": "instrument", "fr": "instrument"},
    "instrument_many": {"en": "instruments", "fr": "instruments"},
    "every_stop_held": {"en": "every stop held", "fr": "tous les stops ont tenu"},
    "mean_word": {"en": "mean", "fr": "moyenne"},
    "reliable_buckets": {
        "en": "above threshold",
        "fr": "au-dessus du seuil",
    },
    "busiest_instrument": {"en": "Busiest Instrument", "fr": "Instrument le Plus Tradé"},
    "of_trades_share": {"en": "of all trades", "fr": "de tous les trades"},
    "where_the_result_comes_from": {
        "en": "Where the result comes from",
        "fr": "D'où vient le résultat",
    },
    "top_contributor_share": {
        "en": "Largest Profit Share",
        "fr": "Part de Profit la Plus Élevée",
    },
    "concentrated_result": {
        "en": "The result rests on one bucket",
        "fr": "Le résultat repose sur un seul groupe",
    },
    "concentrated_result_body": {
        "en": "{label} accounts for {share} of the gross profit. Remove it and the rest of the book is what remains.",
        "fr": "{label} représente {share} du profit brut. Retirez-le et il reste le reste du carnet.",
    },
    "concentrated_footnote": {
        "en": "Threshold: 60% of gross profit in one bucket. This is a description, not a verdict — a specialist's book looks like this, and so does one carried by a single lucky run. Only a longer history separates them.",
        "fr": "Seuil : 60% du profit brut dans un seul groupe. C'est une description, pas un verdict — le carnet d'un spécialiste ressemble à cela, celui porté par une seule série chanceuse aussi. Seul un historique plus long les distingue.",
    },
    "page": {"en": "Page", "fr": "Page"},
    "trade_required_fields": {
        "en": "A trade needs a symbol, an entry price above zero and a size above zero. Everything else can be filled in later.",
        "fr": "Un trade exige un instrument, un prix d'entrée supérieur à zéro et une taille supérieure à zéro. Tout le reste peut être complété plus tard.",
    },
    "open_excluded_note": {
        "en": "Open positions are listed here but excluded from every metric on the other pages. A position with no exit has no result to measure, and counting it as zero would pull every average toward it.",
        "fr": "Les positions ouvertes sont listées ici mais exclues de toutes les métriques des autres pages. Une position sans sortie n'a pas de résultat à mesurer, et la compter comme zéro tirerait toutes les moyennes vers elle.",
    },
    "sign_in_trading": {
        "en": "Sign in to keep a journal",
        "fr": "Connectez-vous pour tenir un journal",
    },
    "sign_in_trading_body": {
        "en": "Trades are filed under an email address so they are still there next time. Enter yours on the Account page.",
        "fr": "Les trades sont classés sous une adresse email pour être retrouvés ensuite. Saisissez la vôtre sur la page Compte.",
    },
    "sample_note": {
        "en": "Buckets below the sample threshold are drawn faded and carry their trade count. A small bucket's win rate is a coincidence, not a finding.",
        "fr": "Les groupes sous le seuil d'échantillon sont estompés et portent leur nombre de trades. Le taux de réussite d'un petit groupe est une coïncidence, pas un constat.",
    },

    # ── Trading: metrics ────────────────────────────────────────────────────
    "net_pnl": {"en": "Net P&L", "fr": "P&L Net"},
    "gross_profit": {"en": "Gross Profit", "fr": "Profit Brut"},
    "gross_loss": {"en": "Gross Loss", "fr": "Perte Brute"},
    "win_rate": {"en": "Win Rate", "fr": "Taux de Réussite"},
    "profit_factor": {"en": "Profit Factor", "fr": "Facteur de Profit"},
    "expectancy": {"en": "Expectancy", "fr": "Espérance"},
    "average_r": {"en": "Average R", "fr": "R Moyen"},
    "total_r": {"en": "Total R", "fr": "R Total"},
    "total_trades": {"en": "Total Trades", "fr": "Trades Totaux"},
    "average_win": {"en": "Average Win", "fr": "Gain Moyen"},
    "average_loss": {"en": "Average Loss", "fr": "Perte Moyenne"},
    "best_trade": {"en": "Best Trade", "fr": "Meilleur Trade"},
    "worst_trade": {"en": "Worst Trade", "fr": "Pire Trade"},
    "avg_holding": {"en": "Average Holding", "fr": "Durée Moyenne"},
    "payoff_ratio": {"en": "Payoff Ratio", "fr": "Ratio Gain/Perte"},
    "costs": {"en": "Costs", "fr": "Frais"},
    "win_streak": {"en": "Win Streak", "fr": "Série de Gains"},
    "loss_streak": {"en": "Loss Streak", "fr": "Série de Pertes"},
    "equity_curve": {"en": "Equity Curve", "fr": "Courbe de Capital"},
    "cumulative_r": {"en": "Cumulative R", "fr": "R Cumulé"},
    "daily_pnl": {"en": "Daily P&L", "fr": "P&L Quotidien"},
    "r_distribution": {"en": "R Distribution", "fr": "Distribution des R"},
    "undefined": {"en": "undefined", "fr": "indéfini"},
    "no_losses_yet": {"en": "no losing trades yet", "fr": "aucune perte pour l'instant"},
    "r_coverage_note": {
        "en": "R statistics cover only trades that had a stop loss. Without a stop there is no amount risked, so R has no denominator — those trades are excluded rather than counted as zero.",
        "fr": "Les statistiques en R ne couvrent que les trades ayant eu un stop. Sans stop, il n'y a pas de montant risqué, donc pas de dénominateur — ces trades sont exclus plutôt que comptés comme zéro.",
    },
    "profit_factor_note": {
        "en": "Profit factor is gross profit divided by gross loss. With no losing trades it has no denominator and is reported as undefined rather than infinite.",
        "fr": "Le facteur de profit est le profit brut divisé par la perte brute. Sans trade perdant, il n'a pas de dénominateur et est indiqué comme indéfini plutôt qu'infini.",
    },

    # ── Trading: overview ───────────────────────────────────────────────────
    "trading_overview_sub": {
        "en": "Your trading, on one screen.",
        "fr": "Votre trading, sur un seul écran.",
    },
    "performance_by": {"en": "Performance by", "fr": "Performance par"},
    "d_symbol": {"en": "Instrument", "fr": "Instrument"},
    "d_setup": {"en": "Setup", "fr": "Setup"},
    "d_combination": {"en": "Setup combination", "fr": "Combinaison de setups"},
    "d_session": {"en": "Session", "fr": "Séance"},
    "d_weekday": {"en": "Weekday", "fr": "Jour de la semaine"},
    "d_month": {"en": "Month", "fr": "Mois"},
    "d_hour": {"en": "Hour", "fr": "Heure"},
    "d_timeframe": {"en": "Timeframe", "fr": "Unité de temps"},
    "d_direction": {"en": "Direction", "fr": "Sens"},
    "d_regime": {"en": "Market regime", "fr": "Régime de marché"},
    "d_risk_band": {"en": "Position size", "fr": "Taille de position"},

    # ── Trading: journal ────────────────────────────────────────────────────
    "trading_journal_sub": {
        "en": "Every trade, with the context and the state of mind behind it.",
        "fr": "Chaque trade, avec le contexte et l'état d'esprit derrière.",
    },
    "add_trade": {"en": "Add a trade", "fr": "Ajouter un trade"},
    "edit_trade": {"en": "Edit", "fr": "Modifier"},
    "delete_trade": {"en": "Delete", "fr": "Supprimer"},
    "save_trade": {"en": "Save trade", "fr": "Enregistrer le trade"},
    "trade_saved": {"en": "Trade saved", "fr": "Trade enregistré"},
    "trade_deleted": {"en": "Trade deleted", "fr": "Trade supprimé"},
    "symbol": {"en": "Symbol", "fr": "Instrument"},
    "direction_label": {"en": "Direction", "fr": "Sens"},
    "entry_price": {"en": "Entry", "fr": "Entrée"},
    "exit_price": {"en": "Exit", "fr": "Sortie"},
    "position_size": {"en": "Size", "fr": "Taille"},
    "stop_loss": {"en": "Stop loss", "fr": "Stop loss"},
    "take_profit": {"en": "Take profit", "fr": "Take profit"},
    "opened_at": {"en": "Opened", "fr": "Ouvert le"},
    "closed_at": {"en": "Closed", "fr": "Clôturé le"},
    "commission": {"en": "Commission", "fr": "Commission"},
    "swap": {"en": "Swap", "fr": "Swap"},
    "r_multiple": {"en": "R multiple", "fr": "Multiple R"},
    "duration": {"en": "Duration", "fr": "Durée"},
    "session_label": {"en": "Session", "fr": "Séance"},
    "setups_label": {"en": "Setups", "fr": "Setups"},
    "timeframe": {"en": "Timeframe", "fr": "Unité de temps"},
    "market_regime": {"en": "Market regime", "fr": "Régime de marché"},
    "setup_quality": {"en": "Setup quality", "fr": "Qualité du setup"},
    "confidence_label": {"en": "Confidence", "fr": "Confiance"},
    "entry_reason": {"en": "Reason for entry", "fr": "Raison d'entrée"},
    "exit_reason": {"en": "Reason for exit", "fr": "Raison de sortie"},
    "emotion_before": {"en": "Before", "fr": "Avant"},
    "emotion_during": {"en": "During", "fr": "Pendant"},
    "emotion_after": {"en": "After", "fr": "Après"},
    "discipline_label": {"en": "Discipline", "fr": "Discipline"},
    "mistakes_label": {"en": "Mistakes", "fr": "Erreurs"},
    "trade_notes": {"en": "Notes", "fr": "Notes"},
    "images": {"en": "Screenshots", "fr": "Captures"},
    "image_pre": {"en": "Before entry", "fr": "Avant l'entrée"},
    "image_post": {"en": "After exit", "fr": "Après la sortie"},
    "image_annotated": {"en": "Annotated chart", "fr": "Graphique annoté"},
    "execution": {"en": "Execution", "fr": "Exécution"},
    "strategy": {"en": "Strategy", "fr": "Stratégie"},
    "psychology_section": {"en": "Psychology", "fr": "Psychologie"},
    "open_position": {"en": "Open position", "fr": "Position ouverte"},
    "data_problems": {"en": "Data problems", "fr": "Problèmes de données"},
    "data_problems_body": {
        "en": "These trades have values that would make their statistics wrong. They are kept and shown rather than rejected, so you can correct them.",
        "fr": "Ces trades ont des valeurs qui fausseraient leurs statistiques. Ils sont conservés et affichés plutôt que rejetés, pour que vous puissiez les corriger.",
    },
    "no_stop_warning": {
        "en": "No stop loss recorded — this trade is excluded from every R statistic.",
        "fr": "Aucun stop enregistré — ce trade est exclu de toutes les statistiques en R.",
    },

    # ── Trading: analytics ──────────────────────────────────────────────────
    "trading_analytics_sub": {
        "en": "Slice your history by anything you recorded.",
        "fr": "Découpez votre historique selon tout ce que vous avez enregistré.",
    },
    "filters": {"en": "Filters", "fr": "Filtres"},
    "clear_filters": {"en": "Clear", "fr": "Effacer"},
    "showing": {"en": "Showing", "fr": "Affichage"},
    "of_trades": {"en": "of", "fr": "sur"},
    "trading_dna": {"en": "Trading DNA", "fr": "ADN de Trading"},
    "trading_dna_sub": {
        "en": "The patterns your own history shows. Descriptive, with the sample size behind each.",
        "fr": "Les tendances que montre votre propre historique. Descriptif, avec la taille d'échantillon derrière chacune.",
    },
    "most_traded": {"en": "Most traded", "fr": "Le plus tradé"},
    "best_instrument": {"en": "Best instrument", "fr": "Meilleur instrument"},
    "best_setup": {"en": "Best setup", "fr": "Meilleur setup"},
    "best_session": {"en": "Best session", "fr": "Meilleure séance"},
    "typical_risk": {"en": "Typical risk", "fr": "Risque habituel"},
    "dna_note": {
        "en": "Every entry is the best-performing bucket among those with enough trades to compare. A bucket below the threshold is never promoted here, however good it looks.",
        "fr": "Chaque entrée est le groupe le plus performant parmi ceux ayant assez de trades pour être comparés. Un groupe sous le seuil n'est jamais promu ici, aussi bon qu'il paraisse.",
    },
    "not_enough_data": {
        "en": "Not enough trades yet for this comparison to mean anything.",
        "fr": "Pas encore assez de trades pour que cette comparaison ait un sens.",
    },

    # ── Trading: risk ───────────────────────────────────────────────────────
    "trading_risk_sub": {
        "en": "How much you risk, how consistently, and how much is on the table at once.",
        "fr": "Combien vous risquez, avec quelle régularité, et combien est engagé simultanément.",
    },
    "risk_per_trade": {"en": "Risk per Trade", "fr": "Risque par Trade"},
    "median_risk": {"en": "Median Risk", "fr": "Risque Médian"},
    "risk_consistency": {"en": "Sizing Consistency", "fr": "Régularité du Dimensionnement"},
    "stop_coverage": {"en": "Stop Coverage", "fr": "Couverture Stop"},
    "stop_discipline": {"en": "Stop Discipline", "fr": "Discipline de Stop"},
    "beyond_stop": {"en": "Losses beyond the stop", "fr": "Pertes au-delà du stop"},
    "max_concurrent": {"en": "Most Positions at Once", "fr": "Positions Simultanées Max"},
    "simultaneous_risk": {"en": "Peak Simultaneous Risk", "fr": "Risque Simultané Max"},
    "risk_drift": {"en": "Risk Drift", "fr": "Dérive du Risque"},
    "expected_streak": {"en": "Expected Losing Run", "fr": "Série Perdante Attendue"},
    "observed_streak": {"en": "Longest Observed", "fr": "Plus Longue Observée"},
    "trades_per_day": {"en": "Trades per Day", "fr": "Trades par Jour"},
    "consistency_note": {
        "en": "Sizing consistency is the spread of position risk relative to its average. Near zero means fixed risk per trade; a high value means the size varies a lot, which makes every average less representative.",
        "fr": "La régularité du dimensionnement est la dispersion du risque par position rapportée à sa moyenne. Proche de zéro : risque fixe par trade ; une valeur élevée signifie que la taille varie beaucoup, ce qui rend chaque moyenne moins représentative.",
    },
    "stop_note": {
        "en": "Measured on price movement alone, before commission and swap. A trade stopped out at exactly -1R lands past -1R once costs are added, so judging stop discipline on the net figure would flag almost every loss.",
        "fr": "Mesuré sur le seul mouvement de prix, avant commission et swap. Un trade stoppé exactement à -1R passe sous -1R une fois les frais ajoutés : juger la discipline de stop sur le chiffre net signalerait presque toutes les pertes.",
    },
    "streak_note": {
        "en": "The expected run is what a win rate like yours produces by chance alone, assuming independent trades. It is an order of magnitude, not a limit — the most common reason a trader abandons a working method is a losing run that was statistically unremarkable.",
        "fr": "La série attendue est ce qu'un taux de réussite comme le vôtre produit par simple hasard, en supposant des trades indépendants. C'est un ordre de grandeur, pas une limite — la raison la plus fréquente d'abandonner une méthode qui marche est une série perdante statistiquement banale.",
    },

    # ── Trading: psychology ─────────────────────────────────────────────────
    "trading_psychology_sub": {
        "en": "What your records and your behaviour line up with. Correlations, not diagnoses.",
        "fr": "Ce avec quoi vos notes et votre comportement coïncident. Des corrélations, pas des diagnostics.",
    },
    "after_losses": {"en": "After Consecutive Losses", "fr": "Après des Pertes Consécutives"},
    "after_wins": {"en": "After Consecutive Wins", "fr": "Après des Gains Consécutifs"},
    "by_mistake": {"en": "By Flagged Mistake", "fr": "Par Erreur Signalée"},
    "by_emotion": {"en": "By Emotion Before Entry", "fr": "Par Émotion Avant l'Entrée"},
    "by_discipline": {"en": "By Discipline Rating", "fr": "Par Note de Discipline"},
    "mistake_frequency": {"en": "Mistake Frequency", "fr": "Fréquence des Erreurs"},
    "usual_risk": {"en": "usual risk", "fr": "risque habituel"},
    "avg": {"en": "avg", "fr": "moy"},
    "no_difference": {"en": "no difference", "fr": "aucune différence"},
    "share": {"en": "Share", "fr": "Part"},
    "what_your_data_shows": {
        "en": "What your data shows",
        "fr": "Ce que montrent vos données",
    },
    "correlation_in_your_data": {
        "en": "A correlation in your data",
        "fr": "Une corrélation dans vos données",
    },
    "correlation_footnote": {
        "en": "Both groups are your own trades. The comparison does not establish cause in either direction.",
        "fr": "Les deux groupes sont vos propres trades. La comparaison n'établit de cause dans aucun sens.",
    },
    "no_patterns_title": {
        "en": "Nothing stands out yet",
        "fr": "Rien ne ressort pour l'instant",
    },
    "no_patterns_body": {
        "en": "No comparison in this view has two groups large enough, and a gap wide enough, to be worth reporting. That is a statement about the sample, not a clean bill of health.",
        "fr": "Aucune comparaison de cette vue n'a deux groupes assez grands, et un écart assez net, pour mériter d'être signalée. C'est un constat sur l'échantillon, pas un satisfecit.",
    },
    "behaviour_around_streaks": {
        "en": "Behaviour around streaks",
        "fr": "Comportement autour des séries",
    },
    "behaviour_around_streaks_sub": {
        "en": "The comparisons neither side self-reported — the broker recorded both the run and the size.",
        "fr": "Les comparaisons qu'aucune des deux parties n'a auto-déclarées — le courtier a enregistré la série comme la taille.",
    },
    "activity_after_losses": {
        "en": "Trades After a Bad Open",
        "fr": "Trades Après une Mauvaise Ouverture",
    },
    "activity_proxy_note": {
        "en": "Median trades on days whose first trade lost, against days whose first trade won. The first trade of the day is a rough proxy.",
        "fr": "Nombre médian de trades les jours dont le premier trade a perdu, contre les jours dont le premier trade a gagné. Le premier trade du jour est un proxy approximatif.",
    },
    "avg_result_in_group": {"en": "Average in this group:", "fr": "Moyenne de ce groupe :"},
    "mistake_flagging_note": {
        "en": "A mistake is flagged by the trader, after the outcome is known, and it is flagged far more readily on a losing trade. That alone widens the gap between the two groups, whatever the mistake did or did not cost.",
        "fr": "Une erreur est signalée par le trader, une fois le résultat connu, et elle l'est bien plus volontiers sur un trade perdant. Cela seul élargit l'écart entre les deux groupes, quel qu'ait été le coût réel de l'erreur.",
    },
    "nothing_recorded_title": {
        "en": "No self-reported fields yet",
        "fr": "Aucun champ auto-déclaré pour l'instant",
    },
    "nothing_recorded_body": {
        "en": "Emotion and discipline are recorded in the Journal, on each trade. Once enough trades carry them, the comparisons appear here.",
        "fr": "L'émotion et la discipline s'enregistrent dans le Journal, trade par trade. Dès qu'assez de trades en portent, les comparaisons apparaissent ici.",
    },
    "self_report_note": {
        "en": "These two comparisons rest on fields you filled in yourself. If they are usually filled in after the trade closed, the label is partly a reaction to the outcome, and the gap between the groups is partly that reaction rather than anything that preceded the trade.",
        "fr": "Ces deux comparaisons reposent sur des champs que vous avez renseignés vous-même. S'ils sont généralement remplis après la clôture, l'étiquette est en partie une réaction au résultat, et l'écart entre les groupes tient en partie à cette réaction plutôt qu'à quoi que ce soit ayant précédé le trade.",
    },
    "flagged": {"en": "Flagged", "fr": "Marqués"},
    "the_rest": {"en": "The rest", "fr": "Les autres"},
    "psychology_note": {
        "en": "Every comparison here is between two groups of your own trades, with both sample sizes shown. None of it establishes cause. Two reasons: the direction of the arrow is unknown — anxiety may cause bad trades, or bad trades may cause anxiety — and self-reported fields are usually recorded after the outcome is known, which creates a correlation on its own.",
        "fr": "Chaque comparaison ici oppose deux groupes de vos propres trades, avec les deux tailles d'échantillon affichées. Rien de tout cela n'établit de cause. Deux raisons : le sens de la flèche est inconnu — l'anxiété peut causer de mauvais trades, ou de mauvais trades peuvent causer l'anxiété — et les champs auto-déclarés sont généralement renseignés une fois le résultat connu, ce qui crée une corrélation à soi seul.",
    },

    "factor_note": {
        "en": "Loadings come from a single multivariate OLS regression of portfolio excess returns on all available factors, so correlated factors do not each claim the same variance. Style factors are long/short ETF spreads, which are proxies for the academic factors rather than the factors themselves. Loadings marked not significant have |t| below 2 and should be read as indistinguishable from zero. Estimates move with the window chosen.",
        "fr": "Les charges proviennent d'une unique régression OLS multivariée des rendements excédentaires du portefeuille sur tous les facteurs disponibles, afin que des facteurs corrélés ne revendiquent pas chacun la même variance. Les facteurs de style sont des spreads d'ETF long/short : ce sont des proxies des facteurs académiques, pas les facteurs eux-mêmes. Les charges marquées non significatives ont un |t| inférieur à 2 et doivent être lues comme indiscernables de zéro. Les estimations varient selon la fenêtre choisie.",
    },
}


# =============================================================================
# METRIC DEFINITIONS (tooltip system)
# =============================================================================

DEFS: dict[str, dict[str, str]] = {
    "sharpe": {
        "en": "Return above the risk-free rate per unit of total volatility, annualised. Higher means more return generated per unit of risk taken. Computed here with a 4% risk-free rate over the selected period.",
        "fr": "Rendement au-dessus du taux sans risque par unité de volatilité totale, annualisé. Plus il est élevé, plus le rendement obtenu par unité de risque est important. Calculé ici avec un taux sans risque de 4% sur la période sélectionnée.",
    },
    "sortino": {
        "en": "Like Sharpe, but divides only by downside volatility. Upward volatility is not penalised, so it reflects the kind of risk investors actually mind.",
        "fr": "Comme le Sharpe, mais ne divise que par la volatilité baissière. La volatilité haussière n'est pas pénalisée : il reflète donc le risque qui préoccupe réellement les investisseurs.",
    },
    "calmar": {
        "en": "Annualised return divided by the depth of the worst peak-to-trough decline. Rewards returns earned without deep drawdowns.",
        "fr": "Rendement annualisé divisé par la profondeur de la pire baisse pic-creux. Récompense les rendements obtenus sans drawdown profond.",
    },
    "volatility": {
        "en": "Annualised standard deviation of daily returns (252 trading days). A measure of dispersion, not of loss — it counts upward moves too.",
        "fr": "Écart-type annualisé des rendements quotidiens (252 jours de bourse). Une mesure de dispersion, pas de perte — elle compte aussi les mouvements haussiers.",
    },
    "downside_vol": {
        "en": "Annualised standard deviation computed on negative days only. Isolates the volatility that actually costs money.",
        "fr": "Écart-type annualisé calculé uniquement sur les jours négatifs. Isole la volatilité qui coûte réellement de l'argent.",
    },
    "max_drawdown": {
        "en": "Largest peak-to-trough decline over the selected period. Recovering a 30% decline requires a 43% gain.",
        "fr": "Plus forte baisse pic-creux sur la période sélectionnée. Récupérer une baisse de 30% exige un gain de 43%.",
    },
    "current_drawdown": {
        "en": "How far below its all-time high the portfolio sits today, over the selected period.",
        "fr": "Écart actuel du portefeuille par rapport à son plus haut historique, sur la période sélectionnée.",
    },
    "var": {
        "en": "Estimated loss threshold over a one-day horizon at the stated confidence level: on the worst 5% of days, losses exceeded this figure. It says nothing about how much worse they got.",
        "fr": "Seuil de perte estimé sur un horizon d'un jour au niveau de confiance indiqué : lors des 5% de jours les plus défavorables, les pertes ont dépassé ce chiffre. Il ne dit rien de l'ampleur au-delà.",
    },
    "cvar": {
        "en": "Average loss on the days that breached VaR — the expected size of a bad day, not just its threshold.",
        "fr": "Perte moyenne les jours qui ont dépassé la VaR — l'ampleur attendue d'une mauvaise journée, pas seulement son seuil.",
    },
    "beta": {
        "en": "Sensitivity to the benchmark from an OLS fit on excess daily returns. 1.0 moves with the index; above 1.0 amplifies it; below 1.0 damps it.",
        "fr": "Sensibilité à l'indice, issue d'une régression OLS sur les rendements quotidiens excédentaires. 1,0 suit l'indice ; au-dessus de 1,0 l'amplifie ; en dessous l'atténue.",
    },
    "alpha": {
        "en": "Annualised return not explained by benchmark exposure, from the same regression. Measured over this period only and sensitive to the window chosen.",
        "fr": "Rendement annualisé non expliqué par l'exposition à l'indice, issu de la même régression. Mesuré sur cette période uniquement et sensible à la fenêtre choisie.",
    },
    "r_squared": {
        "en": "Share of the portfolio's movement explained by the benchmark. Near 1.0 means the portfolio is essentially tracking the index.",
        "fr": "Part des mouvements du portefeuille expliquée par l'indice. Proche de 1,0, le portefeuille suit essentiellement l'indice.",
    },
    "tracking_error": {
        "en": "Annualised volatility of the difference between portfolio and benchmark returns. How far the portfolio wanders from the index.",
        "fr": "Volatilité annualisée de l'écart entre les rendements du portefeuille et ceux de l'indice. À quel point le portefeuille s'écarte de l'indice.",
    },
    "information_ratio": {
        "en": "Active return divided by tracking error — excess return earned per unit of deviation from the benchmark.",
        "fr": "Rendement actif divisé par la tracking error — rendement excédentaire obtenu par unité d'écart à l'indice.",
    },
    "capture": {
        "en": "Share of the benchmark's move captured on its up days and its down days, computed separately. Up above 100% with down below 100% is the favourable pattern.",
        "fr": "Part du mouvement de l'indice captée lors de ses jours de hausse et de baisse, calculée séparément. Hausse au-dessus de 100% et baisse en dessous de 100% est le profil favorable.",
    },
    "risk_contribution": {
        "en": "Share of total portfolio volatility attributable to each holding, via Euler decomposition. Contributions sum exactly to portfolio volatility, so the percentages add to 100%.",
        "fr": "Part de la volatilité totale du portefeuille attribuable à chaque position, par décomposition d'Euler. Les contributions somment exactement à la volatilité du portefeuille : les pourcentages totalisent donc 100%.",
    },
    "marginal_risk": {
        "en": "How much portfolio volatility changes per unit of additional weight in this holding, with everything else held constant.",
        "fr": "Variation de la volatilité du portefeuille par unité de poids supplémentaire sur cette position, tout le reste étant constant.",
    },
    "correlation": {
        "en": "Co-movement between two holdings, from -1 (opposite) through 0 (unrelated) to +1 (identical). Computed on daily returns over the selected period.",
        "fr": "Co-mouvement entre deux positions, de -1 (opposé) à 0 (sans lien) jusqu'à +1 (identique). Calculé sur les rendements quotidiens de la période sélectionnée.",
    },
    "avg_correlation": {
        "en": "Mean of every pairwise correlation in the portfolio. Low values mean holdings genuinely behave differently from one another.",
        "fr": "Moyenne de toutes les corrélations par paires du portefeuille. Des valeurs faibles signifient que les positions se comportent réellement différemment.",
    },
    "effective_assets": {
        "en": "1 divided by the Herfindahl index (sum of squared weights): the equal-weight portfolio size that would be equally concentrated. Ten holdings with an effective count of 4.8 are concentrated like an equal-weight book of five.",
        "fr": "1 divisé par l'indice de Herfindahl (somme des poids au carré) : la taille d'un portefeuille équipondéré qui serait aussi concentré. Dix lignes avec 4,8 actifs effectifs sont concentrées comme un portefeuille équipondéré de cinq.",
    },
    "hhi": {
        "en": "Herfindahl-Hirschman Index — the sum of squared weights. 1/n for an equal-weight portfolio, 1.0 for a single position.",
        "fr": "Indice de Herfindahl-Hirschman — la somme des poids au carré. 1/n pour un portefeuille équipondéré, 1,0 pour une position unique.",
    },
    "diversification_ratio": {
        "en": "Weighted average of individual asset volatilities divided by portfolio volatility. 1.00 means correlations delivered no risk reduction at all; higher means the mix genuinely damps risk.",
        "fr": "Moyenne pondérée des volatilités individuelles divisée par la volatilité du portefeuille. 1,00 signifie que les corrélations n'ont apporté aucune réduction de risque ; plus haut, le mélange atténue réellement le risque.",
    },
    "skewness": {
        "en": "Asymmetry of the return distribution. Negative means the left tail is longer — occasional large losses against more frequent small gains.",
        "fr": "Asymétrie de la distribution des rendements. Négative, la queue gauche est plus longue — des pertes importantes occasionnelles face à des gains plus fréquents mais petits.",
    },
    "kurtosis": {
        "en": "Excess kurtosis of daily returns; 0 matches a normal distribution. Positive means fatter tails — extreme days happen more often than a normal model predicts.",
        "fr": "Kurtosis excédentaire des rendements quotidiens ; 0 correspond à une distribution normale. Positive, les queues sont plus épaisses — les journées extrêmes surviennent plus souvent que ne le prédit un modèle normal.",
    },
    "time_underwater": {
        "en": "Share of days the portfolio spent below a previous peak over the selected period.",
        "fr": "Part des jours passés sous un sommet précédent sur la période sélectionnée.",
    },
    "health_score": {
        "en": "Composite 0-100 score from five weighted components. It describes the portfolio's structure over the analysed period — not a forecast, not a rating, not advice.",
        "fr": "Score composite 0-100 issu de cinq composantes pondérées. Il décrit la structure du portefeuille sur la période analysée — ni prévision, ni notation, ni conseil.",
    },
    "attribution": {
        "en": "Each holding's contribution to total portfolio return, compounded forward day by day. Under the daily-rebalanced constant-weight assumption the contributions sum exactly to the portfolio's total return.",
        "fr": "Contribution de chaque position au rendement total, capitalisée jour après jour. Sous l'hypothèse de poids constants rééquilibrés quotidiennement, les contributions somment exactement au rendement total du portefeuille.",
    },
    "lookthrough": {
        "en": "Fund positions resolved into their underlying exposures and aggregated by weight, so a book holding index funds shows its true sector, geography, cap and style tilts.",
        "fr": "Positions en fonds résolues en leurs expositions sous-jacentes puis agrégées par poids : un portefeuille détenant des fonds indiciels révèle ainsi ses véritables biais sectoriels, géographiques, de capitalisation et de style.",
    },
}


def tr(key: str, lang: str = "en") -> str:
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get("en") or key


def define(key: str, lang: str = "en") -> str:
    entry = DEFS.get(key)
    if not entry:
        return ""
    return entry.get(lang) or entry.get("en") or ""


# =============================================================================
# LEGACY SURFACE
# =============================================================================
# The original product's translations, moved out of the Streamlit entry point in
# V2 Phase 2. Unchanged: the seven legacy pages render these exact strings.

LEGACY_STRINGS = {
    "en": {
        "dashboard": "Dashboard", "new_analysis": "New Analysis",
        "models": "Model Portfolios", "improve": "Optimise",
        "library": "Asset Library", "account": "Account",
        "robustness": "Robustness Index", "recommendations": "Recommendations",
        "stress_test": "Stress Tests", "asset_info": "Asset Details",
        "portfolio_summary": "Portfolio Summary",
        "selected_assets": "Selected Assets",
        "analyse_btn": "Analyse Portfolio",
        "run_stress": "Run Stress Tests",
        "optimise_btn": "Optimise Portfolio",
        "apply_opt": "Apply Optimisation",
        "current": "Current", "optimised": "Optimised",
        "use_model": "Use this portfolio",
        "expected_return": "Expected Return",
        "volatility": "Volatility",
        "sharpe": "Sharpe Ratio",
        "annual_return": "Annual Return",
        "max_drawdown": "Max Drawdown",
        "total_weight": "Total",
        "add": "Add", "remove": "Remove",
        "search_ph": "Apple, Bitcoin, S&P 500...",
        "browse": "Browse",
        "search": "Search",
        "welcome": "Welcome! Start by creating a portfolio.",
        "create_portfolio": "Create Portfolio",
        "no_portfolio": "Create a portfolio first.",
        "loading": "Fetching market data...",
        "analysis_done": "Analysis complete!",
        "fetch_error": "Could not fetch data. Check ticker symbols.",
        "upgrade_pro": "Upgrade to Pro",
        "login": "Continue",
        "logout": "Log out",
        "profile_label": "Risk Profile",
        "profile_safe": "Prudent",
        "profile_balanced": "Balanced",
        "profile_aggressive": "Aggressive",
        "filter_type": "Filter by type",
        "filter_all": "All",
        "normalised": "Total normalised to 100%.",
        "mode_simulation": "Portfolio Simulation",
        "mode_real": "Real Portfolio Analysis",
        "real_portfolio": "Real Portfolio",
        "real_portfolio_desc": "Enter your actual holdings to see your real portfolio value.",
        "add_holding": "Add Holding",
        "quantity": "Quantity",
        "ticker": "Ticker",
        "fetch_prices": "Fetch Prices & Analyse",
        "total_value": "Total Value",
        "num_assets": "Number of Assets",
        "top_asset": "Top Asset",
        "portfolio_health": "Portfolio Health",
        "asset_class_breakdown": "Asset Class Breakdown",
        "dominant_asset": "Dominant Asset",
        "diversification": "Diversification Level",
        "overall_risk": "Overall Risk",
        "real_synthesis": "Portfolio Synthesis",
        "real_holdings": "Your Holdings",
        "price": "Price",
        "value": "Value",
        "weight_pct": "Weight",
        "remove_holding": "Remove",
        "no_holdings": "Add assets and their quantities to analyse your real portfolio.",
        "high_div": "High",
        "medium_div": "Medium",
        "low_div": "Low",
        "very_low_div": "Very Low",
    },
    "fr": {
        "dashboard": "Tableau de Bord", "new_analysis": "Nouvelle Analyse",
        "models": "Portefeuilles Modèles", "improve": "Optimiser",
        "library": "Bibliothèque", "account": "Compte",
        "robustness": "Indice de Robustesse", "recommendations": "Recommandations",
        "stress_test": "Tests de Stress", "asset_info": "Détail des Actifs",
        "portfolio_summary": "Résumé du Portefeuille",
        "selected_assets": "Actifs Sélectionnés",
        "analyse_btn": "Analyser le Portefeuille",
        "run_stress": "Lancer les Tests de Stress",
        "optimise_btn": "Optimiser le Portefeuille",
        "apply_opt": "Appliquer l'Optimisation",
        "current": "Actuel", "optimised": "Optimisé",
        "use_model": "Utiliser ce portefeuille",
        "expected_return": "Rendement Attendu",
        "volatility": "Volatilité",
        "sharpe": "Ratio de Sharpe",
        "annual_return": "Rendement Annuel",
        "max_drawdown": "Perte Max",
        "total_weight": "Total",
        "add": "Ajouter", "remove": "Supprimer",
        "search_ph": "Apple, Bitcoin, S&P 500...",
        "browse": "Parcourir",
        "search": "Rechercher",
        "welcome": "Bienvenue ! Commencez par créer un portefeuille.",
        "create_portfolio": "Créer un Portefeuille",
        "no_portfolio": "Créez d'abord un portefeuille.",
        "loading": "Récupération des données...",
        "analysis_done": "Analyse terminée !",
        "fetch_error": "Impossible de récupérer les données. Vérifiez les tickers.",
        "upgrade_pro": "Passer à Pro",
        "login": "Continuer",
        "logout": "Se déconnecter",
        "profile_label": "Profil de Risque",
        "profile_safe": "Prudent",
        "profile_balanced": "Équilibré",
        "profile_aggressive": "Agressif",
        "filter_type": "Filtrer par type",
        "filter_all": "Tous",
        "normalised": "Total normalisé à 100%.",
        "mode_simulation": "Simulation de Portefeuille",
        "mode_real": "Analyse de Mon Portefeuille Réel",
        "real_portfolio": "Portefeuille Réel",
        "real_portfolio_desc": "Entrez vos positions réelles pour voir la valeur de votre portefeuille.",
        "add_holding": "Ajouter une Position",
        "quantity": "Quantité",
        "ticker": "Ticker",
        "fetch_prices": "Récupérer les Prix & Analyser",
        "total_value": "Valeur Totale",
        "num_assets": "Nombre d'Actifs",
        "top_asset": "Actif Principal",
        "portfolio_health": "Santé du Portefeuille",
        "asset_class_breakdown": "Répartition par Classe d'Actifs",
        "dominant_asset": "Actif Dominant",
        "diversification": "Niveau de Diversification",
        "overall_risk": "Risque Global",
        "real_synthesis": "Synthèse du Portefeuille",
        "real_holdings": "Vos Positions",
        "price": "Prix",
        "value": "Valeur",
        "weight_pct": "Poids",
        "remove_holding": "Supprimer",
        "no_holdings": "Ajoutez des actifs et leurs quantités pour analyser votre portefeuille réel.",
        "high_div": "Élevée",
        "medium_div": "Moyenne",
        "low_div": "Faible",
        "very_low_div": "Très Faible",
    }
}


def legacy_tr(key, lang="en"):
    """Look-up for the legacy surface. Falls back to English, then to the key."""
    return LEGACY_STRINGS.get(lang, LEGACY_STRINGS.get("en", {})).get(key, key)
