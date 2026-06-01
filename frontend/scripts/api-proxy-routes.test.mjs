import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");

test("work log detail proxy supports backend mutation methods", () => {
  const route = read("app/api/work-logs/[workLogId]/route.ts");

  assert.match(route, /export async function PATCH/);
  assert.match(route, /export async function DELETE/);
  assert.match(route, /`\/work-logs\/\$\{encodePathSegment\(workLogId\)\}`/);
});

test("project outcome detail proxy supports backend mutation methods", () => {
  const route = read("app/api/projects/[projectId]/outcomes/[outcomeId]/route.ts");

  assert.match(route, /export async function PATCH/);
  assert.match(route, /export async function DELETE/);
  assert.match(route, /`\/projects\/\$\{encodePathSegment\(projectId\)\}\/outcomes\/\$\{encodePathSegment\(outcomeId\)\}`/);
});
