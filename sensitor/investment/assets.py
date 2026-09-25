"""
Asset reference data.

The library the app describes instruments from: bilingual descriptions, sector
and geography mappings, the search catalogue and the model portfolios.

Pure data — no Streamlit, no I/O, no computation. It lived in the Streamlit entry
point until the V2 restructure, which meant the report generator, the tests and
any future API had to import a 3,900-line UI module to learn what SPY is.

`ASSET_INFO` is the detailed record per instrument; `SECTOR_MAPPING` and
`GEOGRAPHY_MAPPING` are the flat lookups the analytics layer uses, kept separate
because they cover tickers that have no full library entry.
"""

from __future__ import annotations

ASSET_INFO = {
    # ── US Large Cap Stocks ──────────────────────────────────────────────────
    # ── US Large Cap Stocks ──────────────────────────────────────────────────
    "AAPL": {
        "name": "Apple Inc.",
        "description": "The world's most valuable company by market cap. Designs and sells iPhones, Macs, iPads, and services (App Store, iCloud, Apple TV+). Revenue mix shifting toward high-margin recurring services.",
        "description_fr": "L'entreprise la plus valorisée au monde. Conçoit et vend iPhones, Macs, iPads et services (App Store, iCloud, Apple TV+). Revenus de plus en plus dominés par les services à haute marge.",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "Large-cap quality growth with expanding services moat",
        "utility_fr": "Croissance de qualité large-cap avec fort avantage concurrentiel services",
        "typical_use": "Core growth holding. 5–15% in balanced/growth portfolios.",
        "typical_use_fr": "Holding de croissance cœur. 5–15% dans les portefeuilles équilibrés/croissance.",
        "risk_level": "Medium-High", "liquidity": 100,
        "dividend_yield": "~0.5%", "market_cap": "~$3 billion",
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "description": "Global leader in cloud computing (Azure, #2 worldwide), enterprise software (Office 365, Teams), and gaming (Xbox, Activision). Benefits from AI integration across all product lines.",
        "description_fr": "Leader mondial du cloud (Azure, n°2 mondial), des logiciels d'entreprise (Office 365, Teams) et du gaming (Xbox, Activision). Bénéficie de l'intégration de l'IA dans toutes ses gammes.",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "Defensive tech with cloud and AI tailwinds",
        "utility_fr": "Tech défensive portée par le cloud et l'IA",
        "typical_use": "Defensive tech core holding. Pairs well with growth assets.",
        "typical_use_fr": "Position cœur tech défensive. Se marie bien avec des actifs de croissance.",
        "risk_level": "Medium", "liquidity": 100,
        "dividend_yield": "~0.7%", "market_cap": "~$3 trillion",
    },
    "GOOGL": {
        "name": "Alphabet (Google)",
        "description": "Parent company of Google Search (dominant ~90% market share), YouTube, Google Cloud, and Waymo. Advertising is the core revenue driver, diversified by fast-growing Cloud.",
        "description_fr": "Maison mère de Google Search (~90% de parts de marché), YouTube, Google Cloud et Waymo. La publicité est le moteur principal, diversifiée par le Cloud en forte croissance.",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "Search monopoly + cloud growth platform",
        "utility_fr": "Monopole de la recherche + plateforme cloud en croissance",
        "typical_use": "Growth or core holding. Diversifier from pure hardware tech.",
        "typical_use_fr": "Position de croissance ou cœur. Diversifie par rapport à la tech hardware.",
        "risk_level": "Medium", "liquidity": 100,
        "dividend_yield": "~0.5%", "market_cap": "~$2 trillion",
    },
    "AMZN": {
        "name": "Amazon",
        "description": "E-commerce giant and owner of AWS (Amazon Web Services), the world's leading cloud platform. AWS generates most of Amazon's profit despite being a fraction of revenue.",
        "description_fr": "Géant du e-commerce et propriétaire d'AWS (Amazon Web Services), la première plateforme cloud mondiale. AWS génère l'essentiel des bénéfices d'Amazon malgré une faible part du chiffre d'affaires.",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "E-commerce + cloud infrastructure dominance",
        "utility_fr": "Domination e-commerce + infrastructure cloud",
        "typical_use": "Growth portfolio core. Strong long-term compounding story.",
        "typical_use_fr": "Cœur de portefeuille croissance. Excellent historique de capitalisation long terme.",
        "risk_level": "Medium-High", "liquidity": 100,
        "dividend_yield": "0%", "market_cap": "~$2 trillion",
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "description": "Designs GPUs and AI chips. Dominant supplier of data center AI accelerators (H100, B200). Near-monopoly in AI training hardware, with expanding software (CUDA ecosystem).",
        "description_fr": "Conçoit des GPU et puces IA. Fournisseur dominant d'accélérateurs IA pour data centers (H100, B200). Quasi-monopole sur le matériel d'entraînement IA, avec l'écosystème logiciel CUDA.",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "Pure-play AI infrastructure exposure",
        "utility_fr": "Exposition pure à l'infrastructure IA",
        "typical_use": "High-conviction growth holding. High volatility, high reward.",
        "typical_use_fr": "Position de croissance forte conviction. Volatilité élevée, rendement élevé.",
        "risk_level": "High", "liquidity": 100,
        "dividend_yield": "~0.03%", "market_cap": "~$3 trillion",
    },
    "META": {
        "name": "Meta Platforms",
        "description": "Operates Facebook, Instagram, WhatsApp, and Threads — reaching 3+ billion daily users. Heavy AI investment in recommendation algorithms and Reality Labs (Quest VR headsets).",
        "description_fr": "Opère Facebook, Instagram, WhatsApp et Threads — atteignant 3 milliards+ d'utilisateurs quotidiens. Lourds investissements IA dans les algorithmes de recommandation et Reality Labs (casques VR Quest).",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "Social media advertising dominance + AI-driven monetization",
        "utility_fr": "Domination publicité réseaux sociaux + monétisation pilotée par l'IA",
        "typical_use": "Growth holding. Strong cash generation and buybacks.",
        "typical_use_fr": "Position de croissance. Forte génération de trésorerie et rachats d'actions.",
        "risk_level": "Medium-High", "liquidity": 100,
        "dividend_yield": "~0.4%", "market_cap": "~$1.5 trillion",
    },
    "TSLA": {
        "name": "Tesla",
        "description": "Pioneer in electric vehicles and energy storage. Also developing autonomous driving (FSD), Robotaxi network, and Optimus humanoid robots. Highly valued for optionality.",
        "description_fr": "Pionnier des véhicules électriques et du stockage d'énergie. Développe aussi la conduite autonome (FSD), le réseau Robotaxi et les robots humanoïdes Optimus. Très valorisé pour ses options de croissance.",
        "sector": "Automotive", "geography": "USA", "asset_class": "Stock",
        "utility": "EV/autonomy/energy disruption play",
        "utility_fr": "Pari disruptif VE / autonomie / énergie",
        "typical_use": "Satellite holding in aggressive portfolios. Expect high volatility.",
        "typical_use_fr": "Position satellite dans les portefeuilles agressifs. Volatilité élevée attendue.",
        "risk_level": "Very High", "liquidity": 100,
        "dividend_yield": "0%", "market_cap": "~$800 billion",
    },
    "JPM": {
        "name": "JPMorgan Chase",
        "description": "America's largest bank by assets. Diversified across investment banking, consumer banking, asset management, and trading. Known for exceptional risk management and consistent profitability.",
        "description_fr": "La plus grande banque américaine par les actifs. Diversifiée en banque d'investissement, banque de détail, gestion d'actifs et trading. Reconnue pour sa gestion des risques et sa rentabilité constante.",
        "sector": "Financials", "geography": "USA", "asset_class": "Stock",
        "utility": "Financial sector exposure, income + stability",
        "utility_fr": "Exposition au secteur financier, revenus + stabilité",
        "typical_use": "Defensive income holding. Benefits from higher interest rates.",
        "typical_use_fr": "Position défensive de revenus. Bénéficie de la hausse des taux d'intérêt.",
        "risk_level": "Medium", "liquidity": 95,
        "dividend_yield": "~2.3%", "market_cap": "~$700 billion",
    },
    "JNJ": {
        "name": "Johnson & Johnson",
        "description": "Healthcare conglomerate spanning pharmaceuticals (Janssen), MedTech (surgical robots, orthopedics), and consumer health. Known as a 'Dividend King' with 60+ years of consecutive dividend increases.",
        "description_fr": "Conglomérat de santé couvrant la pharmacie (Janssen), le MedTech (robots chirurgicaux, orthopédie) et la santé grand public. 'Dividend King' avec 60+ ans d'augmentations consécutives.",
        "sector": "Healthcare", "geography": "USA", "asset_class": "Stock",
        "utility": "Defensive healthcare with reliable income",
        "utility_fr": "Santé défensive avec revenus fiables",
        "typical_use": "Defensive anchor for conservative portfolios.",
        "typical_use_fr": "Ancre défensive pour les portefeuilles conservateurs.",
        "risk_level": "Low-Medium", "liquidity": 95,
        "dividend_yield": "~3%", "market_cap": "~$400 billion",
    },
    "XOM": {
        "name": "ExxonMobil",
        "description": "One of the world's largest oil & gas companies. Integrated operations span exploration, refining, and chemicals. Strong free cash flow used for dividends and buybacks.",
        "description_fr": "L'un des plus grands groupes pétroliers et gaziers mondiaux. Opérations intégrées couvrant l'exploration, le raffinage et la chimie. Fort cash-flow libre reversé en dividendes et rachats d'actions.",
        "sector": "Energy", "geography": "USA", "asset_class": "Stock",
        "utility": "Energy sector and inflation hedge",
        "utility_fr": "Exposition au secteur énergie et couverture contre l'inflation",
        "typical_use": "Inflation hedge, income holding. Performs well in rising oil price environments.",
        "typical_use_fr": "Couverture inflation, revenu. Performe bien en période de hausse du pétrole.",
        "risk_level": "Medium", "liquidity": 95,
        "dividend_yield": "~3.5%", "market_cap": "~$450 billion",
    },
    "V": {
        "name": "Visa Inc.",
        "description": "The world's largest payment network. Processes billions of transactions globally. Asset-light, high-margin business model — earns a toll on every digital payment.",
        "description_fr": "Le plus grand réseau de paiement mondial. Traite des milliards de transactions. Modèle économique léger en actifs et à forte marge — perçoit un péage sur chaque paiement numérique.",
        "sector": "Financials", "geography": "USA", "asset_class": "Stock",
        "utility": "Global payments infrastructure, digital economy exposure",
        "utility_fr": "Infrastructure paiements mondiale, exposition à l'économie numérique",
        "typical_use": "Quality compounder for long-term growth portfolios.",
        "typical_use_fr": "Capitaliseur de qualité pour les portefeuilles de croissance long terme.",
        "risk_level": "Medium", "liquidity": 98,
        "dividend_yield": "~0.8%", "market_cap": "~$550 billion",
    },
    # ── US ETFs ──────────────────────────────────────────────────────────────
    "SPY": {
        "name": "SPDR S&P 500 ETF",
        "description": "The world's most traded ETF. Tracks the S&P 500 index — 500 largest US companies by market cap. Provides instant, low-cost exposure to American large-cap equities.",
        "description_fr": "L'ETF le plus échangé au monde. Réplique l'indice S&P 500 — les 500 plus grandes entreprises américaines. Offre une exposition instantanée et peu coûteuse aux actions américaines large-cap.",
        "sector": "Diversified", "geography": "USA", "asset_class": "ETF",
        "utility": "Core US large-cap equity exposure",
        "utility_fr": "Exposition cœur aux actions américaines large-cap",
        "typical_use": "Foundation of most diversified portfolios. 20–50% core holding.",
        "typical_use_fr": "Socle de la plupart des portefeuilles diversifiés. Position cœur de 20–50%.",
        "risk_level": "Medium", "liquidity": 100,
        "dividend_yield": "~1.3%", "market_cap": "~$500 billion AUM",
    },
    "QQQ": {
        "name": "Invesco Nasdaq 100 ETF",
        "description": "Tracks the 100 largest non-financial companies on the Nasdaq. Heavily concentrated in technology and growth stocks (Apple, Microsoft, NVIDIA, Amazon, Meta). Higher volatility than SPY.",
        "description_fr": "Réplique les 100 plus grandes entreprises non financières du Nasdaq. Fortement concentré en tech et croissance (Apple, Microsoft, NVIDIA, Amazon, Meta). Plus volatile que SPY.",
        "sector": "Technology-Heavy", "geography": "USA", "asset_class": "ETF",
        "utility": "Tech-focused growth exposure via index",
        "utility_fr": "Exposition croissance axée tech via indice",
        "typical_use": "Growth tilt, tech overweight. Complement to SPY.",
        "typical_use_fr": "Surpondération croissance/tech. Complément de SPY.",
        "risk_level": "Medium-High", "liquidity": 100,
        "dividend_yield": "~0.5%", "market_cap": "~$250 billion AUM",
    },
    "VTI": {
        "name": "Vanguard Total Market ETF",
        "description": "Broadest US equity ETF — tracks over 3,700 US stocks including small, mid, and large caps. More diversified than SPY. Ultra-low expense ratio (0.03%).",
        "description_fr": "L'ETF actions américaines le plus large — réplique 3 700+ titres US incluant petites, moyennes et grandes capitalisations. Plus diversifié que SPY. Frais ultra-faibles (0,03%).",
        "sector": "Diversified", "geography": "USA", "asset_class": "ETF",
        "utility": "Total US market exposure in one ticker",
        "utility_fr": "Exposition à l'ensemble du marché américain en un seul ticker",
        "typical_use": "Ultimate US equity core holding for long-term investors.",
        "typical_use_fr": "Position cœur actions américaines idéale pour les investisseurs long terme.",
        "risk_level": "Medium", "liquidity": 100,
        "dividend_yield": "~1.3%", "market_cap": "~$400 billion AUM",
    },
    "VOO": {
        "name": "Vanguard S&P 500 ETF",
        "description": "Vanguard's version of the S&P 500 tracker. Nearly identical holdings to SPY but with a lower expense ratio (0.03% vs 0.09%). Preferred by long-term buy-and-hold investors.",
        "description_fr": "La version Vanguard du tracker S&P 500. Composition quasi identique à SPY mais frais inférieurs (0,03% vs 0,09%). Préféré des investisseurs buy-and-hold long terme.",
        "sector": "Diversified", "geography": "USA", "asset_class": "ETF",
        "utility": "Low-cost S&P 500 exposure",
        "utility_fr": "Exposition S&P 500 à faible coût",
        "typical_use": "Core US equity holding, especially for tax-advantaged accounts.",
        "typical_use_fr": "Position cœur actions US, idéale pour les comptes fiscalement avantageux.",
        "risk_level": "Medium", "liquidity": 100,
        "dividend_yield": "~1.3%", "market_cap": "~$550 billion AUM",
    },
    "VXUS": {
        "name": "Vanguard Total International ETF",
        "description": "Tracks non-US stock markets — 7,000+ companies across developed (Europe, Japan, Canada) and emerging markets (China, India, Brazil). Essential for true global diversification.",
        "description_fr": "Réplique les marchés actions hors USA — 7 000+ entreprises dans les marchés développés (Europe, Japon, Canada) et émergents (Chine, Inde, Brésil). Indispensable pour une diversification mondiale.",
        "sector": "International Diversified", "geography": "Ex-US Global", "asset_class": "ETF",
        "utility": "Single-ticker access to all non-US equities",
        "utility_fr": "Accès en un seul ticker à toutes les actions hors USA",
        "typical_use": "International diversification — 20–40% of equity allocation.",
        "typical_use_fr": "Diversification internationale — 20–40% de l'allocation actions.",
        "risk_level": "Medium", "liquidity": 98,
        "dividend_yield": "~2.8%", "market_cap": "~$70 billion AUM",
    },
    "EFA": {
        "name": "iShares MSCI EAFE ETF",
        "description": "Tracks large and mid-cap stocks in developed markets outside the US: Europe, Australasia, and the Far East (Japan, UK, France, Germany, Switzerland). No emerging market exposure.",
        "description_fr": "Réplique les grandes et moyennes capitalisations des marchés développés hors USA : Europe, Australasie, Extrême-Orient (Japon, UK, France, Allemagne, Suisse). Pas d'exposition aux marchés émergents.",
        "sector": "International Developed", "geography": "Developed Ex-US", "asset_class": "ETF",
        "utility": "Developed market diversification (Europe + Asia)",
        "utility_fr": "Diversification marchés développés (Europe + Asie)",
        "typical_use": "Conservative international allocation. Lower vol than EEM.",
        "typical_use_fr": "Allocation internationale conservatrice. Moins volatile qu'EEM.",
        "risk_level": "Medium", "liquidity": 98,
        "dividend_yield": "~3%", "market_cap": "~$50 billion AUM",
    },
    "EEM": {
        "name": "iShares MSCI Emerging Markets ETF",
        "description": "Tracks large and mid-cap stocks in 24 emerging market countries. Top exposures: China, India, Taiwan, South Korea, Brazil. Higher growth potential, higher volatility.",
        "description_fr": "Réplique les grandes et moyennes caps dans 24 pays émergents. Principales expositions : Chine, Inde, Taïwan, Corée du Sud, Brésil. Potentiel de croissance élevé, volatilité élevée.",
        "sector": "Emerging Markets", "geography": "Emerging Markets", "asset_class": "ETF",
        "utility": "Emerging market growth exposure",
        "utility_fr": "Exposition à la croissance des marchés émergents",
        "typical_use": "Satellite allocation (5–15%) for return enhancement.",
        "typical_use_fr": "Allocation satellite (5–15%) pour améliorer les rendements.",
        "risk_level": "High", "liquidity": 97,
        "dividend_yield": "~2.5%", "market_cap": "~$20 billion AUM",
    },
    "VNQ": {
        "name": "Vanguard Real Estate ETF",
        "description": "Tracks US Real Estate Investment Trusts (REITs). Provides exposure to commercial real estate (offices, apartments, retail, industrial, data centers) without directly owning property.",
        "description_fr": "Réplique les fonds d'investissement immobilier américains (REITs). Donne accès à l'immobilier commercial (bureaux, appartements, commerces, entrepôts, data centers) sans détenir directement de biens.",
        "sector": "Real Estate", "geography": "USA", "asset_class": "ETF",
        "utility": "Real estate income + inflation hedge",
        "utility_fr": "Revenus immobiliers + couverture contre l'inflation",
        "typical_use": "Income and diversification. Often 5–10% in balanced portfolios.",
        "typical_use_fr": "Revenus et diversification. Souvent 5–10% dans les portefeuilles équilibrés.",
        "risk_level": "Medium", "liquidity": 95,
        "dividend_yield": "~3.8%", "market_cap": "~$35 billion AUM",
    },
    "TLT": {
        "name": "iShares 20+ Year Treasury Bond ETF",
        "description": "Tracks long-duration US government bonds (20+ year maturities). High sensitivity to interest rate changes — falls when rates rise, surges when rates fall. Classic safe-haven and recession hedge.",
        "description_fr": "Réplique les obligations d'État américaines à long terme (maturités 20+ ans). Très sensible aux taux : baisse quand les taux montent, monte quand ils baissent. Valeur refuge classique et couverture récession.",
        "sector": "Fixed Income", "geography": "USA", "asset_class": "ETF",
        "utility": "Long-duration rate hedge and crisis buffer",
        "utility_fr": "Couverture taux longue durée et tampon de crise",
        "typical_use": "Recession hedge, deflation protection. High duration risk.",
        "typical_use_fr": "Couverture récession, protection déflation. Risque de duration élevé.",
        "risk_level": "Medium", "liquidity": 99,
        "dividend_yield": "~4%", "market_cap": "~$50 billion AUM",
    },
    "AGG": {
        "name": "iShares Core US Aggregate Bond ETF",
        "description": "Broad US investment-grade bond market — government, corporate, and mortgage-backed securities. The benchmark fixed income ETF. Lower yield than TLT but much less rate sensitivity.",
        "description_fr": "Marché obligataire américain investment-grade au sens large — obligations d'État, d'entreprises et titres adossés à des créances hypothécaires. L'ETF obligataire de référence. Rendement inférieur à TLT mais bien moins sensible aux taux.",
        "sector": "Fixed Income", "geography": "USA", "asset_class": "ETF",
        "utility": "Portfolio stability, income, capital preservation",
        "utility_fr": "Stabilité du portefeuille, revenus, préservation du capital",
        "typical_use": "Ballast in balanced portfolios. Classic 40% in 60/40 allocation.",
        "typical_use_fr": "Lest des portefeuilles équilibrés. Le classique 40% dans l'allocation 60/40.",
        "risk_level": "Low", "liquidity": 100,
        "dividend_yield": "~3.5%", "market_cap": "~$100 billion AUM",
    },
    "LQD": {
        "name": "iShares Investment Grade Corporate Bond ETF",
        "description": "Tracks investment-grade corporate bonds. Higher yield than AGG (includes corporate credit premium). More rate-sensitive than short-term bonds.",
        "description_fr": "Réplique les obligations d'entreprises investment-grade. Rendement supérieur à AGG (prime de crédit corporate incluse). Plus sensible aux taux que les obligations court terme.",
        "sector": "Fixed Income", "geography": "USA", "asset_class": "ETF",
        "utility": "Higher-yield bond exposure with manageable credit risk",
        "utility_fr": "Exposition obligataire à rendement élevé avec risque de crédit maîtrisé",
        "typical_use": "Enhanced income vs AGG. Complement to government bonds.",
        "typical_use_fr": "Revenus améliorés par rapport à AGG. Complément aux obligations souveraines.",
        "risk_level": "Low-Medium", "liquidity": 98,
        "dividend_yield": "~4.5%", "market_cap": "~$35 billion AUM",
    },
    "SCHD": {
        "name": "Schwab US Dividend Equity ETF",
        "description": "Tracks US dividend-paying stocks with a quality filter (high yield + stable growth). Concentrated in Financials, Healthcare, Consumer Staples, and Industrials.",
        "description_fr": "Réplique les actions américaines à dividende avec filtre qualité (rendement élevé + croissance stable). Concentré en Financières, Santé, Biens de consommation courante et Industrie.",
        "sector": "Dividend/Income", "geography": "USA", "asset_class": "ETF",
        "utility": "Quality dividend income + capital appreciation",
        "utility_fr": "Dividendes de qualité + appréciation du capital",
        "typical_use": "Income-focused portion of equity allocation.",
        "typical_use_fr": "Partie revenus de l'allocation actions.",
        "risk_level": "Low-Medium", "liquidity": 98,
        "dividend_yield": "~3.5%", "market_cap": "~$55 billion AUM",
    },
    "GLD": {
        "name": "SPDR Gold Shares ETF",
        "description": "Physically-backed gold ETF. Holds actual gold bars in vaults. Tracks the spot gold price minus a small expense ratio (0.40%). The most liquid gold ETF in the world.",
        "description_fr": "ETF or physique. Détient de véritables lingots d'or en coffre-fort. Réplique le cours spot de l'or moins de faibles frais (0,40%). Le plus liquide des ETF or au monde.",
        "sector": "Commodities", "geography": "Global", "asset_class": "ETF",
        "utility": "Inflation hedge, safe haven, portfolio insurance",
        "utility_fr": "Couverture inflation, valeur refuge, assurance portefeuille",
        "typical_use": "Crisis protection and inflation hedge — 5–15% allocation.",
        "typical_use_fr": "Protection en crise et couverture inflation — allocation 5–15%.",
        "risk_level": "Low-Medium", "liquidity": 100,
        "dividend_yield": "0%", "market_cap": "~$60 billion AUM",
    },
    "SLV": {
        "name": "iShares Silver Trust ETF",
        "description": "Physically-backed silver ETF. Tracks the spot price of silver. More volatile than gold but also more industrial use (solar panels, electronics). Can outperform gold in bull markets.",
        "description_fr": "ETF argent physique. Réplique le cours spot de l'argent. Plus volatile que l'or mais avec des usages industriels importants (panneaux solaires, électronique). Peut surperformer l'or en phase haussière.",
        "sector": "Commodities", "geography": "Global", "asset_class": "ETF",
        "utility": "Industrial metal + precious metal speculation",
        "utility_fr": "Métal industriel + spéculation métal précieux",
        "typical_use": "Small satellite (1–5%). More speculative than GLD.",
        "typical_use_fr": "Petit satellite (1–5%). Plus spéculatif que GLD.",
        "risk_level": "Medium-High", "liquidity": 95,
        "dividend_yield": "0%", "market_cap": "~$12 billion AUM",
    },
    "XLK": {
        "name": "Technology Select Sector SPDR ETF",
        "description": "Pure tech sector ETF tracking S&P 500 technology companies. Top holdings: Apple, Microsoft, NVIDIA. More concentrated sector bet than QQQ.",
        "description_fr": "ETF purement tech répliquant les entreprises technologiques du S&P 500. Principales positions : Apple, Microsoft, NVIDIA. Pari sectoriel plus concentré que QQQ.",
        "sector": "Technology", "geography": "USA", "asset_class": "ETF",
        "utility": "Pure US technology sector exposure",
        "utility_fr": "Exposition pure au secteur technologique américain",
        "typical_use": "Tactical tech overweight in growth portfolios.",
        "typical_use_fr": "Surpondération tactique tech dans les portefeuilles de croissance.",
        "risk_level": "High", "liquidity": 98,
        "dividend_yield": "~0.6%", "market_cap": "~$65 billion AUM",
    },
    "XLF": {
        "name": "Financial Select Sector SPDR ETF",
        "description": "Tracks S&P 500 financial companies: banks, insurance, asset managers. Benefits from rising interest rates. Top holdings: JPMorgan, Berkshire, Visa, Mastercard.",
        "description_fr": "Réplique les entreprises financières du S&P 500 : banques, assurances, gestionnaires d'actifs. Bénéficie des hausses de taux. Principales positions : JPMorgan, Berkshire, Visa, Mastercard.",
        "sector": "Financials", "geography": "USA", "asset_class": "ETF",
        "utility": "Financial sector exposure, rate-sensitive",
        "utility_fr": "Exposition au secteur financier, sensible aux taux",
        "typical_use": "Tactical sector allocation when rates are rising.",
        "typical_use_fr": "Allocation sectorielle tactique en période de hausse des taux.",
        "risk_level": "Medium", "liquidity": 98,
        "dividend_yield": "~1.8%", "market_cap": "~$40 billion AUM",
    },
    "ARKK": {
        "name": "ARK Innovation ETF",
        "description": "Actively managed fund focusing on disruptive technology: AI, genomics, robotics, fintech, crypto. High concentration in small and mid-cap growth companies. Very high volatility.",
        "description_fr": "Fonds actif axé sur la technologie disruptive : IA, génomique, robotique, fintech, crypto. Forte concentration en entreprises de croissance petites et moyennes caps. Volatilité très élevée.",
        "sector": "Disruptive Tech", "geography": "USA", "asset_class": "ETF",
        "utility": "High-conviction disruptive innovation exposure",
        "utility_fr": "Exposition forte conviction à l'innovation disruptive",
        "typical_use": "Speculative satellite allocation (max 5%). Very high risk/reward.",
        "typical_use_fr": "Allocation satellite spéculative (max 5%). Risque/rendement très élevé.",
        "risk_level": "Very High", "liquidity": 88,
        "dividend_yield": "0%", "market_cap": "~$6 billion AUM",
    },
    # ── Crypto ───────────────────────────────────────────────────────────────
    "BTC-USD": {
        "name": "Bitcoin (BTC)",
        "description": "The first and largest cryptocurrency by market cap. Operates on a decentralised blockchain with a hard-capped supply of 21 million coins. Increasingly viewed as 'digital gold' by institutions.",
        "description_fr": "La première et plus grande cryptomonnaie par capitalisation. Fonctionne sur une blockchain décentralisée avec une offre limitée à 21 millions de coins. De plus en plus considéré comme 'l'or numérique' par les institutions.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Digital scarcity store-of-value, speculative return driver",
        "utility_fr": "Réserve de valeur par rareté numérique, moteur de rendement spéculatif",
        "typical_use": "Small allocation (3–10%) as portfolio diversifier and return booster.",
        "typical_use_fr": "Petite allocation (3–10%) comme diversificateur et booster de rendement.",
        "risk_level": "Very High", "liquidity": 85,
        "dividend_yield": "0%", "market_cap": "~$1.5 trillion",
    },
    "ETH-USD": {
        "name": "Ethereum (ETH)",
        "description": "The leading smart contract platform powering DeFi, NFTs, and Web3. Transitioned to Proof-of-Stake in 2022, reducing energy use by 99.9%. Ether is used to pay transaction fees.",
        "description_fr": "La principale plateforme de contrats intelligents alimentant la DeFi, les NFTs et le Web3. Passé en Proof-of-Stake en 2022, réduisant la consommation d'énergie de 99,9%. L'Ether sert à payer les frais de transaction.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Web3 infrastructure platform exposure",
        "utility_fr": "Exposition à la plateforme d'infrastructure Web3",
        "typical_use": "Complement to Bitcoin. Typically smaller allocation (1–5%).",
        "typical_use_fr": "Complément du Bitcoin. Allocation généralement plus petite (1–5%).",
        "risk_level": "Very High", "liquidity": 82,
        "dividend_yield": "0% (staking ~4%)", "market_cap": "~$300 billion",
    },
    "SOL-USD": {
        "name": "Solana (SOL)",
        "description": "High-performance Layer 1 blockchain processing 50,000+ transactions per second at low cost. Dominant in meme coins, NFTs, and DeFi. More volatile than BTC/ETH but higher growth potential.",
        "description_fr": "Blockchain Layer 1 haute performance traitant 50 000+ transactions/seconde à faible coût. Dominante dans les meme coins, NFTs et DeFi. Plus volatile que BTC/ETH mais potentiel de croissance élevé.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "High-growth crypto ecosystem exposure",
        "utility_fr": "Exposition à l'écosystème crypto à forte croissance",
        "typical_use": "Speculative satellite (1–3%). Very high volatility.",
        "typical_use_fr": "Satellite spéculatif (1–3%). Volatilité très élevée.",
        "risk_level": "Very High", "liquidity": 70,
        "dividend_yield": "0% (staking ~7%)", "market_cap": "~$70 billion",
    },
    "BNB-USD": {
        "name": "Binance Coin (BNB)",
        "description": "Native token of the Binance ecosystem — the world's largest crypto exchange. Used for trading fee discounts, BNB Chain transactions (DeFi/dApps), and token launches via Binance Launchpad.",
        "description_fr": "Token natif de l'écosystème Binance — le plus grand exchange crypto au monde. Utilisé pour les réductions de frais de trading, les transactions BNB Chain (DeFi/dApps) et les lancements via Binance Launchpad.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Exchange utility token + BNB Chain ecosystem",
        "utility_fr": "Token utilitaire d'exchange + écosystème BNB Chain",
        "typical_use": "Speculative satellite (1–2%). Tied to Binance exchange health.",
        "typical_use_fr": "Satellite spéculatif (1–2%). Lié à la santé de l'exchange Binance.",
        "risk_level": "Very High", "liquidity": 78,
        "dividend_yield": "0%", "market_cap": "~$80 billion",
    },
    "XRP-USD": {
        "name": "XRP (Ripple)",
        "description": "Digital asset designed for fast, low-cost international payments. Used by banks and financial institutions via RippleNet. Won a landmark SEC lawsuit in 2023 clarifying its legal status in the US.",
        "description_fr": "Actif numérique conçu pour des paiements internationaux rapides et peu coûteux. Utilisé par les banques via RippleNet. A gagné un procès historique contre la SEC en 2023 clarifiant son statut légal aux USA.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Cross-border payments and banking infrastructure crypto",
        "utility_fr": "Crypto dédiée aux paiements transfrontaliers et à l'infrastructure bancaire",
        "typical_use": "Speculative satellite (1–3%). High regulatory sensitivity.",
        "typical_use_fr": "Satellite spéculatif (1–3%). Très sensible aux évolutions réglementaires.",
        "risk_level": "Very High", "liquidity": 80,
        "dividend_yield": "0%", "market_cap": "~$120 billion",
    },
    "ADA-USD": {
        "name": "Cardano (ADA)",
        "description": "Proof-of-Stake Layer 1 blockchain built with a research-first, peer-reviewed approach. Developed by IOHK (co-founded by Ethereum co-founder Charles Hoskinson). Focuses on scalability and sustainability.",
        "description_fr": "Blockchain Layer 1 Proof-of-Stake construite avec une approche académique et revue par les pairs. Développée par IOHK (cofondé par le co-fondateur d'Ethereum Charles Hoskinson). Axée sur la scalabilité et la durabilité.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Proof-of-Stake smart contract platform, sustainable blockchain",
        "utility_fr": "Plateforme de contrats intelligents PoS, blockchain durable",
        "typical_use": "Speculative alt-coin (0.5–2%). Higher risk than ETH.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–2%). Risque plus élevé qu'ETH.",
        "risk_level": "Very High", "liquidity": 72,
        "dividend_yield": "0% (staking ~4%)", "market_cap": "~$25 billion",
    },
    "AVAX-USD": {
        "name": "Avalanche (AVAX)",
        "description": "High-speed Layer 1 blockchain with sub-second finality and low fees. Uses a unique 3-chain architecture (X, P, C chains). Growing DeFi and gaming ecosystem, strong institutional adoption.",
        "description_fr": "Blockchain Layer 1 haute vitesse avec finalité en sous-seconde et frais bas. Architecture unique à 3 chaînes (X, P, C). Écosystème DeFi et gaming en croissance, forte adoption institutionnelle.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "High-performance DeFi and institutional blockchain",
        "utility_fr": "Blockchain DeFi haute performance et institutionnelle",
        "typical_use": "Speculative alt-coin (0.5–2%). Competitive with SOL.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–2%). En compétition avec SOL.",
        "risk_level": "Very High", "liquidity": 68,
        "dividend_yield": "0% (staking ~8%)", "market_cap": "~$15 billion",
    },
    "DOT-USD": {
        "name": "Polkadot (DOT)",
        "description": "Multi-chain protocol enabling different blockchains to communicate and share security. Uses a Relay Chain + Parachain architecture. Developed by Ethereum co-founder Gavin Wood and the Web3 Foundation.",
        "description_fr": "Protocole multi-chaînes permettant à différentes blockchains de communiquer et partager leur sécurité. Architecture Relay Chain + Parachain. Développé par le co-fondateur d'Ethereum Gavin Wood et la Web3 Foundation.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Cross-chain interoperability protocol",
        "utility_fr": "Protocole d'interopérabilité multi-chaînes",
        "typical_use": "Speculative alt-coin (0.5–1.5%). High technical complexity.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–1,5%). Complexité technique élevée.",
        "risk_level": "Very High", "liquidity": 65,
        "dividend_yield": "0% (staking ~15%)", "market_cap": "~$10 billion",
    },
    "LINK-USD": {
        "name": "Chainlink (LINK)",
        "description": "Decentralised oracle network that connects smart contracts to real-world data (prices, weather, sports results). Critical DeFi infrastructure — used by 1,000+ blockchain protocols.",
        "description_fr": "Réseau oracle décentralisé connectant les smart contracts aux données du monde réel (prix, météo, résultats sportifs). Infrastructure DeFi critique — utilisée par 1 000+ protocoles blockchain.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "DeFi infrastructure — blockchain oracle network",
        "utility_fr": "Infrastructure DeFi — réseau oracle blockchain",
        "typical_use": "Speculative alt-coin (0.5–2%). Fundamental DeFi infrastructure bet.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–2%). Pari sur l'infrastructure DeFi fondamentale.",
        "risk_level": "Very High", "liquidity": 65,
        "dividend_yield": "0%", "market_cap": "~$8 billion",
    },
    "MATIC-USD": {
        "name": "Polygon (POL/MATIC)",
        "description": "Ethereum Layer 2 scaling solution dramatically reducing gas fees and transaction times. Now rebranding to POL as it transitions to a multi-chain aggregator. Used by major brands (Starbucks, Nike, Reddit).",
        "description_fr": "Solution de mise à l'échelle Layer 2 d'Ethereum réduisant drastiquement les frais de gas et les temps de transaction. En cours de rebranding vers POL dans sa transition vers un agrégateur multi-chaînes. Utilisé par Starbucks, Nike, Reddit.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Ethereum Layer 2 scaling and multi-chain aggregation",
        "utility_fr": "Mise à l'échelle Layer 2 d'Ethereum et agrégation multi-chaînes",
        "typical_use": "Speculative alt-coin (0.5–2%). Strong enterprise adoption.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–2%). Forte adoption entreprises.",
        "risk_level": "Very High", "liquidity": 70,
        "dividend_yield": "0%", "market_cap": "~$5 billion",
    },
    "DOGE-USD": {
        "name": "Dogecoin (DOGE)",
        "description": "Originally a meme coin, Dogecoin has become a widely recognised crypto asset with strong community support. Favoured by Elon Musk. Used for tipping and micro-payments. Unlimited supply.",
        "description_fr": "À l'origine un meme coin, Dogecoin est devenu un actif crypto reconnu avec une forte communauté. Soutenu par Elon Musk. Utilisé pour les pourboires et micro-paiements. Offre illimitée.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Meme coin / community-driven speculative asset",
        "utility_fr": "Meme coin / actif spéculatif piloté par la communauté",
        "typical_use": "Pure speculation (0–1%). Very high sentiment sensitivity.",
        "typical_use_fr": "Pure spéculation (0–1%). Très sensible au sentiment de marché.",
        "risk_level": "Very High", "liquidity": 75,
        "dividend_yield": "0%", "market_cap": "~$25 billion",
    },
    "INJ-USD": {
        "name": "Injective (INJ)",
        "description": "Layer 1 blockchain optimised for DeFi applications — particularly decentralised exchanges (DEX), derivatives, and prediction markets. Fast (10,000+ TPS), EVM-compatible, with a deflationary token burn mechanism.",
        "description_fr": "Blockchain Layer 1 optimisée pour les applications DeFi — notamment les échanges décentralisés (DEX), les dérivés et les marchés prédictifs. Rapide (10 000+ TPS), compatible EVM, avec un mécanisme de burn déflationniste.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "DeFi-native blockchain for derivatives and exchanges",
        "utility_fr": "Blockchain native DeFi pour dérivés et échanges décentralisés",
        "typical_use": "High-risk alt-coin (0.5–1%). Emerging DeFi infrastructure.",
        "typical_use_fr": "Alt-coin à haut risque (0,5–1%). Infrastructure DeFi émergente.",
        "risk_level": "Very High", "liquidity": 55,
        "dividend_yield": "0% (staking ~10%)", "market_cap": "~$3 billion",
    },
    "TON-USD": {
        "name": "Toncoin (TON)",
        "description": "Blockchain developed originally by Telegram, now operated by the TON Foundation. Deeply integrated with Telegram's 900M users. Fast, scalable, and increasingly used for payments and Web3 games.",
        "description_fr": "Blockchain développée à l'origine par Telegram, désormais gérée par la TON Foundation. Profondément intégrée aux 900M d'utilisateurs Telegram. Rapide, scalable, de plus en plus utilisée pour les paiements et les jeux Web3.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Telegram-integrated payments and Web3 gateway",
        "utility_fr": "Passerelle paiements et Web3 intégrée à Telegram",
        "typical_use": "Speculative alt-coin (0.5–1.5%). Unique Telegram distribution advantage.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–1,5%). Avantage unique de distribution via Telegram.",
        "risk_level": "Very High", "liquidity": 60,
        "dividend_yield": "0% (staking ~4%)", "market_cap": "~$20 billion",
    },
}

