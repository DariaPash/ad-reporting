import { request } from "./client";
import type { ApiCheckOut } from "../types/api";

export function checkApiAvailability(): Promise<ApiCheckOut> {
  return request<ApiCheckOut>("/monitoring/api-check", { method: "POST" });
}
