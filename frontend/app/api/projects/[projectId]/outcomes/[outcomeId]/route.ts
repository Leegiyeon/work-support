import { NextRequest } from "next/server";

import { encodePathSegment, proxyBackend } from "../../../../backend";

type RouteContext = {
  params: Promise<{ projectId: string; outcomeId: string }>;
};

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { projectId, outcomeId } = await context.params;
  return proxyBackend(request, `/projects/${encodePathSegment(projectId)}/outcomes/${encodePathSegment(outcomeId)}`);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  const { projectId, outcomeId } = await context.params;
  return proxyBackend(request, `/projects/${encodePathSegment(projectId)}/outcomes/${encodePathSegment(outcomeId)}`);
}
