import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { getAccessToken } from "./session";

interface ProtectedRouteProps {
  children: ReactNode;
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const accessToken = getAccessToken();

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export default ProtectedRoute;