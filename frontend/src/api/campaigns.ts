import { request } from "./client";
import type { CampaignOut } from "../types/api";

export function getCampaigns(): Promise<CampaignOut[]> {
  return request<CampaignOut[]>("/campaigns");
}
