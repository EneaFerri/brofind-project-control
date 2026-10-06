from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath

from sqlalchemy.orm import Session

from .clock import utcnow
from .models import Project, ProjectSourceFile, ProjectSourceScan

SOURCE_DEFINITIONS = (
    ("GALILEO", "Galileo", "Galileo", {".xlsx"}),
    ("DOCUMENT", "Documenti", "Documenti", {".pdf", ".docx", ".xlsx"}),
    ("OUTLOOK", "Outlook", "Outlook", {".msg", ".eml"}),
)
SOURCE_LABELS = {source_type: label for source_type, label, _, _ in SOURCE_DEFINITIONS}
SOURCE_STATUS_LABELS = {
    "NOT_CONFIGURED": "Non configurato",
    "NO_FILES": "Nessun file",
    "AVAILABLE": "Disponibile",
    "UPDATED": "Aggiornato",
    "ERROR": "Errore",
}
FILE_STATUS_LABELS = {
    "NEW": "Nuovo",
    "UNCHANGED": "Invariato",
    "MODIFIED": "Modificato",
    "MISSING": "Non più presente",
}
IGNORED_SUFFIXES = {".tmp", ".temp", ".part"}


class SourceCenterError(ValueError):
    pass


@dataclass(frozen=True)
class SourceObservation:
    source_type: str
    file_name: str
    relative_path: str
    size_bytes: int
    modified_at: datetime
    sha256: str


@dataclass
class SourceDirectoryResult:
    source_type: str
    configured: bool
    observations: list[SourceObservation]
    error_message: str | None = None


@dataclass(frozen=True)
class GalileoImportCandidate:
    source_file: ProjectSourceFile
    content: bytes


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _safe_project_directory(source_root: Path, project_code: str) -> Path:
    if not project_code or project_code in {".", ".."} or any(part in project_code for part in ("/", "\\", "\x00")):
        raise SourceCenterError("Codice commessa non valido per le fonti.")
    root = source_root.resolve(strict=False)
    project_directory = (root / project_code).resolve(strict=False)
    if not _is_within(project_directory, root):
        raise SourceCenterError("Cartella commessa non valida per le fonti.")
    return project_directory


def _is_ignored(path: Path) -> bool:
    name = path.name
    if name.startswith((".", "~$")) or path.suffix.lower() in IGNORED_SUFFIXES:
        return True
    try:
        hidden_flag = getattr(__import__("stat"), "FILE_ATTRIBUTE_HIDDEN", 0)
        attributes = getattr(path.stat(), "st_file_attributes", 0)
        return bool(hidden_flag and attributes & hidden_flag)
    except OSError:
        return False


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _scan_source_directory(
    source_root: Path, project_directory: Path, source_type: str, folder_name: str, extensions: set[str]
) -> SourceDirectoryResult:
    directory = (project_directory / folder_name).resolve(strict=False)
    if not _is_within(directory, source_root) or not _is_within(directory, project_directory):
        return SourceDirectoryResult(source_type, False, [], "Cartella sorgente non valida.")
    if not directory.exists():
        return SourceDirectoryResult(source_type, False, [])
    if not directory.is_dir():
        return SourceDirectoryResult(source_type, False, [], "Il percorso sorgente non è una cartella.")

    observations: list[SourceObservation] = []
    try:
        for candidate in directory.iterdir():
            if _is_ignored(candidate) or candidate.suffix.lower() not in extensions:
                continue
            resolved = candidate.resolve(strict=False)
            if not _is_within(resolved, directory) or not _is_within(resolved, source_root) or not candidate.is_file():
                continue
            metadata = candidate.stat()
            observations.append(
                SourceObservation(
                    source_type=source_type,
                    file_name=candidate.name,
                    relative_path=resolved.relative_to(source_root).as_posix(),
                    size_bytes=metadata.st_size,
                    modified_at=datetime.fromtimestamp(metadata.st_mtime, tz=UTC).replace(tzinfo=None),
                    sha256=_hash_file(candidate),
                )
            )
    except OSError as exc:
        return SourceDirectoryResult(source_type, True, [], f"Impossibile leggere la cartella sorgente: {exc}")
    return SourceDirectoryResult(source_type, True, sorted(observations, key=lambda item: item.relative_path))


def scan_project_sources(project_code: str, source_root: Path) -> list[SourceDirectoryResult]:
    root = source_root.resolve(strict=False)
    project_directory = _safe_project_directory(root, project_code)
    return [
        _scan_source_directory(root, project_directory, source_type, folder_name, extensions)
        for source_type, _, folder_name, extensions in SOURCE_DEFINITIONS
    ]


def refresh_project_sources(
    db: Session, project: Project, source_root: Path, now: datetime | None = None
) -> list[SourceDirectoryResult]:
    now = now or utcnow()
    results = scan_project_sources(project.code, source_root)
    existing_files = {
        (item.source_type, item.relative_path): item
        for item in db.query(ProjectSourceFile).filter(ProjectSourceFile.project_id == project.id).all()
    }
    scans = {
        item.source_type: item
        for item in db.query(ProjectSourceScan).filter(ProjectSourceScan.project_id == project.id).all()
    }

    for result in results:
        scan = scans.get(result.source_type)
        if scan is None:
            scan = ProjectSourceScan(project_id=project.id, source_type=result.source_type)
            db.add(scan)
            scans[result.source_type] = scan
        scan.last_scanned_at = now
        scan.error_message = result.error_message

        if result.error_message:
            scan.status = "ERROR"
            continue

        observed_paths = set()
        changed = False
        for observed in result.observations:
            key = (observed.source_type, observed.relative_path)
            observed_paths.add(key)
            record = existing_files.get(key)
            if record is None:
                record = ProjectSourceFile(
                    project_id=project.id,
                    source_type=observed.source_type,
                    file_name=observed.file_name,
                    relative_path=observed.relative_path,
                    size_bytes=observed.size_bytes,
                    modified_at=observed.modified_at,
                    sha256=observed.sha256,
                    first_seen_at=now,
                    last_seen_at=now,
                    is_present=True,
                    change_status="NEW",
                )
                db.add(record)
                existing_files[key] = record
                changed = True
            else:
                record.change_status = "UNCHANGED" if record.sha256 == observed.sha256 else "MODIFIED"
                changed = changed or record.change_status == "MODIFIED" or not record.is_present
                record.file_name = observed.file_name
                record.size_bytes = observed.size_bytes
                record.modified_at = observed.modified_at
                record.sha256 = observed.sha256
                record.last_seen_at = now
                record.is_present = True

        for key, record in existing_files.items():
            if key[0] == result.source_type and key not in observed_paths and record.is_present:
                record.is_present = False
                record.change_status = "MISSING"
                changed = True

        scan.file_count = len(result.observations)
        if not result.configured:
            scan.status = "NOT_CONFIGURED"
        elif not result.observations:
            scan.status = "NO_FILES"
        elif changed:
            scan.status = "UPDATED"
        else:
            scan.status = "AVAILABLE"
        if changed:
            scan.last_updated_at = now
    return results


def _present_source_files(project: Project, source_type: str) -> list[ProjectSourceFile]:
    return sorted(
        [item for item in project.source_files if item.is_present and item.source_type == source_type],
        key=lambda item: item.file_name.lower(),
    )


def _safe_recorded_source_path(source_root: Path, project: Project, source_file: ProjectSourceFile) -> Path:
    if source_file.project_id != project.id or source_file.source_type != "GALILEO":
        raise SourceCenterError("File Galileo non valido per la commessa.")
    relative = PurePosixPath(source_file.relative_path)
    if relative.is_absolute() or not relative.parts or any(part in ("", ".", "..") for part in relative.parts):
        raise SourceCenterError("Percorso Galileo registrato non valido.")
    root = source_root.resolve(strict=False)
    project_directory = _safe_project_directory(root, project.code)
    galileo_directory = (project_directory / "Galileo").resolve(strict=False)
    if not _is_within(galileo_directory, root) or not _is_within(galileo_directory, project_directory):
        raise SourceCenterError("Cartella Galileo non valida.")
    candidate = (root.joinpath(*relative.parts)).resolve(strict=True)
    if not candidate.is_file() or not _is_within(candidate, galileo_directory) or not _is_within(candidate, root):
        raise SourceCenterError("File Galileo non disponibile nella cartella della commessa.")
    metadata = candidate.stat()
    if metadata.st_size != source_file.size_bytes or _hash_file(candidate) != source_file.sha256:
        raise SourceCenterError("Il file Galileo è cambiato dopo la scansione. Aggiorna fonti prima di importare.")
    return candidate


def resolve_source_file_content(project: Project, source_root: Path, source_file: ProjectSourceFile) -> bytes:
    folders = {"DOCUMENT": "Documenti", "OUTLOOK": "Outlook"}
    folder = folders.get(source_file.source_type)
    if source_file.project_id != project.id or folder is None:
        raise SourceCenterError("File sorgente non valido per la commessa.")
    relative = PurePosixPath(source_file.relative_path)
    if relative.is_absolute() or not relative.parts or any(part in ("", ".", "..") for part in relative.parts):
        raise SourceCenterError("Percorso sorgente registrato non valido.")
    root = source_root.resolve(strict=False)
    project_directory = _safe_project_directory(root, project.code)
    directory = (project_directory / folder).resolve(strict=False)
    candidate = (root.joinpath(*relative.parts)).resolve(strict=True)
    if not candidate.is_file() or not _is_within(candidate, directory) or not _is_within(candidate, root):
        raise SourceCenterError("File sorgente non disponibile nella cartella della commessa.")
    if candidate.stat().st_size != source_file.size_bytes or _hash_file(candidate) != source_file.sha256:
        raise SourceCenterError("Il file sorgente è cambiato dopo la scansione. Aggiorna fonti prima di leggere.")
    try:
        return candidate.read_bytes()
    except OSError as exc:
        raise SourceCenterError("Impossibile leggere il file sorgente selezionato.") from exc


