import type { ReportCampaignRow } from "../../types/api";
import { formatKpi } from "../../utils/format";

/** Без выбранных целей конверсионные столбцы скрываются. */
export function CampaignTable({ rows, hasGoals }: { rows: ReportCampaignRow[]; hasGoals: boolean }) {
  return (
    <div className="panel">
      <h2>По кампаниям</h2>
      <div className="table-scroll">
        <table>
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
                <td>{row.campaign_name}</td>
                <td>{formatKpi(row.kpi.cost, "money")}</td>
                <td>{formatKpi(row.kpi.impressions, "int")}</td>
                <td>{formatKpi(row.kpi.clicks, "int")}</td>
                <td>{formatKpi(row.kpi.ctr, "percent")}</td>
                <td>{formatKpi(row.kpi.cpc, "money")}</td>
                {hasGoals && (
                  <>
                    <td>{formatKpi(row.kpi.conversions, "int")}</td>
                    <td>{formatKpi(row.kpi.cr, "percent")}</td>
                    <td>{formatKpi(row.kpi.cpa, "money")}</td>
                    <td>{formatKpi(row.kpi.cpl, "money")}</td>
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
