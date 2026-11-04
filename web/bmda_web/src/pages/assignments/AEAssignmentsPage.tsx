import {
  Fragment,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
} from "react";

import { useNavigate } from "react-router-dom";
import { useCurrentUser } from "../../auth/useCurrentUser";
import {
  getTubewells,
  type TubewellItem,
} from "../../api/tubewells.api";
import {
  getAssignments,
  getCurrentAssignment,
  getEligibleFieldUsers,
  getAssignmentHistory,
  createOrReassignAssignment,
  type AssignmentItem,
  type EligibleFieldUserItem,
} from "../../api/assignments.api";

// ============================================================
// BMDA — ASSISTANT ENGINEER TUBEWELL ASSIGNMENTS
//
// Only Assistant Engineers may manage assignments.
// All records are limited to the authenticated management unit.
// Backend remains the final authorization authority.
//
// Explicit confirmation required before any POST.
// No automatic POST retry.
// ============================================================

const colors = {
  green: "#187345",
  dark: "#194b32",
  pale: "#eaf6ee",
  border: "#d8e9dd",
  text: "#243b2d",
  muted: "#64796b",
  white: "#ffffff",
};

const panel: CSSProperties = {
  background: colors.white,
  border: `1px solid ${colors.border}`,
  borderRadius: 16,
  padding: 22,
  marginBottom: 20,
  boxShadow: "0 3px 14px rgba(25,75,50,0.035)",
};

const inputStyle: CSSProperties = {
  width: "100%",
  minWidth: 0,
  boxSizing: "border-box",
  padding: "11px 12px",
  border: "1px solid #bfd7c7",
  borderRadius: 9,
  background: "#fff",
  color: colors.text,
  font: "inherit",
};

const buttonStyle: CSSProperties = {
  padding: "10px 15px",
  border: "1px solid #9bc7aa",
  borderRadius: 9,
  background: "#fff",
  color: colors.green,
  font: "inherit",
  cursor: "pointer",
};

const primaryStyle: CSSProperties = {
  ...buttonStyle,
  color: "#fff",
  background: colors.green,
  borderColor: colors.green,
  fontWeight: 650,
};

const cellStyle: CSSProperties = {
  padding: "12px 13px",
  borderBottom: "1px solid #e7eee9",
  textAlign: "left",
  verticalAlign: "middle",
};

function message(error: unknown): string {
  if (error instanceof Error) {
    return error.message === "SESSION_EXPIRED"
      ? "Your session has expired. Please log in again."
      : error.message;
  }
  return "An unexpected error occurred.";
}

function sameAssignment(
  a: AssignmentItem | undefined,
  b: AssignmentItem | null
): boolean {
  if (!a && !b) return true;
  if (!a || !b) return false;
  return (
    a.id === b.id &&
    a.tubewell_id === b.tubewell_id &&
    a.field_user_id === b.field_user_id &&
    a.assigned_at === b.assigned_at &&
    a.ended_at === b.ended_at
  );
}

function showDate(value: string | null): string {
  return value || "Not recorded";
}