SECTOR_MAPPING = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", "AMZN": "Technology",
    "TSLA": "Automotive", "NVDA": "Technology", "META": "Technology", "NFLX": "Technology",
    "JPM": "Financials", "JNJ": "Healthcare", "XOM": "Energy", "V": "Financials",
    "MA": "Financials", "WMT": "Consumer", "HD": "Consumer", "BRK-B": "Financials",
    "SPY": "Diversified", "QQQ": "Technology", "VTI": "Diversified", "VOO": "Diversified",
    "VXUS": "International", "EFA": "International", "EEM": "Emerging Markets",
    "VNQ": "Real Estate", "TLT": "Bonds", "AGG": "Bonds", "LQD": "Bonds",
    "SCHD": "Dividend", "GLD": "Commodities", "SLV": "Commodities",
    "XLK": "Technology", "XLF": "Financials", "XLE": "Energy", "XLV": "Healthcare",
    "ARKK": "Technology",
    "BTC-USD": "Crypto", "ETH-USD": "Crypto", "SOL-USD": "Crypto", "BNB-USD": "Crypto",
    "XRP-USD": "Crypto", "ADA-USD": "Crypto", "AVAX-USD": "Crypto", "DOT-USD": "Crypto",
    "LINK-USD": "Crypto", "MATIC-USD": "Crypto", "DOGE-USD": "Crypto",
    "INJ-USD": "Crypto", "TON-USD": "Crypto",
}

GEOGRAPHY_MAPPING = {
    "AAPL": "USA", "MSFT": "USA", "GOOGL": "USA", "AMZN": "USA",
    "NVDA": "USA", "META": "USA", "TSLA": "USA", "NFLX": "USA",
    "JPM": "USA", "JNJ": "USA", "XOM": "USA", "V": "USA",
    "MA": "USA", "WMT": "USA", "HD": "USA", "BRK-B": "USA",
    "SPY": "USA", "QQQ": "USA", "VTI": "USA", "VOO": "USA",
    "VXUS": "International", "EFA": "Developed Ex-US", "EEM": "Emerging Markets",
    "VNQ": "USA", "TLT": "USA", "AGG": "USA", "LQD": "USA",
    "SCHD": "USA", "XLK": "USA", "XLF": "USA", "XLE": "USA", "XLV": "USA",
    "ARKK": "USA", "GLD": "Global", "SLV": "Global",
    "BTC-USD": "Global", "ETH-USD": "Global", "SOL-USD": "Global", "BNB-USD": "Global",
    "XRP-USD": "Global", "ADA-USD": "Global", "AVAX-USD": "Global", "DOT-USD": "Global",
    "LINK-USD": "Global", "MATIC-USD": "Global", "DOGE-USD": "Global",
    "INJ-USD": "Global", "TON-USD": "Global",
    "VWO": "Emerging Markets",
}

