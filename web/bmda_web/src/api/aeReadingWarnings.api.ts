import { apiRequest } from "./client";

// ============================================================
// SECTION 1: AE READING WARNINGS RESPONSE
// Matches the verified backend API response.
// ============================================================

export interface AEReadingWarnings {
  management_unit_id: number;
  overdue_tubewells: number;
  energy_warnings: number;
  prepaid_warnings: number;
  reading_not_started: number;
  warning_threshold_days: number;
}

// ============================================================
// SECTION 2: GET AE READING WARNINGS
// Uses the existing JWT-enabled API client.
// Backend determines the management unit from authentication.
// ============================================================

export async function getAEReadingWarnings(): Promise<AEReadingWarnings> {
  return apiRequest("/dashboard/ae/reading-warnings", {
    method: "GET",
  });
}
