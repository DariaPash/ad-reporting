import { useExport } from "../../hooks/useExport";
import { Toast } from "../common/Toast";

export function ExportButtons({ reportId }: { reportId: number }) {
  const { phase, download, errorMessage } = useExport(reportId);
  const busy = phase.kind === "preparing";

  return (
    <div className="row">
      <button type="button" className="btn" disabled={busy} aria-busy={busy} onClick={() => download("pdf")}>
        {phase.kind === "preparing" && phase.format === "pdf" ? "Подготовка…" : "Экспорт PDF"}
      </button>
      <button type="button" className="btn" disabled={busy} aria-busy={busy} onClick={() => download("xlsx")}>
        {phase.kind === "preparing" && phase.format === "xlsx" ? "Подготовка…" : "Экспорт XLSX"}
      </button>
      {phase.kind === "ready" && <Toast message="Файл готов" />}
      {phase.kind === "error" && <Toast message={errorMessage} tone="error" />}
    </div>
  );
}