POPULAR_ASSETS = {
    "US Stocks": {
        "Apple": "AAPL", "Microsoft": "MSFT", "Google": "GOOGL", "Amazon": "AMZN",
        "NVIDIA": "NVDA", "Meta": "META", "Tesla": "TSLA", "JPMorgan": "JPM",
        "Johnson & Johnson": "JNJ", "ExxonMobil": "XOM", "Visa": "V",
    },
    "US ETFs": {
        "S&P 500 (SPY)": "SPY", "S&P 500 (VOO)": "VOO", "Nasdaq 100": "QQQ",
        "Total Market": "VTI", "Dividends": "SCHD", "Real Estate": "VNQ",
        "Long Bonds": "TLT", "Aggregate Bonds": "AGG", "Tech Sector": "XLK",
        "ARK Innovation": "ARKK",
    },
    "International ETFs": {
        "All World Ex-US": "VXUS", "Developed Markets": "EFA", "Emerging Markets": "EEM",
    },
    "Commodities & Gold": {
        "Gold": "GLD", "Silver": "SLV",
    },
    "Crypto": {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD",
        "BNB": "BNB-USD", "XRP": "XRP-USD", "Cardano": "ADA-USD",
        "Avalanche": "AVAX-USD", "Polkadot": "DOT-USD", "Chainlink": "LINK-USD",
        "Polygon": "MATIC-USD", "Dogecoin": "DOGE-USD", "Injective": "INJ-USD",
        "Toncoin": "TON-USD",
    },
}

