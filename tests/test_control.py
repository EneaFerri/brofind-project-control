from fastapi.testclient import TestClient

from app.main import app


def _reset(client):
    response = client.post("/api/demo/reset", follow_redirects=False)
    assert response.status_code == 303


def test_9028_control_totals_and_no_etc_forecast():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        c = p["control"]
        assert round(c["baseline_budget"], 2) == 657708.26
        assert round(c["operational_budget"], 2) == 730797.00
        assert round(c["actual_total"], 2) == 204518.21
        assert round(c["absorbed_committed"], 2) == 459035.48
        assert round(c["uncommitted_budget"], 2) == 271761.52
        assert c["forecast_available"] is False
        assert "ETC" in c["forecast_message"]


def test_9028_contract_and_extra_reconstruct_budget_bridge():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        c = p["control"]
        assert round(c["contract"]["base_net"], 2) == 985550.00
        assert round(c["contract"]["extra_net"], 2) == 113350.00
        assert round(c["contract"]["net_total"], 2) == 1098900.00
        assert round(c["approved_change_cost"], 2) == 73091.00
        assert round(c["theoretical_authorized_budget"], 2) == 730799.26
        assert round(c["budget_bridge_difference"], 2) == -2.26
        assert round(c["contract"]["budget_margin_pct"], 1) == 33.5


def test_control_aggregates_all_analysis_centers_before_vda_comparison():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        row = next(r for r in p["control"]["vda_rows"] if r["vda_code"] == "C000026")
        assert round(row["operational_budget"], 2) == 57200.00
        assert round(row["ordered"], 2) == 31140.19
        assert round(row["received"], 2) == 12580.00
        assert round(row["open_order_commitment"], 2) == 18560.19
        assert len(row["centers"]) == 3
        assert row["purchases_closed"] is True


def test_all_baseline_vdas_are_visible_and_scope_delta_is_explicit():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        rows = p["control"]["vda_rows"]
        assert len(rows) == 34
        fan = next(r for r in rows if r["vda_code"] == "C000001")
        assert round(fan["baseline_budget"], 2) == 12612.15
        assert round(fan["scope_delta"], 2) == 13000.00
        assert round(fan["operational_budget"], 2) == 25612.15


def test_spedizioni_local_overrun_becomes_yellow_project_budget_alert():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        c = p["control"]
        assert c["budget_health"]["key"] == "WATCH"
        assert c["budget_health"]["tone"] == "amber"
        assert c["budget_health"]["closed_headroom"] > c["budget_health"]["gross_overrun"]
        alert = next(a for a in p["alerts"] if a["type"] == "CONTROL_BUDGET_POSITION")
        assert alert["severity"] == "MEDIUM"
        assert "saving" in alert["title"].lower()
        assert not any(a["type"] == "FORECAST_OVERRUN" for a in p["alerts"])
        assert p["health"]["BUDGET"] == "YELLOW"
        assert p["priority"]["key"] == "MEDIUM"


def test_missing_dimensions_are_not_green():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        assert p["health"]["FINANCE"] == "ND"
        assert p["health"]["TECHNICAL"] == "ND"
        assert p["health"]["SCHEDULE"] == "ND"
        assert p["health"]["CONTRACT"] == "GREEN"


def test_control_quality_exposes_reconciliations_and_allocation_gaps():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        q = p["control"]["quality"]
        assert q["status"] == "WARNING"
        assert round(q["orders_difference"], 2) == 172.81
        assert round(q["residual_difference"], 2) == 0.00
        assert round(q["unallocated_labor"], 2) == 409.92
        assert round(q["unallocated_overhead"], 2) == 3025.06


def test_project_page_explains_control_boundaries_cda_and_contract_evidence():
    with TestClient(app) as client:
        _reset(client)
        response = client.get("/project/9028/economics")
        assert response.status_code == 200
        assert "Economic Control" in response.text
        assert "Forecast finale" in response.text and "non consolidabile" in response.text
        assert "Budget non ancora coperto" in response.text
        assert "Centri di Analisi" in response.text
        assert "Un saving entra nel margine solo dopo conferma" in response.text
        # Contract Baseline (drawer condiviso): evidenze dei PO cliente.
        assert "PO-PILOT-001" in response.text
        assert "PO-PILOT-002" in response.text
        assert "Affidabilità dei dati" in response.text


