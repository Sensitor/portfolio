"""
The working portfolio, kept across restarts.

The trading journal never lost anything: a trade is a row in SQLite the moment
it exists. The investment side did not work that way. The allocation being
edited — the tickers, the weights, the mode — lived in `st.session_state`,
which is memory belonging to one browser session in one Python process. Closing
the tab, redeploying, or rebooting the machine threw it away. Saving existed,
but it was a button you had to remember to press, and the portfolio you forgot
to save was simply gone.

This module gives the investment half the journal's property. Two functions:

* `restore()` reads the row back once per session, when somebody signs in.
* `persist()` writes it whenever it has actually changed.

**Why persist by signature rather than on every edit.** Streamlit reruns the
whole script on every keystroke and every slider drag. Writing on each rerun
would mean thousands of pointless transactions; writing only where an edit
happens would mean finding all eleven places that mutate the allocation and
never missing a twelfth. Comparing a signature of the current state against the
last one written costs one dictionary comparison per rerun and cannot be
out-of-date, because it is derived from the state rather than maintained
alongside it.

**Why the analyzer is not restored.** It holds a price history — megabytes of
it, already stale by the next session. Only the allocation is written down;
prices are re-fetched, which is also what guarantees the restored portfolio is
priced at today's market rather than at whatever the market did before the
reboot.
"""

from __future__ import annotations

import streamlit as st

# The session-state keys that make up "the portfolio I am working on". Listed
# once, here, so restore and persist cannot disagree about what that means.
RESTORED_FLAG = "_workspace_restored_for"
SIGNATURE_KEY = "_workspace_signature"
RESUME_FLAG = "_workspace_resume_pending"


def signature() -> dict:
    """
    What the workspace currently is, as plain data.

    Weights are rounded to six places before comparison. A slider drag produces
    floating-point noise far below anything a person can see or a metric can
    reflect, and without the rounding the signature would differ on reruns where
    nothing meaningful changed.
    """
    weights = st.session_state.get("weights") or {}
    quantities = st.session_state.get("real_portfolio_holdings") or {}
    return {
        "holdings": {str(k): round(float(v), 6) for k, v in weights.items()},
        "mode": st.session_state.get("analysis_mode", "simulation"),
        "base_currency": st.session_state.get("base_currency", "USD"),
        "profile": st.session_state.get("user_profile", "balanced"),
        "period": st.session_state.get("sensitor_period", "MAX"),
        "quantities": {str(k): round(float(v), 6) for k, v in quantities.items()},
        "total_value": st.session_state.get("real_portfolio_total_value"),
        "portfolio_id": (st.session_state.get("sensitor_loaded_portfolio") or {}).get("id"),
        "portfolio_name": (st.session_state.get("sensitor_loaded_portfolio") or {}).get("name"),
    }


def restore(store, email: str) -> bool:
    """
    Put the last working portfolio back into session state.

    Runs once per signed-in address. Keyed by the address rather than by a
    boolean so that signing out and back in as somebody else restores *their*
    workspace instead of leaving the previous person's allocation on screen —
    the same isolation the store enforces, carried into the session.

    Returns True when something was actually restored, so the caller can decide
    whether to offer to re-run the analysis.
    """
    if store is None or not email:
        return False
    if st.session_state.get(RESTORED_FLAG) == email:
        return False

    st.session_state[RESTORED_FLAG] = email

    try:
        saved = store.load_workspace(email)
    except Exception:                                    # noqa: BLE001
        # A workspace that cannot be read is not worth failing the app over.
        # The person gets an empty one, which is what they had before this
        # feature existed.
        return False

    if saved is None or saved.is_empty:
        return False

    st.session_state.selected_tickers = list(saved.holdings)
    st.session_state.weights = dict(saved.holdings)
    st.session_state.analysis_mode = saved.mode or "simulation"
    st.session_state.base_currency = (saved.base_currency or "USD").upper()
    st.session_state.user_profile = saved.profile or "balanced"
    if saved.period:
        st.session_state.sensitor_period = saved.period
    if saved.quantities:
        st.session_state.real_portfolio_holdings = dict(saved.quantities)
    if saved.total_value is not None:
        st.session_state.real_portfolio_total_value = saved.total_value
    if saved.portfolio_id is not None:
        st.session_state["sensitor_loaded_portfolio"] = {
            "id": saved.portfolio_id,
            "name": saved.portfolio_name,
            "holdings": dict(saved.holdings),
            "currency": saved.base_currency,
            "mode": saved.mode,
        }

    # Sliders read their own widget keys, so the restored weights have to be
    # written there too or the page shows the allocation and the sliders
    # disagree about it.
    for ticker, weight in saved.holdings.items():
        st.session_state[f"ws_{ticker}"] = round(float(weight) * 100, 1)

    # The prices are not restored — only the allocation is. This tells the app
    # to fetch them, once.
    st.session_state[RESUME_FLAG] = True
    st.session_state[SIGNATURE_KEY] = signature()
    return True


def persist(store, email: str) -> None:
    """
    Write the workspace down if it has changed since the last write.

    Called from a `finally` around the whole script run, so it happens whichever
    branch rendered and whether or not the run ended in a rerun. It never raises
    into the app: a failed write should cost the last edit, not the session.
    """
    if store is None or not email:
        return
    # Restoring has to have happened first. Without this guard, the first run
    # after a restart would compare an empty session against a full row and
    # write the empty one over it — persistence that deletes what it was built
    # to keep.
    if st.session_state.get(RESTORED_FLAG) != email:
        return

    current = signature()
    if current == st.session_state.get(SIGNATURE_KEY):
        return

    try:
        store.save_workspace(
            email,
            current["holdings"],
            mode=current["mode"],
            base_currency=current["base_currency"],
            profile=current["profile"],
            period=current["period"],
            quantities=current["quantities"],
            total_value=current["total_value"],
            portfolio_id=current["portfolio_id"],
            portfolio_name=current["portfolio_name"],
        )
    except Exception:                                    # noqa: BLE001
        return
    st.session_state[SIGNATURE_KEY] = current


def forget() -> None:
    """
    Drop the workspace from this session, on sign-out.

    The row stays in the database — it belongs to the person who signed out, and
    they get it back next time. What is cleared is the copy in memory, so the
    next person to use this browser does not inherit an allocation that is not
    theirs.
    """
    for ticker in list(st.session_state.get("weights") or {}):
        st.session_state.pop(f"ws_{ticker}", None)
    st.session_state.selected_tickers = []
    st.session_state.weights = {}
    st.session_state.current_portfolio = None
    st.session_state.real_portfolio_holdings = {}
    st.session_state.real_portfolio_total_value = None
    st.session_state.pop("sensitor_loaded_portfolio", None)
    st.session_state.pop(RESTORED_FLAG, None)
    st.session_state.pop(SIGNATURE_KEY, None)
    st.session_state.pop(RESUME_FLAG, None)


def take_resume_flag() -> bool:
    """True once, on the run after a restore, so the analysis is re-run exactly once."""
    if st.session_state.pop(RESUME_FLAG, False):
        return True
    return False
