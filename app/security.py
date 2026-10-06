from fastapi import Request
from sqlalchemy.orm import Session
from .models import User

DEFAULT_USER = "director"

def current_user(request: Request, db: Session) -> User:
    username = request.cookies.get("demo_user") or DEFAULT_USER
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = db.query(User).filter(User.username == DEFAULT_USER).first()
    return user

def visible_projects_query(db: Session, user: User):
    from .models import Action, Project
    q = db.query(Project)
    if user.role == "SALES":
        q = q.filter(Project.sales_owner == user.owner_key)
    elif user.role == "PM":
        q = q.filter(Project.pm_owner == user.owner_key)
    elif user.role == "ADMIN":
        # Administration sees only projects with at least one task explicitly
        # assigned to its operational queue. No broad portfolio access is implied.
        q = q.join(Action, Action.project_id == Project.id).filter(Action.owner == user.owner_key).distinct()
    return q
