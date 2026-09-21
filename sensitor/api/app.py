"""
The FastAPI application.

    uvicorn sensitor.api.app:app --reload

Or, from Python:

    from sensitor.api.app import create_app
    app = create_app()

What this process does *not* contain is the point of it. There is no metric
here, no P&L arithmetic, no definition of a profit factor. Every number it
serves comes from `sensitor.trading` and `sensitor.investment` — the same
modules the Streamlit pages call, reached through the same `Store` and the same
`Auth`. A phone and the desktop app therefore cannot disagree about a trader's
expectancy, because there is one implementation of it and both of them read it.

`tests/test_api.py` asserts that: it parses the router modules for arithmetic
and for imports of numpy, pandas and scipy, and fails if a calculation appears.
"""

from __future__ import annotations

import os

from fastapi import FastAPI

from .. import __product__, __version__
from ..core.auth import auth_mode
from ..database.models import SCHEMA_VERSION
from .deps import single_user_key_configured
from .routers import auth as auth_router
from .routers import portfolios as portfolios_router
from .routers import trading as trading_router
from .schemas import MetaResponse

DESCRIPTION = """
The HTTP surface over Sensitor's analysis engine.

**Authentication.** Every endpoint that touches your data requires
`Authorization: Bearer <token>`, obtained from `POST /auth/sign-in`. The token
is the same session the desktop app issues: one credential store, one
verification path.

**Whose data.** The caller is read from the token and nowhere else. No endpoint
takes a user as a parameter, so none can be asked for somebody else's data.

**Undefined is not zero.** A profit factor with no losing trades, an R multiple
on a trade that had no stop, a percentage drawdown from a peak at zero — each
comes back `null`. Rendering those as `0` produces a confident wrong number.
Sample sizes travel with every grouped figure for the same reason.
"""


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{__product__} API",
        version=__version__,
        description=DESCRIPTION,
        openapi_tags=[
            {"name": "auth", "description": "Sessions and identity."},
            {"name": "trading", "description": "The journal and its analytics."},
            {"name": "portfolios", "description": "Saved allocations and their history."},
            {"name": "meta", "description": "What this deployment is."},
        ],
    )

    _add_cors(app)

    app.include_router(auth_router.router)
    app.include_router(trading_router.router)
    app.include_router(portfolios_router.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        """Liveness. Deliberately requires no authentication and reads nothing."""
        return {"status": "ok"}

    @app.get("/meta", response_model=MetaResponse, tags=["meta"])
    def meta() -> MetaResponse:
        """
        What this deployment is and how it protects data.

        `auth_mode` and `issues_sessions` are exposed so a client can tell the
        person which it is talking to. A deployment running single-user with no
        API key issues no sessions at all, and a client that cannot see that has
        no way to explain why sign-in fails.
        """
        return MetaResponse(
            product=__product__,
            version=__version__,
            schema_version=SCHEMA_VERSION,
            auth_mode=auth_mode(),
            issues_sessions=auth_mode() == "multi" or single_user_key_configured(),
        )

    return app


def _add_cors(app: FastAPI) -> None:
    """
    Cross-origin access, off unless configured.

    `SENSITOR_CORS_ORIGINS` is a comma-separated list. It is not defaulted to
    `*`: credentials travel on these requests, and a wildcard that arrived by
    default rather than by decision is how a browser on any site ends up able to
    call this API with a user's token. A native mobile client sends no `Origin`
    and needs none of this.
    """
    raw = (os.getenv("SENSITOR_CORS_ORIGINS") or "").strip()
    if not raw:
        return
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if not origins:
        return

    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )


app = create_app()
