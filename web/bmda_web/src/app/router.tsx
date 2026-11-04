import { createBrowserRouter } from "react-router-dom";

import ProtectedRoute from "../auth/ProtectedRoute";
import RoleRoute from "../auth/RoleRoute";
import AdminLayout from "../layouts/AdminLayout";

import LoginPage from "../pages/auth/LoginPage";
import AdminDashboard from "../pages/dashboard/AdminDashboard";
import AEDashboard from "../pages/dashboard/AEDashboard";
import SupervisorDashboard from "../pages/dashboard/SupervisorDashboard";
import UsersPage from "../pages/users/UsersPage";
import CreateUserPage from "../pages/users/CreateUserPage";
import EditUserPage from "../pages/users/EditUserPage";
import TubewellsPage from "../pages/tubewells/TubewellsPage";
import CreateTubewellPage from "../pages/tubewells/CreateTubewellPage";
import EditTubewellPage from "../pages/tubewells/EditTubewellPage";
import DtwMasterCorrectionPage from "../pages/tubewells/DtwMasterCorrectionPage";
import AssignmentsPage from "../pages/assignments/AssignmentsPage";
import AEAssignmentsPage from "../pages/assignments/AEAssignmentsPage";
import MeterManagementPage from "../pages/meters/MeterManagementPage";
import ForbiddenPage from "../pages/errors/ForbiddenPage";
import ApprovalPage from "../pages/approvals/ApprovalPage";

// ============================================================
// BMDA APPLICATION ROUTER
//
// Admin:
// - User and Tubewell Management
// - Read-only Assignment Monitoring
// - Read-only Meter Monitoring
//
// Assistant Engineer:
// - Existing dashboard, assignments and approvals
//
// Sub-Assistant Engineer:
// - Existing dashboard and approvals
//
// Backend permissions remain unchanged.
// ============================================================

export const router = createBrowserRouter([
  { path: "/", element: <LoginPage /> },
  { path: "/login", element: <LoginPage /> },

  // ==========================================================
  // ADMIN WORKSPACE
  // ==========================================================

  {
    element: (
      <ProtectedRoute>
        <RoleRoute allowedRoles={["admin"]}>
          <AdminLayout />
        </RoleRoute>
      </ProtectedRoute>
    ),
    children: [
      { path: "/admin/dashboard", element: <AdminDashboard /> },
      { path: "/admin/users", element: <UsersPage /> },
      { path: "/admin/users/create", element: <CreateUserPage /> },
      {
        path: "/admin/users/:userId/edit",
        element: <EditUserPage />,
      },
      { path: "/admin/tubewells", element: <TubewellsPage /> },
      {
        path: "/admin/tubewells/create",
        element: <CreateTubewellPage />,
      },
      {
        path: "/admin/tubewells/:tubewellId/edit",
        element: <EditTubewellPage />,
      },
      {
        path: "/admin/assignments",
        element: <AssignmentsPage />,
      },
      {
        path: "/admin/meters",
        element: <MeterManagementPage />,
      },
      {
        path: "/admin/dtw-master/correction",
        element: <DtwMasterCorrectionPage />,
      },
    ],
  },

  // ==========================================================
  // ASSISTANT ENGINEER DASHBOARD
  // ==========================================================

  {
    path: "/ae/dashboard",
    element: (
      <ProtectedRoute>
        <RoleRoute allowedRoles={["assistant_engineer"]}>
          <AEDashboard />
        </RoleRoute>
      </ProtectedRoute>
    ),
  },

  // ==========================================================
  // ASSISTANT ENGINEER ASSIGNMENT MANAGEMENT
  // ==========================================================

  {
    path: "/ae/assignments",
    element: (
      <ProtectedRoute>
        <RoleRoute allowedRoles={["assistant_engineer"]}>
          <AEAssignmentsPage />
        </RoleRoute>
      </ProtectedRoute>
    ),
  },

  // ==========================================================
  // SUB-ASSISTANT ENGINEER DASHBOARD
  // Internal role identifier remains "supervisor".
  // ==========================================================

  {
    path: "/supervisor/dashboard",
    element: (
      <ProtectedRoute>
        <RoleRoute allowedRoles={["supervisor"]}>
          <SupervisorDashboard />
        </RoleRoute>
      </ProtectedRoute>
    ),
  },

  // ==========================================================
  // ASSISTANT ENGINEER APPROVALS
  // ==========================================================

  {
    path: "/ae/approvals",
    element: (
      <ProtectedRoute>
        <RoleRoute allowedRoles={["assistant_engineer"]}>
          <ApprovalPage role="assistant_engineer" />
        </RoleRoute>
      </ProtectedRoute>
    ),
  },

  // ==========================================================
  // SUB-ASSISTANT ENGINEER APPROVALS
  // ==========================================================

  {
    path: "/supervisor/approvals",
    element: (
      <ProtectedRoute>
        <RoleRoute allowedRoles={["supervisor"]}>
          <ApprovalPage role="supervisor" />
        </RoleRoute>
      </ProtectedRoute>
    ),
  },

  // ACCESS DENIED
  { path: "/403", element: <ForbiddenPage /> },
]);
