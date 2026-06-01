from uuid import UUID

from app.core.config import Settings
from app.db.connection import connect
from app.schemas.career_assets import CareerAsset


class CareerAssetProjectNotFoundError(Exception):
    pass


def list_project_career_assets(settings: Settings, owner_id: str, project_id: UUID) -> list[CareerAsset]:
    with connect(settings) as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE owner_id = %(owner_id)s AND id = %(project_id)s",
            {"owner_id": owner_id, "project_id": project_id},
        ).fetchone()
        if project is None:
            raise CareerAssetProjectNotFoundError()
        rows = connection.execute(
            """
            SELECT id::text,
                   project_id::text,
                   source_summary,
                   work_summary,
                   outcome_summary,
                   resume_bullets,
                   career_description,
                   portfolio_description,
                   star_answer,
                   markdown,
                   generation_method,
                   created_at::text,
                   updated_at::text
            FROM career_assets
            WHERE owner_id = %(owner_id)s AND project_id = %(project_id)s
            ORDER BY updated_at DESC, created_at DESC
            """,
            {"owner_id": owner_id, "project_id": project_id},
        ).fetchall()
    return [_career_asset_from_row(row) for row in rows]


def _career_asset_from_row(row) -> CareerAsset:
    return CareerAsset(
        id=row["id"],
        project_id=row["project_id"],
        source_summary=row.get("source_summary") or "",
        work_summary=row.get("work_summary") or "",
        outcome_summary=row.get("outcome_summary") or "",
        resume_bullets=row.get("resume_bullets") or "",
        career_description=row.get("career_description") or "",
        portfolio_description=row.get("portfolio_description") or "",
        star_answer=row.get("star_answer") or "",
        markdown=row.get("markdown") or "",
        generation_method=row.get("generation_method") or "template",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
