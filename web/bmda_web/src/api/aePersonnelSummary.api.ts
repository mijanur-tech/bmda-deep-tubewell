import { apiRequest } from "./client";

// ============================================================
// SECTION 1: PERSONNEL STATUS COUNTS
// Matches the backend read-only response schema.
// ============================================================

export interface PersonnelStatusCounts {
  total: number;
  active: number;
  inactive: number;
}

// ============================================================
// SECTION 2: AE PERSONNEL SUMMARY RESPONSE
// Contains aggregate data for the authenticated AE's unit.
// ============================================================

export interface AEPersonnelSummary {
  management_unit_id: number;
  sub_assistant_engineers: PersonnelStatusCounts;
  field_visitors: PersonnelStatusCounts;
}

// ============================================================
// SECTION 3: GET AE PERSONNEL SUMMARY
// Uses the existing JWT-enabled API client.
// Backend determines the management unit from authentication.
// ============================================================

export async function getAEPersonnelSummary(): Promise<AEPersonnelSummary> {
  return apiRequest("/dashboard/ae/personnel-summary", {
    method: "GET",
  });
}
