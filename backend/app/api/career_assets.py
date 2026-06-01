import psycopg
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.errors import http_error
from app.api.security import require_report_access
from app.core.config import Settings, get_settings
from app.schemas.career_assets import CareerAsset
from app.services.career_assets import CareerAssetProjectNotFoundError, list_project_career_assets

router = APIRouter(prefix="/projects/{project_id}/career-assets", tags=["career-assets"])


@router.get("", response_model=list[CareerAsset])
def get_career_assets(
    project_id: UUID,
    owner_id: str = Depends(require_report_access),
    settings: Settings = Depends(get_settings),
) -> list[CareerAsset]:
    try:
        return list_project_career_assets(settings, owner_id, project_id)
    except CareerAssetProjectNotFoundError as exc:
        raise http_error(status.HTTP_404_NOT_FOUND, "PROJECT_NOT_FOUND", "Project was not found.") from exc
    except psycopg.Error as exc:
        raise http_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc
