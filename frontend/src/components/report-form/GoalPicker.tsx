import type { AsyncListState } from "../../hooks/useAsyncList";
import type { GoalOut } from "../../types/api";
import { goalBadgeLabel } from "../../utils/goalBadge";

interface Props {
  state: AsyncListState<GoalOut>;
  onRetry: () => void;
  selectedIds: number[];
  onToggle: (id: number) => void;
  disabled: boolean;
}

/** Необязательный список: ошибка загрузки целей не блокирует выбор кампаний и отправку формы. */
export function GoalPicker({ state, onRetry, selectedIds, onToggle, disabled }: Props) {
  return (
    <div>
      <label className="title">
        Цели Яндекс.Метрики <span className="hint">(необязательно)</span>
      </label>
      <div className="hint" style={{ minHeight: 38 }}>
        Без целей отчет будет содержать показатели Direct.
      </div>

      {state.status === "loading" && <div className="hint">Загрузка целей…</div>}

      {state.status === "error" && (
        <div className="field-error" role="alert">
          {state.error.message}{" "}
          <button type="button" className="btn" onClick={onRetry}>
            Повторить
          </button>
        </div>
      )}

      {state.status === "empty" && <div className="hint">Цели пока не синхронизированы.</div>}

      {state.status === "success" && (
        <div className="choicebox" role="group" aria-label="Цели Яндекс.Метрики">
          {state.data.map((goal) => (
            <label key={goal.id}>
              <input type="checkbox" disabled={disabled} checked={selectedIds.includes(goal.id)} onChange={() => onToggle(goal.id)} />
              {goal.name} <span className="badge">{goalBadgeLabel(goal)}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
