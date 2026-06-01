import { NextRequest } from "next/server";

import { proxyBackend } from "../backend";

export async function GET(request: NextRequest) {
  return proxyBackend(request, "/work-logs");
}

export async function POST(request: NextRequest) {
  return proxyBackend(request, "/work-logs");
}