export default function AEAssignmentsPage() {
  const navigate = useNavigate();
  const { user, loading: authLoading, error: authError } =
    useCurrentUser();

  const isAuthorized =
    user?.role === "assistant_engineer" &&
    user.is_active &&
    user.upazila_id !== null;

  const unitId = isAuthorized ? user.upazila_id : null;

  const [wells, setWells] = useState<TubewellItem[]>([]);
  const [fieldUsers, setFieldUsers] = useState<
    EligibleFieldUserItem[]
  >([]);
  const [assignments, setAssignments] = useState<AssignmentItem[]>(
    []
  );

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const [selectedId, setSelectedId] = useState<number | null>(
    null
  );
  const [fieldUserId, setFieldUserId] = useState("");
  const [assignmentDate, setAssignmentDate] = useState("");
  const [preview, setPreview] = useState(false);

  const [checking, setChecking] = useState(false);
  const [saving, setSaving] = useState(false);
  const [needsRefresh, setNeedsRefresh] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [success, setSuccess] = useState("");

  const submissionLock = useRef(false);
  const confirmationPending = useRef(false);

  const [historyWell, setHistoryWell] =
    useState<TubewellItem | null>(null);
  const [history, setHistory] = useState<AssignmentItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");

  // ==========================================================
  // LOAD ONLY AUTHORIZED MANAGEMENT-UNIT DATA
  // ==========================================================

  useEffect(() => {
    if (authLoading) return;

    if (!isAuthorized || unitId === null) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function loadData() {
      setLoading(true);
      setError("");

      try {
        const [tubewellData, userData, assignmentData] =
          await Promise.all([
            getTubewells(),
            getEligibleFieldUsers(),
            getAssignments(true),
          ]);

        if (cancelled) return;

        if (
          !Array.isArray(tubewellData) ||
          !Array.isArray(userData) ||
          !Array.isArray(assignmentData)
        ) {
          throw new Error("Unexpected API response.");
        }

        // Defense in depth: backend also scopes all results.
        const scopedWells = tubewellData.filter(
          (well) => well.management_unit_id === unitId
        );

        const scopedUsers = userData.filter(
          (person) => person.management_unit_id === unitId
        );

        const allowedIds = new Set(
          scopedWells.map((well) => well.id)
        );

        const scopedAssignments = assignmentData.filter(
          (item) => allowedIds.has(item.tubewell_id)
        );

        setWells(scopedWells);
        setFieldUsers(scopedUsers);
        setAssignments(scopedAssignments);

        setSelectedId(null);
        setFieldUserId("");
        setAssignmentDate("");
        setPreview(false);
        setHistoryWell(null);
        setNeedsRefresh(false);
      } catch (err) {
        if (!cancelled) {
          setError(message(err));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadData();

    return () => {
      cancelled = true;
    };
  }, [authLoading, isAuthorized, unitId, reloadKey]);

  // ==========================================================
  // CURRENT ASSIGNMENTS AND SEARCH
  // ==========================================================

  const currentByWell = useMemo(() => {
    const map = new Map<number, AssignmentItem>();

    for (const assignment of assignments) {
      if (assignment.ended_at === null) {
        map.set(assignment.tubewell_id, assignment);
      }
    }

    return map;
  }, [assignments]);

  const userById = useMemo(
    () => new Map(fieldUsers.map((person) => [
      person.id,
      person,
    ])),
    [fieldUsers]
  );

  const assignedCount = wells.filter((well) =>
    currentByWell.has(well.id)
  ).length;

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();

    return wells.filter((well) => {
      const assignment = currentByWell.get(well.id);
      const person = assignment
        ? userById.get(assignment.field_user_id)
        : undefined;

      const searchable = [
        well.tubewell_number,
        well.name,
        well.actual_upazila,
        well.union_name,
        well.mouza,
        person?.full_name ?? "",
      ].join(" ").toLowerCase();

      if (query && !searchable.includes(query)) return false;
      if (statusFilter === "assigned" && !assignment) {
        return false;
      }
      if (statusFilter === "unassigned" && assignment) {
        return false;
      }
      return true;
    });
  }, [
    wells,
    currentByWell,
    userById,
    search,
    statusFilter,
  ]);

  const totalPages = Math.max(
    1,
    Math.ceil(filtered.length / pageSize)
  );
  const safePage = Math.min(page, totalPages);
  const startIndex = (safePage - 1) * pageSize;
  const visible = filtered.slice(
    startIndex,
    startIndex + pageSize
  );

  const selectedWell = wells.find(
    (well) => well.id === selectedId
  );

  const currentAssignment = selectedWell
    ? currentByWell.get(selectedWell.id)
    : undefined;

  const chosenUser = fieldUsers.find(
    (person) => String(person.id) === fieldUserId
  );

  const sameUser =
    chosenUser !== undefined &&
    currentAssignment?.field_user_id === chosenUser.id;

  const reassignment =
    currentAssignment !== undefined && !sameUser;

  const validDate =
    !assignmentDate ||
    /^\d{4}-\d{2}-\d{2}$/.test(assignmentDate);

  const canPreview =
    isAuthorized &&
    selectedWell !== undefined &&
    selectedWell.is_active &&
    chosenUser !== undefined &&
    chosenUser.management_unit_id === unitId &&
    validDate &&
    (!reassignment || Boolean(assignmentDate)) &&
    (!reassignment ||
      currentAssignment?.assigned_at == null ||
      assignmentDate >= currentAssignment.assigned_at);

  const busy = checking || saving || loading;

  const canSave =
    canPreview &&
    preview &&
    !sameUser &&
    !busy &&
    !needsRefresh &&
    !error;

  // ==========================================================
  // SELECTION AND REFRESH
  // ==========================================================

  function selectWell(well: TubewellItem, preferredUserId?: number) {
    if (busy || needsRefresh || confirmationPending.current) {
      return;
    }

    setSelectedId(well.id);

    const existing = currentByWell.get(well.id);

    setFieldUserId(
      preferredUserId !== undefined
        ? String(preferredUserId)
        : existing
          ? String(existing.field_user_id)
          : ""
    );
    setAssignmentDate("");
    setPreview(false);
    setSaveError("");
  }

  function refresh() {
    if (busy || confirmationPending.current) return;
    setSaveError("");
    setSuccess("");
    setReloadKey((value) => value + 1);
  }

  // ==========================================================
  // EXPLICIT CONFIRMATION AND SAFE SINGLE POST
  // ==========================================================

  async function confirmAndSave() {
    if (
      !canSave ||
      !selectedWell ||
      !chosenUser ||
      submissionLock.current ||
      confirmationPending.current
    ) {
      return;
    }

    const targetWellId = selectedWell.id;
    const targetWellNumber = selectedWell.tubewell_number;
    const targetUserId = chosenUser.id;
    const targetUserName = chosenUser.full_name;
    const effectiveDate = assignmentDate || null;
    const previousAssignment = currentAssignment;
    const isReassignment = reassignment;

    confirmationPending.current = true;
    setChecking(true);
    setSaveError("");

    try {
      const latest = await getCurrentAssignment(targetWellId);

      if (!sameAssignment(previousAssignment, latest)) {
        setPreview(false);
        setNeedsRefresh(true);
        setSaveError(
          "The current assignment changed on the server. " +
          "No save request was sent. Refresh before continuing."
        );
        return;
      }

      if (latest?.field_user_id === targetUserId) {
        setPreview(false);
        setNeedsRefresh(true);
        setSaveError(
          "This Field Visitor is already assigned. " +
          "No save request was sent."
        );
        return;
      }

      const confirmed = window.confirm([
        isReassignment
          ? "Confirm Tubewell Reassignment"
          : "Confirm First Tubewell Assignment",
        "",
        `DTW: ${targetWellNumber}`,
        `Field Visitor: ${targetUserName}`,
        `Effective Date: ${effectiveDate ?? "Not provided"}`,
        "",
        isReassignment
          ? "The previous assignment will be preserved in history."
          : "A new current assignment will be created.",
        "",
        "Do you want to save?",
      ].join("\n"));

      if (!confirmed) return;

      submissionLock.current = true;
      setSaving(true);
      setChecking(false);
      setNeedsRefresh(true);

      try {
        const saved = await createOrReassignAssignment({
          tubewell_id: targetWellId,
          field_user_id: targetUserId,
          assigned_at: effectiveDate,
        });

        if (
          saved.tubewell_id !== targetWellId ||
          saved.field_user_id !== targetUserId ||
          saved.ended_at !== null
        ) {
          throw new Error(
            "The save response did not match the requested assignment."
          );
        }

        setAssignments((previous) => [
          ...previous.filter(
            (item) => item.tubewell_id !== targetWellId
          ),
          saved,
        ]);

        setSelectedId(null);
        setPreview(false);
        setFieldUserId("");
        setAssignmentDate("");
        setSaveError("");

        setSuccess(
          `${isReassignment ? "Reassignment" : "Assignment"} ` +
          `saved for ${targetWellNumber}. ` +
          `Field Visitor: ${targetUserName}. ` +
          "Refresh records before making another assignment."
        );
      } catch (err) {
        setPreview(false);
        setSaveError(
          "The save result could not be confirmed. " +
          "The request may have reached the server. " +
          "Do not submit again until you refresh the records. " +
          `Details: ${message(err)}`
        );
      } finally {
        submissionLock.current = false;
        setSaving(false);
      }
    } catch (err) {
      setPreview(false);
      setSaveError(
        "Unable to verify the latest assignment. " +
        "No save request was sent. " +
        `Details: ${message(err)}`
      );
    } finally {
      confirmationPending.current = false;
      setChecking(false);
    }
  }

  // ==========================================================
  // READ-ONLY ASSIGNMENT HISTORY
  // ==========================================================

  useEffect(() => {
    if (!historyWell || !isAuthorized) {
      setHistory([]);
      setHistoryError("");
      setHistoryLoading(false);
      return;
    }

    let cancelled = false;
    const wellId = historyWell.id;

    async function loadHistory() {
      setHistoryLoading(true);
      setHistory([]);
      setHistoryError("");

      try {
        const data = await getAssignmentHistory(wellId);

        if (cancelled) return;

        if (!Array.isArray(data)) {
          throw new Error("Unexpected history response.");
        }

        setHistory(
          data.filter((item) => item.tubewell_id === wellId)
        );
      } catch (err) {
        if (!cancelled) setHistoryError(message(err));
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    }

    void loadHistory();

    return () => {
      cancelled = true;
    };
  }, [historyWell, isAuthorized, reloadKey]);

  // ==========================================================
  // AUTHENTICATION / ROLE GUARDS
  // ==========================================================

  if (authLoading) {
    return (
      <main style={panel} role="status">
        Checking your account...
      </main>
    );
  }

  if (authError || !user) {
    return (
      <main style={panel} role="alert">
        {authError || "Unable to load your account."}
      </main>
    );
  }

  if (!isAuthorized) {
    return (
      <main style={panel} role="alert">
        <h2>Access Denied</h2>
        <p>
          Only Assistant Engineers with an assigned management
          unit may access this workspace.
        </p>
        <button
          type="button"
          style={buttonStyle}
          onClick={() => navigate("/403")}
        >
          Return
        </button>
      </main>
    );
  }

  // ==========================================================
  // PAGE UI
  // ==========================================================

  return (
    <main
      style={{
        background: "#f5faf6",
        minHeight: "100vh",
        padding: "clamp(14px, 3vw, 32px)",
        color: colors.text,
        fontFamily: "Segoe UI, Arial, sans-serif",
      }}
    >
      <div style={{ maxWidth: 1450, margin: "0 auto" }}>
        <header style={{ marginBottom: 24 }}>
          <button
            type="button"
            style={buttonStyle}
            onClick={() => navigate("/ae/dashboard")}
          >
            Back to Dashboard
          </button>

          <h1
            style={{
              color: colors.dark,
              marginBottom: 8,
              marginTop: 22,
              fontSize: "clamp(24px, 3vw, 32px)",
            }}
          >
            Tubewell Assignment Management
          </h1>

          <p style={{ color: colors.muted }}>
            Assistant Engineer Workspace
          </p>

          <div
            style={{
              background: colors.pale,
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
              padding: "14px 17px",
              marginTop: 16,
            }}
          >
            <strong>{user.upazila_name || `Unit ${unitId}`}</strong>
            <div style={{ marginTop: 5, fontSize: 13 }}>
              Authorized Officer: {user.full_name}
            </div>
            <div
              style={{
                marginTop: 5,
                fontSize: 12,
                color: colors.muted,
              }}
            >
              Assignments are restricted to your management unit.
            </div>
          </div>
        </header>

        {success && (
          <section
            role="status"
            style={{
              ...panel,
              background: "#eaf8ee",
              borderColor: "#9dceb0",
            }}
          >
            <strong>Assignment Saved</strong>
            <p>{success}</p>
            <button
              type="button"
              style={buttonStyle}
              disabled={busy}
              onClick={refresh}
            >
              Refresh Current Records
            </button>
          </section>
        )}

        {saveError && (
          <section
            role="alert"
            style={{
              ...panel,
              background: "#fff5f3",
              borderColor: "#ecc4bc",
            }}
          >
            <strong>Assignment Notice</strong>
            <p>{saveError}</p>
            <button
              type="button"
              style={buttonStyle}
              disabled={busy}
              onClick={refresh}
            >
              Refresh Current Records
            </button>
          </section>
        )}

        {error && (
          <section role="alert" style={panel}>
            <strong>Unable to load assignments</strong>
            <p>{error}</p>
            <button
              type="button"
              style={buttonStyle}
              disabled={busy}
              onClick={refresh}
            >
              Retry
            </button>
          </section>
        )}

        {loading ? (
          <section style={panel} role="status">
            Loading your management-unit assignments...
          </section>
        ) : error ? null : (
          <>
            {/* SUMMARY CARDS */}

            <section
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(auto-fit, minmax(180px, 1fr))",
                gap: 15,
                marginBottom: 20,
              }}
            >
              {[
                {
                  title: "Registered Tubewells",
                  value: wells.length,
                },
                {
                  title: "Assigned Tubewells",
                  value: assignedCount,
                },
                {
                  title: "Unassigned Tubewells",
                  value: wells.length - assignedCount,
                },
                {
                  title: "Active Field Visitors",
                  value: fieldUsers.length,
                },
              ].map((item) => (
                <div
                  key={item.title}
                  style={{
                    ...panel,
                    marginBottom: 0,
                    padding: 21,
                  }}
                >
                  <div
                    style={{
                      fontSize: 13,
                      color: colors.muted,
                    }}
                  >
                    {item.title}
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 750,
                      color: colors.green,
                      marginTop: 8,
                    }}
                  >
                    {item.value}
                  </div>
                </div>
              ))}
            </section>

            {/* SEARCH AND FILTER */}

            <section style={panel}>
              <h2
                style={{
                  marginTop: 0,
                  color: colors.dark,
                }}
              >
                Find Tubewells
              </h2>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(220px, 1fr))",
                  gap: 14,
                }}
              >
                <label>
                  Search
                  <input
                    type="search"
                    style={inputStyle}
                    placeholder="DTW, union, mouza or visitor"
                    value={search}
                    onChange={(event) => {
                      setSearch(event.target.value);
                      setPage(1);
                    }}
                  />
                </label>

                <label>
                  Assignment Status
                  <select
                    style={inputStyle}
                    value={statusFilter}
                    onChange={(event) => {
                      setStatusFilter(event.target.value);
                      setPage(1);
                    }}
                  >
                    <option value="all">All Tubewells</option>
                    <option value="assigned">Assigned</option>
                    <option value="unassigned">Unassigned</option>
                  </select>
                </label>
              </div>

              <button
                type="button"
                style={{
                  ...buttonStyle,
                  marginTop: 16,
                }}
                disabled={busy}
                onClick={refresh}
              >
                Refresh
              </button>
            </section>

            {/* TUBEWELL TABLE */}

            <section style={panel}>
              <h2
                style={{
                  color: colors.dark,
                  marginTop: 0,
                }}
              >
                Tubewell Assignments
              </h2>

              <div style={{ overflowX: "auto" }}>
                <table
                  style={{
                    borderCollapse: "collapse",
                    width: "100%",
                    minWidth: 850,
                    fontSize: 13,
                  }}
                >
                  <thead style={{ background: colors.pale }}>
                    <tr>
                      {[
                        "SL",
                        "DTW Number",
                        "Union / Mouza",
                        "Field Visitor",
                        "Status",
                        "Manage",
                        "History",
                      ].map((label) => (
                        <th key={label} style={cellStyle}>
                          {label}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {visible.map((well, index) => {
                      const assignment =
                        currentByWell.get(well.id);

                      const visitor = assignment
                        ? userById.get(
                            assignment.field_user_id
                          )
                        : undefined;

                      return (
                        <Fragment key={well.id}>
                        <tr>
                          <td style={cellStyle}>
                            {startIndex + index + 1}
                          </td>

                          <td style={cellStyle}>
                            <strong>
                              {well.tubewell_number}
                            </strong>
                          </td>

                          <td style={cellStyle}>
                            {well.union_name}
                            <div
                              style={{
                                fontSize: 12,
                                color: colors.muted,
                              }}
                            >
                              {well.mouza}
                            </div>
                          </td>

                          <td style={cellStyle}>
                            {assignment
                              ? visitor?.full_name ??
                                `Field Visitor ID ${assignment.field_user_id}`
                              : "—"}
                          </td>

                          <td style={cellStyle}>
                            <strong
                              style={{
                                color: assignment
                                  ? colors.green
                                  : "#a56d16",
                              }}
                            >
                              {assignment
                                ? "Assigned"
                                : "Unassigned"}
                            </strong>

                            {!well.is_active && (
                              <div style={{ color: "#b42318" }}>
                                Inactive Tubewell
                              </div>
                            )}
                          </td>

                          <td style={cellStyle}>
                            <div
                              style={{
                                display: "inline-flex",
                                alignItems: "stretch",
                                whiteSpace: "nowrap",
                              }}
                            >
                              <button
                                type="button"
                                style={{
                                  ...buttonStyle,
                                  borderTopRightRadius: 0,
                                  borderBottomRightRadius: 0,
                                  borderRight: 0,
                                }}
                                disabled={
                                  busy ||
                                  needsRefresh ||
                                  !well.is_active
                                }
                                onClick={() => selectWell(well)}
                              >
                                {assignment ? "Reassign" : "Assign"}
                              </button>
                              <select
                                aria-label={`Choose Field Visitor for ${well.tubewell_number}`}
                                title="Select a Field Visitor"
                                value=""
                                disabled={
                                  busy ||
                                  needsRefresh ||
                                  !well.is_active ||
                                  fieldUsers.length === 0
                                }
                                onChange={(event) => {
                                  const id = Number(event.target.value);
                                  if (event.target.value && Number.isFinite(id)) {
                                    selectWell(well, id);
                                  }
                                }}
                                style={{
                                  ...buttonStyle,
                                  width: 44,
                                  minWidth: 44,
                                  padding: "10px 5px",
                                  borderTopLeftRadius: 0,
                                  borderBottomLeftRadius: 0,
                                  textAlign: "center",
                                  fontWeight: 700,
                                  background: colors.pale,
                                }}
                              >
                                <option value=""> </option>
                                {fieldUsers.map((person) => (
                                  <option key={person.id} value={person.id}>
                                    {person.full_name}
                                  </option>
                                ))}
                              </select>
                            </div>
                          </td>

                          <td style={cellStyle}>
                            <button
                              type="button"
                              style={buttonStyle}
                              onClick={() => {
                                setHistoryWell(well);
                              }}
                            >
                              View History
                            </button>
                          </td>
                        </tr>
                        {selectedWell?.id === well.id && (
                        <tr>
                          <td colSpan={7} style={{ padding: 0, borderBottom: `1px solid ${colors.border}` }}>
                  <section
                    style={{ ...panel, background: "#EADDCA" }}
                    aria-label="Tubewell assignment form"
                  >
                    <h2
                      style={{
                        color: colors.dark,
                        marginTop: 0,
                      }}
                    >
                      {currentAssignment
                        ? "Reassign Tubewell"
                        : "Assign Tubewell"}
                      {" — "}
                      {selectedWell.tubewell_number}
                    </h2>

                    <p style={{ color: colors.muted }}>
                      Current Field Visitor:{" "}
                      <strong>
                        {currentAssignment
                          ? userById.get(
                              currentAssignment.field_user_id
                            )?.full_name ??
                            `ID ${currentAssignment.field_user_id}`
                          : "Unassigned"}
                      </strong>
                    </p>

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns:
                          "repeat(auto-fit, minmax(230px, 1fr))",
                        gap: 15,
                      }}
                    >
                      <label>
                        Select Active Field Visitor
                        <select
                          style={inputStyle}
                          value={fieldUserId}
                          disabled={busy || needsRefresh}
                          onChange={(event) => {
                            setFieldUserId(event.target.value);
                            setPreview(false);
                            setSaveError("");
                          }}
                        >
                          <option value="">
                            Select Field Visitor
                          </option>

                          {fieldUsers.map((person) => (
                            <option
                              key={person.id}
                              value={person.id}
                            >
                              {person.full_name} (ID {person.id})
                            </option>
                          ))}
                        </select>
                      </label>

                      <label>
                        Assignment Date{" "}
                        {reassignment
                          ? "(Required)"
                          : "(Optional)"}

                        <input
                          type="date"
                          style={inputStyle}
                          value={assignmentDate}
                          disabled={busy || needsRefresh}
                          onChange={(event) => {
                            setAssignmentDate(event.target.value);
                            setPreview(false);
                            setSaveError("");
                          }}
                        />
                      </label>
                    </div>

                    {fieldUsers.length === 0 && (
                      <p role="status">
                        No active Field Visitors in this unit.
                      </p>
                    )}

                    {reassignment && !assignmentDate && (
                      <p style={{ color: "#a56d16" }}>
                        An effective date is required for reassignment.
                      </p>
                    )}

                    {reassignment &&
                      assignmentDate &&
                      currentAssignment?.assigned_at &&
                      assignmentDate <
                        currentAssignment.assigned_at && (
                        <p
                          role="alert"
                          style={{ color: "#b42318" }}
                        >
                          Date cannot precede the current
                          assignment date.
                        </p>
                      )}

                    <div
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: 12,
                        marginTop: 20,
                      }}
                    >
                      <button
                        type="button"
                        style={primaryStyle}
                        disabled={
                          !canPreview ||
                          busy ||
                          needsRefresh
                        }
                        onClick={() => {
                          setPreview(true);
                          setSaveError("");
                        }}
                      >
                        Review Assignment
                      </button>

                      <button
                        type="button"
                        style={buttonStyle}
                        disabled={busy}
                        onClick={() => {
                          setSelectedId(null);
                          setPreview(false);
                          setSaveError("");
                        }}
                      >
                        Close
                      </button>
                    </div>

                    {preview && canPreview && chosenUser && (
                      <div
                        style={{
                          background: colors.pale,
                          border: `1px solid ${colors.border}`,
                          borderRadius: 12,
                          padding: 20,
                          marginTop: 20,
                        }}
                      >
                        <h3 style={{ color: colors.dark }}>
                          {sameUser
                            ? "No Change Required"
                            : reassignment
                              ? "Reassignment Preview"
                              : "First Assignment Preview"}
                        </h3>

                        <p>
                          <strong>DTW:</strong>{" "}
                          {selectedWell.tubewell_number}
                        </p>
                        <p>
                          <strong>Field Visitor:</strong>{" "}
                          {chosenUser.full_name}
                        </p>
                        <p>
                          <strong>Effective Date:</strong>{" "}
                          {sameUser
                            ? showDate(
                                currentAssignment?.assigned_at ??
                                  null
                              )
                            : assignmentDate ||
                              "Not provided"}
                        </p>

                        {sameUser ? (
                          <p>
                            This visitor is already assigned.
                            No save is necessary.
                          </p>
                        ) : (
                          <>
                            <p>
                              Review all details before confirming.
                            </p>

                            <button
                              type="button"
                              style={primaryStyle}
                              disabled={!canSave}
                              onClick={() => {
                                void confirmAndSave();
                              }}
                            >
                              {saving
                                ? "Saving..."
                                : checking
                                  ? "Checking..."
                                  : "Confirm & Save Assignment"}
                            </button>

                            <p
                              style={{
                                color: colors.muted,
                                fontSize: 12,
                              }}
                            >
                              A final confirmation is required.
                              Existing assignment history is preserved.
                            </p>
                          </>
                        )}
                      </div>
                    )}
                  </section>
                          </td>
                        </tr>
                        )}
                        </Fragment>
                      );
                    })}

                    {visible.length === 0 && (
                      <tr>
                        <td colSpan={7} style={cellStyle}>
                          No matching tubewells found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  alignItems: "center",
                  gap: 12,
                  marginTop: 18,
                }}
              >
                <span>
                  Showing{" "}
                  {filtered.length
                    ? startIndex + 1
                    : 0}
                  {"–"}
                  {Math.min(
                    startIndex + pageSize,
                    filtered.length
                  )}{" "}
                  of {filtered.length}
                </span>

                <label>
                  Rows:{" "}
                  <select
                    value={pageSize}
                    onChange={(event) => {
                      setPageSize(Number(event.target.value));
                      setPage(1);
                    }}
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                  </select>
                </label>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                  }}
                >
                  <button
                    type="button"
                    disabled={safePage <= 1}
                    onClick={() => setPage(safePage - 1)}
                  >
                    Previous
                  </button>

                  <span>
                    Page {safePage} of {totalPages}
                  </span>

                  <button
                    type="button"
                    disabled={safePage >= totalPages}
                    onClick={() => setPage(safePage + 1)}
                  >
                    Next
                  </button>
                </div>
              </div>
            </section>

            {/* ASSIGNMENT HISTORY */}

            {historyWell && (
              <section style={panel}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: 12,
                  }}
                >
                  <h2
                    style={{
                      color: colors.dark,
                      marginTop: 0,
                    }}
                  >
                    Assignment History —{" "}
                    {historyWell.tubewell_number}
                  </h2>

                  <button
                    type="button"
                    style={buttonStyle}
                    onClick={() => setHistoryWell(null)}
                  >
                    Close
                  </button>
                </div>

                {historyLoading ? (
                  <p role="status">Loading history...</p>
                ) : historyError ? (
                  <p role="alert">{historyError}</p>
                ) : history.length === 0 ? (
                  <p>No assignment history recorded.</p>
                ) : (
                  <div style={{ overflowX: "auto" }}>
                    <table
                      style={{
                        width: "100%",
                        borderCollapse: "collapse",
                        fontSize: 13,
                        minWidth: 650,
                      }}
                    >
                      <thead
                        style={{
                          background: colors.pale,
                        }}
                      >
                        <tr>
                          {[
                            "Assignment ID",
                            "Field Visitor",
                            "Assigned Date",
                            "Ended Date",
                            "Status",
                          ].map((label) => (
                            <th
                              key={label}
                              style={cellStyle}
                            >
                              {label}
                            </th>
                          ))}
                        </tr>
                      </thead>

                      <tbody>
                        {history.map((record) => (
                          <tr key={record.id}>
                            <td style={cellStyle}>
                              {record.id}
                            </td>
                            <td style={cellStyle}>
                              {userById.get(
                                record.field_user_id
                              )?.full_name ??
                                `Field Visitor ID ${record.field_user_id}`}
                            </td>
                            <td style={cellStyle}>
                              {showDate(
                                record.assigned_at
                              )}
                            </td>
                            <td style={cellStyle}>
                              {record.ended_at || "—"}
                            </td>
                            <td style={cellStyle}>
                              {record.ended_at === null
                                ? "Current"
                                : "Previous"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            )}
          </>
        )}
      </div>
    </main>
  );
}