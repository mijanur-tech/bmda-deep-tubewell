import { apiRequest } from "./client";

export type SAEReadingStatus = "not_available" | "not_started" | "up_to_date" | "overdue";

export interface SAEReadingTypeActivity {
  status: SAEReadingStatus;
  meter_id: number | null;
  latest_reading_date: string | null;
  days_since_last_reading: number | null;
  collected_by_field_visitor: string | null;
  note: string | null;
}

export interface SAEReadingTubewellActivity {
  tubewell_id: number;
  tubewell_number: string;
  tubewell_name: string;
  tubewell_is_active: boolean;
  field_user_id: number;
  field_user_name: string;
  energy: SAEReadingTypeActivity;
  prepaid: SAEReadingTypeActivity;
}

export interface SAEReadingActivityResponse {
  supervisor_id: number;
  management_unit_id: number;
  warning_threshold_days: number;
  total_assigned_tubewells: number;
  energy_overdue: number;
  prepaid_overdue: number;
  overdue_tubewells: number;
  tubewells: SAEReadingTubewellActivity[];
}

/** SAE identity and team scope are enforced by the backend; no client-supplied IDs. */
export async function getSAEReadingActivity(): Promise<SAEReadingActivityResponse> {
  return apiRequest("/dashboard/sae/reading-activity", { method: "GET" });
}
