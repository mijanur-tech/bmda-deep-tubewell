
 // ============================================================
 // BMDA TUBEWELL ASSIGNMENT API
 //
 // Admin: Read-only access across all management units.
 // Assistant Engineer: Read/write access within own unit.
 // Supervisor / Field User: No assignment-management access.
 //
 // Authorization is enforced by FastAPI.
 // ============================================================

 import { apiRequest } from "./client";

 // ============================================================
 // SECTION 1: ASSIGNMENT DATA TYPE
 // Matches FastAPI AssignmentResponse.
 // ============================================================

 export interface AssignmentItem {
   id: number;
   tubewell_id: number;
   field_user_id: number;
   assigned_at: string | null;
   ended_at: string | null;
 }

 // ============================================================
 // SECTION 2: ASSIGNMENT CREATE REQUEST TYPE
 // ============================================================

 export interface AssignmentCreateRequest {
   tubewell_id: number;
   field_user_id: number;
   assigned_at: string | null;
 }

 // ============================================================
 // SECTION 3: ELIGIBLE FIELD USER DATA TYPE
 // Matches FastAPI EligibleFieldUserResponse.
 // ============================================================

 export interface EligibleFieldUserItem {
   id: number;
   full_name: string;
   management_unit_id: number;
 }

 // ============================================================
 // SECTION 4: LIST ASSIGNMENTS
 //
 // Admin: All management units, read-only.
 // Assistant Engineer: Own management unit only.
 // ============================================================

 export async function getAssignments(
   currentOnly = false
 ): Promise<AssignmentItem[]> {
   const query = currentOnly ? "?current_only=true" : "";

   return apiRequest(`/assignments${query}`, {
     method: "GET",
   });
 }

 // ============================================================
 // SECTION 5: ELIGIBLE FIELD USERS
 //
 // Admin: All active Field Users, read-only.
 // Assistant Engineer: Active Field Users from own unit.
 //
 // Backend enforces role and management-unit isolation.
 // ============================================================

 export async function getEligibleFieldUsers(): Promise<
   EligibleFieldUserItem[]
 > {
   return apiRequest("/assignments/eligible-field-users", {
     method: "GET",
   });
 }

 // ============================================================
 // SECTION 6: CURRENT ASSIGNMENT FOR ONE TUBEWELL
 // ============================================================

 export async function getCurrentAssignment(
   tubewellId: number
 ): Promise<AssignmentItem | null> {
   return apiRequest(
     `/assignments/current?tubewell_id=${tubewellId}`,
     {
       method: "GET",
     }
   );
 }

 // ============================================================
 // SECTION 7: ASSIGNMENT HISTORY
 // ============================================================

 export async function getAssignmentHistory(
   tubewellId: number
 ): Promise<AssignmentItem[]> {
   return apiRequest(
     `/assignments/history/${tubewellId}`,
     {
       method: "GET",
     }
   );
 }

 // ============================================================
 // SECTION 8: CREATE OR REASSIGN TUBEWELL
 //
 // Assistant Engineer only, within own management unit.
 // Admin is not authorized to create or reassign.
 //
 // This function sends POST only when explicitly called.
 // ============================================================

 export async function createOrReassignAssignment(
   request: AssignmentCreateRequest
 ): Promise<AssignmentItem> {
   return apiRequest("/assignments", {
     method: "POST",
     body: JSON.stringify(request),
   });
 }
