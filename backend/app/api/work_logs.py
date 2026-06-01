import psycopg
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.errors import http_error
from app.api.security import require_report_access
from app.core.config import Settings, get_settings
from app.schemas.reports import WorkLogCreate, WorkLogItem, WorkLogUpdate
from app.services.work_logs import (
    WorkLogNotFoundError,
    WorkLogProjectNotFoundError,
    create_work_log,
    delete_work_log,
    get_work_log,
    list_work_logs,
    update_work_log,
)

router = APIRouter(prefix="/work-logs", tags=["work-logs"])


def _work_log_not_found() -> Exception:
    return http_error(status.HTTP_404_NOT_FOUND, "WORK_LOG_NOT_FOUND", "Work log was not found.")


def _project_not_found() -> Exception:
    return http_error(status.HTTP_404_NOT_FOUND, "PROJECT_NOT_FOUND", "Project was not found.")


@router.get("", response_model=list[WorkLogItem])
def get_work_logs(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    project_id: UUID | None = Query(default=None),
    owner_id: str = Depends(require_report_access),
    settings: Settings = Depends(get_settings),
) -> list[WorkLogItem]:
    if (start_date is None) != (end_date is None):
        raise http_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_PERIOD", "start_date and end_date must be provided together.")
    if start_date is not None and end_date is not None and end_date < start_date:
        raise http_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_PERIOD", "end_date must be on or after start_date.")
    try:
        return list_work_logs(settings, owner_id, start_date, end_date, project_id)
    except WorkLogProjectNotFoundError as exc:
        raise _project_not_found() from exc
    except psycopg.Error as exc:
        raise http_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc


@router.post("", response_model=WorkLogItem, status_code=status.HTTP_201_CREATED)
def post_work_log(
    payload: WorkLogCreate,
    owner_id: str = Depends(require_report_access),
    settings: Settings = Depends(get_settings),
) -> WorkLogItem:
    try:
        return create_work_log(settings, owner_id, payload)
    except WorkLogProjectNotFoundError as exc:
        raise _project_not_found() from exc
    except psycopg.Error as exc:
        raise http_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc


@router.get("/{work_log_id}", response_model=WorkLogItem)
def get_work_log_detail(
    work_log_id: UUID,
    owner_id: str = Depends(require_report_access),
    settings: Settings = Depends(get_settings),
) -> WorkLogItem:
    try:
        return get_work_log(settings, owner_id, work_log_id)
    except WorkLogNotFoundError as exc:
        raise _work_log_not_found() from exc
    except psycopg.Error as exc:
        raise http_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc


@router.patch("/{work_log_id}", response_model=WorkLogItem)
def patch_work_log(
    work_log_id: UUID,
    payload: WorkLogUpdate,
    owner_id: str = Depends(require_report_access),
    settings: Settings = Depends(get_settings),
) -> WorkLogItem:
    try:
        return update_work_log(settings, owner_id, work_log_id, payload)
    except WorkLogNotFoundError as exc:
        raise _work_log_not_found() from exc
    except WorkLogProjectNotFoundError as exc:
        raise _project_not_found() from exc
    except psycopg.Error as exc:
        raise http_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc


@router.delete("/{work_log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_log_detail(
    work_log_id: UUID,
    owner_id: str = Depends(require_report_access),
    settings: Settings = Depends(get_settings),
) -> Response:
    try:
        delete_work_log(settings, owner_id, work_log_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except WorkLogNotFoundError as exc:
        raise _work_log_not_found() from exc
    except psycopg.Error as exc:
        raise http_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc
