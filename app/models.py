from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .clock import utcnow
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    display_name = Column(String(120), nullable=False)
    role = Column(String(30), nullable=False)  # DIRECTOR | SALES | PM | ADMIN
    owner_key = Column(String(120), nullable=True)


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True, nullable=False)
    customer = Column(String(160), nullable=False)
    sales_owner = Column(String(120), nullable=False)
    pm_owner = Column(String(120), nullable=False)
    order_value = Column(Float, nullable=False, default=0)
    status = Column(String(40), nullable=False, default="EXECUTION")
    technical_status = Column(String(40), nullable=False, default="IN_PROGRESS")
    country = Column(String(2), nullable=False, default="IT")
    description = Column(String(255), nullable=True)
    delivery_window = Column(String(30), nullable=False, default="UNKNOWN")  # UNKNOWN | FAR | NEAR | IMMINENT
    delivery_context = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    milestones = relationship("Milestone", cascade="all, delete-orphan", back_populates="project")
    budget_lines = relationship("BudgetLine", cascade="all, delete-orphan", back_populates="project")
    invoices = relationship("Invoice", cascade="all, delete-orphan", back_populates="project")
    payments = relationship("Payment", cascade="all, delete-orphan", back_populates="project")
    actions = relationship("Action", cascade="all, delete-orphan", back_populates="project")
    issues = relationship("Issue", cascade="all, delete-orphan", back_populates="project")
    communications = relationship("Communication", cascade="all, delete-orphan", back_populates="project")
    changes = relationship("ChangeRequest", cascade="all, delete-orphan", back_populates="project")
    alerts = relationship("Alert", cascade="all, delete-orphan", back_populates="project")
    agent_findings = relationship("AgentFinding", cascade="all, delete-orphan", back_populates="project")
    agent_runs = relationship("AgentRun", cascade="all, delete-orphan", back_populates="project")
    control_snapshots = relationship("ProjectControlSnapshot", cascade="all, delete-orphan", back_populates="project")
    customer_orders = relationship("CustomerOrder", cascade="all, delete-orphan", back_populates="project")
    requirements = relationship("ProjectRequirement", cascade="all, delete-orphan", back_populates="project")
    cockpit_decisions = relationship("CockpitDecision", cascade="all, delete-orphan", back_populates="project")
    source_scans = relationship("ProjectSourceScan", cascade="all, delete-orphan", back_populates="project")
    source_files = relationship("ProjectSourceFile", cascade="all, delete-orphan", back_populates="project")
    source_imports = relationship("ProjectSourceImport", cascade="all, delete-orphan", back_populates="project")
    source_contents = relationship("ProjectSourceContent", cascade="all, delete-orphan", back_populates="project")
    extracted_fields = relationship("ProjectExtractedField", cascade="all, delete-orphan", back_populates="project")


class CockpitDecision(Base):
    """Small writable operational layer owned by the cockpit.

    Source/master data remain read-only. This table stores only reviewed interpretations,
    classifications and operational decisions made inside the cockpit.
    """

    __tablename__ = "cockpit_decisions"
    __table_args__ = (UniqueConstraint("project_id", "decision_type", "decision_key", name="uq_cockpit_decision"),)
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    decision_type = Column(String(50), nullable=False)
    decision_key = Column(String(120), nullable=False)
    value = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="ACTIVE")
    note = Column(Text, nullable=True)
    source_ref = Column(String(180), nullable=True)
    created_by = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    project = relationship("Project", back_populates="cockpit_decisions")


class CustomerOrder(Base):
    __tablename__ = "customer_orders"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    order_number = Column(String(80), nullable=False)
    order_date = Column(Date, nullable=False)
    order_kind = Column(String(30), nullable=False, default="BASE")  # BASE | EXTRA | AMENDMENT
    quote_ref = Column(String(120), nullable=True)
    net_value = Column(Float, nullable=False, default=0)
    tax_value = Column(Float, nullable=False, default=0)
    gross_value = Column(Float, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="EUR")
    payment_terms = Column(String(160), nullable=True)
    incoterm = Column(String(40), nullable=True)
    scope_summary = Column(Text, nullable=True)
    source_ref = Column(String(180), nullable=True)
    note = Column(Text, nullable=True)
    document_status = Column(String(30), nullable=False, default="PARTIAL")  # COMPLETE | RECEIVED | PARTIAL
    document_note = Column(Text, nullable=True)
    project = relationship("Project", back_populates="customer_orders")


