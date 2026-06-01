import psycopg
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.api.errors import http_error
from app.api.security import require_report_access
from app.core.config import Settings, get_settings
from app.schemas.outcomes import ProjectOutcome, ProjectOutcomeCreate, ProjectOutcomeUpdate
from app.services.outcomes import (
    ProjectOutcomeEvidenceError,
    ProjectOutcomeNotFoundError,
    ProjectOutcomeProjectNotFoundError,
    create_project_outcome,
    delete_project_outcome,
    get_project_outcome,
    list_project_outcomes,
    update_project_outcome,
)

router = APIRouter(prefix="/projects/{project_id}/outcomes", tags=["project-outcomes"])


def _outcome_not_found() -> Exception:
    return http_error(status.HTTP_404_NOT_FOUND, "PROJECT_OUTCOME_NOT_FOUND", "Project outcome was not found.")


def _project_not_found() -> Exception:
    return http_error(status.HTTP_404_NOT_FOUND, "PROJECT_NOT_FOUND", "Project was not found.")


def _invalid_outcome(message: str) -> Exception:
    return http_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_PROJECT_OUTCOME", message)


@router.get("", response_model=list[ProjectOutcome])
def get_outcomes(
    project_id: UUID,
    owner_id: str = Depends(require_report_access),
    settings: Settings = Depends(get_settings),
) -> list[ProjectOutcome]:
    try:
        return list_project_outcomes(settings, owner_id, project_id)
    except ProjectOutcomeProjectNotFoundError as exc:
        raise _project_not_found() from exc
    except psycopg.Error as exc:
        raise http_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc


@router.post("", response_model=ProjectOutcome, status_code=status.HTTP_201_CREATED)
def post_outcome(
    project_id: UUID,
    payload: ProjectOutcomeCreate,
    owner_id: str = Depends(require_report_access),
    settings: Settings = Depends(get_settings),
) -> ProjectOutcome:
    try:
        return create_project_outcome(settings, owner_id, project_id, payload)
    except ProjectOutcomeProjectNotFoundError as exc:
        raise _project_not_found() from exc
    except ProjectOutcomeEvidenceError as exc:
        raise _invalid_outcome(str(exc)) from exc
    except psycopg.Error as exc:
        raise http_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc


@router.get("/{outcome_id}", response_model=ProjectOutcome)
def get_outcome_detail(
    project_id: UUID,
    outcome_id: UUID,
    owner_id: str = Depends(require_report_access),
    settings: Settings = Depends(get_settings),
) -> ProjectOutcome:
    try:
        return get_project_outcome(settings, owner_id, project_id, outcome_id)
    except ProjectOutcomeNotFoundError as exc:
        raise _outcome_not_found() from exc
    except psycopg.Error as exc:
        raise http_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc


@router.patch("/{outcome_id}", response_model=ProjectOutcome)
def patch_outcome(
    project_id: UUID,
    outcome_id: UUID,
    payload: ProjectOutcomeUpdate,
    owner_id: str = Depends(require_report_access),
    settings: Settings = Depends(get_settings),
) -> ProjectOutcome:
    try:
        return update_project_outcome(settings, owner_id, project_id, outcome_id, payload)
    except ProjectOutcomeNotFoundError as exc:
        raise _outcome_not_found() from exc
    except ProjectOutcomeProjectNotFoundError as exc:
        raise _project_not_found() from exc
    except ProjectOutcomeEvidenceError as exc:
        raise _invalid_outcome(str(exc)) from exc
    except psycopg.Error as exc:
        raise http_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc


@router.delete("/{outcome_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_outcome(
    project_id: UUID,
    outcome_id: UUID,
    owner_id: str = Depends(require_report_access),
    settings: Settings = Depends(get_settings),
) -> Response:
    try:
        delete_project_outcome(settings, owner_id, project_id, outcome_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ProjectOutcomeNotFoundError as exc:
        raise _outcome_not_found() from exc
    except psycopg.Error as exc:
        raise http_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc
