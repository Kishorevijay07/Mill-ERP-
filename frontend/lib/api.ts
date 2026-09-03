/**
 * Thin API client for the FastAPI backend.
 *
 * Server state is owned by TanStack Query (see app/providers.tsx). This module
 * only handles transport concerns: base URL, credentials, and the shared error
 * contract returned by the backend ({ error: { code, message, field_errors? } }).
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    field_errors?: unknown;
  };
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fieldErrors?: unknown;

  constructor(status: number, body: ApiErrorBody) {
    super(body.error?.message ?? "Request failed");
    this.name = "ApiError";
    this.status = status;
    this.code = body.error?.code ?? "unknown";
    this.fieldErrors = body.error?.field_errors;
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    // Session auth uses HttpOnly cookies; always include credentials.
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let body: ApiErrorBody;
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      body = { error: { code: "http_error", message: response.statusText } };
    }
    throw new ApiError(response.status, body);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
