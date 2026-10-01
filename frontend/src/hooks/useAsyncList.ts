import { useCallback, useEffect, useRef, useState } from "react";
import type { AppError } from "../types/errors";
import { isAppError } from "../types/errors";

export type AsyncListState<T> =
  | { status: "loading" }
  | { status: "error"; error: AppError }
  | { status: "empty" }
  | { status: "success"; data: T[] };

const UNKNOWN_ERROR: AppError = { kind: "unknown", httpStatus: null, code: null, message: "Не удалось загрузить данные." };

/** Общая логика loading/error/empty/success + reload() для списков. У каждого списка
 * свой экземпляр, чтобы ошибка одного не маскировала состояние другого. */
export function useAsyncList<T>(fetcher: () => Promise<T[]>): { state: AsyncListState<T>; reload: () => void } {
  const [state, setState] = useState<AsyncListState<T>>({ status: "loading" });
  const requestIdRef = useRef(0);

  const load = useCallback(() => {
    const requestId = ++requestIdRef.current;
    setState({ status: "loading" });
    fetcher().then(
      (data) => {
        if (requestIdRef.current !== requestId) return;
        setState(data.length === 0 ? { status: "empty" } : { status: "success", data });
      },
      (error: unknown) => {
        if (requestIdRef.current !== requestId) return;
        setState({ status: "error", error: isAppError(error) ? error : UNKNOWN_ERROR });
      },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { state, reload: load };
}
