"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { parseApiErrorMessage } from "./api-error";
import type { WeeklyReportResponse } from "./types";


function formatDate(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getDefaultStartDate() {
  const today = new Date();
  const day = today.getDay();
  const daysFromMonday = day === 0 ? 6 : day - 1;
  today.setDate(today.getDate() - daysFromMonday);
  return formatDate(today);
}

function getDefaultEndDate() {
  return formatDate(new Date());
}

export default function WeeklyReportPage() {
  const [startDate, setStartDate] = useState(getDefaultStartDate);
  const [endDate, setEndDate] = useState(getDefaultEndDate);
  const [report, setReport] = useState<WeeklyReportResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [copyMessage, setCopyMessage] = useState("");

  const periodLabel = useMemo(() => `${startDate} ~ ${endDate}`, [startDate, endDate]);
  const reportMetrics = useMemo(() => {
    if (!report) return { projects: 0, tasks: 0, decisions: 0, risks: 0 };
    return report.projects.reduce(
      (totals, project) => ({
        projects: totals.projects + 1,
        tasks: totals.tasks + project.tasks.length,
        decisions: totals.decisions + project.decisions.length,
        risks: totals.risks + project.risks.length
      }),
      { projects: 0, tasks: 0, decisions: 0, risks: 0 }
    );
  }, [report]);

  async function handleGenerateReport() {
    setIsLoading(true);
    setErrorMessage("");
    setCopyMessage("");

    try {
      const response = await fetch("/api/reports/weekly", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ start_date: startDate, end_date: endDate })
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(parseApiErrorMessage(detail));
      }

      const data = (await response.json()) as WeeklyReportResponse;
      setReport(data);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCopy() {
    if (!report?.markdown) return;

    try {
      await navigator.clipboard.writeText(report.markdown);
      setCopyMessage("Markdown 리포트를 클립보드에 복사했습니다.");
    } catch {
      setCopyMessage("브라우저 권한 문제로 복사하지 못했습니다. 아래 내용을 직접 선택해 복사하세요.");
    }
  }

  return (
    <main className="page-shell report-page">
      <header className="dashboard-topbar compact-topbar">
        <div>
          <Link className="text-link" href="/">← 대시보드</Link>
          <span className="section-kicker">Reports</span>
          <h1>주간 리포트</h1>
          <p className="page-subtitle">기간을 선택해 업무 로그와 성과를 Markdown으로 정리합니다.</p>
        </div>
        <div className="task-meta"><span className="meta-pill status-navy">{periodLabel}</span></div>
      </header>

      <section className="panel report-controls" aria-label="리포트 기간 선택">
        <label>시작일<input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
        <label>종료일<input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} /></label>
        <button type="button" onClick={handleGenerateReport} disabled={isLoading}>{isLoading ? "생성 중" : "리포트 생성"}</button>
      </section>

      {errorMessage ? <div className="alert error">{errorMessage}</div> : null}

      {report ? (
        <>
          <section className="summary-grid dashboard-metrics" aria-label="리포트 지표">
            <div className="metric-card"><span>프로젝트</span><strong>{reportMetrics.projects}</strong></div>
            <div className="metric-card"><span>업무</span><strong>{reportMetrics.tasks}</strong></div>
            <div className="metric-card"><span>결정</span><strong>{reportMetrics.decisions}</strong></div>
            <div className="metric-card"><span>리스크</span><strong>{reportMetrics.risks}</strong></div>
          </section>
          <section className="panel report-result" aria-label={`${periodLabel} 주간 리포트 결과`}>
            <div className="report-result-header"><h2>{periodLabel}</h2><button type="button" className="secondary-button" onClick={handleCopy}>Markdown 복사</button></div>
            {copyMessage ? <div className="alert success">{copyMessage}</div> : null}
            <pre className="markdown-output">{report.markdown}</pre>
          </section>
        </>
      ) : (
        <section className="panel muted"><div className="empty-state">리포트 없음</div></section>
      )}
    </main>
  );
}
