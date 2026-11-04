// ============================================================
// SECTION 1: IMPORTS
// Use existing authenticated APIs and React utilities.
// ============================================================
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./TubewellsPage.css";
import {
  getTubewells,
  updateTubewellStatus,
  type TubewellItem,
} from "../../api/tubewells.api";
import {
  getManagementUnits,
  type ManagementUnit,
} from "../../api/users.api";
import {
  getActualUpazilas,
  type ActualUpazila,
} from "../../api/actualUpazilas.api";

// ============================================================
// SECTION 2: TUBEWELL MANAGEMENT PAGE
// Keep Add, Edit, Deactivate and Reactivate functionality.
// All search/filter operations are local (no database writes).
// ============================================================
function TubewellsPage() {
  const navigate = useNavigate();
  const [tubewells, setTubewells] = useState<TubewellItem[]>([]);
  const [managementUnits, setManagementUnits] = useState<ManagementUnit[]>([]);
  const [upazilas, setUpazilas] = useState<ActualUpazila[]>([]);

  const [loading, setLoading] = useState(true);
  const [loadingUpazilas, setLoadingUpazilas] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [filterError, setFilterError] = useState("");
  const [message, setMessage] = useState("");

  // SECTION 3: FILTER VALUES
  const [searchText, setSearchText] = useState("");
  const [managementUnitId, setManagementUnitId] = useState("");
  const [actualUpazila, setActualUpazila] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // ==========================================================
  // SECTION 4: LOAD INITIAL DATA
  // Get the full Admin list and Management Units once.
  // ==========================================================
  useEffect(() => {
    let cancelled = false;
    async function loadData() {
      try {
        const [tubewellData, unitData] = await Promise.all([
          getTubewells(),
          getManagementUnits(),
        ]);
        if (!cancelled) {
          setTubewells(tubewellData);
          setManagementUnits(unitData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load tubewells.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadData();
    return () => { cancelled = true; };
  }, []);

  // ==========================================================
  // SECTION 5: LOAD UPAZILAS FOR SELECTED MANAGEMENT UNIT
  // Changing Management Unit resets the selected Upazila.
  // Cancellation prevents an old response replacing newer data.
  // ==========================================================
  useEffect(() => {
    let cancelled = false;
    setUpazilas([]);
    setFilterError("");
    if (!managementUnitId) {
      setLoadingUpazilas(false);
      return () => { cancelled = true; };
    }

    setLoadingUpazilas(true);
    async function loadUpazilas() {
      try {
        const result = await getActualUpazilas(Number(managementUnitId));
        if (!cancelled) setUpazilas(result);
      } catch (err) {
        if (!cancelled) {
          setFilterError(err instanceof Error ? err.message : "Failed to load upazilas.");
        }
      } finally {
        if (!cancelled) setLoadingUpazilas(false);
      }
    }
    void loadUpazilas();
    return () => { cancelled = true; };
  }, [managementUnitId]);

  // ==========================================================
  // SECTION 6: LOCAL SEARCH AND FILTER
  // Match DTW Number, Management Unit, Upazila and status.
  // ==========================================================
  const filteredTubewells = useMemo(() => {
    const query = searchText.trim().toLowerCase();
    return tubewells.filter((well) => {
      if (query && !well.tubewell_number.toLowerCase().includes(query)) return false;
      if (managementUnitId && well.management_unit_id !== Number(managementUnitId)) return false;
      if (actualUpazila && well.actual_upazila !== actualUpazila) return false;
      if (statusFilter === "active" && !well.is_active) return false;
      if (statusFilter === "inactive" && well.is_active) return false;
      return true;
    });
  }, [tubewells, searchText, managementUnitId, actualUpazila, statusFilter]);

  function getManagementUnitName(id: number): string {
    const unit = managementUnits.find((item) => item.id === id);
    return unit?.name ?? `ID: ${id}`;
  }

  // ==========================================================
  // SECTION 7: RESET FILTERS
  // ==========================================================
  function clearFilters() {
    setSearchText("");
    setManagementUnitId("");
    setActualUpazila("");
    setStatusFilter("all");
    setFilterError("");
  }

  // ==========================================================
  // SECTION 8: STATUS CHANGE (EXISTING BEHAVIOR)
  // Always ask for confirmation. Never permanently delete.
  // ==========================================================
  async function handleStatusChange(tubewell: TubewellItem) {
    if (busyId !== null) return;
    const nextStatus = !tubewell.is_active;
    const action = nextStatus ? "Reactivate" : "Deactivate";
    if (!window.confirm(`${action} tubewell ${tubewell.tubewell_number}?`)) return;

    setError("");
    setMessage("");
    setBusyId(tubewell.id);
    try {
      const updated = await updateTubewellStatus(tubewell.id, nextStatus);
      setTubewells((current) =>
        current.map((item) => item.id === updated.id ? updated : item)
      );
      setMessage(`${updated.tubewell_number} ${updated.is_active ? "reactivated" : "deactivated"} successfully.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update tubewell status.");
    } finally {
      setBusyId(null);
    }
  }

  // ==========================================================
  // SECTION 9: PAGE COUNTS AND DISPLAY
  // ==========================================================
  const activeCount = tubewells.filter((well) => well.is_active).length;
  const inactiveCount = tubewells.length - activeCount;

  if (loading) {
    return <div className="bmda-tubewells"><p>Loading tubewells...</p></div>;
  }

  return (
    <main className="bmda-tubewells">
      {/* SECTION 10: PAGE HEADER AND NAVIGATION */}
      <header className="tw-header">
        <div>
          <h1 className="tw-title">Tubewells Management</h1>
          <p className="tw-subtitle">Manage deep tubewell records and their active status.</p>
        </div>
        <div className="tw-actions">
          <button
            className="tw-btn tw-btn-outline"
            type="button"
            onClick={() => navigate("/admin/dashboard")}
          >
            Back to Dashboard
          </button>
          <button
            className="tw-btn tw-btn-primary"
            type="button"
            onClick={() => navigate("/admin/tubewells/create")}
          >
            + Add Tubewell
          </button>
        </div>
      </header>

      {/* SECTION 11: SUMMARY CARDS */}
      <section className="tw-summary" aria-label="Tubewell summary">
        <div className="tw-summary-card">
          <div className="tw-summary-label">Total Tubewells</div>
          <div className="tw-summary-value">{tubewells.length}</div>
        </div>
        <div className="tw-summary-card">
          <div className="tw-summary-label">Active Tubewells</div>
          <div className="tw-summary-value">{activeCount}</div>
        </div>
        <div className="tw-summary-card">
          <div className="tw-summary-label">Inactive Tubewells</div>
          <div className="tw-summary-value">{inactiveCount}</div>
        </div>
      </section>

      {/* SECTION 12: SEARCH AND FILTER CONTROLS */}
      <section className="tw-filter-card" aria-label="Search and filter tubewells">
        <h2 className="tw-section-title">Search &amp; Filter</h2>
        <div className="tw-filter-grid">
          <div className="tw-field">
            <label htmlFor="dtwSearch">Search DTW Number</label>
            <input
              className="tw-input"
              id="dtwSearch"
              type="search"
              placeholder="e.g. PT-08"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
            />
          </div>
          <div className="tw-field">
            <label htmlFor="unitFilter">Management Unit</label>
            <select
              className="tw-select"
              id="unitFilter"
              value={managementUnitId}
              onChange={(event) => {
                setManagementUnitId(event.target.value);
                setActualUpazila("");
              }}
            >
              <option value="">All Management Units</option>
              {managementUnits.map((unit) => (
                <option key={unit.id} value={unit.id}>{unit.name}</option>
              ))}
            </select>
          </div>
          <div className="tw-field">
            <label htmlFor="upazilaFilter">Upazila</label>
            <select
              className="tw-select"
              id="upazilaFilter"
              value={actualUpazila}
              disabled={!managementUnitId || loadingUpazilas || Boolean(filterError)}
              onChange={(event) => setActualUpazila(event.target.value)}
            >
              <option value="">{loadingUpazilas ? "Loading Upazilas..." : "All Upazilas"}</option>
              {upazilas.map((item) => (
                <option key={item.id} value={item.name}>{item.name}</option>
              ))}
            </select>
          </div>
          <div className="tw-field">
            <label htmlFor="statusFilter">Status</label>
            <select
              className="tw-select"
              id="statusFilter"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>
        <div className="tw-actions" style={{ marginTop: 16 }}>
          <button className="tw-btn tw-btn-outline" type="button" onClick={clearFilters}>
            Clear Filters
          </button>
        </div>
      </section>

      {/* SECTION 13: FEEDBACK */}
      {error && <p role="alert" style={{ color: "#b42318", marginBottom: 12 }}>{error}</p>}
      {filterError && <p role="alert" style={{ color: "#b42318", marginBottom: 12 }}>{filterError}</p>}
      {message && <p role="status" style={{ color: "#116738", marginBottom: 12 }}>{message}</p>}

      {/* SECTION 14: TUBEWELLS TABLE */}
      <section className="tw-table-card" aria-label="Tubewells list">
        <div className="tw-table-toolbar">
          Showing <strong>{filteredTubewells.length}</strong> of{" "}
          <strong>{tubewells.length}</strong> Tubewells
        </div>
        <div className="tw-table-scroll">
          <table className="tw-table">
            <thead>
              <tr>
                <th>DTW Number</th>
                <th>Management Unit</th>
                <th>Upazila</th>
                <th>Union</th>
                <th>Mouza</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTubewells.map((well) => (
                <tr key={well.id}>
                  <td><strong>{well.tubewell_number}</strong></td>
                  <td>{getManagementUnitName(well.management_unit_id)}</td>
                  <td>{well.actual_upazila}</td>
                  <td>{well.union_name}</td>
                  <td>{well.mouza}</td>
                  <td>
                    <span className={`tw-status ${well.is_active ? "tw-status-active" : "tw-status-inactive"}`}>
                      {well.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td>
                    <div className="tw-actions">
                      <button
                        className="tw-btn tw-btn-outline"
                        type="button"
                        disabled={busyId !== null}
                        onClick={() => navigate(`/admin/tubewells/${well.id}/edit`)}
                      >
                        Edit
                      </button>
                      <button
                        className={`tw-btn ${well.is_active ? "tw-btn-danger" : "tw-btn-primary"}`}
                        type="button"
                        disabled={busyId !== null}
                        onClick={() => void handleStatusChange(well)}
                      >
                        {busyId === well.id ? "Updating..." : well.is_active ? "Deactivate" : "Reactivate"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filteredTubewells.length === 0 && (
                <tr>
                  <td colSpan={7} className="tw-empty">
                    No tubewells match the selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

export default TubewellsPage;
