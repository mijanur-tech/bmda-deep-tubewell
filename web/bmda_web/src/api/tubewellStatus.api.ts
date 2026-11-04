// ============================================================
// SECTION 1: SHARED API CLIENT
// Reuses existing JWT authentication and error handling.
// ============================================================

import { apiRequest } from "./client";

// ============================================================
// SECTION 2: BACKEND-ALIGNED TYPES
// ============================================================

export type ApprovalAction = "approved" | "rejected";

export type TubewellRequestedStatus = "active" | "inactive";

export type TubewellApprovalStatus =
  | "pending"
  | "pending_ae_approval"
  | "approved"
  | "rejected";

export interface TubewellStatusRequest {
  id: number;
  tubewell_id: number;
  requested_by_user_id: number;
  requested_status: TubewellRequestedStatus;
  reason: string;
  status: TubewellApprovalStatus;
  requested_at: string;

  reviewed_by_user_id: number | null;
  reviewed_at: string | null;
  review_comment: string | null;

  ae_reviewed_by_user_id: number | null;
  ae_reviewed_at: string | null;
  ae_review_comment: string | null;
}

export interface ApprovalReviewPayload {
  action: ApprovalAction;
  review_comment?: string | null;
}

const BASE_PATH = "/tubewell-status-requests";

// ============================================================
// SECTION 3: SUPERVISOR APPROVAL API
// ============================================================

export async function getSupervisorPendingRequests():
  Promise<TubewellStatusRequest[]> {
  return apiRequest(`${BASE_PATH}/pending`);
}

export async function reviewSupervisorRequest(
  requestId: number,
  payload: ApprovalReviewPayload
): Promise<TubewellStatusRequest> {
  return apiRequest(`${BASE_PATH}/pending/${requestId}/review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ============================================================
// SECTION 4: ASSISTANT ENGINEER APPROVAL API
// ============================================================

export async function getAEPendingRequests():
  Promise<TubewellStatusRequest[]> {
  return apiRequest(`${BASE_PATH}/ae/pending`);
}

export async function reviewAERequest(
  requestId: number,
  payload: ApprovalReviewPayload
): Promise<TubewellStatusRequest> {
  return apiRequest(`${BASE_PATH}/ae/pending/${requestId}/review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
