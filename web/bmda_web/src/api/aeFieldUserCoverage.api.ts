import { apiRequest } from "./client";

export interface AEFieldUserCoverageItem {
  field_user_id: number;
  full_name: string;
  is_active: boolean;
  assigned_tubewells: number;
  coverage_percentage: number;
}

export interface AEFieldUserCoverageResponse {
  management_unit_id: number;
  total_tubewells: number;
  assigned_tubewells: number;
  unassigned_tubewells: number;
  unmatched_assignments: number;
  field_users: AEFieldUserCoverageItem[];
}

export async function getAEFieldUserCoverage(): Promise<AEFieldUserCoverageResponse> {
  const response = await apiRequest(
    "/dashboard/ae/field-user-coverage"
  );

  return response as AEFieldUserCoverageResponse;
}
