
import { useEffect, useMemo, useState, type CSSProperties } from "react";

import { getTubewells, type TubewellItem } from "../../api/tubewells.api";
import {
  getUsers,
  getManagementUnits,
  type UserItem,
  type ManagementUnit,
} from "../../api/users.api";
import {
  getAssignments,
  getAssignmentHistory,
  type AssignmentItem,
} from "../../api/assignments.api";

// ============================================================
// BMDA ADMIN — TUBEWELL ASSIGNMENT MONITORING
//
// Executive Engineer: Read-only across all management units.
// Assignment and reassignment are performed by Assistant
// Engineers within their authorized management units.
//
// No POST, PUT, PATCH or DELETE requests in this component.
// ============================================================

const OFFICIAL_TUBEWELL_TOTAL = 448;

const panel: CSSProperties = {
  background: "#ffffff",
  border: "1px solid #dcece0",
  borderRadius: 14,
  padding: 20,
  marginBottom: 18,
};

const fieldStyle: CSSProperties = {
  padding: "10px 12px",
  border: "1px solid #cbded0",
  borderRadius: 8,
  background: "#ffffff",
  color: "#183c2b",
  width: "100%",
  minWidth: 0,
  fontFamily: "inherit",
};

const cellStyle: CSSProperties = {
  padding: 12,
  borderBottom: "1px solid #e3ece5",
  textAlign: "left",
  whiteSpace: "nowrap",
};

const actionStyle: CSSProperties = {
  padding: "8px 12px",
  border: "1px solid #97c4a4",
  borderRadius: 8,
  background: "#ffffff",
  color: "#176d3e",
  cursor: "pointer",
  fontFamily: "inherit",
};

const errorStyle: CSSProperties = {
  ...panel,
  background: "#fff5f4",
  borderColor: "#f1c1bd",
  color: "#a32620",
};

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message === "SESSION_EXPIRED"
      ? "Your session has expired. Please log in again."
      : error.message;
  }
  return "An unexpected error occurred.";
}

function formatDate(value: string | null): string {
  return value || "Not recorded";
}

