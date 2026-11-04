import { apiRequest } from "./client";

export interface UnionItem {
  id: number;
  name: string;
  actual_upazila_id: number;
}

export interface CreateUnionRequest {
  name: string;
  actual_upazila_id: number;
}

export async function getUnions(
  actualUpazilaId?: number
): Promise<UnionItem[]> {
  const query = actualUpazilaId
    ? `?actual_upazila_id=${actualUpazilaId}`
    : "";

  return apiRequest(`/unions${query}`, { method: "GET" });
}

export async function createUnion(
  request: CreateUnionRequest
): Promise<UnionItem> {
  return apiRequest("/unions", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
