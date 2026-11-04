import { apiRequest } from "./client";

export interface MouzaItem {
  id: number;
  name: string;
  union_id: number;
}

export interface CreateMouzaRequest {
  name: string;
  union_id: number;
}

export async function getMouzas(
  unionId?: number
): Promise<MouzaItem[]> {
  const query = unionId ? `?union_id=${unionId}` : "";
  return apiRequest(`/mouzas${query}`, { method: "GET" });
}

export async function createMouza(
  request: CreateMouzaRequest
): Promise<MouzaItem> {
  return apiRequest("/mouzas", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