class ProjectRequirement(Base):
    __tablename__ = "project_requirements"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    requirement_key = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    vda_code = Column(String(30), nullable=True)
    status = Column(String(30), nullable=False, default="TO_VERIFY")  # REQUIRED | TO_VERIFY | EXCLUDED
    source_kind = Column(String(40), nullable=False, default="DOCUMENT")
    source_ref = Column(String(180), nullable=True)
    source_date = Column(Date, nullable=True)
    quantity = Column(Float, nullable=True)
    procurement_mode = Column(String(40), nullable=False, default="UNKNOWN")
    confidence = Column(Float, nullable=False, default=1.0)
    note = Column(Text, nullable=True)
    project = relationship("Project", back_populates="requirements")


class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(120), nullable=False)
    contract_date = Column(Date, nullable=True)
    forecast_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)
    invoice_value = Column(Float, nullable=False, default=0)
    invoice_required = Column(Boolean, default=False)
    ld_applicable = Column(Boolean, default=False)
    ld_rate_weekly_pct = Column(Float, default=0)
    project = relationship("Project", back_populates="milestones")


class BudgetLine(Base):
    __tablename__ = "budget_lines"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    category = Column(String(120), nullable=False)
    budget = Column(Float, default=0)
    actual = Column(Float, default=0)
    committed = Column(Float, default=0)
    etc = Column(Float, default=0)
    etc_source = Column(String(30), default="MANUAL")
    project = relationship("Project", back_populates="budget_lines")


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    number = Column(String(60), nullable=False)
    milestone_name = Column(String(120), nullable=True)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    paid_amount = Column(Float, nullable=False, default=0)
    project = relationship("Project", back_populates="invoices")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    invoice_number = Column(String(60), nullable=False)
    payment_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    project = relationship("Project", back_populates="payments")


class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    owner = Column(String(120), nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(30), nullable=False, default="OPEN")
    source = Column(String(30), default="MANUAL")
    action_type = Column(String(30), nullable=False, default="VERIFY")  # VERIFY | DECISION | INTERVENTION
    priority = Column(String(20), nullable=False, default="NORMAL")  # NORMAL | HIGH | BLOCKING
    requester = Column(String(120), nullable=True)
    owner_kind = Column(String(20), nullable=False, default="USER")  # USER | DEPARTMENT
    response_summary = Column(Text, nullable=True)
    validated_by = Column(String(120), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    project = relationship("Project", back_populates="actions")
    messages = relationship("ActionMessage", cascade="all, delete-orphan", back_populates="action")


class ActionMessage(Base):
    __tablename__ = "action_messages"
    id = Column(Integer, primary_key=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False)
    author = Column(String(120), nullable=False)
    body = Column(Text, nullable=False)
    source = Column(String(30), nullable=False, default="MANUAL")
    created_at = Column(DateTime, default=utcnow)
    action = relationship("Action", back_populates="messages")


class Issue(Base):
    __tablename__ = "issues"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    category = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False, default="MEDIUM")
    status = Column(String(30), nullable=False, default="OPEN")
    blocking = Column(Boolean, default=False)
    due_date = Column(Date, nullable=True)
    source_ref = Column(String(180), nullable=True)
    project = relationship("Project", back_populates="issues")


