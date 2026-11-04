// ============================================================
// SECTION 1: IMPORTS
// Keep existing user data APIs and navigation.
// ============================================================
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  getManagementUnits,
  getUsers,
  type ManagementUnit,
  type UserItem,
} from "../../api/users.api";
import "./UsersPage.css";

// ============================================================
// SECTION 2: USER MANAGEMENT PAGE
// Only presentation has changed; data and routes are unchanged.
// ============================================================
function UsersPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [managementUnits, setManagementUnits] = useState<ManagementUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // SECTION 3: LOAD EXISTING USER AND UNIT DATA
  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      try {
        const [usersData, managementUnitsData] = await Promise.all([
          getUsers(),
          getManagementUnits(),
        ]);
        if (!cancelled) {
          setUsers(usersData);
          setManagementUnits(managementUnitsData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load users.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadData();
    return () => { cancelled = true; };
  }, []);

  // SECTION 4: EXISTING NAVIGATION
  function handleBack() {
    navigate("/admin/dashboard");
  }

  function handleCreateUser() {
    navigate("/admin/users/create");
  }

  // SECTION 4A: EDIT USER NAVIGATION
  // Open the selected user's profile without changing other data.
  function handleEditUser(userId: number) {
    navigate(`/admin/users/${userId}/edit`);
  }

  // SECTION 5: DISPLAY HELPERS
  function getManagementUnitName(upazilaId: number | null): string {
    if (!upazilaId) return "-";
    const unit = managementUnits.find((item) => item.id === upazilaId);
    return unit?.name ?? `ID: ${upazilaId}`;
  }

  function getParentName(supervisorId: number | null): string {
    if (!supervisorId) return "-";
    const parentUser = users.find((user) => user.id === supervisorId);
    return parentUser?.full_name ?? `User ID: ${supervisorId}`;
  }

  function getRoleName(role: string): string {
    if (role === "admin") return "Admin";
    if (role === "assistant_engineer") return "Assistant Engineer";
    if (role === "supervisor") return "Sub-Assistant Engineer";
    if (role === "field_user") return "Field User";
    return role;
  }

  // SECTION 6: LOADING AND ERROR STATES
  if (loading) {
    return <main className="bmda-users-page"><p className="users-notice" role="status">Loading users...</p></main>;
  }

  if (error) {
    return <main className="bmda-users-page"><p className="users-notice users-error" role="alert">{error}</p></main>;
  }

  // SECTION 7: GREEN + WHITE PAGE LAYOUT
  return (
    <main className="bmda-users-page">
      <header className="users-page-header">
        <div>
          <h1 className="users-page-title">Users Management</h1>
          <p className="users-page-subtitle">View registered users, roles and reporting lines.</p>
        </div>
        <div className="users-page-actions">
          <button type="button" className="users-btn users-btn-outline" onClick={handleBack}>Back to Dashboard</button>
          <button type="button" className="users-btn users-btn-primary" onClick={handleCreateUser}>+ Create User</button>
        </div>
      </header>

      {/* SECTION 8: TOTAL USERS SUMMARY */}
      <section className="users-summary" aria-label="User summary">
        <span>Total Users</span>
        <strong>{users.length}</strong>
      </section>

      {/* SECTION 9: INDEPENDENT SCROLLABLE USER TABLE */}
      <section className="users-table-card" aria-label="Registered users">
        <div className="users-table-caption">Showing <strong>{users.length}</strong> users</div>
        <div className="users-table-scroll" role="region" aria-label="Scrollable users table" tabIndex={0}>
          <table className="users-table">
            <thead>
              <tr>
                <th scope="col">ID</th>
                <th scope="col">Full Name</th>
                <th scope="col">Username</th>
                <th scope="col">Role</th>
                <th scope="col">Management Unit</th>
                <th scope="col">Reports To</th>
                <th scope="col">Active</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td>{user.full_name}</td>
                  <td>{user.username}</td>
                  <td>{getRoleName(user.role)}</td>
                  <td>{getManagementUnitName(user.upazila_id)}</td>
                  <td>{getParentName(user.supervisor_id)}</td>
                  <td>
                    <span className={`users-status ${user.is_active ? "users-status-active" : "users-status-inactive"}`}>
                      {user.is_active ? "Yes" : "No"}
                    </span>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="users-btn users-btn-outline"
                      onClick={() => handleEditUser(user.id)}
                      aria-label={`Edit ${user.full_name}`}
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan={8} className="users-empty">No users found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

export default UsersPage;
