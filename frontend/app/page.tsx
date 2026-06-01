"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { parseApiErrorMessage } from "./reports/api-error";
import type { ProjectSummary } from "./projects/types";
import { projectStatusLabels } from "./projects/types";

const outOfScope = ["파일 업로드", "AI 분석 실행", "RAG", "경력 문장 생성", "배포/백업", "n8n 연동"];

export default function HomePage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const dashboard = useMemo(() => {
    const activeProjects = projects.filter((project) => project.status === "in_progress" || project.status === "review" || project.status === "idea");
    const remainingTasks = projects.reduce((sum, project) => sum + project.remaining_tasks, 0);
    const inProgressTasks = activeProjects.reduce((sum, project) => sum + project.remaining_tasks, 0);
    return { activeProjects, remainingTasks, inProgressTasks };
  }, [projects]);

  useEffect(() => {
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
        setErrorMessage(error instanceof Error ? error.message : "프로젝트 현황을 불러오지 못했습니다.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadProjects();
  }, []);

  return (
    <main className="page-shell">
      <section className="hero-card">
        <p className="eyebrow">work-support progress dashboard</p>
        <h1>프로젝트 진척도와 잔여 업무를 관리하는 개인 업무 플랫폼</h1>
        <p className="hero-description">
          현재 단계는 프로젝트별 업무를 기록하고, 완료 업무 기준 진척도와 잔여 업무를 확인하는 데 집중합니다.
        </p>
        <div className="hero-actions">
          <Link className="primary-link" href="/projects">프로젝트 관리하기</Link>
          <Link className="secondary-button" href="/reports">리포트 보기</Link>
          <div className="status-pill">파일 업로드·AI·RAG·경력 생성은 후속 범위</div>
        </div>
      </section>

      {errorMessage ? <div className="alert error">{errorMessage}</div> : null}

      <section className="summary-grid" aria-label="대시보드 요약">
        <div className="metric-card"><span>진행 중 프로젝트</span><strong>{dashboard.activeProjects.length}</strong></div>
        <div className="metric-card"><span>진행 프로젝트 잔여 업무</span><strong>{dashboard.inProgressTasks}</strong></div>
        <div className="metric-card"><span>전체 잔여 업무</span><strong>{dashboard.remainingTasks}</strong></div>
      </section>

      <section className="content-grid" aria-label="프로젝트 현황">
        <div className="panel">
          <h2>진행 중 프로젝트</h2>
          {isLoading ? <p className="muted-text">프로젝트를 불러오는 중입니다.</p> : null}
          {!isLoading && dashboard.activeProjects.length === 0 ? <p className="muted-text">진행 중 프로젝트가 없습니다.</p> : null}
          <div className="compact-list">
            {dashboard.activeProjects.slice(0, 5).map((project) => (
              <Link className="compact-project" href={`/projects/${project.id}`} key={project.id}>
                <span>{project.title}</span>
                <small>{projectStatusLabels[project.status]} · 잔여 {project.remaining_tasks}개 · {project.progress_percent}%</small>
              </Link>
            ))}
          </div>
        </div>

        <div className="panel muted">
          <h2>이번 범위에서 제외</h2>
          <p>이번 구현은 첫 번째 목적(진척도·잔여 업무 관리)에 집중합니다.</p>
          <ul>
            {outOfScope.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  );
}
