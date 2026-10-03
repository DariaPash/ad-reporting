import type { GoalOut } from "../types/api";

/** GoalOut не содержит макро/микро-флага — бейдж выводится из is_conversion/is_lead. */
export function goalBadgeLabel(goal: Pick<GoalOut, "is_conversion" | "is_lead">): string {
  return goal.is_conversion || goal.is_lead ? "макроцель" : "микроцель";
}
