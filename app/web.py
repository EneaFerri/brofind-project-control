"""Elementi condivisi dai router web: template, versione e regole sulle attività."""

from fastapi.templating import Jinja2Templates

from .config import settings
from .models import Action, User
from .version import VERSION

templates = Jinja2Templates(directory=settings.project_root / "templates")
templates.env.globals["version"] = VERSION

DEPARTMENTS = {"Responsabile Tecnico", "Acquisti", "Amministrazione", "Commerciale", "Direzione"}


def is_action_owner(user: User, action: Action) -> bool:
    return bool(user and user.owner_key and action.owner == user.owner_key)


def is_action_requester(user: User, action: Action) -> bool:
    return bool(user and action.requester and action.requester == user.display_name)


def can_answer_action(user: User, action: Action) -> bool:
    return user.role == "DIRECTOR" or is_action_owner(user, action)


def can_validate_action(user: User, action: Action) -> bool:
    return user.role == "DIRECTOR" or is_action_requester(user, action)
