import { apiRequest } from "./client";

export interface SAEFieldVisitorItem {
  field_user_id: number;
  full_name: string;
  is_active: boolean;
  assigned_tubewells: number;
}

export interface SAEFieldVisitorSummaryResponse {
  supervisor_id: number;
  management_unit_id: number;

  total_field_visitors: number;
  active_field_visitors: number;
  inactive_field_visitors: number;

  assigned_tubewells: number;
  visitors_without_assignments: number;

  field_visitors: SAEFieldVisitorItem[];
}

/**
 * Read-only SAE Field Visitor Monitoring API.
 *
 * Backend enforces the authenticated supervisor's scope.
 * No management unit or supervisor ID is accepted from UI.
 */
export async function getSAEFieldVisitorSummary():
  Promise<SAEFieldVisitorSummaryResponse> {
  const response = await apiRequest(
    "/dashboard/sae/field-visitor-summary"
  );

  return response as SAEFieldVisitorSummaryResponse;
}