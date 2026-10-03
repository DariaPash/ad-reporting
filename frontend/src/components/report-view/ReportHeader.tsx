import type { ReportDetailOut } from "../../types/api";
import { formatDate } from "../../utils/format";
import { ExportButtons } from "./ExportButtons";

export function ReportHeader({ report }: { report: ReportDetailOut }) {
  const goalNames = report.goals.map((g) => g.goal_name);
  return (
    <div className="row space">
      <div>
        <h1>Отчет</h1>
        <div className="meta">
          <span>
            Период: {formatDate(report.date_from)} — {formatDate(report.date_to)}
          </span>
          <span>Кампании: {report.by_campaign.length}</span>
          <span>Цели: {goalNames.length > 0 ? goalNames.join(", ") : "не выбраны"}</span>
        </div>
      </div>
      <ExportButtons reportId={report.id} />
    </div>
  );
}
