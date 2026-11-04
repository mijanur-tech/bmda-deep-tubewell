import { getAccessToken, removeAccessToken } from "../auth/session";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
) {
  const token = getAccessToken();

  const headers = new Headers(options.headers);

  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    removeAccessToken();
    throw new Error("SESSION_EXPIRED");
  }

  if (!response.ok) {
    let errorMessage = `API request failed with status ${response.status}`;

    try {
      const errorData = await response.json();

      if (errorData?.detail) {
        if (typeof errorData.detail === "string") {
          errorMessage = errorData.detail;
        }
      }
    } catch {
      // Response JSON না হলে default error message থাকবে
    }

    throw new Error(errorMessage);
  }

  const contentType = response.headers.get("content-type");

  if (contentType?.includes("application/json")) {
    return response.json();
  }

  return response;
}

export { API_BASE_URL };