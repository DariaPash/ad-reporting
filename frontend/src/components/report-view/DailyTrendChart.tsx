import type { ReportDatePoint } from "../../types/api";
import { SvgLineChart } from "../common/SvgLineChart";
import { formatKpi } from "../../utils/format";

export function DailyTrendChart({ points }: { points: ReportDatePoint[] }) {
  const chartPoints = points.map((p) => ({ date: p.stat_date, value: p.cost }));
  return (
    <SvgLineChart points={chartPoints} title="Динамика расходов по дням" formatValue={(v) => formatKpi(v, "money")} />
  );
}
