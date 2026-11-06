// ============================================================
// BMDA Phase 06 / Step 34 â€” User Directory
// Existing admin-only API, navigation, and user data are preserved.
// ============================================================
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  changeUserStatus,
  getDirectSubordinates,
  getManagementUnits,
  getUsers,
  type ManagementUnit,
  type UserItem,
} from "../../api/users.api";
import "./UsersPage.css";

const PAGE_SIZE = 10;

type TeamBranch = { supervisor: UserItem; visitors: UserItem[] };

function StatusPill({ active }: { active: boolean }) {
  return <span className={`users-status ${active ? "users-status-active" : "users-status-inactive"}`}>{active ? "Active" : "Inactive"}</span>;
}


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
  const [pendingUserId, setPendingUserId] = useState<number | null>(null);
  const [actionError, setActionError] = useState("");
  const [actionSuccess, setActionSuccess] = useState("");
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);
  const [teamReloadKey, setTeamReloadKey] = useState(0);
  const [teamLoading, setTeamLoading] = useState(false);
  const [teamError, setTeamError] = useState("");
  const [teamBranches, setTeamBranches] = useState<TeamBranch[]>([]);
  const [teamVisitors, setTeamVisitors] = useState<UserItem[]>([]);
  const teamPanelRef = useRef<HTMLElement | null>(null);

  // Step 39.20: Make the already-rendered team visible after every View Team click.
  useEffect(() => {
    if (selectedTeamId === null) return;
    teamPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [selectedTeamId, teamReloadKey]);

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

  const selectedTeamUser = users.find((item) => item.id === selectedTeamId) ?? null;

  // Fetch only when Admin opens a team; prevent stale responses after switching teams.
  useEffect(() => {
    if (selectedTeamId === null) return;
    const selected = users.find((item) => item.id === selectedTeamId);
    if (!selected || !["assistant_engineer", "supervisor"].includes(selected.role)) return;
    let cancelled = false;
    async function loadTeam() {
      setTeamLoading(true);
      setTeamError("");
      setTeamBranches([]);
      setTeamVisitors([]);
      try {
        const direct = await getDirectSubordinates(selectedTeamId as number);
        if (selected?.role === "assistant_engineer") {
          const branches = await Promise.all(direct.map(async (supervisor) => ({
            supervisor,
            visitors: await getDirectSubordinates(supervisor.id),
          })));
          if (!cancelled) setTeamBranches(branches);
        } else if (!cancelled) {
          setTeamVisitors(direct);
        }
      } catch (err) {
        if (!cancelled) setTeamError(err instanceof Error ? err.message : "Unable to load team.");
      } finally {
        if (!cancelled) setTeamLoading(false);
      }
    }
    void loadTeam();
    return () => { cancelled = true; };
  }, [selectedTeamId, teamReloadKey]);

  async function handleStatusChange(user: UserItem) {
    if (pendingUserId !== null || user.role === "admin") return;

    const nextStatus = !user.is_active;
    const verb = nextStatus ? "Reactivate" : "Deactivate";
    const confirmed = window.confirm(
      `${verb} ${user.full_name} (${user.username})?\n\n` +
      (nextStatus
        ? "The account will be able to sign in again if its reporting hierarchy is active."
        : "The account will no longer be allowed to sign in. Active direct reports must be deactivated first.")
    );
    if (!confirmed) return;

    setPendingUserId(user.id);
    setActionError("");
    setActionSuccess("");

    try {
      await changeUserStatus(user.id, { is_active: nextStatus });
      // Always refresh from the backend rather than assuming local state.
      const latestUsers = await getUsers();
      setUsers(latestUsers);
      setActionSuccess(`${user.full_name} was ${nextStatus ? "reactivated" : "deactivated"} successfully.`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to change account status.";
      setActionError(
        `Could not ${verb.toLowerCase()} ${user.full_name}. ${message} ` +
        "If this is a hierarchy conflict, update active direct reports or the reporting officer first. " +
        "Use Retry to refresh the directory if the account may already have changed."
      );
    } finally {
      setPendingUserId(null);
    }
  }

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

      {selectedTeamUser && (
        <section ref={teamPanelRef} className="users-team-panel" aria-label={`Team of ${selectedTeamUser.full_name}`}>
          <div className="users-team-heading">
            <div>
              <p className="users-team-eyebrow">READ-ONLY REPORTING HIERARCHY</p>
              <h2>Team of {selectedTeamUser.full_name}</h2>
              <p>{getRoleName(selectedTeamUser.role)} · {unitNames.get(selectedTeamUser.upazila_id ?? -1) ?? "No management unit"}</p>
            </div>
            <button type="button" className="users-btn users-btn-outline" onClick={() => setSelectedTeamId(null)}>Close team</button>
          </div>
          {teamLoading ? <p className="users-team-message" role="status">Loading team hierarchy...</p> : teamError ? (
            <div className="users-notice users-error" role="alert">
              <p>Could not load team: {teamError}</p>
              <button type="button" className="users-btn users-btn-outline" onClick={() => setTeamReloadKey((key) => key + 1)}>Retry team</button>
            </div>
          ) : selectedTeamUser.role === "assistant_engineer" ? (
            teamBranches.length === 0 ? <p className="users-team-message">No directly reporting Sub-Assistant Engineers.</p> : (
              <div className="users-team-branches">
                {teamBranches.map(({ supervisor, visitors }) => (
                  <article className="users-team-branch" key={supervisor.id}>
                    <div className="users-team-person users-team-supervisor">
                      <div><strong>{supervisor.full_name}</strong><span>Sub-Assistant Engineer · {supervisor.username}</span></div>
                      <StatusPill active={supervisor.is_active} />
                    </div>
                    <div className="users-team-children">
                      {visitors.length === 0 ? <p className="users-team-empty">No directly reporting Field Visitors.</p> : visitors.map((visitor) => (
                        <div className="users-team-person" key={visitor.id}>
                          <div><strong>{visitor.full_name}</strong><span>Field Visitor · {visitor.username}</span></div>
                          <StatusPill active={visitor.is_active} />
                        </div>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            )
          ) : teamVisitors.length === 0 ? <p className="users-team-message">No directly reporting Field Visitors.</p> : (
            <div className="users-team-branches">
              <article className="users-team-branch"><div className="users-team-children">
                {teamVisitors.map((visitor) => (
                  <div className="users-team-person" key={visitor.id}>
                    <div><strong>{visitor.full_name}</strong><span>Field Visitor · {visitor.username}</span></div>
                    <StatusPill active={visitor.is_active} />
                  </div>
                ))}
              </div></article>
            </div>
          )}
        </section>
      )}

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

        {actionError && (
          <div className="users-notice users-error" role="alert">
            <p>{actionError}</p>
            <button type="button" className="users-btn users-btn-outline" onClick={() => setReloadKey((key) => key + 1)}>Retry</button>
          </div>
        )}
        {actionSuccess && <p className="users-notice" role="status">{actionSuccess}</p>}

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
              Showing <strong>{filteredUsers.length === 0 ? 0 : start + 1}â€“{Math.min(start + PAGE_SIZE, filteredUsers.length)}</strong> of <strong>{filteredUsers.length}</strong> matching users ({users.length} total)
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
                      <td>
                        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                          <button type="button" className="users-btn users-btn-outline" onClick={() => navigate(`/admin/users/${user.id}/edit`)} aria-label={`Edit ${user.full_name}`} disabled={pendingUserId !== null}>Edit</button>
                          {(user.role === "assistant_engineer" || user.role === "supervisor") && (
                            <button type="button" className="users-btn users-btn-outline"
                              aria-label={`View team of ${user.full_name}`}
                              aria-expanded={selectedTeamId === user.id}
                              onClick={() => { setSelectedTeamId(user.id); setTeamReloadKey((key) => key + 1); }}>
                              View Team
                            </button>
                          )}
                          {user.role !== "admin" && (
                            <button
                              type="button"
                              className="users-btn users-btn-outline"
                              style={user.is_active ? { color: "#9f1239", borderColor: "#fda4af" } : { color: "#166534", borderColor: "#86efac" }}
                              disabled={pendingUserId !== null}
                              aria-label={`${user.is_active ? "Deactivate" : "Reactivate"} ${user.full_name}`}
                              onClick={() => void handleStatusChange(user)}
                            >
                              {pendingUserId === user.id ? "Saving..." : user.is_active ? "Deactivate" : "Reactivate"}
                            </button>
                          )}
                        </div>
                      </td>
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
