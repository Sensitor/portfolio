"""
Who may do what, in one place.

Every access decision of the platform, the analyzer and the API is a question
asked here: `can(member, capability)` for a yes or no, `limit(member, name)`
for a quantity. The pages no longer compare level strings themselves; a search
for a level name outside this module and the database migrations finds nothing,
and `tests/test_permissions.py` checks it.

Levels and roles
----------------
A member has one **level**, worked out from their active entitlements (the
`entitlements` table: a manual grant by an administrator today, a verified
payment later), and any number of **roles**, which are orthogonal to the level:

* `visitor`  no account;
* `free`     an account;
* `premium`  an account with an active entitlement;
* role `coach`  answers trade reviews, writes the trading room's sessions;
* role `admin`  manages members and their access. An administrator does not
  open premium content by being one: the role manages access, it is not access.

**Accompagné** is not a level of its own: it is premium plus membership of an
open cohort (`Member.cohorts`), given by an administrator. It opens the
cohort's workshops and the accompaniment requests.

The values written by earlier versions (`pro`, `premium` in `users.tier`, the
`PRO_EMAILS` variable) are read here, by `level_of`, and nowhere else.

No Streamlit, no database: the store hands this module plain values.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VISITOR, FREE, PREMIUM = "visitor", "free", "premium"
LEVELS = (VISITOR, FREE, PREMIUM)                       # in order: each includes the one before
LEVEL_LABELS = {VISITOR: "Visiteur", FREE: "Gratuit", PREMIUM: "Premium"}

COACH, ADMIN = "coach", "admin"
ROLES = (COACH, ADMIN)
ROLE_LABELS = {COACH: "Coach", ADMIN: "Administrateur"}

# Values an earlier version wrote for an account with extended access.
_LEGACY_PREMIUM = frozenset({"pro", "premium"})

# Content access levels, as declared on a lesson, a resource or a session.
CONTENT_LEVELS = {"public": VISITOR, "member": FREE, "premium": PREMIUM}


@dataclass(frozen=True)
class Rule:
    level: str | None = None        # the least level that has it
    role: str | None = None         # or the role that has it
    label: str = ""
    accompanied: bool = False       # and, on top of the level, membership of an open cohort


# The capabilities. A new protected feature adds a line here and asks `can()`.
CAPABILITIES: dict[str, Rule] = {
    "content.read.public": Rule(level=VISITOR, label="Lire le contenu en accès libre"),
    "content.read.member": Rule(level=FREE, label="Lire le contenu réservé aux membres"),
    "content.read.premium": Rule(level=PREMIUM, label="Lire le contenu Premium"),
    "progress.save": Rule(level=FREE, label="Enregistrer sa progression et ses journaux"),
    "review.request": Rule(level=FREE, label="Demander la revue d'un trade"),
    "portfolio.optimize": Rule(level=PREMIUM, label="Optimiser un portefeuille"),
    "portfolio.stress_test": Rule(level=PREMIUM, label="Lancer les stress tests"),
    "portfolio.models": Rule(level=PREMIUM, label="Charger une allocation type dans l'analyseur"),
    "cohort.read": Rule(level=PREMIUM, accompanied=True, label="Suivre les ateliers de sa cohorte"),
    "support.request": Rule(level=PREMIUM, accompanied=True, label="Demander un accompagnement"),
    "review.answer": Rule(role=COACH, label="Répondre aux revues de trades"),
    "support.answer": Rule(role=COACH, label="Répondre aux demandes d'accompagnement"),
    "cohort.manage": Rule(role=ADMIN, label="Gérer les cohortes et les ateliers"),
    "admin.stats": Rule(role=ADMIN, label="Consulter les statistiques"),
    "market.publish": Rule(role=COACH, label="Rédiger et publier les séances"),
    "admin.members": Rule(role=ADMIN, label="Consulter les membres"),
    "admin.access": Rule(role=ADMIN, label="Attribuer et retirer les accès"),
}

# Quantities, per level.
LIMITS: dict[str, dict[str, int]] = {
    "portfolio.max_assets": {VISITOR: 5, FREE: 5, PREMIUM: 50},
    "review.monthly_quota": {VISITOR: 0, FREE: 1, PREMIUM: 8},
    # Asked only once `support.request` is granted, i.e. for an accompanied member.
    "support.monthly_quota": {VISITOR: 0, FREE: 0, PREMIUM: 4},
}


@dataclass(frozen=True)
class Member:
    email: str | None = None
    level: str = VISITOR
    roles: frozenset = field(default_factory=frozenset)
    cohorts: frozenset = field(default_factory=frozenset)   # ids of the open cohorts they belong to

    @property
    def signed_in(self) -> bool:
        return bool(self.email)

    @property
    def accompanied(self) -> bool:
        return self.signed_in and self.level == PREMIUM and bool(self.cohorts)


def status_label(who: Member) -> str:
    """« Accompagné » for a premium member in an open cohort, else the level's label."""
    return "Accompagné" if who.accompanied else LEVEL_LABELS.get(who.level, who.level)


