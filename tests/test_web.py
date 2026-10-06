from fastapi.testclient import TestClient

from app.main import app
from app.version import VERSION

CANONICAL_NAV = [
    "Overview",
    "Master",
    "Technical",
    "Procurement",
    "Documents",
    "Economics",
    "Billing &amp; Payment",
    "Criticità",
    "Attività",
    "Conversazioni",
    "Storico",
]
SURFACES = [
    "",
    "/master",
    "/technical",
    "/procurement",
    "/documents",
    "/economics",
    "/billing",
    "/criticita",
    "/attivita",
    "/conversazioni",
    "/storico",
]


def test_portfolio_renders_v1_structure():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        html = response.text
        assert "Project Portfolio" in html
        assert "Principale esposizione" in html
        for domain in ("Master", "Technical", "Procurement", "Documents", "Economics", "Billing", "Payment"):
            assert f'data-sort="{domain.lower()}"' in html
        assert "Esporta elenco" in html
        # La sidebar è solo globale: nessuna voce di dominio di commessa.
        sidebar = html[html.index('<aside class="sidebar">') : html.index("</aside>")]
        assert "Economics" not in sidebar and "Control" not in sidebar


def test_overview_follows_canonical_monitoring_first_structure():
    with TestClient(app) as client:
        response = client.get("/project/P-26002")
        assert response.status_code == 200
        html = response.text
        order = [html.index(x) for x in ("Stato domini", "Principale esposizione", "Altre attenzioni", "Prossimo gate")]
        assert order == sorted(order)
        nav = html[html.index('class="project-nav"') : html.index("</nav>", html.index('class="project-nav"'))]
        positions = [nav.index(f">{label}") for label in CANONICAL_NAV]
        assert positions == sorted(positions)


def test_every_surface_renders_for_every_seeded_project_with_identical_navigation():
    with TestClient(app) as client:
        codes = [p["code"] for p in client.get("/api/projects").json()]
        assert codes
        for code in codes:
            for suffix in SURFACES:
                response = client.get(f"/project/{code}{suffix}")
                assert response.status_code == 200, (code, suffix)
                assert 'class="project-nav"' in response.text
        assert client.get("/project/P-26002/control").status_code == 404


def test_sales_visibility_api():
    with TestClient(app) as client:
        login = client.post("/login", data={"username": "sales_riva"}, follow_redirects=False)
        assert login.status_code == 303
        response = client.get("/api/projects")
        assert response.status_code == 200
        projects = response.json()
        assert projects
        assert all(p["sales_owner"] == "S. Riva" for p in projects)


def test_pm_visibility_api():
    with TestClient(app) as client:
        client.post("/login", data={"username": "pm_sala"}, follow_redirects=False)
        response = client.get("/api/projects")
        assert response.status_code == 200
        projects = response.json()
        assert projects
        assert all(p["pm_owner"] == "P. Sala" for p in projects)


def test_create_and_complete_action_does_not_close_rule_alert():
    with TestClient(app) as client:
        detail = client.get("/api/projects/P-26006").json()
        alert = next(a for a in detail["alerts"] if a["type"] == "LD_EXPOSURE")
        response = client.post(f"/api/alerts/{alert['id']}/create-action")
        assert response.status_code == 200
        assert "alert resta aperto" in response.json()["message"].lower()
        action_id = response.json()["action_id"]

        done = client.post(f"/api/actions/{action_id}/status", data={"status": "CLOSED"})
        assert done.status_code == 200
        assert "restano attivi" in done.json()["message"]

        detail2 = client.get("/api/projects/P-26006").json()
        assert any(a["id"] == alert["id"] for a in detail2["alerts"])


def test_rule_alert_cannot_be_manually_closed():
    with TestClient(app) as client:
        detail = client.get("/api/projects/P-26006").json()
        alert_id = detail["alerts"][0]["id"]
        response = client.post(f"/api/alerts/{alert_id}/status", data={"status": "RESOLVED"})
        assert response.status_code == 409
        assert "dato sorgente" in response.json()["detail"]


