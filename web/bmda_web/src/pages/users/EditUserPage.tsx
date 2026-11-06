import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getUser,
  getUsers,
  getManagementUnits,
  updateUser,
  type UserItem,
  type ManagementUnit,
} from "../../api/users.api";
import "./EditUserPage.css";

// SECTION 1: Display labels. Backend role identifiers never change.
const roleLabels: Record<string, string> = {
  admin: "Executive Engineer (Admin)",
  assistant_engineer: "Assistant Engineer",
  supervisor: "Sub-Assistant Engineer",
  field_user: "Field Visitor",
};

function EditUserPage() {
  const navigate = useNavigate();
  const { userId } = useParams();

  // SECTION 2: Server data, form data and request states.
  const [user, setUser] = useState<UserItem | null>(null);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [managementUnits, setManagementUnits] = useState<ManagementUnit[]>([]);
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  // SECTION 3: Load all information needed for a safe edit.
  useEffect(() => {
    let cancelled = false;
    const id = Number(userId);
    setLoading(true);
    setLoadError("");
    setError("");
    setSuccessMessage("");
    setUser(null);

    if (!Number.isSafeInteger(id) || id <= 0) {
      setLoadError("Invalid User ID.");
      setLoading(false);
      return () => { cancelled = true; };
    }

    async function loadData() {
      try {
        const [userData, usersData, unitData] = await Promise.all([
          getUser(id),
          getUsers(),
          getManagementUnits(),
        ]);
        if (cancelled) return;
        setUser(userData);
        setUsers(usersData);
        setManagementUnits(unitData);
        setFullName(userData.full_name);
        setUsername(userData.username);
      } catch (err) {
        if (!cancelled) {
          setLoadError(err instanceof Error ? err.message : "Failed to load user information.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadData();
    return () => { cancelled = true; };
  }, [userId, reloadKey]);

  // SECTION 4: Validation is guidance; the backend is authoritative.
  const trimmedName = fullName.trim();
  const trimmedUsername = username.trim();
  const duplicateUsername = useMemo(() => {
    const candidate = trimmedUsername.toLowerCase();
    return Boolean(candidate) && users.some(
      (item) => item.id !== user?.id && item.username.toLowerCase() === candidate,
    );
  }, [trimmedUsername, users, user?.id]);
  const usernameHasWhitespace = username !== trimmedUsername;
  const hasChanges = Boolean(user) && (
    trimmedName !== user?.full_name || username !== user?.username
  );
  const formIsValid = Boolean(trimmedName) && trimmedName.length <= 150 &&
    Boolean(trimmedUsername) && trimmedUsername.length <= 100 &&
    !usernameHasWhitespace && !duplicateUsername;

  const managementUnitName = managementUnits.find(
    (unit) => unit.id === user?.upazila_id,
  )?.name ?? (user?.upazila_id == null ? "Not assigned" : "Unknown unit");
  const reportingOfficerName = users.find(
    (item) => item.id === user?.supervisor_id,
  )?.full_name ?? (user?.supervisor_id == null ? "Not assigned" : "Officer not found");

  function handleBack() {
    navigate("/admin/users");
  }

  function handleReset() {
    if (!user) return;
    setFullName(user.full_name);
    setUsername(user.username);
    setError("");
    setSuccessMessage("");
  }

  // SECTION 5: Update only the two fields allowed by the existing API.
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user || submitting) return;
    setError("");
    setSuccessMessage("");

    if (!trimmedName || trimmedName.length > 150) {
      setError("Full Name is required and must not exceed 150 characters.");
      return;
    }
    if (!trimmedUsername || trimmedUsername.length > 100 || usernameHasWhitespace) {
      setError("Username is required, must not exceed 100 characters, and cannot have leading or trailing spaces.");
      return;
    }
    if (duplicateUsername) {
      setError("This username is already in use. Choose another username.");
      return;
    }
    if (!hasChanges) {
      setSuccessMessage("No changes were necessary.");
      return;
    }

    try {
      setSubmitting(true);
      const updatedUser = await updateUser(user.id, {
        full_name: trimmedName,
        username,
      });
      setUser(updatedUser);
      setFullName(updatedUser.full_name);
      setUsername(updatedUser.username);
      setUsers((previous) => previous.map((item) =>
        item.id === updatedUser.id ? updatedUser : item,
      ));
      setSuccessMessage("User information updated successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user information.");
    } finally {
      setSubmitting(false);
    }
  }

  // SECTION 6: Loading and recoverable error states.
  if (loading) {
    return <main className="bmda-edit-user"><p className="eu-notice" role="status">Loading user information...</p></main>;
  }

  if (!user) {
    return (
      <main className="bmda-edit-user">
        <header className="eu-header"><div><p className="eu-eyebrow">BMDA · Users Management</p><h1>Edit User</h1></div></header>
        <p className="eu-alert eu-alert-error" role="alert">{loadError || "User not found."}</p>
        <div className="eu-actions">
          <button type="button" className="eu-button eu-button-primary" onClick={() => setReloadKey((value) => value + 1)}>Retry Loading</button>
          <button type="button" className="eu-button eu-button-outline" onClick={handleBack}>Back to Users</button>
        </div>
      </main>
    );
  }

  // SECTION 7: Editable profile and protected read-only account identity.
  return (
    <main className="bmda-edit-user">
      <header className="eu-header">
        <div>
          <p className="eu-eyebrow">BMDA · Users Management</p>
          <h1>Edit User</h1>
          <p>Correct the user's name and username without changing their account identity.</p>
        </div>
        <button type="button" className="eu-button eu-button-outline" onClick={handleBack} disabled={submitting}>Back to Users</button>
      </header>

      <section className="eu-card" aria-labelledby="eu-form-title">
        <div className="eu-card-heading">
          <h2 id="eu-form-title">User Information</h2>
          <p>Only Full Name and Username can be edited. All other account information is protected.</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="eu-form-grid">
            <div className="eu-field">
              <label htmlFor="editFullName">Full Name *</label>
              <input id="editFullName" type="text" value={fullName} maxLength={150} autoComplete="name" required disabled={submitting}
                onChange={(event) => { setFullName(event.target.value); setError(""); setSuccessMessage(""); }} />
            </div>
            <div className="eu-field">
              <label htmlFor="editUsername">Username *</label>
              <input id="editUsername" type="text" value={username} maxLength={100} autoComplete="username" required disabled={submitting}
                aria-invalid={duplicateUsername || usernameHasWhitespace} aria-describedby="eu-username-help"
                onChange={(event) => { setUsername(event.target.value); setError(""); setSuccessMessage(""); }} />
              <p id="eu-username-help" className={duplicateUsername || usernameHasWhitespace ? "eu-alert eu-alert-error" : "eu-notice"} role={duplicateUsername || usernameHasWhitespace ? "alert" : "status"}>
                {duplicateUsername ? "Username already exists. Choose a different one." : usernameHasWhitespace ? "Remove leading or trailing spaces." : "Username must be unique."}
              </p>
            </div>
            <div className="eu-field"><label htmlFor="editUserId">User ID</label><input id="editUserId" value={user.id} readOnly aria-readonly="true" className="eu-readonly" /></div>
            <div className="eu-field"><label htmlFor="editRole">Role</label><input id="editRole" value={roleLabels[user.role] || user.role} readOnly aria-readonly="true" className="eu-readonly" /></div>
            <div className="eu-field"><label htmlFor="editManagementUnit">Management Unit</label><input id="editManagementUnit" value={managementUnitName} readOnly aria-readonly="true" className="eu-readonly" /></div>
            <div className="eu-field"><label htmlFor="editReportingOfficer">Reporting Officer</label><input id="editReportingOfficer" value={reportingOfficerName} readOnly aria-readonly="true" className="eu-readonly" /></div>
            <div className="eu-field"><label htmlFor="editAccountStatus">Account Status</label><input id="editAccountStatus" value={user.is_active ? "Active" : "Inactive"} readOnly aria-readonly="true" className="eu-readonly" /></div>
          </div>

          {error && <p className="eu-alert eu-alert-error" role="alert">{error}</p>}
          {successMessage && <p className="eu-alert eu-alert-success" role="status">{successMessage}</p>}

          <div className="eu-actions">
            <button type="submit" className="eu-button eu-button-primary" disabled={submitting || !hasChanges || !formIsValid}>
              {submitting ? "Saving..." : "Save Changes"}
            </button>
            <button type="button" className="eu-button eu-button-outline" onClick={handleReset} disabled={submitting || !hasChanges}>Discard Changes</button>
            <button type="button" className="eu-button eu-button-outline" onClick={handleBack} disabled={submitting}>Cancel</button>
          </div>
        </form>
      </section>
    </main>
  );
}

export default EditUserPage;
