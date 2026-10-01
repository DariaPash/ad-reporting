import type { AppError } from "../types/errors";

const GENERIC_MESSAGE = "Не удалось выполнить запрос. Повторите попытку позднее.";
const NETWORK_MESSAGE = "Сервер недоступен. Проверьте подключение и повторите попытку.";

function domainMessage(code: string, backendMessage: string): string {
  // `code` задаёт безопасную категорию, backendMessage не содержит токенов/трасс;
  // конкретные экраны могут подменить текст своей формулировкой.
  if (code === "not_implemented_yet") {
    return "Эта функция ещё не реализована.";
  }
  return backendMessage || GENERIC_MESSAGE;
}

async function parseErrorBody(response: Response): Promise<AppError> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return { kind: "unknown", httpStatus: response.status, code: null, message: GENERIC_MESSAGE };
  }

  if (
    body &&
    typeof body === "object" &&
    "code" in body &&
    "message" in body &&
    typeof (body as { code: unknown }).code === "string" &&
    typeof (body as { message: unknown }).message === "string"
  ) {
    const code = (body as { code: string }).code;
    const message = (body as { message: string }).message;
    return { kind: "domain", httpStatus: response.status, code, message: domainMessage(code, message) };
  }

  if (body && typeof body === "object" && "detail" in body) {
    // Валидация FastAPI (неверный литерал/regex query-параметра и т.п.) —
    // detail[].msg/loc может содержать введённые значения, наружу не отдаём.
    return {
      kind: "validation",
      httpStatus: response.status,
      code: "request_validation",
      message: "Некорректные параметры запроса.",
    };
  }

  return { kind: "unknown", httpStatus: response.status, code: null, message: GENERIC_MESSAGE };
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
  query?: Record<string, string | number | undefined | null>;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  // Префикс /api отделяет вызовы API от SPA-маршрутов (например, /reports — и то и другое);
  // снимается прокси в vite.config.ts (dev) и nginx.conf.
  const prefixed = `/api${path}`;
  if (!query) return prefixed;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  const qs = params.toString();
  return qs ? `${prefixed}?${qs}` : prefixed;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = buildUrl(path, options.query);
  let response: Response;
  try {
    response = await fetch(url, {
      method: options.method ?? "GET",
      headers: options.body ? { "Content-Type": "application/json" } : undefined,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    const networkError: AppError = { kind: "network", httpStatus: null, code: null, message: NETWORK_MESSAGE };
    throw networkError;
  }

  if (!response.ok) {
    throw await parseErrorBody(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export interface BinaryResult {
  blob: Blob;
  filename: string;
}

function filenameFromContentDisposition(header: string | null, fallback: string): string {
  if (!header) return fallback;
  const match = /filename="?([^"]+)"?/.exec(header);
  return match?.[1] ?? fallback;
}

export async function requestBinary(path: string, query: RequestOptions["query"], fallbackFilename: string): Promise<BinaryResult> {
  const url = buildUrl(path, query);
  let response: Response;
  try {
    response = await fetch(url);
  } catch {
    const networkError: AppError = { kind: "network", httpStatus: null, code: null, message: NETWORK_MESSAGE };
    throw networkError;
  }

  if (!response.ok) {
    throw await parseErrorBody(response);
  }

  const blob = await response.blob();
  const filename = filenameFromContentDisposition(response.headers.get("Content-Disposition"), fallbackFilename);
  return { blob, filename };
}
