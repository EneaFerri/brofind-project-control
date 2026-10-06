from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from .models import (
    Action,
    AgentFinding,
    BudgetLine,
    ChangeRequest,
    Communication,
    CustomerOrder,
    Invoice,
    Issue,
    Milestone,
    Project,
    ProjectControlLine,
    ProjectControlSnapshot,
    ProjectRequirement,
    User,
)

SALES = ["S. Riva", "L. Ferri", "M. Conti"]
PMS = ["A. Greco", "P. Sala", "E. Costa"]

DEMO_USERS = [
    {"username": "director", "display_name": "Direzione", "role": "DIRECTOR", "owner_key": None},
    {"username": "sales_riva", "display_name": "Commerciale — S. Riva", "role": "SALES", "owner_key": "S. Riva"},
    {"username": "sales_ferri", "display_name": "Commerciale — L. Ferri", "role": "SALES", "owner_key": "L. Ferri"},
    {"username": "sales_conti", "display_name": "Commerciale — M. Conti", "role": "SALES", "owner_key": "M. Conti"},
    {"username": "pm_greco", "display_name": "PM — A. Greco", "role": "PM", "owner_key": "A. Greco"},
    {"username": "pm_sala", "display_name": "PM — P. Sala", "role": "PM", "owner_key": "P. Sala"},
    {"username": "pm_costa", "display_name": "PM — E. Costa", "role": "PM", "owner_key": "E. Costa"},
    {
        "username": "admin_demo",
        "display_name": "Amministrazione — Demo",
        "role": "ADMIN",
        "owner_key": "Amministrazione",
    },
]


def ensure_demo_users(db: Session):
    existing = {u.username for u in db.query(User).all()}
    for spec in DEMO_USERS:
        if spec["username"] not in existing:
            db.add(User(**spec))
    db.flush()


def add_budget(p, budget, actual, committed, etc, split=(0.42, 0.28, 0.18, 0.12)):
    cats = ["Mechanical", "Electrical & Automation", "Site activities", "Engineering"]
    for cat, share in zip(cats, split, strict=True):
        p.budget_lines.append(
            BudgetLine(
                category=cat,
                budget=round(budget * share, 2),
                actual=round(actual * share, 2),
                committed=round(committed * share, 2),
                etc=round(etc * share, 2),
                etc_source="MANUAL",
            )
        )


