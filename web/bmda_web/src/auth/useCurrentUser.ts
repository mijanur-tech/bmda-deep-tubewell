import { useEffect, useState } from "react";

import { getCurrentUser } from "../api/auth.api";
import type { CurrentUser } from "../types/auth";
import { getAccessToken, removeAccessToken } from "./session";

interface UseCurrentUserResult {
  user: CurrentUser | null;
  loading: boolean;
  error: string | null;
}

export function useCurrentUser(): UseCurrentUserResult {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCurrentUser() {
      const token = getAccessToken();

      if (!token) {
        setError("No active session.");
        setLoading(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser(token);
        setUser(currentUser);
      } catch (err) {
        removeAccessToken();

        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Failed to load current user.");
        }
      } finally {
        setLoading(false);
      }
    }

    loadCurrentUser();
  }, []);

  return {
    user,
    loading,
    error,
  };
}