import { useEffect, useState } from "react";
import { getMe } from "../api/auth";
import type { UserOut } from "../types/api";

export type CurrentUserState =
  | { status: "loading" }
  | { status: "error" }
  | { status: "success"; user: UserOut };

/** Текущий пользователь и его роль — определяет видимость админ-разделов. Это только UX
 * (проверка на бэкенде), поэтому ошибка не блокирует интерфейс, а лишь скрывает их. */
export function useCurrentUser(): CurrentUserState {
  const [state, setState] = useState<CurrentUserState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    getMe().then(
      (user) => {
        if (!cancelled) setState({ status: "success", user });
      },
      () => {
        if (!cancelled) setState({ status: "error" });
      },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

export function isAdmin(state: CurrentUserState): boolean {
  return state.status === "success" && state.user.role === "admin";
}
