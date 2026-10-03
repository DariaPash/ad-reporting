import type { Ref } from "react";
import type { AsyncListState } from "../../hooks/useAsyncList";
import type { CampaignOut } from "../../types/api";

interface Props {
  state: AsyncListState<CampaignOut>;
  onRetry: () => void;
  search: string;
  onSearchChange: (value: string) => void;
  selectedIds: number[];
  onToggle: (id: number) => void;
  error?: string;
  disabled: boolean;
  searchRef: Ref<HTMLInputElement>;
}

const STATE_LABELS: Record<string, string> = {
  ON: "активна",
  SUSPENDED: "остановлена",
  ARCHIVED: "архив",
  LIKELY_ACTIVE: "активна",
  LIKELY_INACTIVE: "нет показов недавно",
};

/** LIKELY_ACTIVE/LIKELY_INACTIVE — не State Директа, а эвристика для кампаний Мастера кампаний
 * (campaigns.get их не возвращает): были ли показы за последние 7 дней. */
function stateLabel(campaignState: string | null): string {
  if (campaignState === null) return "статус неизвестен";
  return STATE_LABELS[campaignState] ?? campaignState.toLowerCase();
}

/** Показываются все кампании, кроме архивных: у кампаний Мастера кампаний state нет,
 * а SUSPENDED — лишь пауза. Статус выводится рядом с названием. */
export function CampaignPicker({ state, onRetry, search, onSearchChange, selectedIds, onToggle, error, disabled, searchRef }: Props) {
  return (
    <div>
      <label className="title" htmlFor="campaign-search">
        Рекламные кампании *
      </label>
      <input
        id="campaign-search"
        ref={searchRef}
        type="search"
        placeholder="Поиск по названию"
        value={search}
        disabled={disabled || state.status !== "success"}
        aria-invalid={Boolean(error)}
        aria-describedby="campaign-error"
        onChange={(e) => onSearchChange(e.target.value)}
      />

      {state.status === "loading" && <div className="hint">Загрузка кампаний…</div>}

      {state.status === "error" && (
        <div className="field-error" role="alert">
          {state.error.message}{" "}
          <button type="button" className="btn" onClick={onRetry}>
            Повторить
          </button>
        </div>
      )}

      {state.status === "empty" && <div className="hint">Кампаний не найдено.</div>}

      {state.status === "success" && (
        <>
          <div className="choicebox" role="group" aria-label="Рекламные кампании">
            {state.data
              .filter((c) => c.state !== "ARCHIVED")
              .filter((c) => c.name.toLowerCase().includes(search.toLowerCase()))
              .map((campaign) => (
                <label key={campaign.id}>
                  <input
                    type="checkbox"
                    disabled={disabled}
                    checked={selectedIds.includes(campaign.id)}
                    onChange={() => onToggle(campaign.id)}
                  />
                  {campaign.name} <span className="hint">({stateLabel(campaign.state)})</span>
                </label>
              ))}
          </div>
          <div className="hint">Выбрано: {selectedIds.length}</div>
        </>
      )}

      <div id="campaign-error" className="field-error">
        {error}
      </div>
    </div>
  );
}
