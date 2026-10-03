import { request, requestBinary } from "./client";
import type { ExportFormat, ReportCreateIn, ReportDetailOut, ReportSummaryOut } from "../types/api";
import type { BinaryResult } from "./client";

export function createReport(payload: ReportCreateIn): Promise<ReportDetailOut> {
  return request<ReportDetailOut>("/reports", { method: "POST", body: payload });
}

export function listReports(limit = 50, offset = 0): Promise<ReportSummaryOut[]> {
  return request<ReportSummaryOut[]>("/reports", { query: { limit, offset } });
}

export function getReport(id: number): Promise<ReportDetailOut> {
  return request<ReportDetailOut>(`/reports/${id}`);
}

export function exportReport(id: number, format: ExportFormat): Promise<BinaryResult> {
  return requestBinary(`/reports/${id}/export`, { format }, `report_${id}.${format}`);
}
