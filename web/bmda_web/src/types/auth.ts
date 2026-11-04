// ============================================================
// SECTION 1: LOGIN RESPONSE
// JWT token returned after a successful login.
// ============================================================

export interface LoginResponse {
  access_token: string;
  token_type?: string;
}

// ============================================================
// SECTION 2: CURRENT USER
// Information returned by the authenticated /auth/me API.
// ============================================================

export interface CurrentUser {
  id: number;
  full_name: string;
  username: string;
  role: string;

  // Assigned Management Unit ID and name.
  upazila_id: number | null;
  upazila_name: string | null;

  supervisor_id: number | null;
  is_active: boolean;
  created_at: string;
}