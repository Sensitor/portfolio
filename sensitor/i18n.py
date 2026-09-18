"""
Bilingual strings for the Sensitor pages.

Kept separate from the legacy `T` dict in the main module so the new product
surface can be translated independently. `tr()` falls back to English, then to the
key itself, so a missing translation degrades to readable text rather than a
KeyError mid-render.

Metric definitions live here too (`DEFS`) and feed the tooltip system: every
quantitative metric on screen can be explained without leaving the app.
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