def test_health_version():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["version"] == VERSION


def test_action_can_be_reassigned_and_have_messages():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        detail = client.get("/api/projects/P-26006").json()
        alert = next(a for a in detail["alerts"] if a["type"] == "LD_EXPOSURE")
        created = client.post(f"/api/alerts/{alert['id']}/create-action").json()
        action_id = created["action_id"]

        assigned = client.post(f"/api/actions/{action_id}/assign", data={"owner": "P. Sala"})
        assert assigned.status_code == 200
        assert "P. Sala" in assigned.json()["message"]

        suggestion = client.get(f"/api/actions/{action_id}/suggest-message")
        assert suggestion.status_code == 200
        assert "P. Sala" in suggestion.json()["text"]

        msg = client.post(
            f"/api/actions/{action_id}/messages", data={"body": "Puoi verificare il recovery plan entro domani?"}
        )
        assert msg.status_code == 200
        detail2 = client.get("/api/projects/P-26006").json()
        action = next(a for a in detail2["actions"] if a["id"] == action_id)
        assert action["owner"] == "P. Sala"
        assert action["messages"][-1]["body"].startswith("Puoi verificare")


def test_p26004_communication_findings_become_visible_only_after_apply():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        detail = client.get("/api/projects/P-26004").json()
        escalation = next(f for f in detail["findings"] if f["type"] == "AGENT_CUSTOMER_ESCALATION")
        assert not any(a["type"] == "COMMUNICATION_ISSUE" for a in detail["alerts"])

        client.post(f"/api/findings/{escalation['id']}/status", data={"status": "VALIDATED"})
        applied = client.post(f"/api/findings/{escalation['id']}/apply")
        assert applied.status_code == 200
        after_escalation = client.get("/api/projects/P-26004").json()
        assert any(
            a["type"] == "COMMUNICATION_ISSUE" and "Cliente in attesa" in a["title"] for a in after_escalation["alerts"]
        )

        doc = next(f for f in after_escalation["findings"] if f["type"] == "AGENT_DOCUMENT_REQUEST")
        client.post(f"/api/findings/{doc['id']}/status", data={"status": "VALIDATED"})
        client.post(f"/api/findings/{doc['id']}/apply")
        after_doc = client.get("/api/projects/P-26004").json()
        assert any(
            a["type"] == "CUSTOMER_FOLLOWUP" and "documentazione" in a["title"].lower() for a in after_doc["alerts"]
        )


def test_action_response_requires_requester_validation_before_close():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        detail = client.get("/api/projects/P-26006").json()
        alert = next(a for a in detail["alerts"] if a["type"] == "LD_EXPOSURE")
        created = client.post(f"/api/alerts/{alert['id']}/create-action").json()
        action_id = created["action_id"]
        response = client.post(
            f"/api/actions/{action_id}/response", data={"body": "Recovery plan verificato; nuova data proposta."}
        )
        assert response.status_code == 200
        middle = client.get("/api/projects/P-26006").json()
        action = next(a for a in middle["actions"] if a["id"] == action_id)
        assert action["status"] == "PENDING_VALIDATION"
        validated = client.post(f"/api/actions/{action_id}/validate")
        assert validated.status_code == 200
        final = client.get("/api/projects/P-26006").json()
        action2 = next(a for a in final["actions"] if a["id"] == action_id)
        assert action2["status"] == "CLOSED"
        assert action2["validated_by"]


def test_portfolio_distinguishes_critical_attention_and_has_tooltip_recaps():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert " critiche</span>" in response.text
        assert " in attenzione</span>" in response.text
        assert "data-tip=" in response.text


