from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from uuid import UUID

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import Settings, get_settings
from app.db.connection import connect
from app.db.schema import init_schema

LOCAL_ENVS = {"local", "dev", "development", "test"}
SAMPLE_PREFIX = "[샘플]"


@dataclass(frozen=True)
class SeedResult:
    projects: int
    tasks: int
    work_logs: int
    outcomes: int
    career_assets: int


def ensure_local_environment(settings: Settings, *, force: bool = False) -> None:
    if force:
        return
    if settings.app_env.lower() not in LOCAL_ENVS:
        raise RuntimeError(
            "seed_local.py is local/dev/test only. "
            "Set APP_ENV=local or pass --force if you intentionally seed this database."
        )


def seed(settings: Settings, *, owner_id: str | None = None, reset: bool = True, force: bool = False) -> SeedResult:
    ensure_local_environment(settings, force=force)
    init_schema(settings)
    seed_owner = owner_id or settings.default_owner_id
    today = date.today()

    with connect(settings) as connection:
        if reset:
            _delete_existing_sample_data(connection, seed_owner)

        automation_project_id = _insert_project(
            connection,
            seed_owner,
            title="[샘플] 업무 자동화 플랫폼 MVP",
            description="샘플 데이터: 파일 기반 업무 기록, 진척도, 성과, 경력 자산화 흐름을 검증하는 프로젝트입니다.",
            status="in_progress",
            role="PM/업무 자동화 기획",
        )
        reporting_project_id = _insert_project(
            connection,
            seed_owner,
            title="[샘플] 주간 리포트 운영 정리",
            description="샘플 데이터: 업무 로그 기반 주간 리포트와 다음 액션 정리 흐름을 확인하는 프로젝트입니다.",
            status="review",
            role="운영 기획/리포트 담당",
        )

        task_count = 0
        for project_id, tasks in {
            automation_project_id: [
                ("[샘플] 프로젝트/업무 CRUD 점검", "화면에서 프로젝트와 업무를 만들고 수정할 수 있는지 확인", "done", "high", today - timedelta(days=3)),
                ("[샘플] 업무 로그 입력 흐름 정리", "수행 내용, 판단, 다음 액션 필드가 경력 근거로 충분한지 확인", "in_progress", "high", today + timedelta(days=1)),
                ("[샘플] 개선 성과 카드 검증", "정량/정성 성과와 근거 업무 로그 연결 확인", "planned", "medium", today + timedelta(days=3)),
                ("[샘플] 경력 자산 문장 검토", "샘플 경력 문장이 과장 없이 생성/저장되는지 확인", "planned", "medium", today + timedelta(days=5)),
            ],
            reporting_project_id: [
                ("[샘플] 이번 주 로그 입력", "기간별 업무 로그가 리포트에 반영되는지 확인", "done", "medium", today - timedelta(days=1)),
                ("[샘플] 리포트 Markdown 복사 확인", "주간 리포트 화면에서 Markdown 출력과 복사 버튼 확인", "in_progress", "medium", today + timedelta(days=2)),
                ("[샘플] 다음 주 확인사항 정리", "잔여 업무와 지연 업무를 다음 액션으로 정리", "on_hold", "low", today + timedelta(days=7)),
            ],
        }.items():
            for title, description, status, priority, due_date in tasks:
                _insert_task(connection, seed_owner, project_id, title, description, status, priority, due_date)
                task_count += 1

        work_logs = [
            (automation_project_id, today - timedelta(days=5), "planning", "[샘플] MVP 범위 재정리", "프로젝트 진척도, 업무 로그, 성과 수치화, 경력 자산화를 v0.1 핵심 흐름으로 정리했다.", "AI 기능보다 수동 기록을 먼저 안정화하기로 결정했다.", "개인 사용자", "업무 로그와 성과 입력 화면을 확인한다.", 90, ""),
            (automation_project_id, today - timedelta(days=4), "development", "[샘플] 프로젝트 업무 상태 점검", "예정/진행/완료/보류 상태와 완료율 계산을 화면에서 확인했다.", "완료율은 완료 업무 수 / 전체 업무 수 기준으로 유지한다.", "", "잔여 업무 카운트를 대시보드에서 확인한다.", 120, ""),
            (automation_project_id, today - timedelta(days=3), "problem_solving", "[샘플] 성과 근거 필드 설계", "성과 수치를 사용자가 직접 입력하고 업무 로그를 근거로 연결하는 방식을 정리했다.", "AI가 임의 수치를 만들지 않도록 수치 입력은 사용자 확정값만 사용한다.", "", "정성 성과와 정량 성과를 분리해 등록한다.", 80, ""),
            (reporting_project_id, today - timedelta(days=2), "reporting", "[샘플] 주간 리포트 구성 확인", "프로젝트별 진행 현황과 다음 확인 사항을 Markdown으로 정리하는 흐름을 점검했다.", "리포트는 메일 발송 없이 앱 내부 생성과 복사까지만 제공한다.", "팀 리드", "다음 주 확인사항을 업무로 전환할지 검토한다.", 60, ""),
            (reporting_project_id, today - timedelta(days=1), "coordination", "[샘플] 리포트 공유 방식 협의", "리포트 Markdown을 복사해 메신저/문서에 붙여넣는 방식을 테스트했다.", "외부 서비스 연동은 v0.1 이후로 미룬다.", "운영 담당", "복사된 Markdown의 가독성을 확인한다.", 45, ""),
            (automation_project_id, today, "testing", "[샘플] 로컬 seed 데이터 검증", "샘플 프로젝트, 업무, 업무 로그, 성과, 경력 자산이 한 번에 생성되는지 확인했다.", "샘플 데이터는 제목에 [샘플]을 붙여 운영 데이터와 구분한다.", "", "대시보드에서 샘플 프로젝트가 보이는지 확인한다.", 40, ""),
        ]
        work_log_ids: list[UUID] = []
        for work_log in work_logs:
            work_log_ids.append(_insert_work_log(connection, seed_owner, *work_log))

        outcome_ids = [
            _insert_outcome(
                connection,
                seed_owner,
                automation_project_id,
                title="[샘플] 업무 상태 확인 시간 단축",
                outcome_type="quantitative",
                before_state="프로젝트별 잔여 업무를 수동으로 확인해야 했다.",
                after_state="대시보드에서 잔여 업무와 완료율을 즉시 확인할 수 있다.",
                metric_name="주간 상태 확인 소요 시간",
                metric_value="30",
                metric_unit="분 절감(샘플)",
                evidence_work_log_ids=[work_log_ids[1], work_log_ids[5]],
                resume_ready=True,
            ),
            _insert_outcome(
                connection,
                seed_owner,
                reporting_project_id,
                title="[샘플] 주간 공유 자료 정리 방식 표준화",
                outcome_type="qualitative",
                before_state="프로젝트별 진행 내용과 다음 액션이 여러 메모에 흩어져 있었다.",
                after_state="업무 로그와 리포트 Markdown으로 주간 공유 자료를 한곳에서 정리할 수 있다.",
                metric_name="",
                metric_value=None,
                metric_unit="",
                evidence_work_log_ids=[work_log_ids[3], work_log_ids[4]],
                resume_ready=True,
            ),
        ]

        _insert_career_asset(
            connection,
            seed_owner,
            automation_project_id,
            source_summary="샘플 경력 자산: 업무 로그 4건과 정량 성과 1건을 근거로 작성했습니다.",
            work_summary="프로젝트/업무 관리 흐름을 정의하고, 상태값과 완료율 계산 기준을 점검했으며, 성과 수치 입력 원칙을 정리했다.",
            outcome_summary="주간 상태 확인 소요 시간을 30분 절감할 수 있는 구조를 샘플 기준으로 확인했다. 이 수치는 샘플 데이터이며 운영 성과와 구분된다.",
            resume_bullets="- [샘플] 프로젝트별 업무 상태와 잔여 업무를 관리하는 로컬 MVP 흐름을 기획하고 검증\n- [샘플] 사용자가 확정한 수치만 성과로 반영하도록 성과 관리 기준을 정리",
            career_description="[샘플] 업무 자동화 플랫폼 MVP에서 PM/업무 자동화 기획 역할로 프로젝트 생성, 업무 상태 관리, 업무 로그, 성과 기록 흐름을 정리했다. AI가 임의 수치를 만들지 않도록 수치 성과는 사용자 확정값과 근거 업무 로그를 기준으로 관리하는 방향을 설계했다.",
            portfolio_description="[샘플] 개인 업무 관리와 경력 자산화를 연결하기 위한 로컬 MVP입니다. 프로젝트별 업무 상태, 잔여 업무, 업무 로그, 개선 성과를 한 흐름에서 확인할 수 있게 구성했습니다.",
            star_answer="Situation: [샘플] 프로젝트 진행 상황과 성과 근거가 여러 메모에 흩어져 있었습니다.\nTask: 개인 업무 관리에 필요한 최소 흐름을 한 서비스에서 확인할 수 있게 정리해야 했습니다.\nAction: 프로젝트/업무 상태, 업무 로그, 성과 입력 기준을 나누고 샘플 데이터로 흐름을 검증했습니다.\nResult: 샘플 기준으로 잔여 업무와 완료율, 성과 근거를 한 화면 흐름에서 확인할 수 있는 기반을 마련했습니다.",
        )
        _insert_career_asset(
            connection,
            seed_owner,
            reporting_project_id,
            source_summary="샘플 경력 자산: 업무 로그 2건과 정성 성과 1건을 근거로 작성했습니다.",
            work_summary="주간 리포트 구성과 Markdown 복사 흐름을 확인하고, 외부 연동 없이 앱 내부에서 공유 자료를 만들 수 있는 방식을 정리했다.",
            outcome_summary="정량 수치 없이, 흩어진 진행 내용과 다음 액션을 한 Markdown 리포트로 정리하는 정성 개선을 기록했다.",
            resume_bullets="- [샘플] 업무 로그 기반 주간 리포트 흐름을 정리하고 Markdown 공유 방식을 검증\n- [샘플] 외부 연동 없이 로컬 앱 내부에서 진행 현황과 다음 액션을 정리하는 운영 방식을 제안",
            career_description="[샘플] 주간 리포트 운영 정리 프로젝트에서 업무 로그와 프로젝트 상태를 기반으로 공유 가능한 Markdown 리포트 흐름을 검토했다. 수치가 없는 개선은 임의 수치를 만들지 않고 정성 성과로 분리해 기록했다.",
            portfolio_description="[샘플] 프로젝트별 업무 로그를 주간 리포트로 연결해 개인 업무 회고와 공유 자료 작성을 돕는 운영 흐름입니다.",
            star_answer="Situation: [샘플] 주간 진행 상황과 다음 액션이 분산되어 있었습니다.\nTask: 한 주의 업무 기록을 프로젝트별로 정리해 공유 가능한 형태로 만들어야 했습니다.\nAction: 업무 로그, 결정사항, 다음 액션을 Markdown 리포트 구조로 정리하고 복사 흐름을 확인했습니다.\nResult: 수치가 없는 개선은 정성 성과로 기록하면서도, 주간 공유 자료를 일관된 형식으로 만들 수 있는 샘플 흐름을 확보했습니다.",
        )

    return SeedResult(projects=2, tasks=task_count, work_logs=len(work_logs), outcomes=len(outcome_ids), career_assets=2)


