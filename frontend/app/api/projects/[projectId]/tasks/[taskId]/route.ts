import { NextRequest } from "next/server";

import { encodePathSegment, proxyBackend } from "../../../../backend";

type RouteContext = {
  params: Promise<{ projectId: string; taskId: string }>;
};

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { projectId, taskId } = await context.params;
  return proxyBackend(request, `/projects/${encodePathSegment(projectId)}/tasks/${encodePathSegment(taskId)}`);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  const { projectId, taskId } = await context.params;
  return proxyBackend(request, `/projects/${encodePathSegment(projectId)}/tasks/${encodePathSegment(taskId)}`);
}