def test_v038_outbound_message_is_registered_but_not_sent():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        detail = client.get("/api/projects/P-26006").json()
        alert = next(a for a in detail["alerts"] if a["type"] == "LD_EXPOSURE")
        action_id = client.post(f"/api/alerts/{alert['id']}/create-action").json()["action_id"]
        r = client.post(f"/api/actions/{action_id}/outbound", data={"body": "Puoi verificare entro domani?"})
        assert r.status_code == 200
        assert "non ha inviato" in r.json()["message"].lower()
        after = client.get("/api/projects/P-26006").json()
        action = next(a for a in after["actions"] if a["id"] == action_id)
        assert action["messages"][-1]["source"] == "OUTBOUND"


def test_v038_confidence_plan_creates_only_operational_actions():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        r = client.post("/api/projects/9028/confidence-plan")
        assert r.status_code == 200
        assert len(r.json()["created"]) >= 1
        after = client.get("/api/projects/9028").json()
        assert any(a["source"].startswith("CONFIDENCE:") for a in after["actions"])
        assert round(after["control"]["operational_budget"], 2) == 730797.00


def test_project_pages_surface_read_many_write_little_policy():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        overview = client.get("/project/9028").text
        assert "Le fonti ufficiali sono in sola lettura" in overview
        assert "Il contratto originale non viene modificato" in overview
        assert "Come migliorarla" in overview
        economics = client.get("/project/9028/economics").text
        assert "Budget non ancora coperto" in economics
        assert "Nessun dato Galileo viene modificato" in economics


def test_administration_user_sees_assigned_project_and_can_reply_for_validation():
    with TestClient(app) as client:
        client.post("/api/demo/reset")

        # Director creates the action from a real financial alert. The rule routes it to Administration.
        detail = client.get("/api/projects/P-26002").json()
        overdue = next(a for a in detail["alerts"] if a["type"] == "OVERDUE_INVOICE")
        created = client.post(f"/api/alerts/{overdue['id']}/create-action")
        assert created.status_code == 200
        action_id = created.json()["action_id"]
        after_create = client.get("/api/projects/P-26002").json()
        action = next(a for a in after_create["actions"] if a["id"] == action_id)
        assert action["owner"] == "Amministrazione"

        # Administration has a dedicated identity and sees only projects assigned to its queue.
        login = client.post("/login", data={"username": "admin_demo"}, follow_redirects=False)
        assert login.status_code == 303
        admin_dashboard = client.get("/")
        assert admin_dashboard.status_code == 200
        assert "Attività Amministrazione" in admin_dashboard.text
        assert "P-26002" in admin_dashboard.text
        assert client.get("/project/P-26002").status_code == 200
        assert client.get("/project/P-26001").status_code == 404

        started = client.post(f"/api/actions/{action_id}/status", data={"status": "IN_PROGRESS"})
        assert started.status_code == 200
        reply = client.post(
            f"/api/actions/{action_id}/response",
            data={"body": "Verifica eseguita: il residuo è ancora aperto e il sollecito è stato avviato."},
        )
        assert reply.status_code == 200

        # The assignee cannot self-validate the reply.
        denied = client.post(f"/api/actions/{action_id}/validate")
        assert denied.status_code == 403

        # The requester/Director validates and closes; the source alert remains until source data changes.
        client.post("/login", data={"username": "director"}, follow_redirects=False)
        validated = client.post(f"/api/actions/{action_id}/validate")
        assert validated.status_code == 200
        final = client.get("/api/projects/P-26002").json()
        closed = next(a for a in final["actions"] if a["id"] == action_id)
        assert closed["status"] == "CLOSED"
        assert any(a["id"] == overdue["id"] for a in final["alerts"])


def test_shared_shell_has_one_ai_drawer_closed_by_default_and_support_drawers():
    with TestClient(app) as client:
        response = client.get("/project/P-26002")
        assert response.status_code == 200
        html = response.text
        for drawer in ("drawer-sources", "drawer-ai", "drawer-contract", "drawer-confidence"):
            assert f'id="{drawer}"' in html
        assert html.count('id="drawer-ai"') == 1
        assert 'class="drawer wide open"' not in html
        assert html.index('id="executiveSnapshot"') < html.index('id="drawer-sources"')
