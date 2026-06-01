import { NextRequest } from "next/server";

import { encodePathSegment, proxyBackend } from "../../backend";

type RouteContext = {
  params: Promise<{ workLogId: string }>;
};

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { workLogId } = await context.params;
  return proxyBackend(request, `/work-logs/${encodePathSegment(workLogId)}`);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  const { workLogId } = await context.params;
  return proxyBackend(request, `/work-logs/${encodePathSegment(workLogId)}`);
}
