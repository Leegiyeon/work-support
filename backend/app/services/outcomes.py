from decimal import Decimal
from uuid import UUID

from app.core.config import Settings
from app.db.connection import connect
from app.schemas.outcomes import ProjectOutcome, ProjectOutcomeCreate, ProjectOutcomeUpdate


class ProjectOutcomeNotFoundError(Exception):
    pass


class ProjectOutcomeProjectNotFoundError(Exception):
    pass


class ProjectOutcomeEvidenceError(Exception):
    pass


def list_project_outcomes(settings: Settings, owner_id: str, project_id: UUID) -> list[ProjectOutcome]:
    _ensure_project_owned(settings, owner_id, project_id)
    with connect(settings) as connection:
        rows = connection.execute(
            _OUTCOME_SELECT_SQL
            + """
            WHERE o.owner_id = %(owner_id)s AND o.project_id = %(project_id)s
            GROUP BY o.id
            ORDER BY o.updated_at DESC, o.title ASC
            """,
            {"owner_id": owner_id, "project_id": project_id},
        ).fetchall()
    return [_outcome_from_row(row) for row in rows]


def create_project_outcome(settings: Settings, owner_id: str, project_id: UUID, payload: ProjectOutcomeCreate) -> ProjectOutcome:
    _ensure_project_owned(settings, owner_id, project_id)
    _validate_metric(payload.outcome_type, payload.metric_value)
    _validate_evidence(settings, owner_id, project_id, payload.evidence_work_log_ids, payload.evidence_document_ids)
    with connect(settings) as connection:
        row = connection.execute(
            """
            INSERT INTO project_outcomes (
                owner_id, project_id, title, outcome_type, before_state, after_state,
                metric_name, metric_value, metric_unit, evidence_work_log_ids,
                evidence_document_ids, resume_ready
            )
            VALUES (
                %(owner_id)s, %(project_id)s, %(title)s, %(outcome_type)s, %(before_state)s,
                %(after_state)s, %(metric_name)s, %(metric_value)s, %(metric_unit)s,
                %(evidence_work_log_ids)s::uuid[], %(evidence_document_ids)s::uuid[], %(resume_ready)s
            )
            RETURNING id
            """,
            {
                "owner_id": owner_id,
                "project_id": project_id,
                "title": payload.title,
                "outcome_type": payload.outcome_type,
                "before_state": payload.before_state,
                "after_state": payload.after_state,
                "metric_name": payload.metric_name,
                "metric_value": payload.metric_value,
                "metric_unit": payload.metric_unit,
                "evidence_work_log_ids": payload.evidence_work_log_ids,
                "evidence_document_ids": payload.evidence_document_ids,
                "resume_ready": payload.resume_ready,
            },
        ).fetchone()
        _touch_project(connection, owner_id, project_id)
    return get_project_outcome(settings, owner_id, project_id, UUID(str(row["id"])))


def get_project_outcome(settings: Settings, owner_id: str, project_id: UUID, outcome_id: UUID) -> ProjectOutcome:
    with connect(settings) as connection:
        row = connection.execute(
            _OUTCOME_SELECT_SQL
            + """
            WHERE o.owner_id = %(owner_id)s AND o.project_id = %(project_id)s AND o.id = %(outcome_id)s
            GROUP BY o.id
            """,
            {"owner_id": owner_id, "project_id": project_id, "outcome_id": outcome_id},
        ).fetchone()
    if row is None:
        raise ProjectOutcomeNotFoundError()
    return _outcome_from_row(row)


def update_project_outcome(
    settings: Settings,
    owner_id: str,
    project_id: UUID,
    outcome_id: UUID,
    payload: ProjectOutcomeUpdate,
) -> ProjectOutcome:
    existing = get_project_outcome(settings, owner_id, project_id, outcome_id)
    updates = payload.model_dump(exclude_unset=True)
    next_values = {
        "title": updates.get("title", existing.title),
        "outcome_type": updates.get("outcome_type", existing.outcome_type),
        "before_state": updates.get("before_state", existing.before_state),
        "after_state": updates.get("after_state", existing.after_state),
        "metric_name": updates.get("metric_name", existing.metric_name),
        "metric_value": updates.get("metric_value", Decimal(existing.metric_value) if existing.metric_value is not None else None),
        "metric_unit": updates.get("metric_unit", existing.metric_unit),
        "evidence_work_log_ids": updates.get("evidence_work_log_ids", [UUID(value) for value in existing.evidence_work_log_ids]),
        "evidence_document_ids": updates.get("evidence_document_ids", [UUID(value) for value in existing.evidence_document_ids]),
        "resume_ready": updates.get("resume_ready", existing.resume_ready),
    }
    _validate_metric(next_values["outcome_type"], next_values["metric_value"])
    _validate_evidence(settings, owner_id, project_id, next_values["evidence_work_log_ids"], next_values["evidence_document_ids"])
    with connect(settings) as connection:
        row = connection.execute(
            """
            UPDATE project_outcomes
            SET title = %(title)s,
                outcome_type = %(outcome_type)s,
                before_state = %(before_state)s,
                after_state = %(after_state)s,
                metric_name = %(metric_name)s,
                metric_value = %(metric_value)s,
                metric_unit = %(metric_unit)s,
                evidence_work_log_ids = %(evidence_work_log_ids)s::uuid[],
                evidence_document_ids = %(evidence_document_ids)s::uuid[],
                resume_ready = %(resume_ready)s,
                updated_at = now()
            WHERE owner_id = %(owner_id)s AND project_id = %(project_id)s AND id = %(outcome_id)s
            RETURNING id
            """,
            {"owner_id": owner_id, "project_id": project_id, "outcome_id": outcome_id, **next_values},
        ).fetchone()
        if row is None:
            raise ProjectOutcomeNotFoundError()
        _touch_project(connection, owner_id, project_id)
    return get_project_outcome(settings, owner_id, project_id, outcome_id)


