import { request } from "./client";
import type { UserOut } from "../types/api";

/** Текущий пользователь (браузер уже прошёл HTTP Basic) — для показа админ-пунктов меню. */
export function getMe(): Promise<UserOut> {
  return request<UserOut>("/auth/me");
}