MODEL_PORTFOLIOS = {
    "Capital Preservation": {
        "description_en": "Ultra-defensive: bonds + gold. Prioritises capital protection over returns.",
        "description_fr": "Ultra-défensif : obligations + or. Priorité à la protection du capital.",
        "profile": "safe",
        "allocation": {"AGG": 0.45, "TLT": 0.20, "GLD": 0.20, "SPY": 0.15},
        "expected_return": 0.05,
        "expected_volatility": 0.06,
    },
    "Defensive Income": {
        "description_en": "Conservative mix generating reliable dividend income with low volatility.",
        "description_fr": "Mix conservateur générant des revenus de dividendes fiables à faible volatilité.",
        "profile": "safe",
        "allocation": {"SCHD": 0.30, "AGG": 0.30, "VNQ": 0.15, "GLD": 0.15, "SPY": 0.10},
        "expected_return": 0.07,
        "expected_volatility": 0.09,
    },
    "Classic 60/40": {
        "description_en": "The timeless 60% stocks / 40% bonds portfolio. Balanced risk-return profile.",
        "description_fr": "Le classique 60% actions / 40% obligations. Profil risque/rendement équilibré.",
        "profile": "balanced",
        "allocation": {"SPY": 0.30, "VXUS": 0.15, "QQQ": 0.15, "AGG": 0.25, "GLD": 0.10, "VNQ": 0.05},
        "expected_return": 0.08,
        "expected_volatility": 0.12,
    },
    "Global Growth": {
        "description_en": "Diversified across US, international and emerging markets. Long-term growth.",
        "description_fr": "Diversifié entre marchés US, internationaux et émergents. Croissance long terme.",
        "profile": "balanced",
        "allocation": {"VTI": 0.30, "EFA": 0.20, "EEM": 0.15, "AGG": 0.20, "GLD": 0.10, "VNQ": 0.05},
        "expected_return": 0.09,
        "expected_volatility": 0.14,
    },
    "Tech Leaders": {
        "description_en": "Concentrated in top technology companies driving the AI and cloud revolution.",
        "description_fr": "Concentré sur les grandes entreprises tech à la pointe de l'IA et du cloud.",
        "profile": "aggressive",
        "allocation": {"MSFT": 0.20, "GOOGL": 0.20, "NVDA": 0.20, "AAPL": 0.15, "AMZN": 0.15, "META": 0.10},
        "expected_return": 0.18,
        "expected_volatility": 0.24,
    },
    "Crypto & Innovation": {
        "description_en": "High-conviction bet on digital assets and disruptive technology. Very high risk.",
        "description_fr": "Pari fort sur les actifs numériques et la tech disruptive. Risque très élevé.",
        "profile": "aggressive",
        "allocation": {"BTC-USD": 0.30, "ETH-USD": 0.20, "NVDA": 0.20, "QQQ": 0.20, "ARKK": 0.10},
        "expected_return": 0.25,
        "expected_volatility": 0.40,
    },
    "Dividend Champion": {
        "description_en": "Quality dividend payers for passive income. Defensive sectors.",
        "description_fr": "Actions à dividendes de qualité pour revenus passifs. Secteurs défensifs.",
        "profile": "balanced",
        "allocation": {"SCHD": 0.35, "JNJ": 0.15, "JPM": 0.15, "XOM": 0.10, "VNQ": 0.15, "GLD": 0.10},
        "expected_return": 0.09,
        "expected_volatility": 0.11,
    },
    "All-Weather": {
        "description_en": "Ray Dalio-inspired portfolio resilient across all economic environments.",
        "description_fr": "Inspiré de Ray Dalio, résilient dans tous les environnements économiques.",
        "profile": "balanced",
        "allocation": {"SPY": 0.30, "TLT": 0.20, "AGG": 0.15, "GLD": 0.15, "EFA": 0.10, "VNQ": 0.10},
        "expected_return": 0.08,
        "expected_volatility": 0.10,
    },
}


# =============================================================================
# EURONEXT PARIS
# =============================================================================
#
# Written as a compact table and expanded below rather than as thirty full
# `ASSET_INFO` literals. Same data, one screen instead of six hundred lines, and
# the fields every entry shares — geography France, asset class Stock, the
# euro — cannot drift between rows because they are written once.
#
# **Every symbol here is a Yahoo symbol and none of them could be checked
# against Yahoo from the environment this was written in**, which has no route
# to any market data host. They follow Yahoo's documented convention for
# Euronext Paris (the Euronext mnemonic plus `.PA`), and the app reports by name
# any symbol that fails to download — so a wrong one is visible immediately
# rather than silently absent. `docs/EURONEXT.md` says how to check one.

