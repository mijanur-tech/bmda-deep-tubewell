import { apiRequest } from "./client";

export interface MeterItem {
  id: number;
  tubewell_id: number;
  meter_number: string | null;
  installed_at: string | null;
  removed_at: string | null;
}

export interface CreateMeterRequest {
  tubewell_id: number;
  meter_number?: string | null;
  installed_at?: string | null;
  removed_at?: string | null;
}

export async function getMeters(
  tubewellId?: number
): Promise<MeterItem[]> {
  const query =
    tubewellId === undefined
      ? ""
      : `?tubewell_id=${encodeURIComponent(tubewellId)}`;

  const result = await apiRequest(`/meters${query}`);

  return result as MeterItem[];
}

export async function getMeter(
  meterId: number
): Promise<MeterItem> {
  const result = await apiRequest(`/meters/${meterId}`);

  return result as MeterItem;
}

export async function createMeter(
  payload: CreateMeterRequest
): Promise<MeterItem> {
  const result = await apiRequest("/meters", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  return result as MeterItem;
}
