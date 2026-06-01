from pathlib import Path

from app.core.config import Settings
from app.db.connection import connect

SCHEMA_SQL_FILENAME = "002_work_support_schema.sql"
DOCKER_SCHEMA_SQL_PATH = Path("/app/infrastructure/postgres/init") / SCHEMA_SQL_FILENAME


def _candidate_schema_paths(settings: Settings) -> list[Path]:
    candidates: list[Path] = []
    if settings.work_support_schema_sql_path:
        candidates.append(Path(settings.work_support_schema_sql_path).expanduser())

    repo_root = Path(__file__).resolve().parents[3]
    candidates.extend(
        [
            DOCKER_SCHEMA_SQL_PATH,
            repo_root / "infrastructure" / "postgres" / "init" / SCHEMA_SQL_FILENAME,
            Path.cwd() / "infrastructure" / "postgres" / "init" / SCHEMA_SQL_FILENAME,
        ]
    )
    return candidates


def resolve_schema_sql_path(settings: Settings) -> Path:
    """Find the canonical SQL file used by both Docker bootstrap and local init."""

    for candidate in _candidate_schema_paths(settings):
        if candidate.is_file():
            return candidate

    checked = ", ".join(str(path) for path in _candidate_schema_paths(settings))
    raise FileNotFoundError(f"Canonical schema SQL file not found. Checked: {checked}")


def load_schema_sql(settings: Settings) -> str:
    """Load the canonical application schema SQL without duplicating DDL in Python."""

    return resolve_schema_sql_path(settings).read_text(encoding="utf-8")


def init_schema(settings: Settings) -> None:
    """Create the minimum MVP tables used by the weekly report feature."""

    with connect(settings, row_factory=None) as connection:
        connection.execute(load_schema_sql(settings))
