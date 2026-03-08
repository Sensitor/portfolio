# CLAUDE.md — AI Assistant Guide for Portfolio Optimizer Pro

This file provides guidance for AI assistants (Claude, Copilot, etc.) working on this codebase.

---

## Project Overview

**Portfolio Optimizer Pro** is a Streamlit-based SaaS web application for financial portfolio analysis and optimization. It provides retail investors and financial professionals with tools to analyze portfolio risk, optimize allocations using Modern Portfolio Theory, and simulate performance under historical crisis scenarios.

**Version:** 3.5 FINAL
**Primary language:** Python 3.11
**Framework:** Streamlit

---

## Repository Structure

```
portfolio/
├── portfolio_optimizer_saas.py   # Main application (1,482 lines) — all logic lives here
├── landing_page.html             # Static marketing/landing page
├── requirements.txt              # Python dependencies
├── README.md                     # User-facing project overview
├── DEPLOYMENT_GUIDE.md           # Deployment + growth playbook
├── MARKETING_KIT.md              # Marketing copy and strategy
└── .devcontainer/
    └── devcontainer.json         # VS Code Dev Container config
```

The **entire application** is in a single file: `portfolio_optimizer_saas.py`. There is no separate `src/`, `tests/`, or multi-module layout.

---

## Technology Stack

| Layer | Library | Version |
|---|---|---|
| Web framework | `streamlit` | >=1.28.0 |
| Data manipulation | `pandas` | >=2.0.0 |
| Numerical computing | `numpy` | >=1.24.0 |
| Scientific computing / optimization | `scipy` | >=1.10.0 |
| Market data | `yfinance` | >=0.2.28 |
| Visualization | `plotly` | >=5.14.0 |
| Date utilities | `python-dateutil` | >=2.8.0 |

---

## Running the Application

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run portfolio_optimizer_saas.py
```

App is served at `http://localhost:8501`.

### Dev Container (VS Code)

Open the repo in VS Code and reopen in container. The container will:
1. Install all Python dependencies automatically
2. Start the Streamlit server on port 8501
3. Forward port 8501 and open a browser preview

Configuration: `.devcontainer/devcontainer.json`

### Deployment

- **App:** Push to GitHub → auto-deploys via Streamlit Cloud at `share.streamlit.io`
- **Landing page:** Deploy `landing_page.html` to Netlify, Vercel, or GitHub Pages

---

## Application Architecture

### Main File Layout (`portfolio_optimizer_saas.py`)

| Lines | Section | Purpose |
|---|---|---|
| 1–224 | Imports & CSS | Dependencies and global custom styles |
| 225–354 | Static data | `ASSET_INFO`, `SECTOR_MAPPING`, `GEOGRAPHY_MAPPING`, `POPULAR_ASSETS`, `MODEL_PORTFOLIOS` |
| 356–415 | Session state | `init_session_state()`, `auto_rebalance_weights()`, translations |
| 421–922 | `UltimatePortfolioAnalyzer` class | Core analysis engine |
| 927–1165 | UI components | Render functions for charts, cards, and panels |
| 1171–1480 | `main()` | App entry point, routing, sidebar, pages |

### Core Class: `UltimatePortfolioAnalyzer`

Instantiated once per analysis run. Key methods:

- **`fetch_data(tickers, period)`** — Downloads OHLCV data from Yahoo Finance via `yfinance`
- **`calculate_metrics(weights)`** — Computes annual return, volatility, Sharpe, Sortino, max drawdown, VaR, Expected Shortfall, Calmar ratio
- **`calculate_robustness_index(weights, metrics)`** — Scores the portfolio 0–100 across 7 dimensions (diversification, concentration, correlation, volatility, drawdown, geography, sector)
- **`generate_improvement_suggestions(weights, metrics)`** — Rule-based recommendations (concentration alerts, missing hedges, diversification gaps)
- **`generate_profile_adapted_suggestions(weights, metrics, profile)`** — Profile-aware advice for Safe / Balanced / Aggressive risk profiles
- **`stress_test_scenarios(weights)`** — Simulates portfolio through 2008 Financial Crisis, COVID-2020, and 2022 Inflation scenarios
- **`optimize_portfolio(weights)`** — Markowitz mean-variance optimization using `scipy.optimize.minimize` (SLSQP), maximizes Sharpe ratio; bounds: 5%–40% per asset; constraint: weights sum to 1
- **`generate_auto_summary(weights, metrics)`** — Text summary of portfolio characteristics

### UI Pages (via sidebar navigation)

| Page | Key Actions |
|---|---|
| Dashboard | View summary, robustness score, metrics, charts, run stress tests, see asset cards |
| New Analysis | Search/select assets, set weights (auto-normalized to 100%), run analysis |
| Model Portfolios | Load pre-built Safe / Balanced / Aggressive portfolios |
| Improve Portfolio | Run Markowitz optimization, compare current vs. optimized, apply changes |

