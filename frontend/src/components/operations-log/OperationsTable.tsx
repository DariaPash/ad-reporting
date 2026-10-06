import type { OperationLogOut } from "../../types/api";
import { StatusBadge } from "../common/StatusBadge";
import { formatDateTime } from "../../utils/format";

const OPERATION_LABELS: Record<string, string> = {
  campaigns_sync: "Синхронизация кампаний (Direct)",
  goals_sync: "Синхронизация целей (Metrika)",
  statistics_import: "Получение статистики",
};

function operationLabel(op: OperationLogOut): string {
  const base = OPERATION_LABELS[op.operation_type] ?? op.operation_type;
  if (op.operation_type === "statistics_import" && op.source) {
    return `${base} (${op.source === "direct" ? "Direct" : "Metrika"})`;
  }
  return base;
}

function statusBadge(status: string) {
  if (status === "success") return <StatusBadge tone="ok">выполнено</StatusBadge>;
  if (status === "error") return <StatusBadge tone="bad">ошибка</StatusBadge>;
  return <StatusBadge tone="neutral">выполняется</StatusBadge>;
}

export function OperationsTable({ operations }: { operations: OperationLogOut[] }) {
  return (
    <div className="panel">
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th style={{ width: 160 }}>Время</th>
              <th style={{ width: 260 }}>Операция</th>
              <th style={{ width: 130 }}>Статус</th>
              <th>Описание</th>
            </tr>
          </thead>
          <tbody>
            {operations.map((op) => (
              <tr key={op.id}>
                <td>{formatDateTime(op.started_at)}</td>
                <td>{operationLabel(op)}</td>
                <td>{statusBadge(op.status)}</td>
                <td>{op.message ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="hint" style={{ marginTop: 14 }}>
        Токены, заголовки Authorization, пароли и трассировки стека не записываются и не отображаются.
      </p>
    </div>
  );
}
