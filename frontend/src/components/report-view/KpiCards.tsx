import type { KpiSet } from "../../types/api";
import { KpiCard } from "../common/KpiCard";
import { formatKpi } from "../../utils/format";

/** Конверсионные карточки показываются только если у отчёта были выбраны цели. */
export function KpiCards({ kpi, hasGoals }: { kpi: KpiSet; hasGoals: boolean }) {
  return (
    <div className="kpis">
      <KpiCard label="Расходы" value={formatKpi(kpi.cost, "money")} />
      <KpiCard label="Показы" value={formatKpi(kpi.impressions, "int")} />
      <KpiCard label="Клики" value={formatKpi(kpi.clicks, "int")} />
      <KpiCard label="CTR" value={formatKpi(kpi.ctr, "percent")} />
      <KpiCard label="CPC" value={formatKpi(kpi.cpc, "money")} />
      {hasGoals && (
        <>
          <KpiCard label="Целевые действия" value={formatKpi(kpi.conversions, "int")} />
          <KpiCard label="CR" value={formatKpi(kpi.cr, "percent")} />
          <KpiCard label="CPA" value={formatKpi(kpi.cpa, "money")} />
          <KpiCard label="CPL" value={formatKpi(kpi.cpl, "money")} />
        </>
      )}
    </div>
  );
}
