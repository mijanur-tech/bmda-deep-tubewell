// ============================================================
// SECTION 1: IMPORTS
// Authentication, navigation, BMDA logo and sidebar styling.
// ============================================================

import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { removeAccessToken } from "../../auth/session";
import bmdaLogo from "../../assets/bmda-logo.png";
import "./Sidebar.css";

// ============================================================
// SECTION 2: ADMIN SIDEBAR
// Preserve existing logout and responsive mobile navigation.
// ============================================================

function Sidebar() {
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  function handleLogout() {
    removeAccessToken();
    navigate("/login", { replace: true });
  }

  function closeMobileMenu() {
    setMobileOpen(false);
  }

  return (
    <>
      <button
        className="bmda-sidebar-mobile-toggle"
        type="button"
        aria-controls="bmda-admin-sidebar"
        aria-expanded={mobileOpen}
        onClick={() => setMobileOpen((current) => !current)}
      >
        {mobileOpen ? "Close Menu" : "Open Menu"}
      </button>

      <aside
        id="bmda-admin-sidebar"
        className={`bmda-sidebar ${mobileOpen ? "bmda-sidebar-open" : ""}`}
        aria-label="Admin navigation"
      >
        <div className="bmda-sidebar-brand">
          <div className="bmda-sidebar-logo-frame">
            <img
              src={bmdaLogo}
              alt="Barind Multipurpose Development Authority logo"
              className="bmda-sidebar-logo"
            />
          </div>

          <strong>BMDA-PANCHAGARH</strong>

          <span className="bmda-sidebar-office">
            Executive Engineer, Panchagarh Region
          </span>

          <span>Deep Tubewell Management System</span>
        </div>

        <nav className="bmda-sidebar-nav" aria-label="Main menu">
          <NavLink
            to="/admin/dashboard"
            end
            onClick={closeMobileMenu}
            className={({ isActive }) =>
              `bmda-sidebar-link ${
                isActive ? "bmda-sidebar-link-active" : ""
              }`
            }
          >
            Dashboard
          </NavLink>

          <NavLink
            to="/admin/users"
            onClick={closeMobileMenu}
            className={({ isActive }) =>
              `bmda-sidebar-link ${
                isActive ? "bmda-sidebar-link-active" : ""
              }`
            }
          >
            Users Management
          </NavLink>

          <NavLink
            to="/admin/tubewells"
            onClick={closeMobileMenu}
            className={({ isActive }) =>
              `bmda-sidebar-link ${
                isActive ? "bmda-sidebar-link-active" : ""
              }`
            }
          >
            Tubewells Management
          </NavLink>

          <NavLink
            to="/admin/assignments"
            onClick={closeMobileMenu}
            className={({ isActive }) =>
              `bmda-sidebar-link ${
                isActive ? "bmda-sidebar-link-active" : ""
              }`
            }
          >
            Tubewell Assignments
          </NavLink>

          {/* Meter Management: Admin read-only monitoring */}
          <NavLink
            to="/admin/meters"
            onClick={closeMobileMenu}
            className={({ isActive }) =>
              `bmda-sidebar-link ${
                isActive ? "bmda-sidebar-link-active" : ""
              }`
            }
          >
            Meter Management
          </NavLink>

          <NavLink
            to="/admin/dtw-master/correction"
            onClick={closeMobileMenu}
            className={({ isActive }) =>
              `bmda-sidebar-link ${
                isActive ? "bmda-sidebar-link-active" : ""
              }`
            }
          >
            DTW Master Correction
          </NavLink>
        </nav>

        <button
          className="bmda-sidebar-logout"
          type="button"
          onClick={handleLogout}
        >
          Logout
        </button>
      </aside>
    </>
  );
}

export default Sidebar;