class Communication(Base):
    __tablename__ = "communications"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    date = Column(Date, nullable=False)
    direction = Column(String(20), nullable=False)  # INBOUND / OUTBOUND
    sender = Column(String(160), nullable=False)
    recipient = Column(String(160), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    topic = Column(String(120), nullable=True)
    responded = Column(Boolean, default=True)
    reminders_count = Column(Integer, default=0)
    promised_date = Column(Date, nullable=True)
    source_ref = Column(String(160), nullable=True)
    project = relationship("Project", back_populates="communications")


class ChangeRequest(Base):
    __tablename__ = "change_requests"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    description = Column(String(255), nullable=False)
    requested_date = Column(Date, nullable=False)
    estimated_cost = Column(Float, default=0)
    quoted_value = Column(Float, default=0)
    order_received = Column(Boolean, default=False)
    work_started = Column(Boolean, default=False)
    source_ref = Column(String(180), nullable=True)
    project = relationship("Project", back_populates="changes")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_alert_fingerprint"),)
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    fingerprint = Column(String(220), nullable=False)
    alert_type = Column(String(60), nullable=False)
    dimension = Column(String(30), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="OPEN")
    source_kind = Column(String(40), nullable=False, default="RULE")
    source_ref = Column(String(180), nullable=True)
    confidence = Column(Float, nullable=True)
    data_status = Column(String(30), nullable=False, default="CALCULATED")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    project = relationship("Project", back_populates="alerts")


class AgentFinding(Base):
    __tablename__ = "agent_findings"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_agent_finding_fingerprint"),)
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    communication_id = Column(Integer, ForeignKey("communications.id"), nullable=True)
    fingerprint = Column(String(220), nullable=False)
    finding_type = Column(String(60), nullable=False)
    dimension = Column(String(30), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    extracted_date = Column(Date, nullable=True)
    extracted_amount = Column(Float, nullable=True)
    suggested_action = Column(String(255), nullable=False)
    suggested_owner = Column(String(120), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    status = Column(String(30), nullable=False, default="NEW")  # NEW | VALIDATED | DISMISSED | APPLIED
    source_ref = Column(String(180), nullable=True)
    applied_kind = Column(String(60), nullable=True)
    applied_ref = Column(String(120), nullable=True)
    applied_summary = Column(Text, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    project = relationship("Project", back_populates="agent_findings")
    communication = relationship("Communication")


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    engine = Column(String(80), nullable=False, default="LOCAL_DEMO_ENGINE")
    status = Column(String(30), nullable=False, default="COMPLETED")
    messages_analyzed = Column(Integer, nullable=False, default=0)
    findings_created = Column(Integer, nullable=False, default=0)
    findings_updated = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, default=utcnow)
    project = relationship("Project", back_populates="agent_runs")


class ProjectControlSnapshot(Base):
    __tablename__ = "project_control_snapshots"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    captured_at = Column(DateTime, nullable=False, default=utcnow)
    source_label = Column(String(160), nullable=False, default="GALILEO")
    baseline_budget = Column(Float, nullable=False, default=0)
    operational_budget = Column(Float, nullable=False, default=0)
    orders_jmrp = Column(Float, nullable=False, default=0)
    orders_extract = Column(Float, nullable=False, default=0)
    received = Column(Float, nullable=False, default=0)
    open_order_commitment = Column(Float, nullable=False, default=0)
    labor = Column(Float, nullable=False, default=0)
    overhead = Column(Float, nullable=False, default=0)
    note = Column(Text, nullable=True)
    project = relationship("Project", back_populates="control_snapshots")
    lines = relationship("ProjectControlLine", cascade="all, delete-orphan", back_populates="snapshot")


class ProjectControlLine(Base):
    __tablename__ = "project_control_lines"
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey("project_control_snapshots.id"), nullable=False)
    vda_code = Column(String(30), nullable=False)
    vda_name = Column(String(160), nullable=False)
    analysis_center = Column(String(80), nullable=False, default="COMM")
    baseline_budget = Column(Float, nullable=False, default=0)
    operational_budget = Column(Float, nullable=False, default=0)
    ordered = Column(Float, nullable=False, default=0)
    received = Column(Float, nullable=False, default=0)
    open_order_commitment = Column(Float, nullable=False, default=0)
    labor = Column(Float, nullable=False, default=0)
    overhead = Column(Float, nullable=False, default=0)
    purchases_closed = Column(Boolean, nullable=True)
    saving_confirmed = Column(Boolean, nullable=True)
    source_ref = Column(String(180), nullable=True)
    snapshot = relationship("ProjectControlSnapshot", back_populates="lines")


class ProjectSourceScan(Base):
    __tablename__ = "project_source_scans"
    __table_args__ = (UniqueConstraint("project_id", "source_type", name="uq_project_source_scan"),)
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    source_type = Column(String(30), nullable=False)  # GALILEO | DOCUMENT | OUTLOOK
    status = Column(String(30), nullable=False, default="NOT_CONFIGURED")
    file_count = Column(Integer, nullable=False, default=0)
    last_scanned_at = Column(DateTime, nullable=True)
    last_updated_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    project = relationship("Project", back_populates="source_scans")


class ProjectSourceFile(Base):
    __tablename__ = "project_source_files"
    __table_args__ = (UniqueConstraint("project_id", "source_type", "relative_path", name="uq_project_source_file"),)
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    source_type = Column(String(30), nullable=False)  # GALILEO | DOCUMENT | OUTLOOK
    file_name = Column(String(255), nullable=False)
    relative_path = Column(String(500), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    modified_at = Column(DateTime, nullable=False)
    sha256 = Column(String(64), nullable=False)
    first_seen_at = Column(DateTime, nullable=False, default=utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=utcnow)
    is_present = Column(Boolean, nullable=False, default=True)
    change_status = Column(String(20), nullable=False, default="NEW")  # NEW | UNCHANGED | MODIFIED | MISSING
    project = relationship("Project", back_populates="source_files")
    imports = relationship("ProjectSourceImport", back_populates="source_file")


class ProjectSourceImport(Base):
    """Outcome of a source processing attempt, reusable by every Source Center adapter."""

    __tablename__ = "project_source_imports"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    source_type = Column(String(30), nullable=False)  # GALILEO | DOCUMENT | OUTLOOK
    source_file_id = Column(Integer, ForeignKey("project_source_files.id"), nullable=True)
    source_hash = Column(String(64), nullable=False)
    processor = Column(String(120), nullable=False)
    status = Column(String(20), nullable=False)  # SUCCESS | ERROR
    processed_at = Column(DateTime, nullable=False, default=utcnow)
    error_message = Column(Text, nullable=True)
    project = relationship("Project", back_populates="source_imports")
    source_file = relationship("ProjectSourceFile", back_populates="imports")


class ProjectSourceContent(Base):
    __tablename__ = "project_source_contents"
    __table_args__ = (
        UniqueConstraint("project_id", "source_file_id", "source_hash", name="uq_project_source_content_version"),
    )
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    source_file_id = Column(Integer, ForeignKey("project_source_files.id"), nullable=False)
    source_hash = Column(String(64), nullable=False)
    content_kind = Column(String(20), nullable=False)  # DOCUMENT | EMAIL
    content_type = Column(String(40), nullable=False)
    extracted_text = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=False, default="{}")
    extracted_at = Column(DateTime, nullable=False, default=utcnow)
    project = relationship("Project", back_populates="source_contents")
    source_file = relationship("ProjectSourceFile")


class ProjectExtractedField(Base):
    __tablename__ = "project_extracted_fields"
    __table_args__ = (
        UniqueConstraint("project_id", "source_content_id", "field_key", name="uq_project_extracted_field"),
    )
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    source_content_id = Column(Integer, ForeignKey("project_source_contents.id"), nullable=False)
    field_key = Column(String(120), nullable=False)
    extracted_value = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    review_status = Column(String(20), nullable=False, default="NEW")  # NEW | CONFIRMED | CORRECTED | TO_VERIFY
    corrected_value = Column(Text, nullable=True)
    operational_value = Column(Text, nullable=True)
    source_ref = Column(String(220), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    project = relationship("Project", back_populates="extracted_fields")
    source_content = relationship("ProjectSourceContent")
