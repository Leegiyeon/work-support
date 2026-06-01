from datetime import date
from uuid import UUID

from app.core.config import Settings
from app.db.connection import connect
from app.schemas.reports import WorkLogCreate, WorkLogItem, WorkLogUpdate


class WorkLogNotFoundError(Exception):
    pass


class WorkLogProjectNotFoundError(Exception):
    pass


def create_work_log(settings: Settings, owner_id: str, payload: WorkLogCreate) -> WorkLogItem:
    if payload.project_id is not None:
        _ensure_project_owned(settings, owner_id, payload.project_id)

    with connect(settings) as connection:
        row = connection.execute(
            _WORK_LOG_INSERT_SQL,
            {
                "owner_id": owner_id,
                "project_id": payload.project_id,
                "log_date": payload.log_date,
                "work_type": payload.work_type,
                "title": payload.title,
                "content": payload.content,
                "decisions": payload.decisions,
                "collaborators": payload.collaborators,
                "next_actions": payload.next_actions,
                "duration_minutes": payload.duration_minutes,
                "blockers": payload.blockers,
            },
        ).fetchone()
        _touch_project(connection, owner_id, payload.project_id)

    return _work_log_item_from_row(row)


def list_work_logs(
    settings: Settings,
    owner_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    project_id: UUID | None = None,
) -> list[WorkLogItem]:
    if project_id is not None:
        _ensure_project_owned(settings, owner_id, project_id)

    with connect(settings) as connection:
        rows = connection.execute(
            _WORK_LOG_SELECT_SQL
            + """
            WHERE wl.owner_id = %(owner_id)s
              AND (%(project_id)s::uuid IS NULL OR wl.project_id = %(project_id)s::uuid)
              AND (%(start_date)s::date IS NULL OR wl.log_date >= %(start_date)s::date)
              AND (%(end_date)s::date IS NULL OR wl.log_date <= %(end_date)s::date)
            ORDER BY wl.log_date DESC, wl.updated_at DESC
            """,
            {"owner_id": owner_id, "start_date": start_date, "end_date": end_date, "project_id": project_id},
        ).fetchall()

    return [_work_log_item_from_row(row) for row in rows]


def get_work_log(settings: Settings, owner_id: str, work_log_id: UUID) -> WorkLogItem:
    with connect(settings) as connection:
        row = connection.execute(
            _WORK_LOG_SELECT_SQL
            + """
            WHERE wl.owner_id = %(owner_id)s AND wl.id = %(work_log_id)s
            """,
            {"owner_id": owner_id, "work_log_id": work_log_id},
        ).fetchone()

    if row is None:
        raise WorkLogNotFoundError()
    return _work_log_item_from_row(row)


def update_work_log(settings: Settings, owner_id: str, work_log_id: UUID, payload: WorkLogUpdate) -> WorkLogItem:
    existing = get_work_log(settings, owner_id, work_log_id)
    updates = payload.model_dump(exclude_unset=True)
    next_project_id = updates.get("project_id", UUID(existing.project_id) if existing.project_id else None)
    if next_project_id is not None:
        _ensure_project_owned(settings, owner_id, next_project_id)

    next_values = {
        "project_id": next_project_id,
        "log_date": updates.get("log_date", existing.log_date),
        "work_type": updates.get("work_type", existing.work_type),
        "title": updates.get("title", existing.title),
        "content": updates.get("content", existing.content),
        "decisions": updates.get("decisions", existing.decisions),
        "collaborators": updates.get("collaborators", existing.collaborators),
        "next_actions": updates.get("next_actions", existing.next_actions),
        "duration_minutes": updates.get("duration_minutes", existing.duration_minutes),
        "blockers": updates.get("blockers", existing.blockers),
    }

    with connect(settings) as connection:
        row = connection.execute(
            """
            UPDATE work_logs wl
            SET project_id = %(project_id)s,
                log_date = %(log_date)s,
                work_type = %(work_type)s,
                title = %(title)s,
                content = %(content)s,
                decisions = %(decisions)s,
                collaborators = %(collaborators)s,
                next_actions = %(next_actions)s,
                duration_minutes = %(duration_minutes)s,
                blockers = %(blockers)s,
                updated_at = now()
            WHERE wl.owner_id = %(owner_id)s AND wl.id = %(work_log_id)s
            RETURNING wl.id::text,
                      wl.log_date,
                      wl.work_type,
                      wl.title,
                      wl.content,
                      wl.decisions,
                      wl.collaborators,
                      wl.next_actions,
                      wl.duration_minutes,
                      wl.blockers,
                      wl.project_id::text,
                      '' AS project_title,
                      wl.updated_at::text
            """,
            {"owner_id": owner_id, "work_log_id": work_log_id, **next_values},
        ).fetchone()
        if row is None:
            raise WorkLogNotFoundError()
        _touch_project(connection, owner_id, UUID(existing.project_id) if existing.project_id else None)
        _touch_project(connection, owner_id, next_project_id)

    if row.get("project_id"):
        return get_work_log(settings, owner_id, UUID(row["id"]))
    return _work_log_item_from_row(row)


