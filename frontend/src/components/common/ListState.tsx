import type { ReactNode } from "react";
import type { AsyncListState } from "../../hooks/useAsyncList";

interface Props<T> {
  state: AsyncListState<T>;
  onRetry: () => void;
  emptyTitle: string;
  emptyHint?: ReactNode;
  children: (data: T[]) => ReactNode;
}

/** Общая обёртка loading/error/empty/success для списков (см. useAsyncList). */
export function ListState<T>({ state, onRetry, emptyTitle, emptyHint, children }: Props<T>) {
  if (state.status === "loading") {
    return (
      <div className="panel" role="status" aria-live="polite">
        Загрузка…
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="panel" role="alert">
        <p>{state.error.message}</p>
        <button type="button" className="btn" onClick={onRetry}>
          Повторить
        </button>
      </div>
    );
  }

  if (state.status === "empty") {
    return (
      <div className="empty">
        <h2>{emptyTitle}</h2>
        {emptyHint}
      </div>
    );
  }

  return <>{children(state.data)}</>;
}
