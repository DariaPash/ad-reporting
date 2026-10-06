import { request } from "./client";
import type { UserCreateIn, UserCreatedOut, UserOut } from "../types/api";

export function listUsers(): Promise<UserOut[]> {
  return request<UserOut[]>("/users");
}

export function createUser(input: UserCreateIn): Promise<UserCreatedOut> {
  return request<UserCreatedOut>("/users", { method: "POST", body: input });
}
