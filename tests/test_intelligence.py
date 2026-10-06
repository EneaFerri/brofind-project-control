from datetime import date

from fastapi.testclient import TestClient

from app.intelligence import analyze_communication, extract_amount, extract_date
from app.main import app
from app.models import Communication, Project


def _project():
    return Project(code="T-AI", customer="Demo", sales_owner="S. Riva", pm_owner="A. Greco", order_value=100000)


def test_schedule_extraction_from_free_text():
    p = _project()
    c = Communication(
        id=999, project_id=1, date=date(2026, 9, 21), direction="INBOUND",
        sender="client@example.com", recipient="pm@example.com", subject="FAT schedule",
        body="Unfortunately the FAT cannot take place on 30 September 2026. We expect two weeks delay.",
        responded=False,
    )
    findings = analyze_communication(p, c)
    schedule = next(x for x in findings if x.finding_type == "AGENT_SCHEDULE_RISK")
    assert schedule.extracted_date == date(2026, 10, 14)
    assert schedule.confidence >= 0.9


def test_payment_amount_and_date_extractors():
    text = "We confirm that payment of EUR 120,000 will be released by 25 September 2026."
    assert extract_amount(text) == 120000
    assert extract_date(text, date(2026, 9, 21)) == date(2026, 9, 25)


def test_validation_does_not_create_alert_before_application():
    with TestClient(app) as client:
        detail = client.get('/api/projects/P-26006').json()
        finding = next(f for f in detail['findings'] if f['type'] == 'AGENT_SCHEDULE_RISK')
        before_types = {a['type'] for a in detail['alerts']}
        assert 'AGENT_SCHEDULE_RISK' not in before_types

        reviewed = client.post(f"/api/findings/{finding['id']}/status", data={'status': 'VALIDATED'})
        assert reviewed.status_code == 200
        assert 'registrare' in reviewed.json()['message']

        detail2 = client.get('/api/projects/P-26006').json()
        validated = next(f for f in detail2['findings'] if f['id'] == finding['id'])
        assert validated['status'] == 'VALIDATED'
        assert validated['application'] is not None
        assert not any(a['type'] == 'AGENT_SCHEDULE_RISK' for a in detail2['alerts'])


def test_live_mail_returns_clear_result_and_creates_finding():
    with TestClient(app) as client:
        response = client.post('/api/projects/P-26001/communications/analyze', data={
            'direction': 'INBOUND',
            'sender': 'client@example.com',
            'subject': 'Additional scope',
            'body': 'Please include an additional duct modification for EUR 18,000 before installation.',
        })
        assert response.status_code == 200
        assert response.json()['ok'] is True
        assert 'Mail aggiunta e analizzata' in response.json()['message']
        detail = client.get('/api/projects/P-26001').json()
        assert any(f['type'] == 'AGENT_CHANGE_REQUEST' for f in detail['findings'])


def test_validated_schedule_finding_creates_verification_without_mutating_forecast():
    with TestClient(app) as client:
        # Add an explicit Delivery date to a project that has a Delivery milestone.
        mail = client.post('/api/projects/P-26001/communications/analyze', data={
            'direction': 'INBOUND',
            'sender': 'client@example.com',
            'subject': 'Delivery schedule update',
            'body': 'Delivery is postponed. The revised delivery date is 30 November 2026.',
        })
        assert mail.status_code == 200
        detail = client.get('/api/projects/P-26001').json()
        finding = next(f for f in detail['findings'] if f['type'] == 'AGENT_SCHEDULE_RISK' and f['status'] == 'NEW')

        assert client.post(f"/api/findings/{finding['id']}/status", data={'status': 'VALIDATED'}).status_code == 200
        applied = client.post(f"/api/findings/{finding['id']}/apply")
        assert applied.status_code == 200
        assert applied.json()['kind'] == 'CREATE_ACTION'

        detail2 = client.get('/api/projects/P-26001').json()
        f2 = next(f for f in detail2['findings'] if f['id'] == finding['id'])
        assert f2['status'] == 'APPLIED'
        assert 'Nessun dato sorgente' in f2['applied_summary']
        delivery = next(m for m in detail2['milestones'] if 'Delivery' in m['name'])
        assert delivery['forecast_date'] != '2026-11-30'
        assert any(a['source'].startswith('FINDING:') for a in detail2['actions'])
