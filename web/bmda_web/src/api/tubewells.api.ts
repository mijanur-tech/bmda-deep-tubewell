// ============================================================
// SECTION 1: IMPORT API CLIENT
// Existing API client handles JWT authentication.
// ============================================================

import { apiRequest } from "./client";


// ============================================================
// SECTION 2: TUBEWELL DATA TYPE
// Information returned by the BMDA backend.
// ============================================================

export interface TubewellItem {
  id: number;
  tubewell_number: string;
  name: string;
  management_unit_id: number;
  actual_upazila: string;
  union_name: string;
  mouza: string;
  is_active: boolean;
}


// ============================================================
// SECTION 3: CREATE TUBEWELL REQUEST
// Information required for a new tubewell.
// ============================================================

export interface CreateTubewellRequest {
  tubewell_number: string;
  name: string;
  management_unit_id: number;
  actual_upazila: string;
  union_name: string;
  mouza: string;
}


// ============================================================
// SECTION 4: UPDATE TUBEWELL REQUEST
// Admin can edit existing tubewell information.
// ============================================================

export type UpdateTubewellRequest = CreateTubewellRequest;


// ============================================================
// SECTION 5: GET ALL TUBEWELLS
// ============================================================

export async function getTubewells(): Promise<TubewellItem[]> {
  return apiRequest("/tubewells", {
    method: "GET",
  });
}


// ============================================================
// SECTION 6: GET ONE TUBEWELL
// Load information for the Edit page.
// ============================================================

export async function getTubewell(
  tubewellId: number
): Promise<TubewellItem> {
  return apiRequest(`/tubewells/${tubewellId}`, {
    method: "GET",
  });
}


// ============================================================
// SECTION 7: CREATE TUBEWELL
// Existing Create functionality remains unchanged.
// ============================================================

export async function createTubewell(
  data: CreateTubewellRequest
): Promise<TubewellItem> {
  return apiRequest("/tubewells", {
    method: "POST",
    body: JSON.stringify(data),
  });
}


// ============================================================
// SECTION 8: UPDATE TUBEWELL
// Only authorized Admin users can edit tubewells.
// Backend validates the request.
// ============================================================

export async function updateTubewell(
  tubewellId: number,
  data: UpdateTubewellRequest
): Promise<TubewellItem> {
  return apiRequest(`/tubewells/${tubewellId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}


// ============================================================
// SECTION 9: DEACTIVATE / REACTIVATE TUBEWELL
//
// true  = Activate
// false = Deactivate
//
// No permanent delete function is provided.
// ============================================================

export async function updateTubewellStatus(
  tubewellId: number,
  isActive: boolean
): Promise<TubewellItem> {
  return apiRequest(`/tubewells/${tubewellId}/status`, {
    method: "PATCH",
    body: JSON.stringify({
      is_active: isActive,
    }),
  });
}