_PARIS_STOCKS = {
    # ── Luxury and consumer ──────────────────────────────────────────────────
    "MC.PA": {
        "name": "LVMH", "sector": "Consumer", "risk": "Medium-High", "liquidity": 88,
        "en": "The world's largest luxury group: Louis Vuitton, Dior, Moët & Chandon, "
              "Hennessy, Sephora and Tiffany. Earnings are driven by leather goods and "
              "by Chinese demand, which is what makes the share cyclical despite the brands.",
        "fr": "Premier groupe de luxe mondial : Louis Vuitton, Dior, Moët & Chandon, "
              "Hennessy, Sephora et Tiffany. Les résultats dépendent de la maroquinerie "
              "et de la demande chinoise — c'est ce qui rend le titre cyclique malgré les marques.",
        "use_en": "Core French holding. Pricing power, but a concentrated bet on luxury demand.",
        "use_fr": "Position cœur française. Pouvoir de fixation des prix, mais pari concentré sur le luxe.",
        "yield": "~2%", "cap": "large",
    },
    "RMS.PA": {
        "name": "Hermès International", "sector": "Consumer", "risk": "Medium", "liquidity": 78,
        "en": "Ultra-luxury, and the most profitable house in the sector. Production is "
              "deliberately capped below demand, which is why its margins and its share "
              "price behave unlike the rest of luxury.",
        "fr": "Ultra-luxe, et la maison la plus rentable du secteur. La production est "
              "volontairement maintenue sous la demande — d'où des marges et un cours "
              "qui ne se comportent pas comme le reste du luxe.",
        "use_en": "Defensive luxury. Rarely cheap; the premium is the business model.",
        "use_fr": "Luxe défensif. Rarement bon marché ; la prime est le modèle économique.",
        "yield": "~0.6%", "cap": "large",
    },
    "KER.PA": {
        "name": "Kering", "sector": "Consumer", "risk": "High", "liquidity": 72,
        "en": "Gucci, Saint Laurent, Bottega Veneta, Balenciaga. Far more concentrated on "
              "Gucci than LVMH is on any one brand, which makes it the high-beta way to "
              "hold European luxury.",
        "fr": "Gucci, Saint Laurent, Bottega Veneta, Balenciaga. Bien plus concentré sur "
              "Gucci que LVMH ne l'est sur une seule marque : c'est la façon la plus "
              "volatile de détenir du luxe européen.",
        "use_en": "Satellite position. Correlates with LVMH — holding both is one bet, not two.",
        "use_fr": "Position satellite. Corrèle avec LVMH — détenir les deux est un seul pari.",
        "yield": "~4%", "cap": "large",
    },
    "OR.PA": {
        "name": "L'Oréal", "sector": "Consumer", "risk": "Medium", "liquidity": 85,
        "en": "The world's largest cosmetics group, from mass market to luxury beauty and "
              "dermatological skincare. Consumer staple behaviour with a luxury tail.",
        "fr": "Premier groupe cosmétique mondial, du grand public à la beauté de luxe et "
              "à la dermocosmétique. Comportement de bien de consommation, avec une part luxe.",
        "use_en": "Defensive consumer core. Lower drawdowns than the luxury names.",
        "use_fr": "Cœur consommation défensif. Baisses moins profondes que les valeurs du luxe.",
        "yield": "~1.7%", "cap": "large",
    },
    "RI.PA": {
        "name": "Pernod Ricard", "sector": "Consumer", "risk": "Medium", "liquidity": 70,
        "en": "Second-largest spirits group worldwide: Absolut, Jameson, Martell, Ricard. "
              "Exposed to the same Chinese and US demand cycle as luxury.",
        "fr": "Deuxième groupe mondial de spiritueux : Absolut, Jameson, Martell, Ricard. "
              "Exposé au même cycle de demande chinoise et américaine que le luxe.",
        "use_en": "Consumer staple with a discretionary cycle underneath.",
        "use_fr": "Bien de consommation courante avec un cycle discrétionnaire en dessous.",
        "yield": "~4%", "cap": "large",
    },
    "BN.PA": {
        "name": "Danone", "sector": "Consumer", "risk": "Low-Medium", "liquidity": 72,
        "en": "Dairy, plant-based, bottled water and specialised nutrition. One of the more "
              "defensive names on the index — slow growth, stable demand.",
        "fr": "Produits laitiers, végétal, eaux et nutrition spécialisée. L'une des valeurs "
              "les plus défensives de l'indice — croissance lente, demande stable.",
        "use_en": "Defensive ballast in a French equity sleeve.",
        "use_fr": "Lest défensif dans une poche actions françaises.",
        "yield": "~3%", "cap": "large",
    },
    "CA.PA": {
        "name": "Carrefour", "sector": "Consumer", "risk": "Medium", "liquidity": 62,
        "en": "European food retailer, thin margins and high volumes. Behaves as an "
              "inflation and consumer-spending proxy rather than as a growth share.",
        "fr": "Distributeur alimentaire européen, marges faibles et volumes élevés. "
              "Se comporte comme un indicateur d'inflation et de consommation, pas comme une valeur de croissance.",
        "use_en": "Value/income position. Low correlation with the luxury block.",
        "use_fr": "Position value/rendement. Faible corrélation avec le bloc luxe.",
        "yield": "~5%", "cap": "mid",
    },
    "EL.PA": {
        "name": "EssilorLuxottica", "sector": "Healthcare", "risk": "Medium", "liquidity": 75,
        "en": "Lenses and frames in one company — Varilux, Ray-Ban, Oakley — plus optical "
              "retail. Sits between healthcare and consumer, and is the dominant player in both halves.",
        "fr": "Verres et montures dans une seule entreprise — Varilux, Ray-Ban, Oakley — "
              "plus la distribution optique. Entre santé et consommation, et dominant des deux côtés.",
        "use_en": "Quality compounder. Demographics do the work.",
        "use_fr": "Valeur de qualité. La démographie fait le travail.",
        "yield": "~1.5%", "cap": "large",
    },

    # ── Industrials and defence ──────────────────────────────────────────────
    "AIR.PA": {
        "name": "Airbus", "sector": "Industrials", "risk": "Medium-High", "liquidity": 84,
        "en": "Half of the commercial aircraft duopoly, plus helicopters, defence and space. "
              "The order book runs years ahead, so the risk is delivery and supply chain, not demand.",
        "fr": "Une moitié du duopole de l'aviation commerciale, plus hélicoptères, défense et "
              "espace. Le carnet de commandes court sur des années : le risque est la livraison "
              "et la chaîne d'approvisionnement, pas la demande.",
        "use_en": "Industrial core. A long-cycle holding, not a trade.",
        "use_fr": "Cœur industriel. Position de cycle long, pas un trade.",
        "yield": "~1.5%", "cap": "large",
    },
    "SAF.PA": {
        "name": "Safran", "sector": "Industrials", "risk": "Medium-High", "liquidity": 78,
        "en": "Aircraft engines through the CFM joint venture, landing gear and interiors. "
              "Most of the profit is the aftermarket — servicing engines already flying — "
              "which makes it less cyclical than the order book suggests.",
        "fr": "Moteurs d'avions via la coentreprise CFM, trains d'atterrissage et intérieurs. "
              "L'essentiel du bénéfice vient de l'après-vente — l'entretien des moteurs déjà "
              "en vol — ce qui le rend moins cyclique que le carnet ne le laisse penser.",
        "use_en": "Aerospace with a recurring revenue base.",
        "use_fr": "Aéronautique avec une base de revenus récurrents.",
        "yield": "~1%", "cap": "large",
    },
    "HO.PA": {
        "name": "Thales", "sector": "Industrials", "risk": "Medium", "liquidity": 70,
        "en": "Defence electronics, avionics, radar, secure communications and cyber. "
              "Revenue is largely governmental, which is what decouples it from the consumer cycle.",
        "fr": "Électronique de défense, avionique, radars, communications sécurisées et cyber. "
              "Chiffre d'affaires largement étatique — c'est ce qui le découple du cycle de consommation.",
        "use_en": "Defence exposure. Moves on budgets and geopolitics, not on rates.",
        "use_fr": "Exposition défense. Bouge avec les budgets et la géopolitique, pas les taux.",
        "yield": "~2%", "cap": "large",
    },
    "SU.PA": {
        "name": "Schneider Electric", "sector": "Industrials", "risk": "Medium", "liquidity": 84,
        "en": "Electrical distribution, industrial automation and energy management. The "
              "data-centre build-out is a direct revenue driver, so it trades partly as an AI proxy.",
        "fr": "Distribution électrique, automatisation industrielle et gestion de l'énergie. "
              "La construction de centres de données est un moteur direct : le titre suit en partie l'IA.",
        "use_en": "Electrification theme, with an industrial balance sheet.",
        "use_fr": "Thème électrification, avec un bilan industriel.",
        "yield": "~1.7%", "cap": "large",
    },
    "LR.PA": {
        "name": "Legrand", "sector": "Industrials", "risk": "Medium", "liquidity": 68,
        "en": "Wiring devices, cable management and data-centre power infrastructure. "
              "Steady, acquisitive, and geared to construction rather than to consumers.",
        "fr": "Appareillage électrique, cheminements de câbles et infrastructure électrique "
              "des centres de données. Régulier, acquéreur, adossé à la construction plutôt qu'au consommateur.",
        "use_en": "Industrial compounder. Correlates with Schneider.",
        "use_fr": "Valeur industrielle régulière. Corrèle avec Schneider.",
        "yield": "~2%", "cap": "large",
    },
    "DG.PA": {
        "name": "Vinci", "sector": "Industrials", "risk": "Medium", "liquidity": 78,
        "en": "Motorway and airport concessions plus a large construction arm. The "
              "concessions are inflation-linked toll revenue, which is why it behaves "
              "more like infrastructure than like a builder.",
        "fr": "Concessions autoroutières et aéroportuaires, plus une importante activité "
              "de construction. Les concessions sont des péages indexés sur l'inflation : "
              "le titre se comporte davantage comme une infrastructure que comme un constructeur.",
        "use_en": "Infrastructure and inflation-linked cash flow.",
        "use_fr": "Infrastructure et flux de trésorerie indexés sur l'inflation.",
        "yield": "~4%", "cap": "large",
    },
    "SGO.PA": {
        "name": "Saint-Gobain", "sector": "Industrials", "risk": "Medium-High", "liquidity": 72,
        "en": "Building materials and light construction products, increasingly positioned "
              "on renovation and insulation. Cyclical with construction and with rates.",
        "fr": "Matériaux de construction et produits d'aménagement, de plus en plus positionné "
              "sur la rénovation et l'isolation. Cyclique avec la construction et les taux.",
        "use_en": "Cyclical value. Rate-sensitive.",
        "use_fr": "Value cyclique. Sensible aux taux.",
        "yield": "~3%", "cap": "large",
    },
    "ML.PA": {
        "name": "Michelin", "sector": "Industrials", "risk": "Medium", "liquidity": 70,
        "en": "Tyres, where the replacement market — not new vehicles — is the bulk of "
              "the profit. That makes it materially less cyclical than the car makers.",
        "fr": "Pneumatiques, où le marché du remplacement — et non les véhicules neufs — "
              "fait l'essentiel du bénéfice. Nettement moins cyclique que les constructeurs.",
        "use_en": "Industrial with a consumable revenue base.",
        "use_fr": "Industriel avec une base de revenus consommables.",
        "yield": "~4%", "cap": "large",
    },
    "AI.PA": {
        "name": "Air Liquide", "sector": "Materials", "risk": "Low-Medium", "liquidity": 82,
        "en": "Industrial gases — oxygen, nitrogen, hydrogen — sold on long contracts with "
              "on-site plants. Among the most predictable revenue streams on the index.",
        "fr": "Gaz industriels — oxygène, azote, hydrogène — vendus sur contrats longs avec "
              "des unités sur site. L'un des chiffres d'affaires les plus prévisibles de l'indice.",
        "use_en": "Defensive industrial. Low-beta ballast.",
        "use_fr": "Industriel défensif. Lest à faible bêta.",
        "yield": "~2%", "cap": "large",
    },

    # ── Energy and utilities ─────────────────────────────────────────────────
    "TTE.PA": {
        "name": "TotalEnergies", "sector": "Energy", "risk": "Medium-High", "liquidity": 90,
        "en": "Integrated oil and gas major, with a growing electricity and renewables arm. "
              "Cash flow tracks the oil price, and the dividend is the reason most holders hold it.",
        "fr": "Major pétrolière et gazière intégrée, avec une activité électricité et "
              "renouvelables en croissance. Les flux suivent le prix du pétrole, et le "
              "dividende est la raison pour laquelle la plupart la détiennent.",
        "use_en": "Energy and income. Hedges an inflation shock the rest of a portfolio suffers.",
        "use_fr": "Énergie et rendement. Couvre un choc inflationniste que le reste du portefeuille subit.",
        "yield": "~5%", "cap": "large",
    },
    "ENGI.PA": {
        "name": "Engie", "sector": "Utilities", "risk": "Medium", "liquidity": 72,
        "en": "Utility: regulated networks, renewables and energy services. Regulated "
              "revenue makes it defensive; leverage makes it rate-sensitive.",
        "fr": "Services aux collectivités : réseaux régulés, renouvelables et services "
              "énergétiques. Le régulé le rend défensif ; l'endettement le rend sensible aux taux.",
        "use_en": "Income and low beta, with rate risk attached.",
        "use_fr": "Rendement et faible bêta, avec un risque de taux attaché.",
        "yield": "~7%", "cap": "large",
    },
    "VIE.PA": {
        "name": "Veolia", "sector": "Utilities", "risk": "Medium", "liquidity": 68,
        "en": "Water, waste and energy services, largely under long municipal contracts. "
              "Revenue is indexed, which is a real inflation pass-through rather than a claimed one.",
        "fr": "Eau, déchets et services énergétiques, largement sous contrats municipaux "
              "longs. Le chiffre d'affaires est indexé — une vraie répercussion de l'inflation.",
        "use_en": "Defensive utility with contractual inflation linkage.",
        "use_fr": "Service public défensif avec indexation contractuelle sur l'inflation.",
        "yield": "~4%", "cap": "large",
    },

    # ── Health ───────────────────────────────────────────────────────────────
    "SAN.PA": {
        "name": "Sanofi", "sector": "Healthcare", "risk": "Medium", "liquidity": 85,
        "en": "Pharmaceutical group built around immunology and vaccines. The concentration "
              "risk is patent expiry on its lead products, not the demand for them.",
        "fr": "Groupe pharmaceutique centré sur l'immunologie et les vaccins. Le risque de "
              "concentration porte sur l'expiration des brevets de ses produits phares, pas sur la demande.",
        "use_en": "Defensive healthcare. Uncorrelated with the industrial block.",
        "use_fr": "Santé défensive. Décorrélée du bloc industriel.",
        "yield": "~4%", "cap": "large",
    },

    # ── Financials ───────────────────────────────────────────────────────────
    "BNP.PA": {
        "name": "BNP Paribas", "sector": "Financials", "risk": "Medium-High", "liquidity": 86,
        "en": "The largest French bank by assets and a eurozone universal bank. Earnings "
              "rise with rates and fall with credit losses, and it carries the sector's tail risk.",
        "fr": "Première banque française par les actifs et banque universelle de la zone euro. "
              "Les résultats montent avec les taux et baissent avec le coût du risque ; "
              "elle porte le risque extrême du secteur.",
        "use_en": "Rate-sensitive value. A hedge against the duration in a bond sleeve.",
        "use_fr": "Value sensible aux taux. Couvre la duration d'une poche obligataire.",
        "yield": "~7%", "cap": "large",
    },
    "GLE.PA": {
        "name": "Société Générale", "sector": "Financials", "risk": "High", "liquidity": 76,
        "en": "French universal bank with a large markets business. Historically the most "
              "volatile of the three listed French banks.",
        "fr": "Banque universelle française avec une forte activité de marché. "
              "Historiquement la plus volatile des trois banques françaises cotées.",
        "use_en": "High-beta financial. Correlates tightly with BNP and Crédit Agricole.",
        "use_fr": "Financière à bêta élevé. Corrèle fortement avec BNP et Crédit Agricole.",
        "yield": "~6%", "cap": "mid",
    },
    "ACA.PA": {
        "name": "Crédit Agricole S.A.", "sector": "Financials", "risk": "Medium-High", "liquidity": 74,
        "en": "The listed vehicle of the Crédit Agricole mutual group, weighted toward "
              "retail banking, insurance and asset management rather than trading.",
        "fr": "Véhicule coté du groupe mutualiste Crédit Agricole, orienté banque de détail, "
              "assurance et gestion d'actifs plutôt que marché.",
        "use_en": "Income financial, less market-sensitive than its peers.",
        "use_fr": "Financière de rendement, moins sensible aux marchés que ses pairs.",
        "yield": "~7%", "cap": "large",
    },

    # ── Technology ───────────────────────────────────────────────────────────
    "STMPA.PA": {
        "name": "STMicroelectronics", "sector": "Technology", "risk": "High", "liquidity": 76,
        "en": "Franco-Italian semiconductor maker: automotive chips, power and analogue, "
              "industrial microcontrollers. Deeply cyclical, and the cycle is inventory, not demand.",
        "fr": "Fabricant de semi-conducteurs franco-italien : puces automobiles, puissance "
              "et analogique, microcontrôleurs industriels. Très cyclique — et le cycle "
              "porte sur les stocks, pas sur la demande.",
        "use_en": "European semiconductor exposure. Expect equity-like drawdowns, doubled.",
        "use_fr": "Exposition aux semi-conducteurs européens. Attendez-vous à des baisses doubles de celles des actions.",
        "yield": "~1%", "cap": "large",
    },
    "CAP.PA": {
        "name": "Capgemini", "sector": "Technology", "risk": "Medium-High", "liquidity": 72,
        "en": "IT services and consulting. Revenue is headcount times day rate, so it tracks "
              "corporate IT budgets — an early-cycle indicator rather than a growth story.",
        "fr": "Services informatiques et conseil. Le chiffre d'affaires est un effectif "
              "multiplié par un taux journalier : il suit les budgets IT des entreprises — "
              "un indicateur de début de cycle plus qu'une histoire de croissance.",
        "use_en": "Cyclical technology services.",
        "use_fr": "Services technologiques cycliques.",
        "yield": "~2%", "cap": "large",
    },
    "DSY.PA": {
        "name": "Dassault Systèmes", "sector": "Technology", "risk": "Medium", "liquidity": 74,
        "en": "3D design and product lifecycle software — CATIA, SOLIDWORKS, Medidata. "
              "Licence and subscription revenue, so it behaves like a software company, "
              "not like the industrials it serves.",
        "fr": "Logiciels de conception 3D et de cycle de vie produit — CATIA, SOLIDWORKS, "
              "Medidata. Revenus de licences et d'abonnements : se comporte comme un "
              "éditeur, pas comme les industriels qu'il sert.",
        "use_en": "European software. Rare on this index, and priced accordingly.",
        "use_fr": "Logiciel européen. Rare sur cet indice, et valorisé en conséquence.",
        "yield": "~0.5%", "cap": "large",
    },
    "ORA.PA": {
        "name": "Orange", "sector": "Telecom", "risk": "Low-Medium", "liquidity": 72,
        "en": "Incumbent French telecom operator. Low growth, heavy capital spending, and "
              "held almost entirely for the dividend.",
        "fr": "Opérateur télécom historique français. Croissance faible, investissements "
              "lourds, détenu presque uniquement pour le dividende.",
        "use_en": "Bond proxy. Behaves like duration, and falls like it when rates rise.",
        "use_fr": "Substitut obligataire. Se comporte comme de la duration — et baisse comme elle quand les taux montent.",
        "yield": "~7%", "cap": "large",
    },

    # ── Automotive ───────────────────────────────────────────────────────────
    "STLAP.PA": {
        "name": "Stellantis", "sector": "Automotive", "risk": "High", "liquidity": 80,
        "en": "Peugeot, Citroën, Fiat, Jeep, Opel and ten more marques in one group. Listed "
              "in Paris, Milan and New York — the Paris line is this one. Deeply cyclical, "
              "and priced on a single year's margin.",
        "fr": "Peugeot, Citroën, Fiat, Jeep, Opel et dix autres marques dans un seul groupe. "
              "Coté à Paris, Milan et New York — la ligne parisienne est celle-ci. Très "
              "cyclique, et valorisé sur la marge d'une seule année.",
        "use_en": "Deep-cyclical value. Sized small, or not at all.",
        "use_fr": "Value très cyclique. À dimensionner petit, ou pas du tout.",
        "yield": "~8%", "cap": "large",
    },
    "RNO.PA": {
        "name": "Renault", "sector": "Automotive", "risk": "High", "liquidity": 70,
        "en": "French car maker, with a large stake in Nissan and an electric-vehicle arm "
              "carved out separately. More leveraged to a European volume recovery than Stellantis.",
        "fr": "Constructeur automobile français, avec une participation importante dans "
              "Nissan et une activité électrique filialisée. Plus exposé qu'un Stellantis "
              "à une reprise des volumes européens.",
        "use_en": "High-beta cyclical. Correlated with Stellantis.",
        "use_fr": "Cyclique à bêta élevé. Corrélé à Stellantis.",
        "yield": "~5%", "cap": "mid",
    },

    # ── Euronext Growth ──────────────────────────────────────────────────────
    "ALTBG.PA": {
        "name": "Capital B (ex-The Blockchain Group)", "sector": "Crypto",
        "risk": "Very High", "liquidity": 30,
        "en": "A bitcoin treasury company listed on Euronext Growth Paris, formerly The "
              "Blockchain Group. The share is a leveraged claim on bitcoin: the balance "
              "sheet holds BTC, and issuance funds more of it. Expect the drawdowns of "
              "bitcoin, amplified by the financing and by a small-cap order book — this "
              "is not a CAC 40 share and it does not trade like one.",
        "fr": "Société de trésorerie bitcoin cotée sur Euronext Growth Paris, anciennement "
              "The Blockchain Group. Le titre est une créance à effet de levier sur le "
              "bitcoin : le bilan détient du BTC, et les émissions en financent davantage. "
              "Attendez-vous aux baisses du bitcoin, amplifiées par le financement et par "
              "un carnet d'ordres de petite capitalisation — ce n'est pas une valeur du "
              "CAC 40 et elle ne se négocie pas comme telle.",
        "use_en": "Speculative satellite only. Its liquidity score is low on purpose: a "
                  "position you cannot exit in a falling market is not the size you think it is.",
        "use_fr": "Satellite spéculatif uniquement. Son score de liquidité est bas "
                  "volontairement : une position dont on ne peut pas sortir dans un marché "
                  "en baisse n'a pas la taille qu'on croit.",
        "yield": "0%", "cap": "small",
    },
}

