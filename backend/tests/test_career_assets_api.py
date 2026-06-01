from uuid import UUID

from fastapi.testclient import TestClient

from app.api import career_assets
from app.main import app
from app.schemas.career_assets import CareerAsset
from app.services.career_assets import CareerAssetProjectNotFoundError

HEADERS = {
    "X-Work-Support-Owner-Id": "local-owner",
    "X-Work-Support-Report-Token": "dev-only-report-token",
}
PROJECT_ID = "00000000-0000-0000-0000-000000000001"


def sample_asset() -> CareerAsset:
    return CareerAsset(
        id="00000000-0000-0000-0000-000000000301",
        project_id=PROJECT_ID,
        source_summary="업무 로그 2건",
        work_summary="업무 요약",
        outcome_summary="성과 요약",
        resume_bullets="- 이력서 문장",
        career_description="경력기술서",
        portfolio_description="포트폴리오",
        star_answer="STAR",
        markdown="## Career",
        generation_method="seed_template",
        created_at="2026-06-01 12:00:00+00",
        updated_at="2026-06-01 12:00:00+00",
    )


def test_career_asset_list_route_uses_owner_context(monkeypatch):
    calls = []

    def fake_list_project_career_assets(settings, owner_id, project_id):
        calls.append((owner_id, project_id))
        return [sample_asset()]

    monkeypatch.setattr(career_assets, "list_project_career_assets", fake_list_project_career_assets)
    client = TestClient(app)

    response = client.get(f"/projects/{PROJECT_ID}/career-assets", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()[0]["generation_method"] == "seed_template"
    assert calls == [("local-owner", UUID(PROJECT_ID))]


def test_career_asset_list_returns_project_not_found(monkeypatch):
    def fake_list_project_career_assets(settings, owner_id, project_id):
        raise CareerAssetProjectNotFoundError()

    monkeypatch.setattr(career_assets, "list_project_career_assets", fake_list_project_career_assets)
    client = TestClient(app)

    response = client.get(f"/projects/{PROJECT_ID}/career-assets", headers=HEADERS)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"
