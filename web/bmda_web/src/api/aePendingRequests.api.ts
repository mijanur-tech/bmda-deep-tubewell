import { apiRequest } from "./client";

export interface AEPendingTubewellStatusRequest {
  id: number;
  tubewell_id: number;
  status: string;
}

export async function getAEPendingTubewellStatusRequests(): Promise<
  AEPendingTubewellStatusRequest[]
> {
  const response = await apiRequest(
    "/tubewell-status-requests/ae/pending",
    { method: "GET" }
  );

  if (!Array.isArray(response)) {
    throw new Error("Unexpected AE pending requests response.");
  }

  return response as AEPendingTubewellStatusRequest[];
}
