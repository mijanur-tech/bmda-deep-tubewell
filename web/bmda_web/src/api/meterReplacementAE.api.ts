
import { apiRequest } from "./client";

// ============================================================
// SECTION 1: RESPONSE TYPES
// ============================================================

export type MeterReplacementStatus =
  | "pending"
  | "pending_ae_approval"
  | "approved"
  | "rejected";

export type MeterType = "energy" | "prepaid";

export interface AEMeterReplacementRequest {
  id: number;
  tubewell_id: number;
  old_meter_id: number;

  // Required: Backend derives this from the old meter.
  meter_type: MeterType;

  requested_by_user_id: number;
  new_meter_number: string;
  reason: string;
  status: MeterReplacementStatus;
  requested_at: string;

  // SAE recommendation
  reviewed_by_user_id: number | null;
  reviewed_at: string | null;
  review_comment: string | null;

  // AE final review
  ae_reviewed_by_user_id: number | null;
  ae_reviewed_at: string | null;
  ae_review_comment: string | null;

  // Created only after AE final approval
  new_meter_id: number | null;
}

// ============================================================
// SECTION 2: AE PENDING APPROVAL LIST
// ============================================================

export async function getAEPendingMeterReplacements():
  Promise<AEMeterReplacementRequest[]> {

  const response = await apiRequest(
    "/meter-replacements/ae/pending",
    { method: "GET" }
  );

  if (!Array.isArray(response)) {
    throw new Error(
      "Unexpected AE meter replacement response."
    );
  }

  return response as AEMeterReplacementRequest[];
}

// ============================================================
// SECTION 3: AE PENDING REQUEST DETAIL
// ============================================================

export async function getAEMeterReplacementDetail(
  requestId: number
): Promise<AEMeterReplacementRequest> {

  if (!Number.isInteger(requestId) || requestId <= 0) {
    throw new Error("Invalid meter replacement request ID.");
  }

  const response = await apiRequest(
    `/meter-replacements/ae/pending/${requestId}`,
    { method: "GET" }
  );

  return response as AEMeterReplacementRequest;
}

// ============================================================
// SECTION 4: AE FINAL APPROVAL / REJECTION
// ============================================================

export async function reviewAEMeterReplacement(
  requestId: number,
  action: "approved" | "rejected",
  reviewComment?: string
): Promise<AEMeterReplacementRequest> {

  if (!Number.isInteger(requestId) || requestId <= 0) {
    throw new Error("Invalid meter replacement request ID.");
  }

  const comment = reviewComment?.trim() || null;

  if (comment && comment.length > 500) {
    throw new Error(
      "Review comment cannot exceed 500 characters."
    );
  }

  const response = await apiRequest(
    `/meter-replacements/ae/pending/${requestId}/review`,
    {
      method: "POST",
      body: JSON.stringify({
        action,
        review_comment: comment,
      }),
    }
  );

  return response as AEMeterReplacementRequest;
}
