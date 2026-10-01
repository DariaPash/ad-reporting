export type AppErrorKind = "network" | "domain" | "validation" | "unknown";

/** Известные коды из backend/app/core/exceptions.py. */
export type DomainErrorCode =
  | "not_found"
  | "validation_error"
  | "external_api_error"
  | "not_implemented_yet"
  | "internal_error"
  | "conflict"
  | "forbidden";

export interface AppError {
  kind: AppErrorKind;
  httpStatus: number | null;
  code: string | null;
  /** Всегда безопасная для показа пользователю строка. */
  message: string;
}

export function isAppError(value: unknown): value is AppError {
  return (
    typeof value === "object" &&
    value !== null &&
    "kind" in value &&
    "message" in value
  );
}
