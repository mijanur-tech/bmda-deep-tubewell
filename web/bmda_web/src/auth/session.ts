const ACCESS_TOKEN_KEY = "bmda_access_token";

export function saveAccessToken(token: string): void {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function getAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function removeAccessToken(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
}

export function hasAccessToken(): boolean {
  return getAccessToken() !== null;
}