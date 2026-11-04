import { apiRequest } from "./client";
import type { CurrentUser, LoginResponse } from "../types/auth";

export interface LoginRequest {
  username: string;
  password: string;
}

export async function loginUser(
  data: LoginRequest
): Promise<LoginResponse> {
  return apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getCurrentUser(
  accessToken: string
): Promise<CurrentUser> {
  return apiRequest("/auth/me", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}