# Broad-market trackers a French investor is likely to hold, quoted in euros on
# Euronext Paris. Same symbol caveat as the shares above.
_PARIS_ETFS = {
    "CW8.PA": {
        "name": "Amundi MSCI World UCITS ETF", "sector": "Diversified",
        "risk": "Medium", "liquidity": 88, "geography": "Global", "asset_class": "ETF",
        "en": "Developed-market world equity in one line, quoted in euros. The default "
              "core holding for a French investor, and PEA-eligible in its synthetic form.",
        "fr": "Actions mondiales des marchés développés en une ligne, cotée en euros. "
              "La position cœur par défaut pour un investisseur français, éligible au PEA "
              "dans sa version synthétique.",
        "use_en": "Portfolio core. 40–80% for most people.",
        "use_fr": "Cœur de portefeuille. 40–80% pour la plupart des profils.",
        "yield": "accumulating", "cap": "—",
    },
    "ESE.PA": {
        "name": "BNP Paribas Easy S&P 500 UCITS ETF", "sector": "Diversified",
        "risk": "Medium", "liquidity": 84, "geography": "USA", "asset_class": "ETF",
        "en": "S&P 500 exposure quoted in euros. Note what that does and does not do: the "
              "price is in euros, the underlying earnings are in dollars, so the currency "
              "risk is still there — it is unhedged, not absent.",
        "fr": "Exposition au S&P 500 cotée en euros. Attention à ce que cela fait et ne "
              "fait pas : le prix est en euros, les bénéfices sous-jacents en dollars — "
              "le risque de change est toujours là, il est non couvert, pas supprimé.",
        "use_en": "US equity sleeve without a dollar account.",
        "use_fr": "Poche actions américaines sans compte en dollars.",
        "yield": "accumulating", "cap": "—",
    },
    "PAEEM.PA": {
        "name": "Amundi MSCI Emerging Markets UCITS ETF", "sector": "Emerging Markets",
        "risk": "High", "liquidity": 76, "geography": "Emerging Markets", "asset_class": "ETF",
        "en": "Emerging-market equity in euros. Higher volatility and a different cycle "
              "from the developed world, which is the reason to hold it.",
        "fr": "Actions des marchés émergents en euros. Volatilité plus élevée et cycle "
              "différent du monde développé — c'est la raison de la détenir.",
        "use_en": "Diversifier. 5–15% alongside a world core.",
        "use_fr": "Diversification. 5–15% à côté d'un cœur monde.",
        "yield": "accumulating", "cap": "—",
    },
}

