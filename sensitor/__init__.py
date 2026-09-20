"""
Sensitor — personal financial intelligence platform.

Two domains over one shared foundation:

    core/          configuration, errors, shared helpers, translations
    investment/    long-term portfolio analytics  (pure computation)
    trading/       active trading analytics       (pure computation, Phase 3)
    integrations/  market data and broker connectors
    database/      schema, connection, repositories
    ai/            copilot — observations and simulatable suggestions
    api/           HTTP surface (Phase 8)
    ui/            design tokens, components, chart factories
    pages/         Streamlit page renderers

The rule the layout enforces: business logic never imports Streamlit. `investment`,
`trading`, `database`, `ai` and `core` are importable from a script, a test or an
API process with no Streamlit runtime present. Only `ui` and `pages` touch it.

Subpackages are not imported here on purpose — `import sensitor` must stay cheap
and must not drag Streamlit in through `ui`. Import what you need:

    from sensitor.investment import analytics
    from sensitor.database import Store
"""

__version__ = "5.1.0"
__product__ = "Sensitor Portfolio Intelligence"
