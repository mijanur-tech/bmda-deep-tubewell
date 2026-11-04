// ============================================================
// SECTION 1: IMPORTS
// Import React hooks, form types and existing API functions.
// ============================================================

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import "./CreateUserPage.css";

import {
  createUser,
  getManagementUnits,
  getUsers,
  type CreateUserRole,
  type ManagementUnit,
  type UserItem,
} from "../../api/users.api";


// ============================================================
// SECTION 2: CREATE USER PAGE
// Admin can create Assistant Engineers, Supervisors,
// and Field Users according to the BMDA role hierarchy.
// ============================================================

function CreateUserPage() {
  const navigate = useNavigate();

  // ==========================================================
  // SECTION 3: DATA STATES
  // Store management units and existing users.
  // ==========================================================

  const [managementUnits, setManagementUnits] =
    useState<ManagementUnit[]>([]);

  const [users, setUsers] = useState<UserItem[]>([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // ==========================================================
  // SECTION 4: FORM STATES
  // Store information entered by the Admin.
  // ==========================================================

  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [role, setRole] = useState<CreateUserRole | "">("");

  const [managementUnitId, setManagementUnitId] =
    useState("");

  const [parentUserId, setParentUserId] = useState("");


  // ==========================================================
  // SECTION 5: LOAD INITIAL DATA
  // Load management units and existing users from the API.
  // ==========================================================

  useEffect(() => {
    async function loadData() {
      try {
        const [managementUnitData, usersData] =
          await Promise.all([
            getManagementUnits(),
            getUsers(),
          ]);

        setManagementUnits(managementUnitData);
        setUsers(usersData);

      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Failed to load required data.");
        }

      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);


  // ==========================================================
  // SECTION 6: NAVIGATION
  // Return to the User Management page.
  // ==========================================================

  function handleBack() {
    navigate("/admin/users");
  }


  // ==========================================================
  // SECTION 7: ROLE CHANGE
  // Clear the previously selected reporting officer.
  // ==========================================================

  function handleRoleChange(
    newRole: CreateUserRole | ""
  ) {
    setRole(newRole);
    setParentUserId("");
  }


  // ==========================================================
  // SECTION 8: MANAGEMENT UNIT CHANGE
  // Reset the reporting officer when the unit changes.
  // ==========================================================

  function handleManagementUnitChange(
    unitId: string
  ) {
    setManagementUnitId(unitId);
    setParentUserId("");
  }


  // ==========================================================
  // SECTION 9: AVAILABLE ASSISTANT ENGINEERS
  // Show only active Assistant Engineers in the selected unit.
  // ==========================================================

  const availableAssistantEngineers = users.filter(
    (user) =>
      user.role === "assistant_engineer" &&
      user.is_active &&
      user.upazila_id === Number(managementUnitId)
  );


  // ==========================================================
  // SECTION 10: AVAILABLE SUPERVISORS
  // Show only active Supervisors in the selected unit.
  // ==========================================================

  const availableSupervisors = users.filter(
    (user) =>
      user.role === "supervisor" &&
      user.is_active &&
      user.upazila_id === Number(managementUnitId)
  );


  // ==========================================================
  // SECTION 11: FORM SUBMISSION
  // Validate input and create a new user through the API.
  // ==========================================================

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setSuccessMessage("");

    // CHECK 1: Full Name.
    if (!fullName.trim()) {
      setError("Full Name is required.");
      return;
    }

    // CHECK 2: Username.
    if (!username.trim()) {
      setError("Username is required.");
      return;
    }

    // CHECK 3: Password.
    if (!password) {
      setError("Password is required.");
      return;
    }

    // CHECK 4: Role.
    if (!role) {
      setError("Role is required.");
      return;
    }

    // CHECK 5: Management Unit.
    if (!managementUnitId) {
      setError("Management Unit is required.");
      return;
    }

    // CHECK 6: Supervisor requires an Assistant Engineer.
    if (role === "supervisor" && !parentUserId) {
      setError(
        "Sub-Assistant Engineer-এর জন্য Assistant Engineer নির্বাচন করতে হবে."
      );
      return;
    }

    // CHECK 7: Field User requires a Supervisor.
    if (role === "field_user" && !parentUserId) {
      setError(
        "Field User-এর জন্য Sub-Assistant Engineer নির্বাচন করতে হবে."
      );
      return;
    }

    // ========================================================
    // SECTION 12: CREATE USER
    // Send the form data to the existing backend API.
    // ========================================================

    try {
      setSubmitting(true);

      const createdUser = await createUser({
        full_name: fullName.trim(),
        username: username.trim(),
        password,
        role,
        upazila_id: Number(managementUnitId),

        supervisor_id:
          role === "assistant_engineer"
            ? null
            : Number(parentUserId),
      });

      setSuccessMessage(
        `${createdUser.full_name} successfully created.`
      );

      // Clear the form after successful creation.
      setFullName("");
      setUsername("");
      setPassword("");
      setRole("");
      setManagementUnitId("");
      setParentUserId("");

      // Refresh the user list.
      const refreshedUsers = await getUsers();
      setUsers(refreshedUsers);

    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to create user.");
      }

    } finally {
      setSubmitting(false);
    }
  }


  // ==========================================================
  // SECTION 13: LOADING / FORM PRESENTATION
  // Keep all original creation rules and API calls unchanged.
  // ==========================================================
  if (loading) {
    return (
      <main className="bmda-create-user">
        <p className="cu-notice" role="status">Loading required data...</p>
      </main>
    );
  }

  return (
    <main className="bmda-create-user">
      {/* SECTION 14: Page header */}
      <header className="cu-header">
        <div>
          <p className="cu-eyebrow">BMDA · Users Management</p>
          <h1>Create User</h1>
          <p>Add a user and assign the correct management unit and reporting officer.</p>
        </div>
        <button className="cu-button cu-button-outline" type="button" onClick={handleBack}>
          Back to Users
        </button>
      </header>

      {/* SECTION 15: User creation form */}
      <section className="cu-card" aria-labelledby="cu-form-title">
        <div className="cu-card-heading">
          <h2 id="cu-form-title">User Details</h2>
          <p>Complete all required fields before creating the user.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="cu-form-grid">
            <div className="cu-field">
              <label htmlFor="fullName">Full Name <span aria-hidden="true">*</span></label>
              <input id="fullName" type="text" value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                autoComplete="name" required disabled={submitting} />
            </div>

            <div className="cu-field">
              <label htmlFor="username">Username <span aria-hidden="true">*</span></label>
              <input id="username" type="text" value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username" required disabled={submitting} />
            </div>

            <div className="cu-field">
              <label htmlFor="password">Password <span aria-hidden="true">*</span></label>
              <input id="password" type="password" value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="new-password" required disabled={submitting} />
            </div>

            <div className="cu-field">
              <label htmlFor="role">Role <span aria-hidden="true">*</span></label>
              <select id="role" value={role}
                onChange={(event) => handleRoleChange(event.target.value as CreateUserRole | "")}
                required disabled={submitting}>
                <option value="" disabled>Select Role</option>
                <option value="assistant_engineer">Assistant Engineer</option>
                <option value="supervisor">Sub-Assistant Engineer</option>
                <option value="field_user">Field User</option>
              </select>
            </div>

            <div className="cu-field">
              <label htmlFor="managementUnit">Management Unit <span aria-hidden="true">*</span></label>
              <select id="managementUnit" value={managementUnitId}
                onChange={(event) => handleManagementUnitChange(event.target.value)}
                required disabled={submitting}>
                <option value="" disabled>Select Management Unit</option>
                {managementUnits.map((unit) => (
                  <option key={unit.id} value={unit.id}>{unit.name}</option>
                ))}
              </select>
            </div>

            {/* SECTION 16: Conditional reporting officer selection */}
            {role === "supervisor" && (
              <div className="cu-field">
                <label htmlFor="assistantEngineer">Assistant Engineer <span aria-hidden="true">*</span></label>
                <select id="assistantEngineer" value={parentUserId}
                  onChange={(event) => setParentUserId(event.target.value)}
                  disabled={!managementUnitId || submitting} required>
                  <option value="">Select Assistant Engineer</option>
                  {availableAssistantEngineers.map((assistantEngineer) => (
                    <option key={assistantEngineer.id} value={assistantEngineer.id}>
                      {assistantEngineer.full_name}
                    </option>
                  ))}
                </select>
                {managementUnitId && availableAssistantEngineers.length === 0 && (
                  <p className="cu-help">এই Management Unit-এ কোনো active Assistant Engineer পাওয়া যায়নি।</p>
                )}
              </div>
            )}

            {role === "field_user" && (
              <div className="cu-field">
                <label htmlFor="supervisor">Sub-Assistant Engineer <span aria-hidden="true">*</span></label>
                <select id="supervisor" value={parentUserId}
                  onChange={(event) => setParentUserId(event.target.value)}
                  disabled={!managementUnitId || submitting} required>
                  <option value="">Select Sub-Assistant Engineer</option>
                  {availableSupervisors.map((supervisor) => (
                    <option key={supervisor.id} value={supervisor.id}>
                      {supervisor.full_name}
                    </option>
                  ))}
                </select>
                {managementUnitId && availableSupervisors.length === 0 && (
                  <p className="cu-help">এই Management Unit-এ কোনো active Sub-Assistant Engineer পাওয়া যায়নি।</p>
                )}
              </div>
            )}
          </div>

          {/* SECTION 17: Messages and form actions */}
          {error && <p className="cu-alert cu-alert-error" role="alert">{error}</p>}
          {successMessage && <p className="cu-alert cu-alert-success" role="status">{successMessage}</p>}

          <div className="cu-actions">
            <button className="cu-button cu-button-primary" type="submit" disabled={submitting}>
              {submitting ? "Creating..." : "Create User"}
            </button>
            <button className="cu-button cu-button-outline" type="button" onClick={handleBack}>
              Cancel
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

export default CreateUserPage;
