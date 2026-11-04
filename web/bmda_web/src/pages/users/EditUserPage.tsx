import { useEffect, useState } from "react";
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

// ============================================================
// SECTION 1: ROLE LABELS
// Convert internal role names to readable labels.
// ============================================================

const roleLabels: Record<string, string> = {
  admin: "Executive Engineer (Admin)",
  assistant_engineer: "Assistant Engineer",
  supervisor: "Sub-Assistant Engineer",
  field_user: "Field Visitor (Field User)",
};

// ============================================================
// SECTION 2: EDIT USER PAGE
// Only authorized Admin users can access this page
// through the protected application router.
// ============================================================

function EditUserPage() {
  const navigate = useNavigate();
  const { userId } = useParams();

  // ==========================================================
  // SECTION 3: DATA STATES
  // Store the selected user and management information.
  // ==========================================================

  const [user, setUser] = useState<UserItem | null>(null);

  const [users, setUsers] = useState<UserItem[]>([]);

  const [managementUnits, setManagementUnits] =
    useState<ManagementUnit[]>([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // ==========================================================
  // SECTION 4: EDITABLE FORM STATES
  // Only Full Name and Username can be changed.
  // ==========================================================

  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");

  // ==========================================================
  // SECTION 5: LOAD EXISTING USER
  // Retrieve existing account details from the backend.
  // ==========================================================

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      const id = Number(userId);

      if (!Number.isSafeInteger(id) || id <= 0) {
        setError("Invalid User ID.");
        setLoading(false);
        return;
      }

      try {
        const [userData, usersData, unitData] =
          await Promise.all([
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
        if (cancelled) return;

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load user information."
        );

      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadData();

    return () => {
      cancelled = true;
    };
  }, [userId]);

  // ==========================================================
  // SECTION 6: DISPLAY MANAGEMENT UNIT
  // Show the assigned unit without allowing changes.
  // ==========================================================

  const managementUnitName = managementUnits.find(
    (unit) => unit.id === user?.upazila_id
  )?.name ?? (user?.upazila_id == null ? "Not assigned" : "Unknown unit");

  // ==========================================================
  // SECTION 7: DISPLAY REPORTING OFFICER
  // This information is read-only on this page.
  // ==========================================================

  const reportingOfficerName = users.find(
    (item) => item.id === user?.supervisor_id
  )?.full_name ?? (
    user?.supervisor_id == null
      ? "Not assigned"
      : "Officer not found"
  );

  // ==========================================================
  // SECTION 8: NAVIGATION
  // Return to the Users Management page.
  // ==========================================================

  function handleBack() {
    navigate("/admin/users");
  }

  // ==========================================================
  // SECTION 9: SAVE USER PROFILE
  // Update only Full Name and Username.
  // ==========================================================

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!user || submitting) return;

    setError("");
    setSuccessMessage("");

    // CHECK 1: Validate Full Name.
    if (!fullName.trim()) {
      setError("Full Name is required.");
      return;
    }

    if (fullName.length > 150) {
      setError("Full Name cannot exceed 150 characters.");
      return;
    }

    // CHECK 2: Validate Username.
    if (!username.trim()) {
      setError("Username is required.");
      return;
    }

    if (
      username !== username.trim() ||
      username.length > 100
    ) {
      setError(
        "Username must not contain leading or trailing spaces and cannot exceed 100 characters."
      );
      return;
    }

    // CHECK 3: Do not submit if nothing changed.
    if (
      fullName === user.full_name &&
      username === user.username
    ) {
      setSuccessMessage("No changes were necessary.");
      return;
    }

    // ========================================================
    // SECTION 10: SEND UPDATE REQUEST
    // Server validates Admin permissions and uniqueness.
    // ========================================================

    try {
      setSubmitting(true);

      const updatedUser = await updateUser(
        user.id,
        {
          full_name: fullName,
          username: username,
        }
      );

      setUser(updatedUser);

      setFullName(updatedUser.full_name);
      setUsername(updatedUser.username);

      setSuccessMessage(
        "User information updated successfully."
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update user information."
      );

    } finally {
      setSubmitting(false);
    }
  }

  // ==========================================================
  // SECTION 11: LOADING STATE
  // ==========================================================

  if (loading) {
    return (
      <main className="bmda-edit-user">
        <p className="eu-notice" role="status">
          Loading user information...
        </p>
      </main>
    );
  }

  // ==========================================================
  // SECTION 12: USER NOT FOUND / LOAD ERROR
  // ==========================================================

  if (!user) {
    return (
      <main className="bmda-edit-user">
        <h1>Edit User</h1>

        <p className="eu-alert eu-alert-error" role="alert">
          {error || "User not found."}
        </p>

        <button
          type="button"
          className="eu-button eu-button-outline"
          onClick={handleBack}
        >
          Back to Users
        </button>
      </main>
    );
  }

  // ==========================================================
  // SECTION 13: EDIT USER FORM
  // Present editable and read-only account information.
  // ==========================================================

  return (
    <main className="bmda-edit-user">

      <header className="eu-header">
        <div>
          <p className="eu-eyebrow">
            BMDA · Users Management
          </p>

          <h1>Edit User</h1>

          <p>
            Correct the user's name and username
            without changing their account identity.
          </p>
        </div>

        <button
          type="button"
          className="eu-button eu-button-outline"
          onClick={handleBack}
        >
          Back to Users
        </button>
      </header>

      <section
        className="eu-card"
        aria-labelledby="eu-form-title"
      >

        <div className="eu-card-heading">
          <h2 id="eu-form-title">
            User Information
          </h2>

          <p>
            Only Full Name and Username can be edited.
            Other account information is protected.
          </p>
        </div>

        <form onSubmit={handleSubmit}>

          <div className="eu-form-grid">

            {/* SECTION 14: Editable Full Name */}
            <div className="eu-field">
              <label htmlFor="editFullName">
                Full Name *
              </label>

              <input
                id="editFullName"
                type="text"
                value={fullName}
                maxLength={150}
                autoComplete="name"
                onChange={(event) => {
                  setFullName(event.target.value);
                  setSuccessMessage("");
                }}
                required
                disabled={submitting}
              />
            </div>

            {/* SECTION 15: Editable Username */}
            <div className="eu-field">
              <label htmlFor="editUsername">
                Username *
              </label>

              <input
                id="editUsername"
                type="text"
                value={username}
                maxLength={100}
                autoComplete="username"
                onChange={(event) => {
                  setUsername(event.target.value);
                  setSuccessMessage("");
                }}
                required
                disabled={submitting}
              />
            </div>

            {/* SECTION 16: Read-only User ID */}
            <div className="eu-field">
              <label htmlFor="editUserId">
                User ID
              </label>

              <input
                id="editUserId"
                value={user.id}
                readOnly
                aria-readonly="true"
                className="eu-readonly"
              />
            </div>

            {/* SECTION 17: Read-only Role */}
            <div className="eu-field">
              <label htmlFor="editRole">
                Role
              </label>

              <input
                id="editRole"
                value={roleLabels[user.role] || user.role}
                readOnly
                aria-readonly="true"
                className="eu-readonly"
              />
            </div>

            {/* SECTION 18: Read-only Management Unit */}
            <div className="eu-field">
              <label htmlFor="editManagementUnit">
                Management Unit
              </label>

              <input
                id="editManagementUnit"
                value={managementUnitName}
                readOnly
                aria-readonly="true"
                className="eu-readonly"
              />
            </div>

            {/* SECTION 19: Read-only Reporting Officer */}
            <div className="eu-field">
              <label htmlFor="editReportingOfficer">
                Reporting Officer
              </label>

              <input
                id="editReportingOfficer"
                value={reportingOfficerName}
                readOnly
                aria-readonly="true"
                className="eu-readonly"
              />
            </div>

            {/* SECTION 20: Read-only Account Status */}
            <div className="eu-field">
              <label htmlFor="editAccountStatus">
                Account Status
              </label>

              <input
                id="editAccountStatus"
                value={user.is_active ? "Active" : "Inactive"}
                readOnly
                aria-readonly="true"
                className="eu-readonly"
              />
            </div>

          </div>

          {/* SECTION 21: Error and Success Messages */}
          {error && (
            <p className="eu-alert eu-alert-error" role="alert">
              {error}
            </p>
          )}

          {successMessage && (
            <p className="eu-alert eu-alert-success" role="status">
              {successMessage}
            </p>
          )}

          {/* SECTION 22: Form Actions */}
          <div className="eu-actions">

            <button
              type="submit"
              className="eu-button eu-button-primary"
              disabled={submitting}
            >
              {submitting ? "Saving..." : "Save Changes"}
            </button>

            <button
              type="button"
              className="eu-button eu-button-outline"
              onClick={handleBack}
              disabled={submitting}
            >
              Cancel
            </button>

          </div>

        </form>
      </section>
    </main>
  );
}

export default EditUserPage;
