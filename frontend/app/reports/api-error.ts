const DEFAULT_REPORT_ERROR_MESSAGE = "주간 리포트 생성에 실패했습니다.";

type ApiErrorDetail = {
  detail?: string | {
    code?: string;
    message?: string;
  };
};

export function parseApiErrorMessage(payload: unknown, fallback = DEFAULT_REPORT_ERROR_MESSAGE): string {
  if (!payload || typeof payload !== "object") {
    return fallback;
  }

  const detail = (payload as ApiErrorDetail).detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (detail && typeof detail === "object" && typeof detail.message === "string" && detail.message.trim()) {
    return detail.message;
  }

  return fallback;
}
