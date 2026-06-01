"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { parseApiErrorMessage } from "../reports/api-error";
import type { ProjectStatus, ProjectSummary } from "./types";
import { projectStatusLabels } from "./types";

const initialForm = {
  title: "",
  description: "",
  role: "",
  status: "idea" as ProjectStatus
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [form, setForm] = useState(initialForm);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const dashboard = useMemo(() => {
    const activeProjects = projects.filter((project) => project.status !== "done" && project.status !== "on_hold");
    const remainingTasks = projects.reduce((sum, project) => sum + project.remaining_tasks, 0);
    const averageProgress = projects.length
      ? Math.round(projects.reduce((sum, project) => sum + project.progress_percent, 0) / projects.length)
      : 0;

    return { activeProjects, remainingTasks, averageProgress };
  }, [projects]);

  async function loadProjects() {
    setIsLoading(true);
    setErrorMessage("");
    try {
      const response = await fetch("/api/projects", { cache: "no-store" });
      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(parseApiErrorMessage(detail));
      }
      setProjects((await response.json()) as ProjectSummary[]);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "프로젝트를 불러오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let isMounted = true;

    fetch("/api/projects", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) {
          const detail = await response.json().catch(() => null);
          throw new Error(parseApiErrorMessage(detail));
        }
        return response.json() as Promise<ProjectSummary[]>;
      })
      .then((data) => {
        if (isMounted) {
          setProjects(data);
        }
      })
      .catch((error: unknown) => {
        if (isMounted) {
          setErrorMessage(error instanceof Error ? error.message : "프로젝트를 불러오지 못했습니다.");
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.title.trim()) {
      setErrorMessage("프로젝트명을 입력하세요.");
      return;
    }

    setIsSaving(true);
    setErrorMessage("");
    try {
      const response = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form)
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(parseApiErrorMessage(detail));
      }
      setForm(initialForm);
      await loadProjects();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "프로젝트를 저장하지 못했습니다.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <main className="page-shell project-page">
      <Link className="text-link" href="/">← 대시보드로</Link>

      <section className="hero-card compact">
        <p className="eyebrow">project progress</p>
        <h1>프로젝트 진척도와 잔여 업무 관리</h1>
        <p className="hero-description">
          프로젝트별 업무를 생성하고 상태를 관리합니다. 진척도는 완료 업무 / 전체 업무 기준으로 계산합니다.
        </p>
      </section>

      <section className="summary-grid" aria-label="프로젝트 요약">
        <div className="metric-card"><span>진행 중 프로젝트</span><strong>{dashboard.activeProjects.length}</strong></div>
        <div className="metric-card"><span>전체 잔여 업무</span><strong>{dashboard.remainingTasks}</strong></div>
        <div className="metric-card"><span>평균 진척도</span><strong>{dashboard.averageProgress}%</strong></div>
      </section>

      <section className="panel">
        <h2>프로젝트 생성</h2>
        <form className="stacked-form" onSubmit={handleCreateProject}>
          <label>
            프로젝트명
            <input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="예: 운영 자동화 개선" />
          </label>
          <label>
            설명
            <textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="프로젝트 목적과 범위를 간단히 적어두세요." />
          </label>
          <label>
            내 역할
            <input value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })} placeholder="예: PM, 기획, 자동화 담당" />
          </label>
          <label>
            상태
            <select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value as ProjectStatus })}>
              {Object.entries(projectStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <button type="submit" disabled={isSaving}>{isSaving ? "저장 중..." : "프로젝트 추가"}</button>
        </form>
      </section>

      {errorMessage ? <div className="alert error">{errorMessage}</div> : null}

      <section className="project-list" aria-label="프로젝트 목록">
        {isLoading ? <div className="panel muted">프로젝트를 불러오는 중입니다.</div> : null}
        {!isLoading && projects.length === 0 ? <div className="panel muted">아직 프로젝트가 없습니다. 첫 프로젝트를 추가하세요.</div> : null}
        {projects.map((project) => (
          <Link className="project-card" key={project.id} href={`/projects/${project.id}`}>
            <div>
              <span className="status-pill small">{projectStatusLabels[project.status]}</span>
              <h2>{project.title}</h2>
              <p className="muted-text">{project.description || "설명 없음"}</p>
            </div>
            <div className="progress-block">
              <strong>{project.progress_percent}%</strong>
              <div className="progress-track"><span style={{ width: `${project.progress_percent}%` }} /></div>
              <p className="muted-text">잔여 {project.remaining_tasks}개 · 완료 {project.completed_tasks}/{project.total_tasks}</p>
            </div>
          </Link>
        ))}
      </section>
    </main>
  );
}
