import { request } from "./client";
import type { OperationLogOut } from "../types/api";

export function listOperations(limit = 50, offset = 0): Promise<OperationLogOut[]> {
  return request<OperationLogOut[]>("/operations", { query: { limit, offset } });
}
