import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.WORK_SUPPORT_BACKEND_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const OWNER_ID = process.env.WORK_SUPPORT_OWNER_ID ?? process.env.NEXT_PUBLIC_WORK_SUPPORT_OWNER_ID ?? "local-owner";
const REPORT_ACCESS_TOKEN = process.env.WORK_SUPPORT_REPORT_TOKEN ?? process.env.REPORT_ACCESS_TOKEN ?? "dev-only-report-token";

export function encodePathSegment(segment: string) {
  return encodeURIComponent(segment);
}

export async function proxyBackend(request: NextRequest, path: string) {
  const url = new URL(`${BACKEND_URL}${path}`);
  request.nextUrl.searchParams.forEach((value, key) => url.searchParams.set(key, value));

  const response = await fetch(url, {
    method: request.method,
    headers: {
      "Content-Type": request.headers.get("Content-Type") ?? "application/json",
      "X-Work-Support-Owner-Id": OWNER_ID,
      "X-Work-Support-Report-Token": REPORT_ACCESS_TOKEN
    },
    body: request.method === "GET" ? undefined : await request.text(),
    cache: "no-store"
  });

  return new NextResponse(await response.text(), {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json"
    }
  });
}
