
// ============================================================
// SECTION 1: IMPORTS
// Import React Router Outlet and the shared Sidebar.
// ============================================================

import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar/Sidebar";
import "./AdminLayout.css";

// ============================================================
// SECTION 2: SHARED ADMIN LAYOUT
// Display one Sidebar across all nested Admin pages.
// ============================================================

function AdminLayout() {
  return (
    <div className="bmda-shared-admin-layout">

      {/* SECTION 3: SHARED SIDEBAR */}
      <div className="bmda-shared-admin-sidebar">
        <Sidebar />
      </div>

      {/* SECTION 4: PAGE CONTENT */}
      <div className="bmda-shared-admin-content">
        <Outlet />
      </div>

    </div>
  );
}

export default AdminLayout;
