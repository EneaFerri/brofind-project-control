"""Elementi condivisi dai router web: template, filtri di formattazione e regole sulle attività."""

from datetime import date, datetime

from fastapi.templating import Jinja2Templates

from .config import settings
from .models import Action, User
from .version import VERSION

templates = Jinja2Templates(directory=settings.project_root / "templates")
templates.env.globals["version"] = VERSION
templates.env.globals["runtime"] = settings.runtime

DEPARTMENTS = {"Responsabile Tecnico", "Acquisti", "Amministrazione", "Commerciale", "Direzione"}


def _thousands(value: float, decimals: int = 0) -> str:
    text = f"{abs(value):,.{decimals}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return ("-" if value < 0 else "") + text


def eur(value, decimals: int = 0, signed: bool = False, nd: str = "N/D") -> str:
    """1234567.8 → '1.234.568 €' (formato italiano)."""
    if value is None:
        return nd
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{_thousands(float(value), decimals)} €"


def keur(value, nd: str = "N/D") -> str:
    if value is None:
        return nd
    return f"{_thousands(float(value) / 1000, 0)} k€"


def pct(value, decimals: int = 0, signed: bool = False, nd: str = "N/D") -> str:
    if value is None:
        return nd
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{_thousands(float(value), decimals)}%"


def dmy(value, nd: str = "–") -> str:
    if value is None or value == "":
        return nd
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    try:
        return date.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except ValueError:
        return str(value)


def num(value, decimals: int = 0, nd: str = "N/D") -> str:
    if value is None:
        return nd
    return _thousands(float(value), decimals)


templates.env.filters.update(eur=eur, keur=keur, pct=pct, dmy=dmy, num=num)


def is_action_owner(user: User, action: Action) -> bool:
    return bool(user and user.owner_key and action.owner == user.owner_key)


def is_action_requester(user: User, action: Action) -> bool:
    return bool(user and action.requester and action.requester == user.display_name)


def can_answer_action(user: User, action: Action) -> bool:
    return user.role == "DIRECTOR" or is_action_owner(user, action)


def can_validate_action(user: User, action: Action) -> bool:
    return user.role == "DIRECTOR" or is_action_requester(user, action)
