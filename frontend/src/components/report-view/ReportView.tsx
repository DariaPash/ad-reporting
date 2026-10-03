import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getReport } from "../../api/reports";
import type { AppError } from "../../types/errors";
import { isAppError } from "../../types/errors";
import type { ReportDetailOut } from "../../types/api";
import { ReportHeader } from "./ReportHeader";
import { KpiCards } from "./KpiCards";
import { CampaignTable } from "./CampaignTable";
import { DailyTrendChart } from "./DailyTrendChart";

type State = { status: "loading" } | { status: "error"; error: AppError } | { status: "success"; report: ReportDetailOut };

const UNKNOWN_ERROR: AppError = { kind: "unknown", httpStatus: null, code: null, message: "Не удалось загрузить отчёт." };

/** Снимок отчёта — только чтение, внешние API не вызываются. */
export function ReportView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    const reportId = Number(id);
    setState({ status: "loading" });
    getReport(reportId).then(
      (report) => setState({ status: "success", report }),
      (error: unknown) => setState({ status: "error", error: isAppError(error) ? error : UNKNOWN_ERROR }),
    );
  }, [id]);

  if (state.status === "loading") {
    return (
      <div className="panel" role="status" aria-live="polite">
        Загрузка…
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="panel" role="alert">
        <p>{state.error.message}</p>
        <Link to="/reports" className="btn">
          К истории отчетов
        </Link>
      </div>
    );
  }

  const { report } = state;
  const hasGoals = report.goals.length > 0;

  if (report.by_campaign.length === 0) {
    return (
      <div className="empty">
        <h2>В отчете нет данных</h2>
        <p className="lead">Сформируйте новый отчет с другими параметрами.</p>
        <button type="button" className="btn primary" onClick={() => navigate("/report/new")}>
          Сформировать отчет
        </button>
      </div>
    );
  }

  return (
    <div style={{ position: "relative" }}>
      <ReportHeader report={report} />
      <KpiCards kpi={report.summary} hasGoals={hasGoals} />
      <CampaignTable rows={report.by_campaign} hasGoals={hasGoals} />
      <DailyTrendChart points={report.by_date} />
    </div>
  );
}
