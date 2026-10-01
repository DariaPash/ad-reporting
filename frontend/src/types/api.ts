/** Повторяет схемы backend/app/schemas/*.py; при расхождении источник истины — бэкенд. */

export interface CampaignOut {
  id: number;
  direct_campaign_id: number;
  name: string;
  state: string | null;
  status: string | null;
  updated_at: string;
}

export interface CampaignSyncResult {
  created: number;
  updated: number;
}

export interface GoalOut {
  id: number;
  counter_id: number;
  metrika_goal_id: number;
  name: string;
  goal_type: string | null;
  is_conversion: boolean;
  is_lead: boolean;
  updated_at: string;
}

export interface GoalSyncResult {
  created: number;
  updated: number;
}

export interface ReportCreateIn {
  date_from: string;
  date_to: string;
  campaign_ids: number[];
  goal_ids: number[];
}

/** null означает «не вычисляется» (нулевой знаменатель) — не 0. */
export interface KpiSet {
  impressions: number;
  clicks: number;
  cost: number;
  conversions: number | null;
  leads: number | null;
  ctr: number | null;
  cpc: number | null;
  cr: number | null;
  cpa: number | null;
  cpl: number | null;
}

export interface ReportCampaignRow {
  campaign_id: number;
  campaign_name: string;
  kpi: KpiSet;
}

export interface ReportDatePoint {
  stat_date: string;
  impressions: number;
  clicks: number;
  cost: number;
  conversions: number | null;
  leads: number | null;
}

export interface ReportGoalOut {
  goal_id: number;
  goal_name: string;
  is_conversion: boolean;
  is_lead: boolean;
}

export interface ReportSummaryOut {
  id: number;
  date_from: string;
  date_to: string;
  created_at: string;
  campaign_names: string[];
  goal_names: string[];
}

export interface ReportDetailOut {
  id: number;
  date_from: string;
  date_to: string;
  created_at: string;
  goals: ReportGoalOut[];
  summary: KpiSet;
  by_campaign: ReportCampaignRow[];
  by_date: ReportDatePoint[];
}

export type OperationStatus = "running" | "success" | "error";

export interface OperationLogOut {
  id: number;
  operation_type: string;
  source: string | null;
  status: string;
  started_at: string;
  finished_at: string | null;
  date_from: string | null;
  date_to: string | null;
  records_processed: number | null;
  report_id: number | null;
  message: string | null;
}

export interface HealthResponse {
  status: string;
  database: string;
}

export type ExportFormat = "pdf" | "xlsx";

export type UserRole = "admin" | "specialist";

export interface UserOut {
  id: number;
  username: string;
  role: UserRole;
  created_at: string;
}

export interface UserCreateIn {
  username: string;
  role: UserRole;
}

/** Пароль есть только в ответе на создание — сервер его не хранит и повторно не отдаёт. */
export interface UserCreatedOut extends UserOut {
  password: string;
}

export type ApiStatus = "ok" | "error";

export interface ApiCheckOut {
  direct: ApiStatus;
  metrika: ApiStatus;
}