def test_9028_vda_view_is_progressive_and_uses_explicit_labels():
    with TestClient(app) as client:
        _reset(client)
        economics = client.get("/project/9028/economics").text
        assert 'onclick="toggleRows(' in economics
        assert "Saving candidato" in economics
        assert "Budget residuo" in economics
        procurement = client.get("/project/9028/procurement").text
        assert "Vista per voce di analisi (VdA)" in procurement
        assert ">Stadio<" in procurement
        assert ">Stato controllo<" in procurement
        assert "Verifica urgente" in procurement


def test_dashboard_renders_nd_as_explicit_neutral_state():
    with TestClient(app) as client:
        _reset(client)
        response = client.get("/")
        assert response.status_code == 200
        assert 'class="dot ND"' in response.text
        assert ">N/D<" in response.text
        assert "non valutabili" in response.text


def test_9028_procurement_engine_flags_analyzers_without_inventing_delay():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        c = p["control"]
        analyzers = next(r for r in c["vda_rows"] if r["vda_code"] == "C000028")
        assert analyzers["procurement_status"]["key"] == "NOT_STARTED"
        assert analyzers["procurement_risk"]["key"] == "HIGH"
        assert analyzers["procurement_risk"]["tone"] == "amber"
        assert analyzers["procurement"]["requirements"][0]["status"] == "REQUIRED"
        alert = next(a for a in p["alerts"] if a["type"] == "PROCUREMENT_MATURITY")
        assert alert["severity"] == "MEDIUM"
        assert "verificare" in alert["title"].lower()
        assert "ritardo" not in alert["title"].lower()


def test_9028_contract_package_and_second_lel_evidence_are_explicit():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        assert p["control"]["contract"]["documentation_complete"] is True
        base = next(o for o in p["control"]["contract"]["orders"] if o["kind"] == "BASE")
        assert base["document_status"] == "COMPLETE"
        reqs = p["requirements"]
        assert any(r["key"] == "LEL_BASE" and r["status"] == "REQUIRED" for r in reqs)
        assert any(r["key"] == "LEL_SECOND" and r["status"] == "TO_VERIFY" for r in reqs)
        assert any(f["type"] == "SCOPE_CHANGE_CANDIDATE" and f["status"] == "NEW" for f in p["findings"])


def test_9028_internal_vdas_do_not_generate_false_missing_purchase_signal():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        engineering = next(r for r in p["control"]["vda_rows"] if r["vda_code"] == "C000025")
        supervision = next(r for r in p["control"]["vda_rows"] if r["vda_code"] == "C000030")
        assert engineering["procurement_status"]["key"] == "NA"
        assert supervision["procurement_status"]["key"] == "NA"
        assert engineering["procurement_risk"]["key"] == "NONE"


def test_9028_confidence_is_domain_specific_and_triggers_review():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        conf = p["confidence"]
        assert conf["domains"]["ECONOMIC"]["level"] == "HIGH"
        assert conf["domains"]["PROCUREMENT"]["level"] == "MEDIUM"
        assert conf["domains"]["SCHEDULE"]["level"] == "INSUFFICIENT"
        assert conf["review_required"] is True
        assert any(a["type"] == "CONFIDENCE_REVIEW" for a in p["alerts"])
        # Governance/data quality must not turn a performance domain red/yellow by itself.
        assert p["health"]["SCHEDULE"] == "ND"