def delete_project_outcome(settings: Settings, owner_id: str, project_id: UUID, outcome_id: UUID) -> None:
    with connect(settings) as connection:
        result = connection.execute(
            """
            DELETE FROM project_outcomes
            WHERE owner_id = %(owner_id)s AND project_id = %(project_id)s AND id = %(outcome_id)s
            """,
            {"owner_id": owner_id, "project_id": project_id, "outcome_id": outcome_id},
        )
        if result.rowcount == 0:
            raise ProjectOutcomeNotFoundError()
        _touch_project(connection, owner_id, project_id)


def _ensure_project_owned(settings: Settings, owner_id: str, project_id: UUID) -> None:
    with connect(settings) as connection:
        row = connection.execute(
            "SELECT id FROM projects WHERE owner_id = %(owner_id)s AND id = %(project_id)s",
            {"owner_id": owner_id, "project_id": project_id},
        ).fetchone()
    if row is None:
        raise ProjectOutcomeProjectNotFoundError()


def _validate_metric(outcome_type: str, metric_value: Decimal | None) -> None:
    if outcome_type == "quantitative" and metric_value is None:
        raise ProjectOutcomeEvidenceError("quantitative outcomes require metric_value")


def _validate_evidence(
    settings: Settings,
    owner_id: str,
    project_id: UUID,
    work_log_ids: list[UUID],
    document_ids: list[UUID],
) -> None:
    with connect(settings) as connection:
        if work_log_ids:
            row = connection.execute(
                """
                SELECT COUNT(*)::int AS count
                FROM work_logs
                WHERE owner_id = %(owner_id)s
                  AND project_id = %(project_id)s
                  AND id = ANY(%(work_log_ids)s::uuid[])
                """,
                {"owner_id": owner_id, "project_id": project_id, "work_log_ids": work_log_ids},
            ).fetchone()
            if row["count"] != len(set(work_log_ids)):
                raise ProjectOutcomeEvidenceError("All evidence work logs must belong to the project.")
        if document_ids:
            row = connection.execute(
                """
                SELECT COUNT(*)::int AS count
                FROM documents
                WHERE owner_id = %(owner_id)s
                  AND project_id = %(project_id)s
                  AND id = ANY(%(document_ids)s::uuid[])
                """,
                {"owner_id": owner_id, "project_id": project_id, "document_ids": document_ids},
            ).fetchone()
            if row["count"] != len(set(document_ids)):
                raise ProjectOutcomeEvidenceError("All evidence documents must belong to the project.")


def _touch_project(connection, owner_id: str, project_id: UUID) -> None:
    connection.execute(
        "UPDATE projects SET updated_at = now() WHERE owner_id = %(owner_id)s AND id = %(project_id)s",
        {"owner_id": owner_id, "project_id": project_id},
    )


def _outcome_from_row(row) -> ProjectOutcome:
    return ProjectOutcome(
        id=row["id"],
        project_id=row["project_id"],
        title=row["title"],
        outcome_type=row["outcome_type"],
        before_state=row.get("before_state") or "",
        after_state=row.get("after_state") or "",
        metric_name=row.get("metric_name") or "",
        metric_value=row.get("metric_value"),
        metric_unit=row.get("metric_unit") or "",
        evidence_work_log_ids=[str(value) for value in row.get("evidence_work_log_ids") or []],
        evidence_document_ids=[str(value) for value in row.get("evidence_document_ids") or []],
        evidence_work_logs=row.get("evidence_work_logs") or [],
        resume_ready=row.get("resume_ready") or False,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


_OUTCOME_SELECT_SQL = """
            SELECT o.id::text,
                   o.project_id::text,
                   o.title,
                   o.outcome_type,
                   o.before_state,
                   o.after_state,
                   o.metric_name,
                   o.metric_value::text,
                   o.metric_unit,
                   o.evidence_work_log_ids,
                   o.evidence_document_ids,
                   o.resume_ready,
                   o.created_at::text,
                   o.updated_at::text,
                   COALESCE(
                     jsonb_agg(
                       jsonb_build_object('id', wl.id::text, 'title', wl.title, 'log_date', wl.log_date::text)
                       ORDER BY wl.log_date DESC, wl.updated_at DESC
                     ) FILTER (WHERE wl.id IS NOT NULL),
                     '[]'::jsonb
                   ) AS evidence_work_logs
            FROM project_outcomes o
            LEFT JOIN LATERAL unnest(o.evidence_work_log_ids) evidence_work_log_id(id) ON true
            LEFT JOIN work_logs wl
              ON wl.id = evidence_work_log_id.id
             AND wl.owner_id = %(owner_id)s
             AND wl.project_id = o.project_id
"""
