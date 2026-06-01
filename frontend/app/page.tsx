"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import type { ProjectSummary, ProjectTask, TaskStatus } from "./projects/types";
import { projectStatusLabels, taskPriorityLabels, taskStatusLabels } from "./projects/types";
import { parseApiErrorMessage } from "./reports/api-error";

const taskStatusOrder: TaskStatus[] = ["planned", "in_progress", "done", "on_hold"];
const activeStatuses = new Set(["idea", "review", "in_progress"]);

function getWeekStart() {
  const today = new Date();
  const day = today.getDay();
  const daysFromMonday = day === 0 ? 6 : day - 1;
  today.setHours(0, 0, 0, 0);
  today.setDate(today.getDate() - daysFromMonday);
  return today;
}


function isDelayed(task: ProjectTask) {
  if (!task.due_date || task.status === "done") return false;
  return new Date(`${task.due_date}T23:59:59`) < new Date();
}

function isCompletedThisWeek(task: ProjectTask, weekStart: Date) {
  if (task.status !== "done") return false;
  return new Date(task.updated_at) >= weekStart;
}

type ProjectTaskBundle = {
  project: ProjectSummary;
  tasks: ProjectTask[];
};

export default function HomePage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [projectTasks, setProjectTasks] = useState<Record<string, ProjectTask[]>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const dashboard = useMemo(() => {
    const taskBundles: ProjectTaskBundle[] = projects.map((project) => ({
      project,
      tasks: projectTasks[project.id] ?? []
    }));
    const allTasks = taskBundles.flatMap(({ project, tasks }) => tasks.map((task) => ({ ...task, project_title: project.title })));
    const weekStart = getWeekStart();
    const activeProjects = projects.filter((project) => activeStatuses.has(project.status));
    const remainingTasks = projects.reduce((sum, project) => sum + project.remaining_tasks, 0);
    const averageProgress = projects.length
      ? Math.round(projects.reduce((sum, project) => sum + project.progress_percent, 0) / projects.length)
      : 0;
    const delayedTasks = allTasks.filter(isDelayed).sort((a, b) => (a.due_date ?? "9999").localeCompare(b.due_date ?? "9999"));
    const completedThisWeek = allTasks
      .filter((task) => isCompletedThisWeek(task, weekStart))
      .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
    const taskStatusCounts = taskStatusOrder.map((status) => ({
      status,
      label: taskStatusLabels[status],
      count: allTasks.filter((task) => task.status === status).length
    }));
    const maxStatusCount = Math.max(1, ...taskStatusCounts.map((item) => item.count));

    return {
      activeProjects,
      averageProgress,
      completedThisWeek,
      delayedTasks,
      maxStatusCount,
      remainingTasks,
      taskStatusCounts,
      totalTasks: allTasks.length
    };
  }, [projectTasks, projects]);

  useEffect(() => {
    async function loadDashboard() {
      setIsLoading(true);
      setErrorMessage("");
      try {
        const projectResponse = await fetch("/api/projects", { cache: "no-store" });
        if (!projectResponse.ok) {
          const detail = await projectResponse.json().catch(() => null);
          throw new Error(parseApiErrorMessage(detail));
        }
        const nextProjects = (await projectResponse.json()) as ProjectSummary[];
        setProjects(nextProjects);

        const taskEntries = await Promise.all(
          nextProjects.map(async (project) => {
            const response = await fetch(`/api/projects/${project.id}/tasks`, { cache: "no-store" });
            if (!response.ok) return [project.id, []] as const;
            return [project.id, (await response.json()) as ProjectTask[]] as const;
          })
        );
        setProjectTasks(Object.fromEntries(taskEntries));
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "대시보드 데이터를 불러오지 못했습니다.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  return (
    <main className="page-shell dashboard-page">
      <header className="dashboard-topbar">
        <div>
          <span className="section-kicker">Dashboard</span>
          <h1>업무 현황</h1>
          <p className="page-subtitle">프로젝트 진척, 지연 업무, 이번 주 완료를 한눈에 확인하세요.</p>
        </div>
        <nav className="hero-actions" aria-label="주요 이동">
          <Link className="primary-link" href="/projects">프로젝트 보기</Link>
          <Link className="secondary-button" href="/reports">리포트 생성</Link>
        </nav>
      </header>

      {errorMessage ? <div className="alert error">{errorMessage}</div> : null}

      <section className="summary-grid dashboard-metrics" aria-label="핵심 지표">
        <div className="metric-card"><span>진행 프로젝트</span><strong>{dashboard.activeProjects.length}</strong></div>
        <div className="metric-card"><span>잔여 업무</span><strong>{dashboard.remainingTasks}</strong></div>
        <div className="metric-card"><span>지연 업무</span><strong>{dashboard.delayedTasks.length}</strong></div>
        <div className="metric-card"><span>평균 진척도</span><strong>{dashboard.averageProgress}%</strong></div>
      </section>

      <section className="dashboard-grid" aria-label="프로젝트 관리 대시보드">
        <section className="panel dashboard-main-panel">
          <div className="panel-title-row">
            <h2>프로젝트 진행률</h2>
            <span className="count-badge">{projects.length}개</span>
          </div>
          {isLoading ? <div className="empty-state">로딩 중</div> : null}
          {!isLoading && projects.length === 0 ? (
            <div className="empty-state"><span>프로젝트 없음</span><Link className="primary-link" href="/projects">추가</Link></div>
          ) : null}
          <div className="progress-chart-list">
            {projects.slice(0, 8).map((project) => (
              <Link className="progress-row" href={`/projects/${project.id}`} key={project.id}>
                <div className="progress-row-head">
                  <strong>{project.title}</strong>
                  <span className="meta-pill status-navy">{projectStatusLabels[project.status]}</span>
                  <span className="meta-pill">잔여 {project.remaining_tasks}</span>
                  <span className="meta-pill">{project.completed_tasks}/{project.total_tasks}</span>
                </div>
                <div className="progress-row-bar" aria-label={`${project.title} 진행률 ${project.progress_percent}%`}>
                  <span style={{ width: `${project.progress_percent}%` }} />
                </div>
                <b>{project.progress_percent}%</b>
              </Link>
            ))}
          </div>
        </section>

        <section className="panel status-graph-panel">
          <div className="panel-title-row">
            <h2>상태별 업무</h2>
            <span className="count-badge">{dashboard.totalTasks}개</span>
          </div>
          <div className="status-bars">
            {dashboard.taskStatusCounts.map((item) => (
              <div className="status-bar-row" key={item.status}>
                <span>{item.label}</span>
                <div className="status-bar-track"><i style={{ width: `${(item.count / dashboard.maxStatusCount) * 100}%` }} /></div>
                <strong>{item.count}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="panel delayed-panel">
          <div className="panel-title-row">
            <h2>지연 업무</h2>
            <span className="count-badge danger-count">{dashboard.delayedTasks.length}개</span>
          </div>
          {dashboard.delayedTasks.length === 0 ? <div className="empty-state">지연 없음</div> : null}
          <div className="dense-list">
            {dashboard.delayedTasks.slice(0, 6).map((task) => (
              <Link className="dense-list-row" href={`/projects/${task.project_id}`} key={task.id}>
                <span>{task.title}</span>
                <small>{task.project_title}</small>
                <b>{task.due_date}</b>
              </Link>
            ))}
          </div>
        </section>

        <section className="panel completed-panel">
          <div className="panel-title-row">
            <h2>이번 주 완료</h2>
            <span className="count-badge">{dashboard.completedThisWeek.length}개</span>
          </div>
          {dashboard.completedThisWeek.length === 0 ? <div className="empty-state">완료 업무 없음</div> : null}
          <div className="data-table-wrap">
            {dashboard.completedThisWeek.length > 0 ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>업무</th>
                    <th>프로젝트</th>
                    <th>우선순위</th>
                    <th>완료일</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.completedThisWeek.slice(0, 8).map((task) => (
                    <tr key={task.id}>
                      <td>{task.title}</td>
                      <td>{task.project_title}</td>
                      <td><span className={`meta-pill priority-${task.priority}`}>{taskPriorityLabels[task.priority]}</span></td>
                      <td>{task.updated_at.slice(0, 10)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
          </div>
        </section>
      </section>
    </main>
  );
}
