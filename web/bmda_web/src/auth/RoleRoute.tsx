import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { getCurrentUser } from "../api/auth.api";
import { getAccessToken, removeAccessToken } from "./session";

interface RoleRouteProps {
  children: ReactNode;
  allowedRoles: string[];
}

type AccessStatus =
  | "loading"
  | "authenticated"
  | "unauthenticated"
  | "forbidden"
  | "error";

function RoleRoute({ children, allowedRoles }: RoleRouteProps) {
  const [status, setStatus] = useState<AccessStatus>("loading");
  const [retryCount, setRetryCount] = useState(0);

  const retry = useCallback(() => {
    setStatus("loading");
    setRetryCount((count) => count + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function checkRole() {
      const token = getAccessToken();

      if (!token) {
        if (!cancelled) {
          setStatus("unauthenticated");
        }
        return;
      }

      try {
        const currentUser = await getCurrentUser(token);

        if (cancelled) return;

        if (allowedRoles.includes(currentUser.role)) {
          setStatus("authenticated");
        } else {
          setStatus("forbidden");
        }
      } catch (error) {
        if (cancelled) return;

        if (
          error instanceof Error &&
          error.message === "SESSION_EXPIRED"
        ) {
          removeAccessToken();
          setStatus("unauthenticated");
        } else {
          setStatus("error");
        }
      }
    }

    void checkRole();

    return () => {
      cancelled = true;
    };
  }, [allowedRoles, retryCount]);

  if (status === "loading") {
    return (
      <p role="status" aria-live="polite">
        Verifying your access...
      </p>
    );
  }

  if (status === "unauthenticated") {
    return <Navigate to="/login" replace />;
  }

  if (status === "forbidden") {
    return <Navigate to="/403" replace />;
  }

  if (status === "error") {
    return (
      <div
        role="alert"
        style={{
          maxWidth: "440px",
          margin: "64px auto",
          padding: "24px",
          textAlign: "center",
          fontFamily: "inherit",
        }}
      >
        <h2>Unable to verify access</h2>
        <p>
          The server could not verify your session.
          Please check your connection and try again.
        </p>
        <button
          type="button"
          onClick={retry}
          style={{
            backgroundColor: "#16834a",
            color: "#ffffff",
            border: "none",
            borderRadius: "8px",
            padding: "12px 24px",
            cursor: "pointer",
          }}
        >
          Retry verification
        </button>
      </div>
    );
  }

  return <>{children}</>;
}

export default RoleRoute;
