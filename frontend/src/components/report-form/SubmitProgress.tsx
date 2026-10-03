import type { SubmitPhase } from "../../hooks/useReportSubmit";
import { LiveRegion } from "../common/LiveRegion";

const STAGE_LABELS: Record<string, string> = {
  checking: "Проверка сохраненных данных…",
  fetching: "Получение статистики…",
  calculating: "Объединение данных и расчет показателей…",
  saving: "Сохранение отчета…",
};

/** Иллюстративный прогресс: единственный реальный сигнал сервера — итоговый ответ POST /reports. */
export function SubmitProgress({ phase }: { phase: SubmitPhase }) {
  const label = STAGE_LABELS[phase.kind];
  if (!label) return null;
  return <LiveRegion className="progress">{label}</LiveRegion>;
}
