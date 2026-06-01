import pytest

from app.core.config import Settings
from scripts.seed_local import SAMPLE_PREFIX, ensure_local_environment


def test_seed_local_guard_allows_local_environment() -> None:
    ensure_local_environment(Settings(app_env="local"))
    ensure_local_environment(Settings(app_env="dev"))
    ensure_local_environment(Settings(app_env="test"))


def test_seed_local_guard_rejects_non_local_without_force() -> None:
    with pytest.raises(RuntimeError, match="local/dev/test only"):
        ensure_local_environment(Settings(app_env="production"))


def test_seed_local_guard_can_be_forced() -> None:
    ensure_local_environment(Settings(app_env="production"), force=True)


def test_seed_local_sample_marker_is_explicit() -> None:
    assert SAMPLE_PREFIX == "[샘플]"