def test_9028_saving_is_candidate_until_human_consolidation():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        carpenteria = next(r for r in p["control"]["vda_rows"] if r["vda_code"] == "C000013")
        assert carpenteria["saving_status"]["key"] == "CANDIDATE"
        amount = carpenteria["saving_status"]["amount"]
        assert amount > 60000
        r = client.post("/api/projects/9028/vda/C000013/saving", data={"confirmed": "true"})
        assert r.status_code == 200
        p2 = client.get("/api/projects/9028").json()
        carpenteria2 = next(r for r in p2["control"]["vda_rows"] if r["vda_code"] == "C000013")
        assert carpenteria2["saving_status"]["key"] == "CONSOLIDATED"
        assert p2["control"]["saving"]["consolidated"] >= amount
        assert round(p2["control"]["operational_budget"], 2) == 730797.00


def test_montaggi_elettrici_uses_uniform_service_profile_not_false_missing_purchase():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        row = next(r for r in p["control"]["vda_rows"] if r["vda_code"] == "C000029")
        assert row["procurement_status"]["key"] == "PREPARATION_UNKNOWN"
        assert row["procurement_risk"]["key"] == "MEDIUM"
        assert row["procurement_risk"]["label"] == "Potenziale ritardo procurement"
        assert "RFQ" in row["procurement_risk"]["reason"]
        assert row["procurement"]["profile"]["expected_order_phase"] == "Tardiva"


def test_contract_baseline_surfaces_clarifications_instead_of_auto_resolving_conflicts():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        baseline = p["contract_baseline"]
        assert baseline["documentation_complete"] is True
        assert baseline["clarify_count"] >= 3
        assert any(c["status"] == "TO_CLARIFY" and "pagamento" in c["name"].lower() for c in baseline["conditions"])


def test_v038_confidence_has_overall_and_recovery_guidance():
    with TestClient(app) as client:
        _reset(client)
        p = client.get("/api/projects/9028").json()
        conf = p["confidence"]
        assert conf["overall"]["level"] == "MEDIUM"
        procurement = conf["domains"]["PROCUREMENT"]
        assert procurement["target_level_label"] == "Alta"
        assert procurement["recovery_actions"]
        assert "Acquisti" in procurement["recovery_owner"]


def test_v038_contract_condition_freezes_in_operational_layer():
    with TestClient(app) as client:
        _reset(client)
        before = client.get("/api/projects/9028").json()
        original_order = before["control"]["contract"]["base_net"]
        r = client.post(
            "/api/projects/9028/contract-condition/payment_terms",
            data={
                "value": "45 giorni data fattura",
                "note": "Agreement prevalente",
                "source_ref": "contract:PO-PILOT-001:agreement",
                "freeze": "true",
            },
        )
        assert r.status_code == 200
        after = client.get("/api/projects/9028").json()
        payment = next(c for c in after["contract_baseline"]["conditions"] if c["key"] == "payment_terms")
        assert payment["status"] == "FROZEN"
        assert payment["value"] == "45 giorni data fattura"
        assert after["control"]["contract"]["base_net"] == original_order


def test_v038_dismiss_engineering_finding_does_not_mutate_requirement_source():
    with TestClient(app) as client:
        _reset(client)
        before = client.get("/api/projects/9028").json()
        req = next(r for r in before["requirements"] if r["key"] == "LEL_SECOND")
        r = client.post(f"/api/projects/9028/requirements/{req['id']}/disposition", data={"disposition": "DISMISSED"})
        assert r.status_code == 200
        after = client.get("/api/projects/9028").json()
        req2 = next(r for r in after["requirements"] if r["key"] == "LEL_SECOND")
        assert req2["status"] == "TO_VERIFY"  # source record remains unchanged
        assert after["contract_baseline"]["potential_change_count"] == 0


def test_v038_saving_classification_does_not_change_operational_budget():
    with TestClient(app) as client:
        _reset(client)
        before = client.get("/api/projects/9028").json()
        budget = before["control"]["operational_budget"]
        r = client.post("/api/projects/9028/vda/C000013/saving", data={"confirmed": "true"})
        assert r.status_code == 200
        after = client.get("/api/projects/9028").json()
        assert after["control"]["operational_budget"] == budget
        row = next(x for x in after["control"]["vda_rows"] if x["vda_code"] == "C000013")
        assert row["saving_status"]["key"] == "CONSOLIDATED"
