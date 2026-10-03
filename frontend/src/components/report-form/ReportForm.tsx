import { useCallback, useEffect, useRef, useState } from "react";
import { useAsyncList } from "../../hooks/useAsyncList";
import { useReportSubmit } from "../../hooks/useReportSubmit";
import { getCampaigns } from "../../api/campaigns";
import { getGoals } from "../../api/goals";
import { firstErrorField } from "../../utils/validation";
import { DateRangeFields } from "./DateRangeFields";
import { CampaignPicker } from "./CampaignPicker";
import { GoalPicker } from "./GoalPicker";
import { SubmitProgress } from "./SubmitProgress";

const BUSY_KINDS = new Set(["checking", "fetching", "calculating", "saving"]);

export function ReportForm() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [campaignSearch, setCampaignSearch] = useState("");
  const [campaignIds, setCampaignIds] = useState<number[]>([]);
  const [goalIds, setGoalIds] = useState<number[]>([]);

  const dateFromRef = useRef<HTMLInputElement>(null);
  const dateToRef = useRef<HTMLInputElement>(null);
  const campaignSearchRef = useRef<HTMLInputElement>(null);

  const campaignsFetcher = useCallback(() => getCampaigns(), []);
  const goalsFetcher = useCallback(() => getGoals(), []);
  const campaigns = useAsyncList(campaignsFetcher);
  const goals = useAsyncList(goalsFetcher);

  const { phase, submit } = useReportSubmit();
  const busy = BUSY_KINDS.has(phase.kind);
  const errors = phase.kind === "validation_error" ? phase.errors : {};

  useEffect(() => {
    if (phase.kind !== "validation_error") return;
    const field = firstErrorField(phase.errors);
    if (field === "dateFrom") dateFromRef.current?.focus();
    else if (field === "dateTo") dateToRef.current?.focus();
    else if (field === "campaigns") campaignSearchRef.current?.focus();
  }, [phase]);

  function toggleCampaign(id: number) {
    setCampaignIds((current) => (current.includes(id) ? current.filter((c) => c !== id) : [...current, id]));
  }

  function toggleGoal(id: number) {
    setGoalIds((current) => (current.includes(id) ? current.filter((g) => g !== id) : [...current, id]));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    void submit({ dateFrom, dateTo, campaignIds, goalIds });
  }

  return (
    <>
      <h1>Формирование отчета</h1>
      <p className="lead">Выберите период, кампании и при необходимости цели Метрики.</p>

      <form className="panel" noValidate onSubmit={handleSubmit}>
        <DateRangeFields
          dateFrom={dateFrom}
          dateTo={dateTo}
          onChangeFrom={setDateFrom}
          onChangeTo={setDateTo}
          errorFrom={errors.dateFrom}
          errorTo={errors.dateTo}
          disabled={busy}
          dateFromRef={dateFromRef}
          dateToRef={dateToRef}
        />

        <div className="grid2">
          <CampaignPicker
            state={campaigns.state}
            onRetry={campaigns.reload}
            search={campaignSearch}
            onSearchChange={setCampaignSearch}
            selectedIds={campaignIds}
            onToggle={toggleCampaign}
            error={errors.campaigns}
            disabled={busy}
            searchRef={campaignSearchRef}
          />
          <GoalPicker state={goals.state} onRetry={goals.reload} selectedIds={goalIds} onToggle={toggleGoal} disabled={busy} />
        </div>

        <SubmitProgress phase={phase} />

        {phase.kind === "api_error" && (
          <div className="field-error" role="alert" style={{ marginTop: 12 }}>
            {phase.message}
          </div>
        )}
        {phase.kind === "save_error" && (
          <div className="field-error" role="alert" style={{ marginTop: 12 }}>
            {phase.message}
          </div>
        )}

        <div className="actions">
          <button type="submit" className="btn primary" disabled={busy} aria-busy={busy}>
            {busy ? "Формирование…" : "Сформировать отчет"}
          </button>
        </div>
      </form>
    </>
  );
}