def resolve_galileo_import_candidate(project: Project, source_root: Path) -> GalileoImportCandidate:
    files = _present_source_files(project, "GALILEO")
    if not files:
        raise SourceCenterError("Nessun file Galileo disponibile.")
    if len(files) > 1:
        raise SourceCenterError("Più file Galileo disponibili: rimuovi l'ambiguità prima di importare.")
    source_file = files[0]
    candidate = _safe_recorded_source_path(source_root, project, source_file)
    try:
        content = candidate.read_bytes()
    except OSError as exc:
        raise SourceCenterError("Impossibile leggere il file Galileo selezionato.") from exc
    return GalileoImportCandidate(source_file=source_file, content=content)


def _galileo_import_summary(project: Project, files: list[ProjectSourceFile], scan: ProjectSourceScan | None) -> dict:
    if not scan or scan.status == "NOT_CONFIGURED":
        return {
            "status": "NOT_CONFIGURED",
            "label": "Non configurato",
            "can_import": False,
            "last_imported_at": None,
            "last_imported_label": "Mai",
            "error_message": None,
        }
    if not files:
        return {
            "status": "NO_FILES",
            "label": "Nessun file Galileo disponibile",
            "can_import": False,
            "last_imported_at": None,
            "last_imported_label": "Mai",
            "error_message": None,
        }
    if len(files) > 1:
        return {
            "status": "AMBIGUOUS",
            "label": "Più file Galileo disponibili",
            "can_import": False,
            "last_imported_at": None,
            "last_imported_label": "Mai",
            "error_message": "Rimuovi l'ambiguità e aggiorna le fonti.",
        }

    current = files[0]
    matching = [
        item
        for item in project.source_imports
        if item.source_type == "GALILEO" and item.source_file_id == current.id and item.source_hash == current.sha256
    ]
    latest = max(matching, key=lambda item: (item.processed_at, item.id or 0)) if matching else None
    latest_success = max(
        (item for item in matching if item.status == "SUCCESS"),
        key=lambda item: (item.processed_at, item.id or 0),
        default=None,
    )
    last_imported_at = latest_success.processed_at if latest_success else None
    if latest and latest.status == "ERROR":
        status, label, error = "ERROR", "Errore import", latest.error_message
    elif latest_success:
        status, label, error = "IMPORTED", "Importato", None
    else:
        status, label, error = "AVAILABLE", "File disponibile", None
    return {
        "status": status,
        "label": label,
        "can_import": True,
        "last_imported_at": last_imported_at,
        "last_imported_label": last_imported_at.strftime("%d/%m/%Y %H:%M") if last_imported_at else "Mai",
        "error_message": error,
    }


def source_summary(project: Project) -> list[dict]:
    scans = {scan.source_type: scan for scan in project.source_scans}
    files_by_source = {
        source_type: _present_source_files(project, source_type) for source_type, _, _, _ in SOURCE_DEFINITIONS
    }
    summaries = []
    for source_type, label, _, _ in SOURCE_DEFINITIONS:
        scan = scans.get(source_type)
        files = files_by_source[source_type]
        status = scan.status if scan else "NOT_CONFIGURED"
        summary = {
            "type": source_type,
            "label": label,
            "status": status,
            "status_label": SOURCE_STATUS_LABELS[status],
            "file_count": len(files),
            "last_scanned_at": scan.last_scanned_at if scan else None,
            "last_scanned_label": scan.last_scanned_at.strftime("%d/%m/%Y %H:%M")
            if scan and scan.last_scanned_at
            else "Mai",
            "files": [
                {
                    "name": item.file_name,
                    "status": item.change_status,
                    "status_label": FILE_STATUS_LABELS[item.change_status],
                }
                for item in files
            ],
        }
        if source_type == "GALILEO":
            summary["import"] = _galileo_import_summary(project, files, scan)
        summaries.append(summary)
    return summaries


def source_update_message(summaries: Iterable[dict]) -> str:
    counts = {item["type"]: item["file_count"] for item in summaries}
    documents = counts.get("DOCUMENT", 0)
    document_label = "documento" if documents == 1 else "documenti"
    return (
        "Fonti aggiornate · "
        f"{counts.get('GALILEO', 0)} file Galileo · "
        f"{documents} {document_label} · "
        f"{counts.get('OUTLOOK', 0)} email"
    )
