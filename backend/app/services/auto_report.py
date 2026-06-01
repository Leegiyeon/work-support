from __future__ import annotations

from collections import defaultdict
from datetime import date

from app.schemas.reports import (
    AutoReportResponse,
    MonthlyPerformanceCandidate,
    ProjectProgressCandidate,
    ProjectWeeklyReport,
    ReportType,
    TaskAlert,
    WorkLogItem,
)
from app.services.weekly_report import (
    DONE_STATUSES,
    WeeklyReportDataset,
    _work_log_to_schema,
    build_weekly_report_response,
)

STATUS_PROGRESS = {
    "idea": 10,
    "review": 30,
    "in_progress": 60,
    "on_hold": 40,
    "done": 100,
}

REPORT_TITLES = {
    "daily": "일일 업무 요약",
    "weekly": "주간 업무 리포트",
    "monthly": "월간 성과 후보 리포트",
}


def build_auto_report_response(
    dataset: WeeklyReportDataset,
    report_type: ReportType,
    start_date: date,
    end_date: date,
) -> AutoReportResponse:
    weekly = build_weekly_report_response(dataset, start_date, end_date)
    work_logs = [_work_log_to_schema(work_log) for work_log in dataset.work_logs]
    remaining_tasks, delayed_tasks = _task_alerts(weekly.projects, end_date)
    progress_candidates = _progress_candidates(weekly.projects, work_logs)
    performance_candidates = _monthly_performance_candidates(weekly.projects, work_logs) if report_type == "monthly" else []
    markdown = _render_auto_markdown(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        work_logs=work_logs,
        projects=weekly.projects,
        remaining_tasks=remaining_tasks,
        delayed_tasks=delayed_tasks,
        progress_candidates=progress_candidates,
        performance_candidates=performance_candidates,
    )
    return AutoReportResponse(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        markdown=markdown,
        work_logs=work_logs,
        projects=weekly.projects,
        remaining_tasks=remaining_tasks,
        delayed_tasks=delayed_tasks,
        progress_candidates=progress_candidates,
        monthly_performance_candidates=performance_candidates,
    )


def _task_alerts(projects: list[ProjectWeeklyReport], end_date: date) -> tuple[list[TaskAlert], list[TaskAlert]]:
    remaining: list[TaskAlert] = []
    delayed: list[TaskAlert] = []
    for project in projects:
        for task in project.tasks:
            if task.status.lower() in DONE_STATUSES:
                continue
            due_date = date.fromisoformat(task.due_date) if task.due_date else None
            is_delayed = bool(due_date and due_date < end_date)
            alert = TaskAlert(
                project_id=project.id,
                project_title=project.title,
                title=task.title,
                status=task.status,
                due_date=task.due_date,
                is_delayed=is_delayed,
            )
            remaining.append(alert)
            if is_delayed:
                delayed.append(alert)
    return remaining, delayed


def _progress_candidates(projects: list[ProjectWeeklyReport], work_logs: list[WorkLogItem]) -> list[ProjectProgressCandidate]:
    logs_by_project: dict[str, list[WorkLogItem]] = defaultdict(list)
    for work_log in work_logs:
        if work_log.project_id:
            logs_by_project[work_log.project_id].append(work_log)

    candidates: list[ProjectProgressCandidate] = []
    for project in projects:
        task_total = len(project.tasks)
        task_done = sum(1 for task in project.tasks if task.status.lower() in DONE_STATUSES)
        task_ratio = int((task_done / task_total) * 100) if task_total else 0
        evidence_score = min(100, len(project.documents) * 10 + len(project.decisions) * 15 + len(logs_by_project[project.id]) * 10)
        suggested = max(STATUS_PROGRESS[project.status], task_ratio, evidence_score)
        if project.status != "done":
            suggested = min(suggested, 95)
        reason = (
            f"문서 {len(project.documents)}건, 결정사항 {len(project.decisions)}건, "
            f"업무 로그 {len(logs_by_project[project.id])}건, 완료 할 일 {task_done}/{task_total}건 기준의 업데이트 후보입니다."
        )
        candidates.append(
            ProjectProgressCandidate(
                project_id=project.id,
                project_title=project.title,
                current_status=project.status,
                suggested_progress_percent=suggested,
                reason=reason,
            )
        )
    return candidates


