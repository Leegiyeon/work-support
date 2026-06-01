import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");

const globals = read("app/globals.css");
const layoutPage = read("app/layout.tsx");
const logoComponent = read("app/components/AppLogo.tsx");
const dashboardPage = read("app/page.tsx");
const projectsPage = read("app/projects/page.tsx");
const detailPage = read("app/projects/[projectId]/page.tsx");
const reportsPage = read("app/reports/page.tsx");

test("global logo always links back to dashboard", () => {
  assert.match(layoutPage, /<AppLogo \/>/);
  assert.match(logoComponent, /href="\/"/);
  assert.match(logoComponent, /대시보드로 이동/);
  assert.match(globals, /\.app-logo/);
});

test("top-level work surfaces keep concise guidance subtitles", () => {
  for (const [name, source] of Object.entries({ dashboardPage, projectsPage, detailPage, reportsPage })) {
    assert.match(source, /className="page-subtitle"/, `${name} should include a compact page subtitle`);
  }
});

test("create and edit flows use explicit action labels", () => {
  assert.match(projectsPage, /프로젝트 생성/);
  assert.match(projectsPage, /프로젝트 추가/);
  assert.match(detailPage, /업무 추가/);
  assert.match(detailPage, /수정 저장/);
  assert.match(reportsPage, /리포트 생성/);
});

test("UI polish styles preserve accessible alignment and focus affordances", () => {
  assert.match(globals, /\.stacked-form > button/);
  assert.match(globals, /\.form-actions\s*\{/);
  assert.match(globals, /focus-visible/);
  assert.match(globals, /\.task-form-panel/);
  assert.match(globals, /\.data-table tbody tr:hover/);
});
