import { useCallback } from "react";
import { useAsyncList } from "../../hooks/useAsyncList";
import { listOperations } from "../../api/operations";
import { ListState } from "../common/ListState";
import { OperationsTable } from "./OperationsTable";

export function OperationsLog() {
  const fetcher = useCallback(() => listOperations(), []);
  const { state, reload } = useAsyncList(fetcher);

  return (
    <>
      <h1>Журнал операций</h1>
      <p className="lead">Безопасные сведения о выполнении системных операций.</p>
      <ListState state={state} onRetry={reload} emptyTitle="Журнал пока пуст">
        {(operations) => <OperationsTable operations={operations} />}
      </ListState>
    </>
  );
}
