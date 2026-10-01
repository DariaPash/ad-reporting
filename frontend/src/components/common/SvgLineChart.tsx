import { formatDate } from "../../utils/format";

export interface ChartPoint {
  date: string;
  value: number;
}

interface Props {
  points: ChartPoint[];
  title: string;
  formatValue: (value: number) => string;
}

const WIDTH = 900;
const HEIGHT = 160;
const PAD_LEFT = 45;
const PAD_RIGHT = 15;
const PAD_TOP = 15;
const PAD_BOTTOM = 30;

/** Минимальный line-chart без библиотек: легенда, подписи осей и визуально скрытая
 * таблица точек, чтобы значения были доступны не только через SVG. */
export function SvgLineChart({ points, title, formatValue }: Props) {
  if (points.length === 0) {
    return <p className="hint">Недостаточно данных для графика.</p>;
  }

  const values = points.map((p) => p.value);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const range = max - min || 1;

  const plotWidth = WIDTH - PAD_LEFT - PAD_RIGHT;
  const plotHeight = HEIGHT - PAD_TOP - PAD_BOTTOM;

  const coords = points.map((p, index) => {
    const x = points.length === 1 ? PAD_LEFT + plotWidth / 2 : PAD_LEFT + (index / (points.length - 1)) * plotWidth;
    const y = PAD_TOP + plotHeight - ((p.value - min) / range) * plotHeight;
    return { x, y, point: p };
  });

  const polylinePoints = coords.map((c) => `${c.x},${c.y}`).join(" ");
  const firstDate = points[0]!.date;
  const lastDate = points[points.length - 1]!.date;

  return (
    <div className="chart">
      <strong>{title}</strong>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={`${title}: от ${formatValue(min)} до ${formatValue(max)}`}>
        <line
          x1={PAD_LEFT}
          y1={PAD_TOP + plotHeight}
          x2={WIDTH - PAD_RIGHT}
          y2={PAD_TOP + plotHeight}
          stroke="#98a2b3"
        />
        <line x1={PAD_LEFT} y1={PAD_TOP} x2={PAD_LEFT} y2={PAD_TOP + plotHeight} stroke="#98a2b3" />
        <polyline points={polylinePoints} fill="none" stroke="#3157c8" strokeWidth={2.5} />
        {coords.map((c) => (
          <circle key={c.point.date} cx={c.x} cy={c.y} r={3} fill="#3157c8" />
        ))}
        <text x={PAD_LEFT} y={HEIGHT - 6} fontSize={11} fill="#667085">
          {formatDate(firstDate)}
        </text>
        <text x={WIDTH - PAD_RIGHT} y={HEIGHT - 6} fontSize={11} fill="#667085" textAnchor="end">
          {formatDate(lastDate)}
        </text>
        <text x={PAD_LEFT - 6} y={PAD_TOP + 4} fontSize={11} fill="#667085" textAnchor="end">
          {formatValue(max)}
        </text>
        <text x={PAD_LEFT - 6} y={PAD_TOP + plotHeight} fontSize={11} fill="#667085" textAnchor="end">
          {formatValue(min)}
        </text>
      </svg>
      <table className="sr-only">
        <caption>{title} по дням</caption>
        <thead>
          <tr>
            <th>Дата</th>
            <th>Значение</th>
          </tr>
        </thead>
        <tbody>
          {points.map((p) => (
            <tr key={p.date}>
              <td>{formatDate(p.date)}</td>
              <td>{formatValue(p.value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
