import { request } from "./client";
import type { GoalOut } from "../types/api";

export function getGoals(): Promise<GoalOut[]> {
  return request<GoalOut[]>("/goals");
}
