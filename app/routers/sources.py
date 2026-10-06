"""Source Center: aggiornamento fonti, import Galileo, lettura documenti/Outlook e review dei campi estratti."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..ai_analysis import analyze_project_sources, apply_reviewed_field
from ..b1_control_adapter import B1ImportError, import_b1_control_workbook
from ..config import settings
from ..db import get_db
from ..models import Project, ProjectExtractedField, ProjectSourceContent, ProjectSourceImport
from ..rules import recompute_alerts
from ..security import current_user, visible_projects_query
from ..source_center import (
    SourceCenterError,
    refresh_project_sources,
    resolve_galileo_import_candidate,
    resolve_source_file_content,
)
from ..source_readers import SourceReadError, read_source_content

router = APIRouter()


def _visible_project(db: Session, request: Request, code: str) -> Project:
    user = current_user(request, db)
    project = visible_projects_query(db, user).filter(Project.code == code).first()
    if not project:
        raise HTTPException(404, "Project not found or not visible")
    return project


@router.post("/project/{code}/sources/refresh")
def refresh_sources(code: str, request: Request, db: Session = Depends(get_db)):
    project = _visible_project(db, request, code)
    try:
        refresh_project_sources(db, project, settings.source_root)
        db.commit()
    except SourceCenterError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    anchor = "#sources-drawer" if project.control_snapshots else "#sources"
    return RedirectResponse(url=f"/project/{project.code}?sources_updated=1{anchor}", status_code=303)


@router.post("/project/{code}/sources/galileo/import")
def import_galileo_source(code: str, request: Request, db: Session = Depends(get_db)):
    project = _visible_project(db, request, code)

    candidate = None
    try:
        candidate = resolve_galileo_import_candidate(project, settings.source_root)
        import_b1_control_workbook(
            candidate.content,
            db,
            expected_project_code=project.code,
            commit=False,
        )
        db.add(
            ProjectSourceImport(
                project_id=project.id,
                source_type="GALILEO",
                source_file_id=candidate.source_file.id,
                source_hash=candidate.source_file.sha256,
                processor="B1_CONTROL_ADAPTER",
                status="SUCCESS",
            )
        )
        recompute_alerts(db)
    except Exception as exc:
        db.rollback()
        message = (
            str(exc) if isinstance(exc, (SourceCenterError, B1ImportError)) else "Errore durante l'import Galileo."
        )
        if candidate is not None:
            db.add(
                ProjectSourceImport(
                    project_id=project.id,
                    source_type="GALILEO",
                    source_file_id=candidate.source_file.id,
                    source_hash=candidate.source_file.sha256,
                    processor="B1_CONTROL_ADAPTER",
                    status="ERROR",
                    error_message=message,
                )
            )
            db.commit()
        return RedirectResponse(url=f"/project/{project.code}?galileo_import_error=1#sources", status_code=303)
    return RedirectResponse(url=f"/project/{project.code}?galileo_imported=1#sources-drawer", status_code=303)


def _read_project_source_type(project: Project, source_type: str, db: Session) -> tuple[int, int]:
    processed = errors = 0
    files = sorted(
        (item for item in project.source_files if item.is_present and item.source_type == source_type),
        key=lambda item: item.file_name.lower(),
    )
    for source_file in files:
        try:
            already_read = (
                db.query(ProjectSourceContent)
                .filter_by(project_id=project.id, source_file_id=source_file.id, source_hash=source_file.sha256)
                .first()
            )
            if already_read:
                continue
            parsed = read_source_content(
                resolve_source_file_content(project, settings.source_root, source_file),
                source_file.file_name,
                source_type,
            )
            db.add(
                ProjectSourceContent(
                    project_id=project.id,
                    source_file_id=source_file.id,
                    source_hash=source_file.sha256,
                    content_kind=parsed.content_kind,
                    content_type=parsed.content_type,
                    extracted_text=parsed.extracted_text,
                    metadata_json=parsed.metadata_json,
                )
            )
            db.add(
                ProjectSourceImport(
                    project_id=project.id,
                    source_type=source_type,
                    source_file_id=source_file.id,
                    source_hash=source_file.sha256,
                    processor="SOURCE_CONTENT_READER",
                    status="SUCCESS",
                )
            )
            processed += 1
        except Exception as exc:
            message = (
                str(exc)
                if isinstance(exc, (SourceCenterError, SourceReadError))
                else "Errore durante la lettura della fonte."
            )
            db.add(
                ProjectSourceImport(
                    project_id=project.id,
                    source_type=source_type,
                    source_file_id=source_file.id,
                    source_hash=source_file.sha256,
                    processor="SOURCE_CONTENT_READER",
                    status="ERROR",
                    error_message=message,
                )
            )
            errors += 1
    db.commit()
    return processed, errors


@router.post("/project/{code}/sources/{source_type}/read")
def read_source_type(code: str, source_type: str, request: Request, db: Session = Depends(get_db)):
    if source_type not in {"DOCUMENT", "OUTLOOK"}:
        raise HTTPException(404, "Source not supported")
    project = _visible_project(db, request, code)
    _read_project_source_type(project, source_type, db)
    anchor = "#sources-drawer" if project.control_snapshots else "#sources"
    return RedirectResponse(url=f"/project/{project.code}?source_read={source_type}{anchor}", status_code=303)


@router.post("/api/projects/{code}/extracted-fields")
def create_extracted_field(
    code: str,
    request: Request,
    source_content_id: int = Form(...),
    field_key: str = Form(...),
    extracted_value: str = Form(...),
    confidence: float = Form(0.0),
    source_ref: str = Form(""),
    db: Session = Depends(get_db),
):
    project = _visible_project(db, request, code)
    content = db.query(ProjectSourceContent).filter_by(id=source_content_id, project_id=project.id).one_or_none()
    if content is None:
        raise HTTPException(404, "Source content not found")
    field_key = field_key.strip()
    extracted_value = extracted_value.strip()
    if not field_key or not extracted_value or confidence < 0 or confidence > 1:
        raise HTTPException(400, "Invalid extracted field")
    field = (
        db.query(ProjectExtractedField)
        .filter_by(project_id=project.id, source_content_id=content.id, field_key=field_key)
        .one_or_none()
    )
    if field is None:
        field = ProjectExtractedField(
            project_id=project.id,
            source_content_id=content.id,
            field_key=field_key,
            extracted_value=extracted_value,
            confidence=confidence,
            source_ref=source_ref.strip() or f"source_content:{content.id}",
        )
        db.add(field)
        db.commit()
        db.refresh(field)
        created = True
    else:
        created = False
    return {
        "ok": True,
        "id": field.id,
        "created": created,
        "review_status": field.review_status,
        "operational_value": field.operational_value,
        "provenance": "EXTRACTED" if field.operational_value is None else "OPERATIONAL",
    }


@router.post("/api/extracted-fields/{field_id}/review")
def review_extracted_field(
    field_id: int,
    request: Request,
    status: str = Form(...),
    corrected_value: str = Form(""),
    return_to: str = Form(""),
    db: Session = Depends(get_db),
):
    user = current_user(request, db)
    field = db.query(ProjectExtractedField).filter_by(id=field_id).one_or_none()
    if field is None:
        raise HTTPException(404, "Extracted field not found")
    project = visible_projects_query(db, user).filter(Project.id == field.project_id).first()
    if project is None:
        raise HTTPException(403, "Not authorized")
    status = status.upper()
    if status not in {"CONFIRMED", "CORRECTED", "TO_VERIFY"}:
        raise HTTPException(400, "Invalid review status")
    corrected_value = corrected_value.strip()
    if status == "CORRECTED" and not corrected_value:
        raise HTTPException(400, "Corrected value is required")
    field.review_status = status
    field.corrected_value = corrected_value or None
    field.operational_value = (
        field.extracted_value if status == "CONFIRMED" else corrected_value if status == "CORRECTED" else None
    )
    apply_reviewed_field(field, db, user.display_name)
    db.commit()
    recompute_alerts(db)
    if return_to.startswith(f"/project/{project.code}"):
        return RedirectResponse(url=return_to, status_code=303)
    return {
        "ok": True,
        "id": field.id,
        "review_status": field.review_status,
        "operational_value": field.operational_value,
        "provenance": "OPERATIONAL" if field.operational_value is not None else "REVIEWED",
    }


@router.post("/project/{code}/ai/analyze")
def analyze_project_ai(code: str, request: Request, db: Session = Depends(get_db)):
    project = _visible_project(db, request, code)
    analyze_project_sources(project, db)
    anchor = "#ai-review" if project.control_snapshots else "#ai-analysis"
    return RedirectResponse(url=f"/project/{project.code}?ai_analyzed=1{anchor}", status_code=303)
