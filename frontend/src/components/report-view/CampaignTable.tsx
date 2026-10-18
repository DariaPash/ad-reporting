import type { ReportCampaignRow } from "../../types/api";
import { formatKpi } from "../../utils/format";

/** Без выбранных целей конверсионные столбцы скрываются. */
export function CampaignTable({ rows, hasGoals }: { rows: ReportCampaignRow[]; hasGoals: boolean }) {
  return (
    <div className="panel">
      <h2>По кампаниям</h2>
      <div className="table-scroll">
        <table className="cards">
          <thead>
            <tr>
              <th>Кампания</th>
              <th>Расходы</th>
              <th>Показы</th>
              <th>Клики</th>
              <th>CTR</th>
              <th>CPC</th>
              {hasGoals && (
                <>
                  <th>Действия</th>
                  <th>CR</th>
                  <th>CPA</th>
                  <th>CPL</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.campaign_id}>
                <td className="cell-title">{row.campaign_name}</td>
                <td data-label="Расходы">{formatKpi(row.kpi.cost, "money")}</td>
                <td data-label="Показы">{formatKpi(row.kpi.impressions, "int")}</td>
                <td data-label="Клики">{formatKpi(row.kpi.clicks, "int")}</td>
                <td data-label="CTR">{formatKpi(row.kpi.ctr, "percent")}</td>
                <td data-label="CPC">{formatKpi(row.kpi.cpc, "money")}</td>
                {hasGoals && (
                  <>
                    <td data-label="Действия">{formatKpi(row.kpi.conversions, "int")}</td>
                    <td data-label="CR">{formatKpi(row.kpi.cr, "percent")}</td>
                    <td data-label="CPA">{formatKpi(row.kpi.cpa, "money")}</td>
                    <td data-label="CPL">{formatKpi(row.kpi.cpl, "money")}</td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
