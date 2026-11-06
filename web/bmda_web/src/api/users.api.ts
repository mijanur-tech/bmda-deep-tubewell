import { apiRequest } from "./client";

// ============================================================
// SECTION 1: USER DATA TYPES
// Define user information returned by the backend.
// ============================================================

export interface UserItem {
  id: number;
  full_name: string;
  username: string;
  role: string;
  upazila_id: number | null;
  supervisor_id: number | null;
  is_active: boolean;
  created_at: string;
}

export interface ManagementUnit {
  id: number;
  name: string;
}

// ============================================================
// SECTION 2: CREATE USER TYPES
// Keep the existing Create User functionality unchanged.
// ============================================================

export type CreateUserRole =
  | "assistant_engineer"
  | "supervisor"
  | "field_user";

export interface CreateUserRequest {
  full_name: string;
  username: string;
  password: string;
  role: CreateUserRole;
  upazila_id: number;
  supervisor_id?: number | null;
}

// ============================================================
// SECTION 3: UPDATE USER TYPE
// Only full name and username can be updated.
// ============================================================

export interface UpdateUserRequest {
  full_name: string;
  username: string;
}

// ============================================================
// SECTION 4: EXISTING USER API FUNCTIONS
// Preserve the working list and create operations.
// ============================================================

export async function getUsers(): Promise<UserItem[]> {
  return apiRequest("/users", {
    method: "GET",
  });
}

export async function getManagementUnits(): Promise<ManagementUnit[]> {
  return apiRequest("/users/management-units", {
    method: "GET",
  });
}

export async function createUser(
  data: CreateUserRequest
): Promise<UserItem> {
  return apiRequest("/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ============================================================
// SECTION 5: GET SINGLE USER
// Load the existing user before opening the Edit form.
// ============================================================

export async function getUser(
  userId: number
): Promise<UserItem> {
  return apiRequest(`/users/${userId}`, {
    method: "GET",
  });
}

// ============================================================
// SECTION 6: UPDATE USER
// Send allowed profile corrections to the backend.
// JWT authentication is handled by the existing API client.
// ============================================================

export async function updateUser(
  userId: number,
  data: UpdateUserRequest
): Promise<UserItem> {
  return apiRequest(`/users/${userId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// ============================================================
// SECTION 7: ACTIVATE / DEACTIVATE USER
// Admin-only status change; server validates hierarchy rules.
// ============================================================

export interface ChangeUserStatusRequest {
  is_active: boolean;
}

export async function changeUserStatus(
  userId: number,
  data: ChangeUserStatusRequest
): Promise<UserItem> {
  return apiRequest(`/users/${userId}/status`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