def _delete_existing_sample_data(connection, owner_id: str) -> None:
    sample_project_ids = connection.execute(
        "SELECT id FROM projects WHERE owner_id = %(owner_id)s AND title LIKE %(prefix)s",
        {"owner_id": owner_id, "prefix": f"{SAMPLE_PREFIX}%"},
    ).fetchall()
    project_ids = [row["id"] for row in sample_project_ids]
    if not project_ids:
        return
    connection.execute(
        "DELETE FROM career_assets WHERE owner_id = %(owner_id)s AND project_id = ANY(%(project_ids)s::uuid[])",
        {"owner_id": owner_id, "project_ids": project_ids},
    )
    connection.execute(
        "DELETE FROM project_outcomes WHERE owner_id = %(owner_id)s AND project_id = ANY(%(project_ids)s::uuid[])",
        {"owner_id": owner_id, "project_ids": project_ids},
    )
    connection.execute(
        "DELETE FROM project_tasks WHERE owner_id = %(owner_id)s AND project_id = ANY(%(project_ids)s::uuid[])",
        {"owner_id": owner_id, "project_ids": project_ids},
    )
    connection.execute(
        "DELETE FROM work_logs WHERE owner_id = %(owner_id)s AND project_id = ANY(%(project_ids)s::uuid[])",
        {"owner_id": owner_id, "project_ids": project_ids},
    )
    connection.execute(
        "DELETE FROM projects WHERE owner_id = %(owner_id)s AND id = ANY(%(project_ids)s::uuid[])",
        {"owner_id": owner_id, "project_ids": project_ids},
    )


