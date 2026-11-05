import { apiRequest } from "./client";

// ============================================================
// SECTION 1: REQUEST TYPES
// ============================================================

export type SAERequestType =
  | "meter_replacement"
  | "tubewell_status"
  | "reading_correction";

export interface SAEPendingRequest {
  request_type: SAERequestType;
  request_id: number;
  tubewell_id: number;
  reading_id: number | null;
  requested_by_user_id: number;
  reason: string;
  status: "pending";
  requested_at: string;

  requested_status: string | null;
  old_meter_id: number | null;
  new_meter_number: string | null;
  reading_type: string | null;
}

export type SAEReviewAction = "approved" | "rejected";

export interface SAEReviewPayload {
  action: SAEReviewAction;
  review_comment?: string | null;
}

// ============================================================
// SECTION 2: VALIDATION
// ============================================================

function validateRequestId(requestId: number): void {
  if (!Number.isInteger(requestId) || requestId <= 0) {
    throw new Error("Invalid request ID.");
  }
}

function validateReviewPayload(payload: SAEReviewPayload): void {
  if (
    payload.action !== "approved" &&
    payload.action !== "rejected"
  ) {
    throw new Error("Invalid review action.");
  }

  const comment = payload.review_comment?.trim() || null;

  if (comment && comment.length > 500) {
    throw new Error(
      "Review comment cannot exceed 500 characters."
    );
  }
}

// ============================================================
// SECTION 3: COMBINED SAE PENDING REQUEST QUEUE
// ============================================================

export async function getSAEPendingRequests():
  Promise<SAEPendingRequest[]> {

  const response = await apiRequest(
    "/pending-requests",
    { method: "GET" }
  );

  if (!Array.isArray(response)) {
    throw new Error(
      "Unexpected SAE pending requests response."
    );
  }

  return response as SAEPendingRequest[];
}

// ============================================================
// SECTION 4: READING CORRECTION REVIEW
// ============================================================

export async function reviewSAEReadingCorrection(
  requestId: number,
  payload: SAEReviewPayload
): Promise<unknown> {

  validateRequestId(requestId);
  validateReviewPayload(payload);

  return apiRequest(
    `/reading-corrections/pending/${requestId}/review`,
    {
      method: "POST",
      body: JSON.stringify({
        action: payload.action,
        review_comment: payload.review_comment?.trim() || null,
      }),
    }
  );
}

// ============================================================
// SECTION 5: METER REPLACEMENT REVIEW
// ============================================================

export async function reviewSAEMeterReplacement(
  requestId: number,
  payload: SAEReviewPayload
): Promise<unknown> {

  validateRequestId(requestId);
  validateReviewPayload(payload);

  return apiRequest(
    `/meter-replacements/pending/${requestId}/review`,
    {
      method: "POST",
      body: JSON.stringify({
        action: payload.action,
        review_comment: payload.review_comment?.trim() || null,
      }),
    }
  );
}

// ============================================================
// SECTION 6: TUBEWELL STATUS REVIEW
// ============================================================

export async function reviewSAETubewellStatus(
  requestId: number,
  payload: SAEReviewPayload
): Promise<unknown> {

  validateRequestId(requestId);
  validateReviewPayload(payload);

  return apiRequest(
    `/tubewell-status-requests/pending/${requestId}/review`,
    {
      method: "POST",
      body: JSON.stringify({
        action: payload.action,
        review_comment: payload.review_comment?.trim() || null,
      }),
    }
  );
}
