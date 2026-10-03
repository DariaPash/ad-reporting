import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAsyncList } from "../../hooks/useAsyncList";
import { listReports } from "../../api/reports";
import { ListState } from "../common/ListState";
import { HistoryTable } from "./HistoryTable";

export function ReportHistory() {
  const navigate = useNavigate();
  const fetcher = useCallback(() => listReports(), []);
  const { state, reload } = useAsyncList(fetcher);

  return (
    <>
      <div className="row space">
        <div>
          <h1>История отчетов</h1>
          <p className="lead">Ранее сформированные и сохраненные отчеты.</p>
        </div>
      </div>
      <ListState
        state={state}
        onRetry={reload}
        emptyTitle="Отчеты еще не сформированы"
        emptyHint={
          <>
            <p className="lead">Создайте первый отчет по рекламным кампаниям.</p>
            <button type="button" className="btn primary" onClick={() => navigate("/report/new")}>
              Сформировать отчет
            </button>
          </>
        }
      >
        {(reports) => <HistoryTable reports={reports} />}
      </ListState>
    </>
  );
}
