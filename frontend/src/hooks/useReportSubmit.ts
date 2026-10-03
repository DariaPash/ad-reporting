import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createReport } from "../api/reports";
import { isAppError } from "../types/errors";
import type { FieldErrors, ReportFormValues } from "../utils/validation";
import { validateReportForm } from "../utils/validation";

export type SubmitPhase =
  | { kind: "input" }
  | { kind: "validation_error"; errors: FieldErrors }
  | { kind: "checking" | "fetching" | "calculating" | "saving" }
  | { kind: "report"; reportId: number }
  | { kind: "api_error"; message: string }
  | { kind: "save_error"; message: string };

export interface SubmitPayload extends ReportFormValues {
  goalIds: number[];
}

const API_ERROR_MESSAGE = "Не удалось получить недостающую статистику. Ранее сохраненные данные не изменены.";
const SAVE_ERROR_MESSAGE = "Не удалось сформировать отчет. Попробуйте еще раз.";

// Косметический таймер поверх одного POST /reports — сервер не присылает прогресс.
// Ветвление ошибки решается только по ответу запроса, а не по отображаемой стадии.
const STAGE_SCHEDULE: Array<{ delay: number; kind: "fetching" | "calculating" | "saving" }> = [
  { delay: 600, kind: "fetching" },
  { delay: 1400, kind: "calculating" },
  { delay: 2600, kind: "saving" },
];

const CYCLING_KINDS = new Set(["checking", "fetching", "calculating"]);

export function useReportSubmit() {
  const [phase, setPhase] = useState<SubmitPhase>({ kind: "input" });
  const navigate = useNavigate();
  const isSubmittingRef = useRef(false);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  function clearTimers() {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  }

  async function submit(payload: SubmitPayload): Promise<void> {
    // Синхронная защита от повторного клика — до любого setState.
    if (isSubmittingRef.current) return;

    const errors = validateReportForm(payload);
    if (Object.keys(errors).length > 0) {
      setPhase({ kind: "validation_error", errors });
      return;
    }

    isSubmittingRef.current = true;
    setPhase({ kind: "checking" });

    for (const { delay, kind } of STAGE_SCHEDULE) {
      timersRef.current.push(
        setTimeout(() => {
          setPhase((current) => (CYCLING_KINDS.has(current.kind) ? { kind } : current));
        }, delay),
      );
    }

    try {
      const report = await createReport({
        date_from: payload.dateFrom,
        date_to: payload.dateTo,
        campaign_ids: payload.campaignIds,
        goal_ids: payload.goalIds,
      });
      clearTimers();
      isSubmittingRef.current = false;
      setPhase({ kind: "report", reportId: report.id });
      navigate(`/reports/${report.id}`, { replace: true });
    } catch (error) {
      clearTimers();
      isSubmittingRef.current = false;
      const appError = isAppError(error) ? error : null;
      const isExternalApiDown =
        appError?.kind === "network" || (appError?.kind === "domain" && appError.code === "external_api_error");
      setPhase(isExternalApiDown ? { kind: "api_error", message: API_ERROR_MESSAGE } : { kind: "save_error", message: SAVE_ERROR_MESSAGE });
    }
  }

  function dismissError() {
    setPhase({ kind: "input" });
  }

  return { phase, submit, dismissError };
}