def _insert_project(connection, owner_id: str, *, title: str, description: str, status: str, role: str) -> UUID:
    row = connection.execute(
        """
        INSERT INTO projects (owner_id, title, description, status, role)
        VALUES (%(owner_id)s, %(title)s, %(description)s, %(status)s, %(role)s)
        RETURNING id
        """,
        {"owner_id": owner_id, "title": title, "description": description, "status": status, "role": role},
    ).fetchone()
    return row["id"]


def _insert_task(connection, owner_id: str, project_id: UUID, title: str, description: str, status: str, priority: str, due_date: date) -> None:
    connection.execute(
        """
        INSERT INTO project_tasks (owner_id, project_id, title, description, status, priority, due_date)
        VALUES (%(owner_id)s, %(project_id)s, %(title)s, %(description)s, %(status)s, %(priority)s, %(due_date)s)
        """,
        {
            "owner_id": owner_id,
            "project_id": project_id,
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "due_date": due_date,
        },
    )


def _insert_work_log(
    connection,
    owner_id: str,
    project_id: UUID,
    log_date: date,
    work_type: str,
    title: str,
    content: str,
    decisions: str,
    collaborators: str,
    next_actions: str,
    duration_minutes: int,
    blockers: str,
) -> UUID:
    row = connection.execute(
        """
        INSERT INTO work_logs (
            owner_id, project_id, log_date, work_type, title, content, decisions,
            collaborators, next_actions, duration_minutes, blockers
        )
        VALUES (
            %(owner_id)s, %(project_id)s, %(log_date)s, %(work_type)s, %(title)s, %(content)s,
            %(decisions)s, %(collaborators)s, %(next_actions)s, %(duration_minutes)s, %(blockers)s
        )
        RETURNING id
        """,
        {
            "owner_id": owner_id,
            "project_id": project_id,
            "log_date": log_date,
            "work_type": work_type,
            "title": title,
            "content": content,
            "decisions": decisions,
            "collaborators": collaborators,
            "next_actions": next_actions,
            "duration_minutes": duration_minutes,
            "blockers": blockers,
        },
    ).fetchone()
    return row["id"]


