import { apiRequest } from "./client";

/** Current tubewell assignment within the authenticated SAE's authorized scope. */
export interface SAETubewellAssignmentItem {
  assignment_id: number;
  field_user_id: number;
  field_user_name: string;
  field_user_is_active: boolean;
  tubewell_id: number;
  tubewell_number: string;
  tubewell_name: string;
  tubewell_is_active: boolean;
  actual_upazila: string | null;
  union_name: string | null;
  mouza: string | null;
  assigned_at: string | null;
}

export interface SAETubewellAssignmentsResponse {
  supervisor_id: number;
  management_unit_id: number;
  total_assignments: number;
  assignments: SAETubewellAssignmentItem[];
}

/**
 * Read-only SAE assignment monitoring endpoint.
 * Supervisor ID and management unit are derived from the server-side session.
 */
export async function getSAETubewellAssignments(): Promise<SAETubewellAssignmentsResponse> {
  return apiRequest("/dashboard/sae/tubewell-assignments", {
    method: "GET",
  });
}
