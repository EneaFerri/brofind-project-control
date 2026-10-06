from datetime import date, timedelta
from app.models import Project, BudgetLine, Invoice, Milestone, ChangeRequest
from app.rules import candidates_for_project, budget_summary
from app.analytics import project_exposure, closing_summary


def test_budget_forecast():
    p=Project(code="T",customer="X",sales_owner="S",pm_owner="P",order_value=100)
    p.budget_lines=[BudgetLine(category="x",budget=100,actual=60,committed=30,etc=20)]
    s=budget_summary(p)
    assert s["forecast"]==110
    assert round(s["variance_pct"],1)==10.0


def test_unbilled_milestone():
    today=date.today(); p=Project(code="T",customer="X",sales_owner="S",pm_owner="P",order_value=100)
    p.milestones=[Milestone(name="Delivery",actual_date=today-timedelta(days=10),invoice_required=True,invoice_value=20)]
    c=candidates_for_project(p,today)
    assert any(x.alert_type=="UNBILLED_MILESTONE" for x in c)
    assert project_exposure(p,today)['unbilled']==20


def test_overdue_invoice_and_closing_blocker():
    today=date.today(); p=Project(code="T",customer="X",sales_owner="S",pm_owner="P",order_value=100,technical_status="CLOSED")
    p.invoices=[Invoice(number="I1",issue_date=today-timedelta(days=60),due_date=today-timedelta(days=30),amount=20,paid_amount=0)]
    c=candidates_for_project(p,today)
    assert any(x.alert_type=="OVERDUE_INVOICE" and "chiusa" in x.title.lower() for x in c)
    closing=closing_summary(p,today)
    assert closing['closeable'] is False
    assert any('incassi' in x for x in closing['blockers'])


def test_uncovered_change_exposure_uses_quoted_value():
    today=date.today(); p=Project(code="T",customer="X",sales_owner="S",pm_owner="P",order_value=100)
    p.changes=[ChangeRequest(description='Extra',requested_date=today-timedelta(days=5),estimated_cost=10,quoted_value=18,order_received=False,work_started=True)]
    assert project_exposure(p,today)['uncovered_changes']==18
