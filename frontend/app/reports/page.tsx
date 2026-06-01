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
      <Link className="text-link" href="/">
        ← 홈으로
      </Link>

      <section className="hero-card compact">
        <p className="eyebrow">weekly report</p>
        <h1>주간 업무 리포트 생성</h1>
        <p className="hero-description">
          선택한 기간에 업데이트된 프로젝트, 문서 요약, 할 일, 결정사항, 리스크를 모아
          근거 기반 Markdown 리포트를 생성합니다. 메일 전송과 n8n 연동은 포함하지 않습니다.
        </p>
      </section>

      <section className="panel report-controls" aria-label="리포트 기간 선택">
        <label>
          시작일
          <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
        </label>
        <label>
          종료일
          <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
        </label>
        <button type="button" onClick={handleGenerateReport} disabled={isLoading}>
          {isLoading ? "생성 중..." : "리포트 생성"}
        </button>
      </section>

      {errorMessage ? <div className="alert error">{errorMessage}</div> : null}

      {report ? (
        <section className="panel report-result" aria-label={`${periodLabel} 주간 리포트 결과`}>
          <div className="report-result-header">
            <div>
              <p className="eyebrow">generated markdown</p>
              <h2>{periodLabel}</h2>
              <p className="muted-text">
                프로젝트 {report.projects.length}개 기준 · 저장된 데이터만 사용
              </p>
            </div>
            <button type="button" className="secondary-button" onClick={handleCopy}>
              Markdown 복사
            </button>
          </div>
          {copyMessage ? <div className="alert success">{copyMessage}</div> : null}
          <pre className="markdown-output">{report.markdown}</pre>
        </section>
      ) : (
        <section className="panel muted">
          <h2>생성 전 안내</h2>
          <p>
            백엔드의 <code>/reports/weekly</code> API가 PostgreSQL에 저장된 프로젝트·문서·추출 항목을 조회합니다.
            데이터베이스가 비어 있으면 “업데이트된 프로젝트 없음” 리포트가 생성됩니다.
          </p>
        </section>
      )}
    </main>
  );
}
