import { apiRequest } from "./client";

export interface ActualUpazila {
  id: number;
  name: string;
  management_unit_id: number;
}

export async function getActualUpazilas(
  managementUnitId?: number
): Promise<ActualUpazila[]> {
  const query = managementUnitId
    ? `?management_unit_id=${managementUnitId}`
    : "";

  return apiRequest(
    `/actual-upazilas${query}`,
    {
      method: "GET",
    }
  );
}