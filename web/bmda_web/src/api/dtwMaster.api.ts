
 // ============================================================
 // SECTION 1: IMPORT API CLIENT
 // Use the existing backend API request function.
 // ============================================================

 import { apiRequest } from "./client";


 // ============================================================
 // SECTION 2: DTW MASTER INTERFACE
 // Define the DTW information returned by the backend.
 // ============================================================

 export interface DtwMasterItem {
   id: number;
   dtw_number: string;
   mouza_id: number;
 }


 // ============================================================
 // SECTION 3: FETCH DTW MASTER DATA
 // Load DTW records for the selected Mouza.
 // Existing behavior remains unchanged.
 // ============================================================

 export async function getDtwMaster(
   mouzaId: number
 ): Promise<DtwMasterItem[]> {

   // CHECK 1: Validate Mouza ID.
   if (!Number.isInteger(mouzaId) || mouzaId <= 0) {
     throw new Error("A valid Mouza must be selected.");
   }

   // CHECK 2: Request DTW records from the backend.
   const data = await apiRequest(
     `/dtw-master?mouza_id=${mouzaId}`,
     {
       method: "GET",
     }
   );

   // RESULT: Return the DTW Master records.
   return data as DtwMasterItem[];
 }


 // ============================================================
 // SECTION 4: CREATE DTW MASTER RECORD
 // Adds a Master number only; it does not register a Tubewell.
 // Existing behavior remains unchanged.
 // ============================================================

 export interface CreateDtwMasterRequest {
   dtw_number: string;
   mouza_id: number;
 }

 export async function createDtwMaster(
   data: CreateDtwMasterRequest
 ): Promise<DtwMasterItem> {
   return apiRequest("/dtw-master", {
     method: "POST",
     body: JSON.stringify(data),
   });
 }


 // ============================================================
 // SECTION 5: ADMIN DTW MASTER CORRECTION
 //
 // The backend determines the actual Upazila and Union from
 // the selected Mouza.
 //
 // The permanent DTW Number and Master ID remain unchanged.
 // ============================================================

 export interface DtwMasterCorrectionRequest {
   mouza_id: number;
   management_unit_id: number;
 }

 export async function correctDtwMaster(
   masterId: number,
   data: DtwMasterCorrectionRequest
 ): Promise<DtwMasterItem> {

   // CHECK 1: Validate Master ID.
   if (!Number.isInteger(masterId) || masterId <= 0) {
     throw new Error("Invalid DTW Master ID.");
   }

   // CHECK 2: Validate correction location IDs.
   if (
     !Number.isInteger(data.mouza_id) ||
     data.mouza_id <= 0 ||
     !Number.isInteger(data.management_unit_id) ||
     data.management_unit_id <= 0
   ) {
     throw new Error("Please select a valid correction location.");
   }

   // CHECK 3: Send the correction to the Admin-only backend.
   return apiRequest(
     `/dtw-master/${masterId}/correction`,
     {
       method: "PUT",
       body: JSON.stringify(data),
     }
   );
 }
