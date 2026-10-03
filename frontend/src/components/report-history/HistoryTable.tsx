import { useNavigate } from "react-router-dom";
import type { ReportSummaryOut } from "../../types/api";
import { formatDate, formatDateTime } from "../../utils/format";

function truncateNames(names: string[]): { text: string; title: string } {
  if (names.length === 0) return { text: "Не выбраны", title: "" };
  if (names.length <= 2) return { text: names.join(", "), title: names.join(", ") };
  return { text: `${names.slice(0, 2).join(", ")} и еще ${names.length - 2}`, title: names.join(", ") };
}

export function HistoryTable({ reports }: { reports: ReportSummaryOut[] }) {
  const navigate = useNavigate();

  return (
    <div className="panel">
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Дата формирования</th>
              <th>Отчетный период</th>
              <th>Кампании</th>
              <th>Цели</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => {
              const campaigns = truncateNames(report.campaign_names);
              const goals = truncateNames(report.goal_names);
              return (
                <tr key={report.id}>
                  <td>{formatDateTime(report.created_at)}</td>
                  <td>
                    {formatDate(report.date_from)} — {formatDate(report.date_to)}
                  </td>
                  <td title={campaigns.title || undefined}>{campaigns.text}</td>
                  <td title={goals.title || undefined}>{goals.text}</td>
                  <td>
                    <button type="button" className="btn" onClick={() => navigate(`/reports/${report.id}`)}>
                      Открыть
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