def _insert_outcome(
    connection,
    owner_id: str,
    project_id: UUID,
    *,
    title: str,
    outcome_type: str,
    before_state: str,
    after_state: str,
    metric_name: str,
    metric_value: str | None,
    metric_unit: str,
    evidence_work_log_ids: list[UUID],
    resume_ready: bool,
) -> UUID:
    row = connection.execute(
        """
        INSERT INTO project_outcomes (
            owner_id, project_id, title, outcome_type, before_state, after_state,
            metric_name, metric_value, metric_unit, evidence_work_log_ids, resume_ready
        )
        VALUES (
            %(owner_id)s, %(project_id)s, %(title)s, %(outcome_type)s, %(before_state)s,
            %(after_state)s, %(metric_name)s, %(metric_value)s, %(metric_unit)s,
            %(evidence_work_log_ids)s::uuid[], %(resume_ready)s
        )
        RETURNING id
        """,
        {
            "owner_id": owner_id,
            "project_id": project_id,
            "title": title,
            "outcome_type": outcome_type,
            "before_state": before_state,
            "after_state": after_state,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "metric_unit": metric_unit,
            "evidence_work_log_ids": evidence_work_log_ids,
            "resume_ready": resume_ready,
        },
    ).fetchone()
    return row["id"]


def _insert_career_asset(
    connection,
    owner_id: str,
    project_id: UUID,
    *,
    source_summary: str,
    work_summary: str,
    outcome_summary: str,
    resume_bullets: str,
    career_description: str,
    portfolio_description: str,
    star_answer: str,
) -> UUID:
    markdown = "\n\n".join(
        [
            "## 수행 업무 요약\n" + work_summary,
            "## 성과 요약\n" + outcome_summary,
            "## 이력서 문장\n" + resume_bullets,
            "## 경력기술서\n" + career_description,
            "## 포트폴리오 설명\n" + portfolio_description,
            "## 면접 STAR\n" + star_answer,
        ]
    )
    row = connection.execute(
        """
        INSERT INTO career_assets (
            owner_id, project_id, source_summary, work_summary, outcome_summary,
            resume_bullets, career_description, portfolio_description, star_answer,
            markdown, generation_method
        )
        VALUES (
            %(owner_id)s, %(project_id)s, %(source_summary)s, %(work_summary)s, %(outcome_summary)s,
            %(resume_bullets)s, %(career_description)s, %(portfolio_description)s, %(star_answer)s,
            %(markdown)s, 'seed_template'
        )
        RETURNING id
        """,
        {
            "owner_id": owner_id,
            "project_id": project_id,
            "source_summary": source_summary,
            "work_summary": work_summary,
            "outcome_summary": outcome_summary,
            "resume_bullets": resume_bullets,
            "career_description": career_description,
            "portfolio_description": portfolio_description,
            "star_answer": star_answer,
            "markdown": markdown,
        },
    ).fetchone()
    return row["id"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed local-only sample work-support data.")
    parser.add_argument("--owner-id", default=None, help="Owner id for the sample data. Defaults to DEFAULT_OWNER_ID.")
    parser.add_argument("--no-reset", action="store_true", help="Append another sample set instead of replacing existing [샘플] data.")
    parser.add_argument("--force", action="store_true", help="Allow seeding even when APP_ENV is not local/dev/test.")
    args = parser.parse_args()

    result = seed(get_settings(), owner_id=args.owner_id, reset=not args.no_reset, force=args.force)
    print("work-support local sample data seeded")
    print(f"- projects: {result.projects}")
    print(f"- tasks: {result.tasks}")
    print(f"- work_logs: {result.work_logs}")
    print(f"- project_outcomes: {result.outcomes}")
    print(f"- career_assets: {result.career_assets}")
    print(f"- marker: {SAMPLE_PREFIX} (local/dev sample data)")


if __name__ == "__main__":
    main()