def seed(db: Session):
    ensure_demo_users(db)
    if db.query(Project).count() > 0:
        db.commit()
        return
    today = date.today()

    # 1 healthy
    p = Project(
        code="P-26001",
        customer="Alpha Coating S.p.A.",
        sales_owner="S. Riva",
        pm_owner="A. Greco",
        order_value=780000,
        status="EXECUTION",
        description="RTO 30.000 Nm³/h",
    )
    add_budget(p, 520000, 260000, 160000, 65000)
    p.milestones += [
        Milestone(
            name="Delivery",
            contract_date=today + timedelta(days=35),
            forecast_date=today + timedelta(days=33),
            invoice_value=156000,
            invoice_required=True,
        ),
        Milestone(name="SAT", contract_date=today + timedelta(days=70), forecast_date=today + timedelta(days=68)),
    ]
    p.invoices += [
        Invoice(
            number="INV-A001",
            milestone_name="Down payment",
            issue_date=today - timedelta(days=90),
            due_date=today - timedelta(days=60),
            amount=156000,
            paid_amount=156000,
        )
    ]
    db.add(p)

    # 2 closed with overdue
    p = Project(
        code="P-26002",
        customer="Beta Packaging S.r.l.",
        sales_owner="S. Riva",
        pm_owner="P. Sala",
        order_value=640000,
        status="CLOSING",
        technical_status="CLOSED",
        description="RTO revamping",
    )
    add_budget(p, 430000, 418000, 0, 0)
    p.invoices += [
        Invoice(
            number="INV-B015",
            milestone_name="Final acceptance",
            issue_date=today - timedelta(days=70),
            due_date=today - timedelta(days=40),
            amount=128000,
            paid_amount=8000,
        )
    ]
    p.milestones += [
        Milestone(
            name="Final acceptance",
            contract_date=today - timedelta(days=70),
            actual_date=today - timedelta(days=65),
            invoice_value=128000,
            invoice_required=True,
        )
    ]
    p.communications += [
        Communication(
            date=today - timedelta(days=4),
            direction="INBOUND",
            sender="finance@beta.example",
            recipient="sales@brofind.example",
            subject="Payment status INV-B015",
            body="We confirm that the remaining payment of EUR 120,000 will be released by 25 September 2026.",
            topic="Payment",
            responded=True,
            source_ref="mail:BETA-PAY-01",
        )
    ]
    db.add(p)

    # 3 delivered but invoice missing
    p = Project(
        code="P-26003",
        customer="Gamma Chemicals S.A.",
        sales_owner="L. Ferri",
        pm_owner="A. Greco",
        order_value=980000,
        status="EXECUTION",
        description="Thermal oxidizer",
    )
    add_budget(p, 665000, 410000, 170000, 55000)
    p.milestones += [
        Milestone(
            name="Delivery",
            contract_date=today - timedelta(days=14),
            actual_date=today - timedelta(days=12),
            invoice_value=196000,
            invoice_required=True,
        )
    ]
    p.invoices += [
        Invoice(
            number="INV-G001",
            milestone_name="Down payment",
            issue_date=today - timedelta(days=180),
            due_date=today - timedelta(days=150),
            amount=294000,
            paid_amount=294000,
        )
    ]
    db.add(p)

    # 4 communication issue
    p = Project(
        code="P-26004",
        customer="Delta Textiles SAS",
        sales_owner="L. Ferri",
        pm_owner="P. Sala",
        order_value=360000,
        status="EXECUTION",
        description="VOC abatement line",
    )
    add_budget(p, 235000, 150000, 52000, 18000)
    p.communications += [
        Communication(
            date=today - timedelta(days=9),
            direction="INBOUND",
            sender="client@delta.example",
            recipient="pm@brofind.example",
            subject="Urgent: revised electrical documentation",
            body="Please send the revised documents as agreed. This is our third reminder.",
            topic="Electrical documentation",
            responded=False,
            reminders_count=3,
            source_ref="mail:DELTA-003",
        )
    ]
    p.actions += [
        Action(
            title="Inviare documentazione elettrica revisionata",
            owner="P. Sala",
            due_date=today - timedelta(days=5),
            status="OPEN",
            source="MAIL",
        )
    ]
    db.add(p)

    # 5 budget overrun
    p = Project(
        code="P-26005",
        customer="Epsilon Films GmbH",
        sales_owner="M. Conti",
        pm_owner="A. Greco",
        order_value=1250000,
        status="EXECUTION",
        description="3-bed RTO",
    )
    add_budget(p, 820000, 590000, 180000, 125000)
    db.add(p)

    # 6 delay + LD
    p = Project(
        code="P-26006",
        customer="Zeta Surface Technologies",
        sales_owner="S. Riva",
        pm_owner="E. Costa",
        order_value=1480000,
        status="EXECUTION",
        description="RTO + heat recovery",
    )
    add_budget(p, 985000, 620000, 260000, 65000)
    p.milestones += [
        Milestone(
            name="Contractual delivery",
            contract_date=today + timedelta(days=9),
            forecast_date=today + timedelta(days=31),
            invoice_value=296000,
            invoice_required=True,
            ld_applicable=True,
            ld_rate_weekly_pct=0.5,
        )
    ]
    p.communications += [
        Communication(
            date=today - timedelta(days=1),
            direction="INBOUND",
            sender="project@zeta.example",
            recipient="pm@brofind.example",
            subject="Delivery schedule update",
            body="Unfortunately the delivery cannot take place on the agreed date. We expect approximately two weeks delay and ask you to confirm the revised shipment plan.",
            topic="Delivery",
            responded=False,
            source_ref="mail:ZETA-SCHED-01",
        )
    ]
    db.add(p)

    # 7 uncovered extra
    p = Project(
        code="P-26007",
        customer="Eta Components S.p.A.",
        sales_owner="M. Conti",
        pm_owner="P. Sala",
        order_value=510000,
        status="EXECUTION",
        description="Catalytic oxidizer",
    )
    add_budget(p, 335000, 205000, 82000, 34000)
    p.changes += [
        ChangeRequest(
            description="Additional duct and platform modification requested by customer",
            requested_date=today - timedelta(days=24),
            estimated_cost=18500,
            quoted_value=27000,
            order_received=False,
            work_started=True,
        )
    ]
    p.communications += [
        Communication(
            date=today - timedelta(days=24),
            direction="INBOUND",
            sender="engineering@eta.example",
            recipient="pm@brofind.example",
            subject="Additional platform modification",
            body="Please include an additional duct section and modify the access platform. We need this change incorporated before installation.",
            topic="Change request",
            responded=True,
            source_ref="mail:ETA-CHANGE-01",
        )
    ]
    db.add(p)

    # 8 documentation blocker
    p = Project(
        code="P-26008",
        customer="Theta Pharma NV",
        sales_owner="L. Ferri",
        pm_owner="E. Costa",
        order_value=890000,
        status="CLOSING",
        description="TO skid",
    )
    add_budget(p, 602000, 570000, 12000, 5000)
    p.issues += [
        Issue(
            category="DOCUMENTATION",
            title="As-built electrical drawings missing; provisional acceptance cannot be signed.",
            severity="HIGH",
            status="OPEN",
            blocking=True,
            due_date=today - timedelta(days=2),
        )
    ]
    p.milestones += [
        Milestone(
            name="Provisional acceptance",
            contract_date=today - timedelta(days=3),
            forecast_date=today + timedelta(days=10),
            invoice_value=89000,
            invoice_required=True,
        )
    ]
    p.communications += [
        Communication(
            date=today - timedelta(days=2),
            direction="INBOUND",
            sender="qa@theta.example",
            recipient="pm@brofind.example",
            subject="Missing as-built documentation",
            body="We are still waiting for the as-built electrical drawings. Provisional acceptance cannot be signed until the missing documentation is received.",
            topic="Documentation",
            responded=False,
            reminders_count=1,
            source_ref="mail:THETA-DOC-01",
        )
    ]
    db.add(p)

    # 9 technical performance issue
    p = Project(
        code="P-26009",
        customer="Iota Resins Ltd.",
        sales_owner="S. Riva",
        pm_owner="A. Greco",
        order_value=730000,
        status="COMMISSIONING",
        description="RTO retrofit",
    )
    add_budget(p, 485000, 430000, 28000, 22000)
    p.issues += [
        Issue(
            category="TECHNICAL",
            title="VOC destruction efficiency below guaranteed value during preliminary test.",
            severity="HIGH",
            status="OPEN",
            blocking=True,
            due_date=today + timedelta(days=4),
        )
    ]
    p.milestones += [
        Milestone(
            name="SAT",
            contract_date=today + timedelta(days=12),
            forecast_date=today + timedelta(days=12),
            invoice_value=73000,
            invoice_required=True,
        )
    ]
    p.communications += [
        Communication(
            date=today - timedelta(days=1),
            direction="INBOUND",
            sender="process@iota.example",
            recipient="pm@brofind.example",
            subject="Preliminary FID test results",
            body="The preliminary FID test shows destruction efficiency below the guaranteed value. Please provide your technical assessment before SAT.",
            topic="Performance",
            responded=False,
            source_ref="mail:IOTA-TECH-01",
        )
    ]
    db.add(p)

    # 10 overdue action
    p = Project(
        code="P-26010",
        customer="Kappa Paper S.p.A.",
        sales_owner="M. Conti",
        pm_owner="P. Sala",
        order_value=440000,
        status="EXECUTION",
        description="Regenerative oxidizer service",
    )
    add_budget(p, 290000, 170000, 76000, 26000)
    p.actions += [
        Action(
            title="Confermare data FAT al cliente",
            owner="P. Sala",
            due_date=today - timedelta(days=13),
            status="OPEN",
            source="MANUAL",
        )
    ]
    db.add(p)

    # 11 mixed medium
    p = Project(
        code="P-26011",
        customer="Lambda Automotive Systems",
        sales_owner="L. Ferri",
        pm_owner="A. Greco",
        order_value=1050000,
        status="EXECUTION",
        description="RTO + scrubber interface",
    )
    add_budget(p, 690000, 480000, 150000, 85000)
    p.milestones += [
        Milestone(
            name="FAT",
            contract_date=today + timedelta(days=12),
            forecast_date=today + timedelta(days=20),
            invoice_value=105000,
            invoice_required=True,
        )
    ]
    p.communications += [
        Communication(
            date=today - timedelta(days=1),
            direction="OUTBOUND",
            sender="pm@brofind.example",
            recipient="client@lambda.example",
            subject="FAT planning",
            body="We expect the FAT to be postponed by 8 days. We will confirm the final date after the internal recovery meeting.",
            topic="FAT",
            responded=True,
            source_ref="mail:LAMBDA-FAT-01",
        )
    ]
    db.add(p)

    # 12 new handover, healthy
    p = Project(
        code="P-26012",
        customer="Mu Coatings BV",
        sales_owner="M. Conti",
        pm_owner="E. Costa",
        order_value=570000,
        status="HANDOVER",
        description="Newly acquired electric RTO feasibility",
    )
    add_budget(p, 385000, 18000, 11000, 330000)
    p.actions += [
        Action(
            title="Kick-off interno e verifica baseline contrattuale",
            owner="E. Costa",
            due_date=today + timedelta(days=5),
            status="OPEN",
            source="HANDOVER",
        )
    ]
    db.add(p)

    # 13 real-data pilot for management/control integration — 9028 (cliente pilota anonimizzato)
    # Owners intentionally N/D: this pilot contains only data actually evidenced in the supplied sources.
    p = Project(
        code="9028",
        customer="Cliente Pilota",
        sales_owner="N/D",
        pm_owner="N/D",
        order_value=1098900.00,
        status="EXECUTION",
        technical_status="IN_PROGRESS",
        country="FR",
        delivery_window="NEAR",
        delivery_context="Pilot: commessa indicata come prossima alla consegna; data planning corrente non ancora acquisita come fonte strutturata.",
        description="RTO per trattamento emissioni VOC + cloro · pilot controllo economico con evidenze reali",
    )

    # Customer PO evidence. Contract value is always stored net of VAT for project revenue/margin.
    p.customer_orders += [
        CustomerOrder(
            order_number="PO-PILOT-001",
            order_date=date(2025, 11, 4),
            order_kind="BASE",
            quote_ref="OFF-PILOT-001 Rev.5",
            net_value=985550.00,
            tax_value=0.00,
            gross_value=985550.00,
            currency="EUR",
            payment_terms="SEPA · 60 giorni data fattura",
            incoterm="DDP",
            scope_summary="Impianto di ossidazione termica rigenerativa per emissioni contenenti COV + cloro; include coibentazione, motori IE4 e BR.A.I.N.; parti critiche Hastelloy valorizzate €0 nel PO.",
            source_ref="contract:PO-PILOT-001",
            note="PO del 04/11/2025 emesso come modifica a seguito emendamento contrattuale n.1 (IVA). La consegna 03/11/2025 riportata sul documento non viene assunta come milestone corrente senza ricostruire le revisioni precedenti.",
            document_status="COMPLETE",
            document_note="Pacchetto contrattuale acquisito: PO/Agreement, clarification table, CGA cliente e offerta Brofind Rev.5 con evidenze di sottoscrizione.",
        ),
        CustomerOrder(
            order_number="PO-PILOT-002",
            order_date=date(2026, 4, 20),
            order_kind="EXTRA",
            quote_ref="OFF-PILOT-002",
            net_value=113350.00,
            tax_value=22670.00,
            gross_value=136020.00,
            currency="EUR",
            payment_terms="SEPA · 60 giorni data fattura",
            incoterm="DDP",
            scope_summary="Extra scope: raddoppio ventilatori, modifica struttura, aggiunta PLC/automate di sicurezza.",
            source_ref="contract:PO-PILOT-002",
            note="Il valore economico di commessa considera l'imponibile €113.350; €22.670 sono IVA e non ricavo di progetto.",
            document_status="COMPLETE",
            document_note="PO extra formalizzato e acquisito.",
        ),
    ]
    p.changes.append(
        ChangeRequest(
            description="Extra 1 · raddoppio ventilatori, modifica struttura, PLC safety",
            requested_date=date(2026, 4, 20),
            estimated_cost=73091.00,
            quoted_value=113350.00,
            order_received=True,
            work_started=True,
            source_ref="contract:PO-PILOT-002",
        )
    )

    # Structured evidence that, in the target architecture, will be produced by contract / engineering agents.
    p.requirements += [
        ProjectRequirement(
            requirement_key="LEL_BASE",
            title="Analizzatore LEL previsto nello scope contrattuale",
            vda_code="C000028",
            status="REQUIRED",
            source_kind="CONTRACT",
            source_ref="contract:PO-PILOT-001:agreement",
            source_date=date(2025, 11, 3),
            quantity=1,
            procurement_mode="DIRECT_OR_PACKAGE",
            confidence=1.0,
            note="L'Agreement del PO include il LIE analyser nello scope; il pacchetto contrattuale definisce la gerarchia documentale applicabile.",
        ),
        ProjectRequirement(
            requirement_key="LEL_SECOND",
            title="Secondo analizzatore LEL / ridondanza",
            vda_code="C000028",
            status="TO_VERIFY",
            source_kind="ENGINEERING",
            source_ref="engineering:openpoints-rev2:LEL",
            source_date=date(2026, 1, 29),
            quantity=1,
            procurement_mode="DIRECT_OR_PACKAGE",
            confidence=0.95,
            note="Open points Rev.2: il cliente indica due LEL; Brofind considera la ridondanza appropriata e necessaria per il livello di sicurezza. Copertura economica/formalizzazione da verificare.",
        ),
    ]
    p.agent_findings.append(
        AgentFinding(
            fingerprint="9028:SECOND_LEL_SCOPE_CHECK",
            finding_type="SCOPE_CHANGE_CANDIDATE",
            dimension="CONTRACT",
            severity="MEDIUM",
            title="Secondo LEL: verificare copertura contrattuale ed economica",
            summary="Gli open points Rev.2 introducono una ridondanza LEL che non compare esplicitamente nel PO Extra 1 acquisito. Verificare se è già inclusa nello scope/prezzo o se richiede una variazione formalizzata.",
            evidence="Open points Rev.2: due analizzatori LEL previsti/probabili per diluizione e safety interlock; Brofind considera la ridondanza necessaria.",
            suggested_action="Confermare scope e copertura economica del secondo LEL",
            suggested_owner="PM / Commerciale",
            confidence=0.95,
            status="NEW",
            source_ref="engineering:openpoints-rev2:LEL",
        )
    )

    snap = ProjectControlSnapshot(
        captured_at=datetime.combine(date(2026, 9, 22), datetime.min.time()),
        source_label="Galileo · JMRP + Interrogazione ordini",
        baseline_budget=657708.26,
        operational_budget=730797.00,
        orders_jmrp=454381.70,
        orders_extract=454208.89,
        received=199691.62,
        open_order_commitment=254517.27,
        labor=1801.53,
        overhead=3025.06,
        note="Snapshot pilota. Baseline + budget Extra 1 = €730.799,26; Galileo mostra €730.797,00. Forecast finale non calcolato: nessun ETC strutturato richiesto al PM.",
    )

    # Baseline commercial budget (REV.0), approved Extra 1 cost budget and purchase-order extraction by VdA.
    # Only purchase-closure flags explicitly evidenced in JMRP are populated; the others remain unknown.
    vdas = [
        ("C999999", "ALTRO", 0.00, 0.00, 127.20, 0.00, None),
        ("C000028", "ANALIZZATORI", 8810.00, 0.00, 0.00, 0.00, None),
        ("C000032", "APPARECCHI A SPECIFICA", 59762.00, 0.00, 50262.00, 50262.00, None),
        ("C000008", "BRUCIATORI", 8850.00, 0.00, 8270.00, 0.00, None),
        ("C000012", "CALDAIE", 0.00, 0.00, 0.00, 0.00, None),
        ("C000036", "CANALIZZAZIONI", 0.00, 0.00, 0.00, 0.00, None),
        ("C000013", "CARPENTERIE METALLICHE", 246255.00, 17150.00, 201475.02, 100670.00, True),
        ("C000017", "COIBENTAZIONE", 8910.00, 0.00, 7000.00, 7000.00, None),
        ("C000020", "EQUIPAGGIAMENTI DI SICUREZZA", 0.00, 0.00, 0.00, 0.00, None),
        ("C000007", "FILTRI", 0.00, 0.00, 0.00, 0.00, None),
        ("C000006", "GIUNTI DI ESPANSIONE", 0.00, 0.00, 0.00, 0.00, None),
        ("C009999", "IMPREVISTI", 19731.25, 1462.00, 0.00, 0.00, None),
        ("C000025", "INGEGNERIA E DOCUMENTAZIONE", 23300.00, 0.00, 3582.00, 0.00, None),
        ("C000004", "INSONORIZZAZIONE", 0.00, 0.00, 196.80, 0.00, None),
        ("C000003", "INVERTER", 4050.00, 1900.00, 3456.36, 0.00, None),
        ("C000019", "MATERIALE CERAMICO", 7273.74, 0.00, 0.00, 0.00, None),
        # C000026 is split across analysis centres below.
        ("C000022", "MEZZI DI SOLLEVAMENTO", 0.00, 0.00, 0.00, 0.00, None),
        ("C000029", "MONTAGGI ELETTRICI", 42160.00, 4550.00, 0.00, 0.00, None),
        ("C000014", "MONTAGGI MECCANICI", 24540.00, 7100.00, 9000.00, 4320.00, None),
        ("C000002", "MOTORI", 5150.00, 3500.00, 3200.00, 0.00, None),
        ("C000033", "PIPING", 2.00, 0.00, 0.00, 0.00, None),
        ("C000011", "POMPE", 9500.00, 0.00, 1253.40, 0.00, None),
        ("C000016", "RIVESTIMENTO INTERNO", 16200.00, 0.00, 15460.00, 15460.00, None),
        ("C000005", "ROTOCONCENTRATORI", 0.00, 0.00, 0.00, 0.00, None),
        ("C000010", "SCAMBIATORI DI CALORE", 0.00, 0.00, 0.00, 0.00, None),
        ("C000015", "SMONTAGGI", 0.00, 0.00, 0.00, 0.00, None),
        ("C000024", "SOFTWARE", 3405.00, 0.00, 1473.55, 0.00, None),
        ("C000021", "SPEDIZIONI", 21600.00, 0.00, 29177.60, 27470.00, False),
        ("C000023", "STOCCAGGIO", 0.00, 0.00, 0.00, 0.00, None),
        ("C000027", "STRUMENTAZIONE", 30700.00, 7280.00, 33411.93, 30273.33, None),
        ("C000030", "SUPERVISIONE E AVVIAMENTO", 31120.00, 0.00, 0.00, 0.00, None),
        ("C000009", "VALVOLE E ATTUATORI", 20377.12, 13349.00, 32322.84, 501.75, None),
        ("C000001", "VENTILATORI", 12612.15, 13000.00, 23400.00, 0.00, None),
    ]
    for code, name, base, extra_cost, ordered, residual, closed in vdas:
        received = ordered - residual
        labor = 1391.61 if code == "C000025" else 0.0
        snap.lines.append(
            ProjectControlLine(
                vda_code=code,
                vda_name=name,
                analysis_center="COMM",
                baseline_budget=base,
                operational_budget=base + extra_cost,
                ordered=ordered,
                received=received,
                open_order_commitment=residual,
                labor=labor,
                overhead=0.0,
                purchases_closed=closed,
                source_ref=f"galileo:9028:{code}:COMM",
            )
        )

    # Materiali elettrici: one VdA, three analysis centres. Budget sits on COMM; CDA rows carry procurement detail.
    snap.lines.append(
        ProjectControlLine(
            vda_code="C000026",
            vda_name="MATERIALI ELETTRICI",
            analysis_center="COMM",
            baseline_budget=53400.00,
            operational_budget=57200.00,
            ordered=8348.00,
            received=4000.00,
            open_order_commitment=4348.00,
            labor=0.0,
            overhead=0.0,
            purchases_closed=True,
            source_ref="galileo:9028:C000026:COMM",
        )
    )
    snap.lines.append(
        ProjectControlLine(
            vda_code="C000026",
            vda_name="MATERIALI ELETTRICI",
            analysis_center="CDA26002",
            baseline_budget=0.0,
            operational_budget=0.0,
            ordered=16192.19,
            received=6000.00,
            open_order_commitment=10192.19,
            labor=0.0,
            overhead=0.0,
            purchases_closed=True,
            source_ref="galileo:9028:C000026:CDA26002",
        )
    )
    snap.lines.append(
        ProjectControlLine(
            vda_code="C000026",
            vda_name="MATERIALI ELETTRICI",
            analysis_center="CDA26003",
            baseline_budget=0.0,
            operational_budget=0.0,
            ordered=6600.00,
            received=2580.00,
            open_order_commitment=4020.00,
            labor=0.0,
            overhead=0.0,
            purchases_closed=True,
            source_ref="galileo:9028:C000026:CDA26003",
        )
    )

    p.control_snapshots.append(snap)
    db.add(p)

    db.commit()
