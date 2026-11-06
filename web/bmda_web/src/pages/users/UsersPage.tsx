// ============================================================
// BMDA Phase 06 / Step 34 — User Directory
// Existing admin-only API, navigation, and user data are preserved.
// ============================================================
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getManagementUnits,
  getUsers,
  type ManagementUnit,
  type UserItem,
} from "../../api/users.api";
import "./UsersPage.css";

const PAGE_SIZE = 10;

function getRoleName(role: string): string {
  switch (role) {
    case "admin": return "Admin";
    case "assistant_engineer": return "Assistant Engineer";
    case "supervisor": return "Sub-Assistant Engineer";
    case "field_user": return "Field Visitor";
    default: return role;
  }
}

function UsersPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [managementUnits, setManagementUnits] = useState<ManagementUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("all");
  const [unit, setUnit] = useState("all");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);

  useEffect(() => {
    let cancelled = false;
    async function loadData() {
      setLoading(true);
      setError("");
      try {
        const [usersData, unitsData] = await Promise.all([
          getUsers(), getManagementUnits(),
        ]);
        if (!cancelled) {
          setUsers(usersData);
          setManagementUnits(unitsData);
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
  }, [reloadKey]);

  const unitNames = useMemo(
    () => new Map(managementUnits.map((item) => [item.id, item.name])),
    [managementUnits],
  );
  const userNames = useMemo(
    () => new Map(users.map((item) => [item.id, item.full_name])),
    [users],
  );

  const filteredUsers = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    return users.filter((user) => {
      if (role !== "all" && user.role !== role) return false;
      if (unit !== "all" && String(user.upazila_id ?? "") !== unit) return false;
      if (status === "active" && !user.is_active) return false;
      if (status === "inactive" && user.is_active) return false;
      if (!query) return true;
      const searchable = [
        String(user.id), user.full_name, user.username,
        getRoleName(user.role),
        unitNames.get(user.upazila_id ?? -1) ?? "",
        userNames.get(user.supervisor_id ?? -1) ?? "",
      ].join(" ").toLocaleLowerCase();
      return searchable.includes(query);
    });
  }, [users, search, role, unit, status, unitNames, userNames]);

  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const start = (currentPage - 1) * PAGE_SIZE;
  const visibleUsers = filteredUsers.slice(start, start + PAGE_SIZE);

  function resetPageAndSearch(value: string) { setSearch(value); setPage(1); }
  function resetFilters() {
    setSearch(""); setRole("all"); setUnit("all"); setStatus("all"); setPage(1);
  }

  return (
    <main className="bmda-users-page">
      <header className="users-page-header">
        <div>
          <h1 className="users-page-title">Users Management</h1>
          <p className="users-page-subtitle">View registered users, roles and reporting lines.</p>
        </div>
        <div className="users-page-actions">
          <button type="button" className="users-btn users-btn-outline" onClick={() => navigate("/admin/dashboard")}>Back to Dashboard</button>
          <button type="button" className="users-btn users-btn-primary" onClick={() => navigate("/admin/users/create")}>+ Create User</button>
        </div>
      </header>

      <section className="users-summary" aria-label="User summary">
        <span>Total Users</span>
        <strong>{users.length}</strong>
      </section>

      <section className="users-table-card" aria-label="Registered users">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, padding: 16, alignItems: "end" }}>
          <label style={{ flex: "2 1 220px", display: "grid", gap: 5 }}>
            <span>Search users</span>
            <input aria-label="Search users" type="search" value={search} onChange={(e) => resetPageAndSearch(e.target.value)} placeholder="Name, username, ID, unit or supervisor" style={{ width: "100%", padding: 10, border: "1px solid #b8cec5", borderRadius: 8 }} />
          </label>
          <label style={{ flex: "1 1 150px", display: "grid", gap: 5 }}>
            <span>Role</span>
            <select aria-label="Filter by role" value={role} onChange={(e) => { setRole(e.target.value); setPage(1); }} style={{ width: "100%", padding: 10, border: "1px solid #b8cec5", borderRadius: 8 }}>
              <option value="all">All roles</option>
              <option value="admin">Admin</option>
              <option value="assistant_engineer">Assistant Engineer</option>
              <option value="supervisor">Sub-Assistant Engineer</option>
              <option value="field_user">Field Visitor</option>
            </select>
          </label>
          <label style={{ flex: "1 1 170px", display: "grid", gap: 5 }}>
            <span>Management unit</span>
            <select aria-label="Filter by management unit" value={unit} onChange={(e) => { setUnit(e.target.value); setPage(1); }} style={{ width: "100%", padding: 10, border: "1px solid #b8cec5", borderRadius: 8 }}>
              <option value="all">All units</option>
              {managementUnits.map((item) => <option key={item.id} value={String(item.id)}>{item.name}</option>)}
            </select>
          </label>
          <label style={{ flex: "1 1 130px", display: "grid", gap: 5 }}>
            <span>Status</span>
            <select aria-label="Filter by status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} style={{ width: "100%", padding: 10, border: "1px solid #b8cec5", borderRadius: 8 }}>
              <option value="all">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </label>
          <button type="button" className="users-btn users-btn-outline" onClick={resetFilters}>Clear filters</button>
        </div>

        {loading ? (
          <p className="users-notice" role="status">Loading users...</p>
        ) : error ? (
          <div className="users-notice users-error" role="alert">
            <p>{error}</p>
            <button type="button" className="users-btn users-btn-outline" onClick={() => setReloadKey((key) => key + 1)}>Retry</button>
          </div>
        ) : (
          <>
            <div className="users-table-caption" aria-live="polite">
              Showing <strong>{filteredUsers.length === 0 ? 0 : start + 1}–{Math.min(start + PAGE_SIZE, filteredUsers.length)}</strong> of <strong>{filteredUsers.length}</strong> matching users ({users.length} total)
            </div>
            <div className="users-table-scroll" role="region" aria-label="Scrollable users table" tabIndex={0}>
              <table className="users-table">
                <thead><tr>
                  <th scope="col">ID</th><th scope="col">Full Name</th><th scope="col">Username</th><th scope="col">Role</th><th scope="col">Management Unit</th><th scope="col">Reports To</th><th scope="col">Active</th><th scope="col">Action</th>
                </tr></thead>
                <tbody>
                  {visibleUsers.map((user) => (
                    <tr key={user.id}>
                      <td>{user.id}</td><td>{user.full_name}</td><td>{user.username}</td>
                      <td>{getRoleName(user.role)}</td>
                      <td>{user.upazila_id == null ? "-" : unitNames.get(user.upazila_id) ?? `ID: ${user.upazila_id}`}</td>
                      <td>{user.supervisor_id == null ? "-" : userNames.get(user.supervisor_id) ?? `User ID: ${user.supervisor_id}`}</td>
                      <td><span className={`users-status ${user.is_active ? "users-status-active" : "users-status-inactive"}`}>{user.is_active ? "Yes" : "No"}</span></td>
                      <td><button type="button" className="users-btn users-btn-outline" onClick={() => navigate(`/admin/users/${user.id}/edit`)} aria-label={`Edit ${user.full_name}`}>Edit</button></td>
                    </tr>
                  ))}
                  {visibleUsers.length === 0 && <tr><td colSpan={8} className="users-empty">{users.length === 0 ? "No users registered." : "No users match the selected filters."}</td></tr>}
                </tbody>
              </table>
            </div>
            {filteredUsers.length > PAGE_SIZE && (
              <nav aria-label="Users pagination" style={{ display: "flex", alignItems: "center", justifyContent: "center", flexWrap: "wrap", gap: 12, padding: 16 }}>
                <button type="button" className="users-btn users-btn-outline" disabled={currentPage <= 1} onClick={() => setPage(currentPage - 1)}>Previous</button>
                <span aria-live="polite">Page {currentPage} of {totalPages}</span>
                <button type="button" className="users-btn users-btn-outline" disabled={currentPage >= totalPages} onClick={() => setPage(currentPage + 1)}>Next</button>
              </nav>
            )}
          </>
        )}
      </section>
    </main>
  );
}

export default UsersPage;