VISITOR_MEMBER = Member()


def level_of(value: str | None, *, signed_in: bool = True) -> str:
    """
    A level from any value the code has ever stored or passed for one: the
    levels themselves, and the legacy `pro` and `premium` of `users.tier`.
    Anything unknown is the lowest level the person can have.
    """
    text = (value or "").strip().lower()
    if not signed_in:
        return VISITOR
    if text in _LEGACY_PREMIUM:
        return PREMIUM
    if text == VISITOR:
        return VISITOR
    return FREE


def is_premium(value: str | None) -> bool:
    return level_of(value) == PREMIUM


def member(email: str | None, level: str | None = None, roles=()) -> Member:
    """A member from what the caller holds: an address (or none), a level or legacy tier, roles."""
    email = (email or "").strip().lower() or None
    if not email:
        return VISITOR_MEMBER
    return Member(email, level_of(level), frozenset(r for r in roles if r in ROLES))


def for_level(level: str | None) -> Member:
    """
    A member known only by level, for screens that hold the level in session and
    not the address (the analyzer's pages). No roles.
    """
    lvl = level_of(level)
    return Member("member@session" if lvl != VISITOR else None, lvl)


def _rank(level: str) -> int:
    return LEVELS.index(level) if level in LEVELS else 0


def can(who: Member, capability: str) -> bool:
    rule = CAPABILITIES.get(capability)
    if rule is None:
        raise KeyError(f"unknown capability: {capability}")
    if rule.role is not None:
        return who.signed_in and rule.role in who.roles
    if rule.level == VISITOR:
        return True
    if rule.accompanied and not who.accompanied:
        return False
    return who.signed_in and _rank(who.level) >= _rank(rule.level)


def limit(who: Member, name: str) -> int:
    table = LIMITS[name]
    return table.get(who.level if who.signed_in else VISITOR, table[VISITOR])


def content_capability(access: str) -> str:
    """The capability that reads content declared at `access` (public, member, premium)."""
    level = CONTENT_LEVELS.get(access)
    if level is None:
        raise KeyError(f"unknown content access: {access}")
    return f"content.read.{access}"


def can_read(who: Member, access: str) -> bool:
    """Whether content declared at `access` is readable; an unknown access is closed."""
    try:
        return can(who, content_capability(access))
    except KeyError:
        return False


def lock_reason(who: Member, access: str) -> str | None:
    """None when readable; « sign-in » when an account would open it; « premium » otherwise."""
    if can_read(who, access):
        return None
    return "premium" if who.signed_in and access == "premium" else "sign-in"


def level_from(entitlements, now: str) -> str:
    """
    The level that active entitlements give. An entitlement is a mapping with
    `level`, `starts_at`, `ends_at` (or None) and `revoked_at` (or None), times
    in the store's ISO text, which compares in order.
    """
    best = FREE
    for item in entitlements or ():
        if item.get("revoked_at"):
            continue
        if (item.get("starts_at") or "") > now:
            continue
        ends = item.get("ends_at")
        if ends and ends <= now:
            continue
        if _rank(level_of(item.get("level"))) > _rank(best):
            best = level_of(item.get("level"))
    return best


def entitlement_level(value: str) -> str:
    """The level an entitlement is written with: only premium is granted."""
    if level_of(value) != PREMIUM:
        raise ValueError("only the premium level is granted by an entitlement")
    return PREMIUM