_CAP_LABEL = {
    "large": {"en": "Large cap", "fr": "Grande capitalisation"},
    "mid": {"en": "Mid cap", "fr": "Moyenne capitalisation"},
    "small": {"en": "Small cap — Euronext Growth", "fr": "Petite capitalisation — Euronext Growth"},
    "—": {"en": "—", "fr": "—"},
}

# The bucket the X-ray aggregates on, as opposed to the label a reader sees.
# Separate because the look-through needs a closed vocabulary and the card needs
# a sentence: parsing "Small cap — Euronext Growth" back into a bucket is how a
# label edit silently becomes a misclassification.
_CAP_BUCKET = {"large": "Large Cap", "mid": "Mid Cap", "small": "Small Cap", "—": None}


def _expand_paris(table: dict, *, default_geography: str, default_class: str) -> dict:
    """Blow a compact row up into the full `ASSET_INFO` shape."""
    out = {}
    for ticker, row in table.items():
        out[ticker] = {
            "name": row["name"],
            "description": row["en"],
            "description_fr": row["fr"],
            "sector": row["sector"],
            "geography": row.get("geography", default_geography),
            "asset_class": row.get("asset_class", default_class),
            "utility": row["use_en"],
            "utility_fr": row["use_fr"],
            "typical_use": row["use_en"],
            "typical_use_fr": row["use_fr"],
            "risk_level": row["risk"],
            "liquidity": row["liquidity"],
            "dividend_yield": row["yield"],
            "market_cap": _CAP_LABEL.get(row.get("cap", "—"), _CAP_LABEL["—"])["en"],
            "cap_bucket": _CAP_BUCKET.get(row.get("cap", "—")),
            # Every line here is quoted in euros. Held explicitly rather than
            # inferred from the `.PA` suffix so a relisting cannot silently
            # change what currency the app thinks a position is in.
            "currency": "EUR",
            "exchange": "Euronext Paris",
        }
    return out


EURONEXT_PARIS = {
    **_expand_paris(_PARIS_STOCKS, default_geography="France", default_class="Stock"),
    **_expand_paris(_PARIS_ETFS, default_geography="Global", default_class="ETF"),
}

ASSET_INFO.update(EURONEXT_PARIS)
SECTOR_MAPPING.update({t: info["sector"] for t, info in EURONEXT_PARIS.items()})
GEOGRAPHY_MAPPING.update({t: info["geography"] for t, info in EURONEXT_PARIS.items()})

# The quote currency of everything the app knows about, for the conversion layer.
# Only the exceptions are listed; `investment.currency.quote_currency` derives the
# rest from the exchange suffix.
QUOTE_CURRENCY = {ticker: info["currency"] for ticker, info in EURONEXT_PARIS.items()}

POPULAR_ASSETS["Paris — CAC 40"] = {
    info["name"].split(" (")[0]: ticker
    for ticker, info in EURONEXT_PARIS.items()
    if info["asset_class"] == "Stock" and ticker != "ALTBG.PA"
}
POPULAR_ASSETS["Paris — ETFs & Growth"] = {
    **{info["name"].split(" UCITS")[0]: ticker
       for ticker, info in EURONEXT_PARIS.items() if info["asset_class"] == "ETF"},
    "Capital B": "ALTBG.PA",
}


# =============================================================================
# FINDING A SYMBOL FROM WHAT SOMEBODY TYPED
# =============================================================================
#
# Nobody types `MC.PA`. They type "LVMH", or "lvmh", or "MC". The search box used
# to match the catalogue's display names only, so "capital b" found nothing and
# offered to add a ticker called `CAPITAL B` — which then failed to download with
# no explanation. These aliases are what turn a company name into the symbol
# Yahoo actually answers to.

_ALIASES: dict[str, str] = {
    # Names, including the ones people actually say
    "lvmh": "MC.PA", "louis vuitton": "MC.PA", "vuitton": "MC.PA", "moet": "MC.PA",
    "hermes": "RMS.PA", "hermès": "RMS.PA",
    "kering": "KER.PA", "gucci": "KER.PA",
    "loreal": "OR.PA", "l'oreal": "OR.PA", "l'oréal": "OR.PA", "oreal": "OR.PA",
    "pernod": "RI.PA", "pernod ricard": "RI.PA", "ricard": "RI.PA",
    "danone": "BN.PA",
    "carrefour": "CA.PA",
    "essilor": "EL.PA", "essilorluxottica": "EL.PA", "luxottica": "EL.PA",
    "airbus": "AIR.PA",
    "safran": "SAF.PA",
    "thales": "HO.PA",
    "schneider": "SU.PA", "schneider electric": "SU.PA",
    "legrand": "LR.PA",
    "vinci": "DG.PA",
    "saint gobain": "SGO.PA", "saint-gobain": "SGO.PA", "gobain": "SGO.PA",
    "michelin": "ML.PA",
    "air liquide": "AI.PA", "airliquide": "AI.PA", "liquide": "AI.PA",
    "total": "TTE.PA", "totalenergies": "TTE.PA", "total energies": "TTE.PA",
    "engie": "ENGI.PA", "gdf": "ENGI.PA",
    "veolia": "VIE.PA",
    "sanofi": "SAN.PA",
    "bnp": "BNP.PA", "bnp paribas": "BNP.PA", "paribas": "BNP.PA",
    "societe generale": "GLE.PA", "société générale": "GLE.PA", "socgen": "GLE.PA",
    "credit agricole": "ACA.PA", "crédit agricole": "ACA.PA", "casa": "ACA.PA",
    "st": "STMPA.PA", "stmicro": "STMPA.PA", "stmicroelectronics": "STMPA.PA",
    "capgemini": "CAP.PA", "cap gemini": "CAP.PA",
    "dassault": "DSY.PA", "dassault systemes": "DSY.PA", "dassault systèmes": "DSY.PA",
    "orange": "ORA.PA", "france telecom": "ORA.PA",
    "stellantis": "STLAP.PA", "peugeot": "STLAP.PA", "psa": "STLAP.PA", "citroen": "STLAP.PA",
    "renault": "RNO.PA",
    "capital b": "ALTBG.PA", "capitalb": "ALTBG.PA",
    "the blockchain group": "ALTBG.PA", "blockchain group": "ALTBG.PA",
    "msci world": "CW8.PA", "world": "CW8.PA",
    "sp500 eur": "ESE.PA", "s&p 500 eur": "ESE.PA",
    "emergents": "PAEEM.PA", "emerging": "PAEEM.PA",
}

# Bare Euronext mnemonics, so typing "MC" or "ALTBG" resolves. Kept separate
# from the name aliases because these must only match a whole word: "or" is the
# mnemonic for L'Oréal and also a French word and an English one, and matching
# it inside a phrase would be worse than not matching it at all.
_MNEMONICS = {ticker.split(".")[0].lower(): ticker for ticker in EURONEXT_PARIS}


def resolve_symbol(text: str) -> str | None:
    """
    The Yahoo symbol for what somebody typed, or None.

    Exact matches only — no fuzzy matching. A near-miss that silently resolves to
    the wrong company is worse than no match, because the portfolio would then
    contain a share the person never chose and every figure would be about it.
    """
    if not text:
        return None
    key = text.strip().lower()
    if not key:
        return None

    upper = text.strip().upper()
    if upper in EURONEXT_PARIS:
        return upper
    if key in _ALIASES:
        return _ALIASES[key]
    if key in _MNEMONICS:
        return _MNEMONICS[key]
    return None


def search_paris(text: str, limit: int = 8) -> list[tuple[str, str]]:
    """
    Euronext names containing `text`, as `(display, ticker)`.

    Substring matching is fine *here* because the result is a list the person
    picks from, not a symbol chosen on their behalf.
    """
    if not text or not text.strip():
        return []
    needle = text.strip().lower()
    hits = []
    for ticker, info in EURONEXT_PARIS.items():
        haystack = f"{info['name']} {ticker}".lower()
        if needle in haystack or needle in ticker.split(".")[0].lower():
            hits.append((f"{info['name']} ({ticker})", ticker))
        if len(hits) >= limit:
            break
    return hits