def _monthly_performance_candidates(
    projects: list[ProjectWeeklyReport],
    work_logs: list[WorkLogItem],
) -> list[MonthlyPerformanceCandidate]:
    logs_by_project: dict[str, list[WorkLogItem]] = defaultdict(list)
    for work_log in work_logs:
        if work_log.project_id:
            logs_by_project[work_log.project_id].append(work_log)

    candidates: list[MonthlyPerformanceCandidate] = []
    for project in projects:
        evidence = []
        evidence.extend([f"문서: {document.filename}" for document in project.documents[:3]])
        evidence.extend([f"결정사항: {decision.title}" for decision in project.decisions[:3]])
        evidence.extend([f"업무 로그: {work_log.title}" for work_log in logs_by_project[project.id][:3]])
        if not evidence:
            continue
        qualitative = f"{project.title}: 저장된 업무 기록을 기반으로 개선 활동을 정리할 수 있습니다."
        candidates.append(
            MonthlyPerformanceCandidate(
                project_id=project.id,
                project_title=project.title,
                qualitative_improvement=qualitative,
                evidence=evidence,
                requires_user_metric_confirmation=True,
                resume_ready=False,
            )
        )
    return candidates


def _render_auto_markdown(
    report_type: ReportType,
    start_date: date,
    end_date: date,
    work_logs: list[WorkLogItem],
    projects: list[ProjectWeeklyReport],
    remaining_tasks: list[TaskAlert],
    delayed_tasks: list[TaskAlert],
    progress_candidates: list[ProjectProgressCandidate],
    performance_candidates: list[MonthlyPerformanceCandidate],
) -> str:
    lines = [f"# {REPORT_TITLES[report_type]} ({start_date.isoformat()} ~ {end_date.isoformat()})", ""]
    lines.extend(_render_work_logs(work_logs))
    lines.extend(["", "## 프로젝트별 자동 요약"])
    if projects:
        for project in projects:
            lines.extend(
                [
                    f"### {project.title}",
                    f"- 상태: {project.status}",
                    f"- 문서 {len(project.documents)}건 / 할 일 {len(project.tasks)}건 / 결정사항 {len(project.decisions)}건 / 리스크 {len(project.risks)}건",
                    "- 기록 후보: 저장된 업무·문서 근거를 사용해 후속 성과 정리에 활용할 수 있습니다.",
                    "",
                ]
            )
    else:
        lines.append("- 선택 기간에 연결된 프로젝트 기록이 없습니다.")

    lines.extend(["", "## 프로젝트별 진행률 업데이트 후보"])
    if progress_candidates:
        for candidate in progress_candidates:
            lines.append(f"- {candidate.project_title}: {candidate.suggested_progress_percent}% 후보 — {candidate.reason}")
    else:
        lines.append("- 진행률 후보를 만들 프로젝트 기록이 없습니다.")

    lines.extend(["", "## 잔여 업무"])
    lines.extend(_render_task_alerts(remaining_tasks, empty="잔여 업무가 없습니다."))
    lines.extend(["", "## 지연 업무"])
    lines.extend(_render_task_alerts(delayed_tasks, empty="지연 업무가 없습니다."))

    if report_type == "monthly":
        lines.extend(["", "## 월간 성과 후보"])
        if performance_candidates:
            for candidate in performance_candidates:
                lines.append(f"- {candidate.project_title}: {candidate.qualitative_improvement}")
                lines.append("  - 수치 확정: 사용자 확인 필요")
                lines.append(f"  - 이력서 반영 가능: {'가능' if candidate.resume_ready else '근거/수치 보강 필요'}")
                for evidence in candidate.evidence:
                    lines.append(f"  - 근거: {evidence}")
        else:
            lines.append("- 성과 후보를 만들 저장 근거가 없습니다.")

    lines.extend(["", "_메일 발송과 외부 서비스 연동 없이 앱 내부 저장 데이터만 사용했습니다._"])
    return "\n".join(lines).strip() + "\n"


def _render_work_logs(work_logs: list[WorkLogItem]) -> list[str]:
    lines = ["## 업무 로그 기반 일일 요약"]
    if not work_logs:
        lines.append("- 선택 기간에 등록된 업무 로그가 없습니다.")
        return lines
    for work_log in work_logs:
        project_label = f" ({work_log.project_title})" if work_log.project_title else ""
        duration = f" · {work_log.duration_minutes}분" if work_log.duration_minutes else ""
        lines.append(f"- {work_log.log_date.isoformat()} · {work_log.title}{project_label}{duration}: {work_log.content or '내용 없음'}")
        if work_log.decisions:
            lines.append(f"  - 판단/결정: {work_log.decisions}")
        if work_log.collaborators:
            lines.append(f"  - 협의 대상: {work_log.collaborators}")
        if work_log.next_actions:
            lines.append(f"  - 다음 액션: {work_log.next_actions}")
        if work_log.blockers:
            lines.append(f"  - 이슈/막힘: {work_log.blockers}")
    return lines


def _render_task_alerts(alerts: list[TaskAlert], *, empty: str) -> list[str]:
    if not alerts:
        return [f"- {empty}"]
    lines = []
    for alert in alerts:
        due = f" / 기한: {alert.due_date}" if alert.due_date else ""
        delayed = " / 지연" if alert.is_delayed else ""
        lines.append(f"- {alert.project_title}: [{alert.status}] {alert.title}{due}{delayed}")
    return lines
