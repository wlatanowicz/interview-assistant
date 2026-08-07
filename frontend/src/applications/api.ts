import { resolveApiError } from "../auth/api";
import type {
  JobApplication,
  JobApplicationCreatePayload,
  JobApplicationListResponse,
} from "./types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

type ApiFailure = { ok: false; errorCode: string; errorParams?: Record<string, string | number> };
type ApiSuccess<T> = { ok: true; data: T };

function apiBase(): string {
  return (apiBaseUrl || "").replace(/\/$/, "");
}

function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

async function parseJson<T>(r: Response): Promise<T | { detail?: unknown }> {
  return (await r.json().catch(() => ({}))) as T | { detail?: unknown };
}

function failureFromBody(body: { detail?: unknown }): ApiFailure {
  const resolved = resolveApiError(body);
  if (resolved) {
    return {
      ok: false,
      errorCode: resolved.code,
      errorParams: resolved.params,
    };
  }
  return { ok: false, errorCode: "request_validation_error" };
}

export async function listApplications(
  token: string,
  options: { active?: boolean } = {},
): Promise<ApiSuccess<JobApplication[]> | ApiFailure> {
  const base = apiBase();
  if (!base) {
    return { ok: false, errorCode: "request_validation_error" };
  }
  const params = new URLSearchParams();
  if (options.active) {
    params.set("active", "true");
  }
  const query = params.toString();
  const url = query ? `${base}/api/applications?${query}` : `${base}/api/applications`;
  const r = await fetch(url, { headers: authHeaders(token) });
  const body = await parseJson<JobApplicationListResponse>(r);
  if (!r.ok) {
    return failureFromBody(body as { detail?: unknown });
  }
  return { ok: true, data: (body as JobApplicationListResponse).applications };
}

export async function createApplication(
  token: string,
  payload: JobApplicationCreatePayload,
): Promise<ApiSuccess<JobApplication> | ApiFailure> {
  const base = apiBase();
  if (!base) {
    return { ok: false, errorCode: "request_validation_error" };
  }
  const r = await fetch(`${base}/api/applications`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  const body = await parseJson<JobApplication>(r);
  if (!r.ok) {
    return failureFromBody(body as { detail?: unknown });
  }
  return { ok: true, data: body as JobApplication };
}
