import { useState } from "react";
import { exportReport } from "../api/reports";
import { triggerDownload } from "../utils/download";
import type { ExportFormat } from "../types/api";

export type ExportPhase =
  | { kind: "idle" }
  | { kind: "preparing"; format: ExportFormat }
  | { kind: "ready" }
  | { kind: "error"; format: ExportFormat };

const SAFE_ERROR_MESSAGE = "Не удалось подготовить файл. Повторите попытку позднее.";

/** Экспорт PDF/XLSX. Технические ответы сервера не показываются. */
export function useExport(reportId: number) {
  const [phase, setPhase] = useState<ExportPhase>({ kind: "idle" });

  async function download(format: ExportFormat) {
    setPhase({ kind: "preparing", format });
    try {
      const { blob, filename } = await exportReport(reportId, format);
      triggerDownload(blob, filename);
      setPhase({ kind: "ready" });
      setTimeout(() => setPhase((current) => (current.kind === "ready" ? { kind: "idle" } : current)), 2000);
    } catch {
      setPhase({ kind: "error", format });
    }
  }

  return { phase, download, errorMessage: SAFE_ERROR_MESSAGE };
}