export default function AssignmentsPage() {
  // ==========================================================
  // SECTION 1: READ-ONLY DATA
  // ==========================================================

  const [tubewells, setTubewells] = useState<TubewellItem[]>([]);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [units, setUnits] = useState<ManagementUnit[]>([]);
  const [assignments, setAssignments] = useState<AssignmentItem[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  // ==========================================================
  // SECTION 2: SEARCH, FILTER AND PAGINATION
  // ==========================================================

  const [search, setSearch] = useState("");
  const [unitFilter, setUnitFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  // ==========================================================
  // SECTION 3: ASSIGNMENT HISTORY STATE
  // ==========================================================

  const [historyWell, setHistoryWell] = useState<TubewellItem | null>(null);
  const [history, setHistory] = useState<AssignmentItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");

  // ==========================================================
  // SECTION 4: LOAD AUTHORIZED ADMIN DATA
  // ==========================================================

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const [wells, people, managementUnits, current] =
          await Promise.all([
            getTubewells(),
            getUsers(),
            getManagementUnits(),
            getAssignments(true),
          ]);

        if (cancelled) return;

        if (
          !Array.isArray(wells) ||
          !Array.isArray(people) ||
          !Array.isArray(managementUnits) ||
          !Array.isArray(current)
        ) {
          throw new Error("Unexpected API response.");
        }

        setTubewells(wells);
        setUsers(people);
        setUnits(managementUnits);
        setAssignments(current);
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  // ==========================================================
  // SECTION 5: LOOKUP MAPS AND SUMMARY
  // ==========================================================

  const userById = useMemo(
    () => new Map(users.map((user) => [user.id, user])),
    [users]
  );

  const unitById = useMemo(
    () => new Map(units.map((unit) => [unit.id, unit.name])),
    [units]
  );

  const currentByTubewell = useMemo(() => {
    const map = new Map<number, AssignmentItem>();

    for (const assignment of assignments) {
      if (assignment.ended_at === null) {
        map.set(assignment.tubewell_id, assignment);
      }
    }

    return map;
  }, [assignments]);

  const assignedCount = tubewells.filter((well) =>
    currentByTubewell.has(well.id)
  ).length;

  const unassignedCount = tubewells.length - assignedCount;

  // ==========================================================
  // SECTION 6: FILTERED TUBEWELLS
  // ==========================================================

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();

    return tubewells.filter((well) => {
      const assignment = currentByTubewell.get(well.id);

      const person = assignment
        ? userById.get(assignment.field_user_id)
        : undefined;

      const searchable = [
        well.tubewell_number,
        well.name,
        well.union_name,
        well.mouza,
        person?.full_name ?? "",
      ]
        .join(" ")
        .toLowerCase();

      if (query && !searchable.includes(query)) return false;

      if (
        unitFilter &&
        well.management_unit_id !== Number(unitFilter)
      ) {
        return false;
      }

      if (statusFilter === "assigned" && !assignment) {
        return false;
      }

      if (statusFilter === "unassigned" && assignment) {
        return false;
      }

      return true;
    });
  }, [
    tubewells,
    currentByTubewell,
    userById,
    search,
    unitFilter,
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

  // ==========================================================
  // SECTION 7: READ-ONLY HISTORY
  // ==========================================================

  useEffect(() => {
    if (!historyWell) {
      setHistory([]);
      setHistoryError("");
      setHistoryLoading(false);
      return;
    }

    let cancelled = false;

    async function loadHistory() {
      setHistoryLoading(true);
      setHistoryError("");
      setHistory([]);

      try {
        const records = await getAssignmentHistory(historyWell!.id);

        if (cancelled) return;

        if (!Array.isArray(records)) {
          throw new Error("Unexpected assignment history response.");
        }

        setHistory(records);
      } catch (err) {
        if (!cancelled) {
          setHistoryError(getErrorMessage(err));
        }
      } finally {
        if (!cancelled) {
          setHistoryLoading(false);
        }
      }
    }

    void loadHistory();

    return () => {
      cancelled = true;
    };
  }, [historyWell, reloadKey]);

  function refreshRecords() {
    if (loading) return;
    setHistoryWell(null);
    setReloadKey((value) => value + 1);
  }

  function openHistory(well: TubewellItem) {
    setHistoryWell(well);
  }

  function closeHistory() {
    setHistoryWell(null);
  }

  // ==========================================================
  // SECTION 8: ADMIN READ-ONLY PAGE
  // ==========================================================

  return (
    <main
      style={{
        padding: 24,
        maxWidth: 1500,
        margin: "0 auto",
        color: "#183c2b",
        fontFamily: "Segoe UI, Arial, sans-serif",
      }}
    >
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ color: "#204f34", marginTop: 0 }}>
          Tubewell Assignment Monitoring
        </h1>

        <p>
          View Field Visitor assignments across all BMDA
          management units.
        </p>

        <p style={{ color: "#607366", fontSize: 13 }}>
          Executive Engineer: Read-only access. Assignment and
          reassignment are managed by authorized Assistant Engineers.
          Previous assignment history is preserved.
        </p>
      </header>

      {/* READ-ONLY INFORMATION */}

      <section style={panel}>
        <strong style={{ color: "#176d3e" }}>
          Assignment Monitoring — Read Only
        </strong>

        <p style={{ marginBottom: 0, color: "#607366" }}>
          This workspace does not allow creating, editing or
          reassigning tubewell assignments.
        </p>
      </section>

      {/* ERROR MESSAGE */}

      {error && (
        <div role="alert" style={errorStyle}>
          <p>{error}</p>

          <button
            type="button"
            style={actionStyle}
            disabled={loading}
            onClick={refreshRecords}
          >
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <p role="status">Loading assignment information...</p>
      ) : error ? null : (
        <>
          {/* ==================================================
              SECTION 9: SUMMARY
              ================================================== */}

          <section style={panel}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(auto-fit, minmax(170px, 1fr))",
                gap: 16,
              }}
            >
              <div>
                <div>Registered Tubewells</div>
                <h2>{tubewells.length}</h2>
              </div>

              <div>
                <div>Assigned Tubewells</div>
                <h2>{assignedCount}</h2>
              </div>

              <div>
                <div>Unassigned Tubewells</div>
                <h2>{unassignedCount}</h2>
              </div>
            </div>

            <p
              style={{
                fontSize: 12,
                color: "#607366",
                marginBottom: 0,
              }}
            >
              BMDA overall inventory: {OFFICIAL_TUBEWELL_TOTAL}.
              {" "}Registered: {tubewells.length}.
              {" "}Remaining not registered:{" "}
              {Math.max(
                0,
                OFFICIAL_TUBEWELL_TOTAL - tubewells.length
              )}.
            </p>
          </section>

          {/* ==================================================
              SECTION 10: SEARCH AND FILTER
              ================================================== */}

          <section style={panel}>
            <h2 style={{ color: "#204f34", marginTop: 0 }}>
              Search &amp; Filter
            </h2>

            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(auto-fit, minmax(190px, 1fr))",
                gap: 12,
              }}
            >
              <label>
                Search
                <input
                  style={fieldStyle}
                  type="search"
                  placeholder="DTW number or Field User"
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                  }}
                />
              </label>

              <label>
                Management Unit
                <select
                  style={fieldStyle}
                  value={unitFilter}
                  onChange={(event) => {
                    setUnitFilter(event.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All Units</option>

                  {units.map((unit) => (
                    <option key={unit.id} value={unit.id}>
                      {unit.name}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Assignment Status
                <select
                  style={fieldStyle}
                  value={statusFilter}
                  onChange={(event) => {
                    setStatusFilter(event.target.value);
                    setPage(1);
                  }}
                >
                  <option value="all">All</option>
                  <option value="assigned">Assigned</option>
                  <option value="unassigned">Unassigned</option>
                </select>
              </label>
            </div>

            <button
              type="button"
              style={{ ...actionStyle, marginTop: 15 }}
              onClick={refreshRecords}
            >
              Refresh
            </button>
          </section>

          {/* ==================================================
              SECTION 11: CURRENT ASSIGNMENTS TABLE
              ================================================== */}

          <section style={panel}>
            <h2 style={{ color: "#204f34", marginTop: 0 }}>
              Current Assignments
            </h2>

            <div style={{ overflowX: "auto" }}>
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  fontSize: 13,
                }}
              >
                <thead style={{ background: "#eaf5ed" }}>
                  <tr>
                    {[
                      "SL",
                      "DTW Number",
                      "Management Unit",
                      "Field User",
                      "Assignment Date",
                      "Status",
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
                      currentByTubewell.get(well.id);

                    const person = assignment
                      ? userById.get(assignment.field_user_id)
                      : undefined;

                    return (
                      <tr key={well.id}>
                        <td style={cellStyle}>
                          {startIndex + index + 1}
                        </td>

                        <td style={cellStyle}>
                          <strong>
                            {well.tubewell_number}
                          </strong>
                        </td>

                        <td style={cellStyle}>
                          {unitById.get(
                            well.management_unit_id
                          ) ??
                            `Unit ${well.management_unit_id}`}
                        </td>

                        <td style={cellStyle}>
                          {assignment
                            ? person?.full_name ??
                              `Field User ID ${assignment.field_user_id}`
                            : "—"}
                        </td>

                        <td style={cellStyle}>
                          {assignment
                            ? formatDate(assignment.assigned_at)
                            : "—"}
                        </td>

                        <td style={cellStyle}>
                          <strong
                            style={{
                              color: assignment
                                ? "#176d3e"
                                : "#9a6100",
                            }}
                          >
                            {assignment
                              ? "Assigned"
                              : "Unassigned"}
                          </strong>
                        </td>

                        <td style={cellStyle}>
                          <button
                            type="button"
                            style={actionStyle}
                            onClick={() => openHistory(well)}
                          >
                            View History
                          </button>
                        </td>
                      </tr>
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

            {/* PAGINATION */}

            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 12,
                marginTop: 20,
              }}
            >
              <span>
                Showing{" "}
                {filtered.length === 0 ? 0 : startIndex + 1}
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
                  gap: 8,
                  alignItems: "center",
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

          {/* ==================================================
              SECTION 12: ASSIGNMENT HISTORY
              ================================================== */}

          {historyWell && (
            <section
              style={panel}
              aria-label="Assignment history"
            >
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 12,
                }}
              >
                <h2
                  style={{
                    color: "#204f34",
                    marginTop: 0,
                  }}
                >
                  Assignment History —{" "}
                  {historyWell.tubewell_number}
                </h2>

                <button
                  type="button"
                  style={actionStyle}
                  onClick={closeHistory}
                >
                  Close
                </button>
              </div>

              <p style={{ color: "#607366" }}>
                Read-only history of Field Visitor assignments
                for this tubewell.
              </p>

              {historyLoading ? (
                <p role="status">
                  Loading assignment history...
                </p>
              ) : historyError ? (
                <div role="alert" style={errorStyle}>
                  {historyError}
                </div>
              ) : history.length === 0 ? (
                <p>
                  No assignment history recorded for this
                  tubewell.
                </p>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table
                    style={{
                      width: "100%",
                      borderCollapse: "collapse",
                      fontSize: 13,
                    }}
                  >
                    <thead style={{ background: "#eaf5ed" }}>
                      <tr>
                        {[
                          "Assignment ID",
                          "Field User",
                          "Assigned Date",
                          "Ended Date",
                          "Record Status",
                        ].map((label) => (
                          <th key={label} style={cellStyle}>
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
                            {userById.get(record.field_user_id)
                              ?.full_name ??
                              `Field User ID ${record.field_user_id}`}
                          </td>

                          <td style={cellStyle}>
                            {formatDate(record.assigned_at)}
                          </td>

                          <td style={cellStyle}>
                            {record.ended_at
                              ? formatDate(record.ended_at)
                              : "—"}
                          </td>

                          <td style={cellStyle}>
                            <strong
                              style={{
                                color:
                                  record.ended_at === null
                                    ? "#176d3e"
                                    : "#607366",
                              }}
                            >
                              {record.ended_at === null
                                ? "Current"
                                : "Previous"}
                            </strong>
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
    </main>
  );
}
