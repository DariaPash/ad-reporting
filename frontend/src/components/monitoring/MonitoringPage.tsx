import { useState } from "react";
import { checkApiAvailability } from "../../api/monitoring";
import { StatusBadge } from "../common/StatusBadge";
import type { ApiCheckOut } from "../../types/api";
import { isAppError } from "../../types/errors";

export function MonitoringPage() {
  const [checkResult, setCheckResult] = useState<ApiCheckOut | null>(null);
  const [checking, setChecking] = useState(false);
  const [checkError, setCheckError] = useState<string | null>(null);

  async function handleCheckApi() {
    setChecking(true);
    setCheckError(null);
    try {
      setCheckResult(await checkApiAvailability());
    } catch (err) {
      setCheckError(isAppError(err) ? err.message : "Не удалось проверить доступность API.");
    } finally {
      setChecking(false);
    }
  }

  return (
    <>
      <h1>Мониторинг</h1>
      <p className="lead">Доступность внешних API.</p>

      <div className="panel">
        <h2>Доступность внешних API</h2>
        <p className="hint">Проверяет обращение к Яндекс.Директу и Яндекс.Метрике; результат также попадает в журнал операций.</p>
        <div className="row" style={{ marginTop: 12 }}>
          <button type="button" className="btn primary" onClick={handleCheckApi} disabled={checking} aria-busy={checking}>
            {checking ? "Проверка…" : "Проверить доступность API"}
          </button>
          {checkResult && (
            <>
              <StatusBadge tone={checkResult.direct === "ok" ? "ok" : "bad"}>Директ: {checkResult.direct === "ok" ? "доступен" : "недоступен"}</StatusBadge>
              <StatusBadge tone={checkResult.metrika === "ok" ? "ok" : "bad"}>Метрика: {checkResult.metrika === "ok" ? "доступна" : "недоступна"}</StatusBadge>
            </>
          )}
        </div>
        {checkError && (
          <div className="field-error" role="alert" style={{ marginTop: 10 }}>
            {checkError}
          </div>
        )}
      </div>
    </>
  );
}