---

## Key Conventions

### State Management

All user state lives in `st.session_state`. Key keys:

- `portfolio` — dict of `{ticker: weight_percent}` (weights are 0–100, not 0–1)
- `analysis_results` — cached output from the last `UltimatePortfolioAnalyzer` run
- `user_profile` — `"Safe"` | `"Balanced"` | `"Aggressive"`
- `language` — `"English"` | `"Français"`
- `current_page` — tracks active page/view

Initialize all keys through `init_session_state()`. Never set session state keys directly outside that function or the specific page logic.

### Weights Convention

- Weights stored as **percentages (0–100)**, not decimals (0–1)
- `auto_rebalance_weights()` normalizes weights so they always sum to 100% after asset add/remove
- Internal calculations in `UltimatePortfolioAnalyzer` convert to decimals: `np.array(list(weights.values())) / 100`

### Asset Tickers

Use Yahoo Finance ticker format (`AAPL`, `BTC-USD`, `SPY`, etc.). The `ASSET_INFO` dict covers 8 pre-defined assets. Arbitrary tickers are supported for user input but will lack rich metadata (description, sector, geography).

### Adding New Assets

1. Add an entry to `ASSET_INFO` (lines ~225–354) with keys: `name`, `description`, `risk`, `category`, `sector`, `geography`, `currency`
2. Add to `SECTOR_MAPPING` and `GEOGRAPHY_MAPPING`
3. Optionally add to `POPULAR_ASSETS` for quick selection

### Adding New Model Portfolios

Add an entry to `MODEL_PORTFOLIOS` dict with keys:
- `name` — display name
- `description` — short explanation
- `risk` — `"Low"` | `"Medium"` | `"High"`
- `assets` — dict of `{ticker: weight_percent}`

### Styling

Custom CSS is injected via `st.markdown(..., unsafe_allow_html=True)` at app startup. The visual theme uses:
- Purple/indigo gradient backgrounds
- Fade-in and slide-in CSS animations
- Card-based layout with hover effects

When adding new UI sections, follow the existing pattern: inject CSS classes via `st.markdown()` with `unsafe_allow_html=True`, then reference those classes in HTML strings passed to `st.markdown()`.

### Language Support

Translation strings are in a `translations` dict inside `init_session_state()`. Use `st.session_state.lang.get("key", "Default Text")` pattern when adding user-facing text.

---

## No Test Suite

There is currently no automated test suite. When making changes:
- Run the app locally with `streamlit run portfolio_optimizer_saas.py` to verify
- Manually test all four pages (Dashboard, New Analysis, Model Portfolios, Improve Portfolio)
- Verify that adding/removing assets correctly rebalances weights to 100%
- Verify that analysis runs without error for both default model portfolios and custom portfolios

---

## No Linting Configuration

No `pyproject.toml`, `.flake8`, or `mypy.ini` exists. The codebase is not strictly typed. Use PEP 8 style when contributing. Avoid adding type annotations to existing code unless refactoring is explicitly requested.

---

## Common Tasks

### Run a portfolio analysis in code
```python
analyzer = UltimatePortfolioAnalyzer()
weights = {"AAPL": 40, "SPY": 40, "GLD": 20}  # percentages
analyzer.fetch_data(list(weights.keys()), period="2y")
metrics = analyzer.calculate_metrics(weights)
score = analyzer.calculate_robustness_index(weights, metrics)
```

### Add a new page/section
1. Add a navigation button to the sidebar section in `main()` (around line 1200)
2. Add a page condition block (e.g., `if st.session_state.current_page == "new_page":`)
3. Implement the render logic; extract to a helper function if >50 lines

### Modify optimization constraints
Edit `optimize_portfolio()` in `UltimatePortfolioAnalyzer` (~line 800). Current bounds are 5%–40% per asset. Adjust the `bounds` variable and update the UI text in the Improve Portfolio page accordingly.

---

## Git Workflow

- **Primary branch for AI work:** `claude/claude-md-mmi43sn45f4r40ma-9d4JB`
- **Main branch:** `main` (production)
- **Deployment:** Streamlit Cloud auto-deploys from `main`

Always develop on the `claude/` branch and never push directly to `main`.

Push command:
```bash
git push -u origin claude/claude-md-mmi43sn45f4r40ma-9d4JB
```

---

## Known Limitations / Future Work

- No real Stripe payment integration — pricing tiers are UI-only (feature gating not enforced)
- No user authentication — all users share the same session on a single Streamlit instance
- No persistent storage — portfolios reset on page refresh
- `yfinance` data fetching has occasional rate-limit failures; no retry logic implemented
- No automated tests
- Translations are incomplete (only partial French support)