def delete_work_log(settings: Settings, owner_id: str, work_log_id: UUID) -> None:
    existing = get_work_log(settings, owner_id, work_log_id)
    with connect(settings) as connection:
        result = connection.execute(
            "DELETE FROM work_logs WHERE owner_id = %(owner_id)s AND id = %(work_log_id)s",
            {"owner_id": owner_id, "work_log_id": work_log_id},
        )
        if result.rowcount == 0:
            raise WorkLogNotFoundError()
        _touch_project(connection, owner_id, UUID(existing.project_id) if existing.project_id else None)


def _ensure_project_owned(settings: Settings, owner_id: str, project_id: UUID) -> None:
    with connect(settings) as connection:
        row = connection.execute(
            "SELECT id FROM projects WHERE owner_id = %(owner_id)s AND id = %(project_id)s",
            {"owner_id": owner_id, "project_id": project_id},
        ).fetchone()
    if row is None:
        raise WorkLogProjectNotFoundError()


def _touch_project(connection, owner_id: str, project_id: UUID | None) -> None:
    if project_id is None:
        return
    connection.execute(
        "UPDATE projects SET updated_at = now() WHERE owner_id = %(owner_id)s AND id = %(project_id)s",
        {"owner_id": owner_id, "project_id": project_id},
    )


def _work_log_item_from_row(row) -> WorkLogItem:
    return WorkLogItem(
        id=row["id"],
        log_date=row["log_date"],
        work_type=row.get("work_type") or "other",
        title=row["title"],
        content=row.get("content") or "",
        decisions=row.get("decisions") or "",
        collaborators=row.get("collaborators") or "",
        next_actions=row.get("next_actions") or "",
        duration_minutes=row.get("duration_minutes") or 0,
        blockers=row.get("blockers") or "",
        project_id=row.get("project_id"),
        project_title=row.get("project_title") or "",
        updated_at=row["updated_at"],
    )


_WORK_LOG_SELECT_SQL = """
            SELECT wl.id::text, wl.log_date, wl.work_type, wl.title, wl.content, wl.decisions,
                   wl.collaborators, wl.next_actions, wl.duration_minutes, wl.blockers,
                   wl.project_id::text, COALESCE(p.title, '') AS project_title, wl.updated_at::text
            FROM work_logs wl
            LEFT JOIN projects p ON p.id = wl.project_id AND p.owner_id = %(owner_id)s
"""

_WORK_LOG_INSERT_SQL = """
            INSERT INTO work_logs (
                owner_id, project_id, log_date, work_type, title, content, decisions,
                collaborators, next_actions, duration_minutes, blockers
            )
            VALUES (
                %(owner_id)s, %(project_id)s, %(log_date)s, %(work_type)s, %(title)s, %(content)s,
                %(decisions)s, %(collaborators)s, %(next_actions)s, %(duration_minutes)s, %(blockers)s
            )
            RETURNING id::text,
                      log_date,
                      work_type,
                      title,
                      content,
                      decisions,
                      collaborators,
                      next_actions,
                      duration_minutes,
                      blockers,
                      project_id::text,
                      '' AS project_title,
                      updated_at::text
"""
