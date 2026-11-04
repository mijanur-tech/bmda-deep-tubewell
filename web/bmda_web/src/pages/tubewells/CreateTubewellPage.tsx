// ============================================================
// SECTION 1: IMPORTS
// Use existing API clients and React utilities.
// ============================================================
import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { createTubewell, getTubewells } from "../../api/tubewells.api";
import { getManagementUnits, type ManagementUnit } from "../../api/users.api";
import { getActualUpazilas, type ActualUpazila } from "../../api/actualUpazilas.api";
import { createUnion, getUnions, type UnionItem } from "../../api/unions.api";
import { createMouza, getMouzas, type MouzaItem } from "../../api/mouzas.api";
import {
  createDtwMaster,
  getDtwMaster,
  type DtwMasterItem,
} from "../../api/dtwMaster.api";
import "./CreateTubewellPage.css";

function CreateTubewellPage() {
  const navigate = useNavigate();

  // ==========================================================
  // SECTION 2: LIST DATA AND SELECTED VALUES
  // ==========================================================
  const [managementUnits, setManagementUnits] = useState<ManagementUnit[]>([]);
  const [actualUpazilas, setActualUpazilas] = useState<ActualUpazila[]>([]);
  const [unions, setUnions] = useState<UnionItem[]>([]);
  const [mouzas, setMouzas] = useState<MouzaItem[]>([]);
  const [dtwMasters, setDtwMasters] = useState<DtwMasterItem[]>([]);
  // Count master numbers before removing already registered numbers.
  const [masterDtwCount, setMasterDtwCount] = useState<number | null>(null);

  const [managementUnitId, setManagementUnitId] = useState("");
  const [actualUpazilaId, setActualUpazilaId] = useState("");
  const [unionId, setUnionId] = useState("");
  const [mouzaId, setMouzaId] = useState("");
  const [dtwNumber, setDtwNumber] = useState("");

  // New DTW Master modal state. Saving here does not create a Tubewell.
  const [showNewDtwForm, setShowNewDtwForm] = useState(false);
  const [newDtwNumber, setNewDtwNumber] = useState("");
  const [savingNewDtw, setSavingNewDtw] = useState(false);
  const [newDtwError, setNewDtwError] = useState("");

  // New Union and Mouza forms are available after their parent location is selected.
  const [showNewUnionForm, setShowNewUnionForm] = useState(false);
  const [newUnionName, setNewUnionName] = useState("");
  const [savingNewUnion, setSavingNewUnion] = useState(false);
  const [newUnionError, setNewUnionError] = useState("");
  const [showNewMouzaForm, setShowNewMouzaForm] = useState(false);
  const [newMouzaName, setNewMouzaName] = useState("");
  const [savingNewMouza, setSavingNewMouza] = useState(false);
  const [newMouzaError, setNewMouzaError] = useState("");

  // ==========================================================
  // SECTION 3: LOADING, STATUS AND REQUEST SAFETY
  // Request IDs prevent old API responses overwriting a newer selection.
  // ==========================================================
  const [loading, setLoading] = useState(true);
  const [loadingUpazilas, setLoadingUpazilas] = useState(false);
  const [loadingUnions, setLoadingUnions] = useState(false);
  const [loadingMouzas, setLoadingMouzas] = useState(false);
  const [loadingDtws, setLoadingDtws] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const upazilaRequest = useRef(0);
  const unionRequest = useRef(0);
  const mouzaRequest = useRef(0);
  const dtwRequest = useRef(0);

  // ==========================================================
  // SECTION 4: INITIAL MANAGEMENT UNIT LIST
  // ==========================================================
  useEffect(() => {
    async function loadManagementUnits() {
      try {
        setManagementUnits(await getManagementUnits());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load management units.");
      } finally {
        setLoading(false);
      }
    }
    void loadManagementUnits();
  }, []);

  // ==========================================================
  // SECTION 5: MANAGEMENT UNIT -> ACTUAL UPAZILA
  // Clear every dependent selection when Management Unit changes.
  // ==========================================================
  async function handleManagementUnitChange(value: string) {
    const requestId = ++upazilaRequest.current;
    ++unionRequest.current;
    ++mouzaRequest.current;
    ++dtwRequest.current;
    setManagementUnitId(value);
    setActualUpazilaId("");
    setUnionId("");
    setMouzaId("");
    setDtwNumber("");
    setActualUpazilas([]);
    setUnions([]);
    setMouzas([]);
    setDtwMasters([]);
    setMasterDtwCount(null);
    setLoadingUpazilas(false);
    setLoadingUnions(false);
    setLoadingMouzas(false);
    setLoadingDtws(false);
    setError("");
    setSuccessMessage("");
    if (!value) return;

    setLoadingUpazilas(true);
    try {
      const data = await getActualUpazilas(Number(value));
      if (requestId === upazilaRequest.current) setActualUpazilas(data);
    } catch (err) {
      if (requestId === upazilaRequest.current) {
        setError(err instanceof Error ? err.message : "Failed to load upazilas.");
      }
    } finally {
      if (requestId === upazilaRequest.current) setLoadingUpazilas(false);
    }
  }

  // ==========================================================
  // SECTION 6: ACTUAL UPAZILA -> UNION
  // ==========================================================
  async function handleUpazilaChange(value: string) {
    const requestId = ++unionRequest.current;
    ++mouzaRequest.current;
    ++dtwRequest.current;
    setActualUpazilaId(value);
    setUnionId("");
    setMouzaId("");
    setDtwNumber("");
    setUnions([]);
    setMouzas([]);
    setDtwMasters([]);
    setMasterDtwCount(null);
    setLoadingUnions(false);
    setLoadingMouzas(false);
    setLoadingDtws(false);
    setError("");
    setSuccessMessage("");
    if (!value) return;

    setLoadingUnions(true);
    try {
      const data = await getUnions(Number(value));
      if (requestId === unionRequest.current) setUnions(data);
    } catch (err) {
      if (requestId === unionRequest.current) {
        setError(err instanceof Error ? err.message : "Failed to load unions.");
      }
    } finally {
      if (requestId === unionRequest.current) setLoadingUnions(false);
    }
  }

  // ==========================================================
  // SECTION 7: UNION -> MOUZA
  // ==========================================================
  async function handleUnionChange(value: string) {
    const requestId = ++mouzaRequest.current;
    ++dtwRequest.current;
    setUnionId(value);
    setMouzaId("");
    setDtwNumber("");
    setMouzas([]);
    setDtwMasters([]);
    setMasterDtwCount(null);
    setLoadingMouzas(false);
    setLoadingDtws(false);
    setError("");
    setSuccessMessage("");
    if (!value) return;

    setLoadingMouzas(true);
    try {
      const data = await getMouzas(Number(value));
      if (requestId === mouzaRequest.current) setMouzas(data);
    } catch (err) {
      if (requestId === mouzaRequest.current) {
        setError(err instanceof Error ? err.message : "Failed to load mouzas.");
      }
    } finally {
      if (requestId === mouzaRequest.current) setLoadingMouzas(false);
    }
  }

  // ==========================================================
  // SECTION 8: MOUZA -> DTW NUMBER
  // Fetch master numbers and remove numbers already registered.
  // Both requests use the existing authenticated API client.
  // ==========================================================
  async function handleMouzaChange(value: string) {
    const requestId = ++dtwRequest.current;
    setMouzaId(value);
    setDtwNumber("");
    setDtwMasters([]);
    setMasterDtwCount(null);
    setLoadingDtws(false);
    setError("");
    setSuccessMessage("");
    if (!value) return;

    setLoadingDtws(true);
    try {
      const [masterData, registeredTubewells] = await Promise.all([
        getDtwMaster(Number(value)),
        getTubewells(),
      ]);
      const registeredNumbers = new Set(
        registeredTubewells.map((item) => item.tubewell_number)
      );
      if (requestId === dtwRequest.current) {
        setMasterDtwCount(masterData.filter((item) => item.mouza_id === Number(value)).length);
        setDtwMasters(
          masterData.filter(
            (item) =>
              item.mouza_id === Number(value) &&
              !registeredNumbers.has(item.dtw_number)
          )
        );
      }
    } catch (err) {
      if (requestId === dtwRequest.current) {
        setError(err instanceof Error ? err.message : "Failed to load available DTW numbers.");
      }
    } finally {
      if (requestId === dtwRequest.current) setLoadingDtws(false);
    }
  }

  // ==========================================================
  // SECTION 7B: ADD A NEW UNION UNDER THE SELECTED UPAZILA
  // ==========================================================
  async function handleCreateUnion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNewUnionError("");
    const name = newUnionName.trim();
    if (!actualUpazilaId) return setNewUnionError("Select an Upazila first.");
    if (!name) return setNewUnionError("Union name is required.");
    if (name !== newUnionName) return setNewUnionError("Remove leading or trailing spaces.");

    try {
      setSavingNewUnion(true);
      const created = await createUnion({
        name,
        actual_upazila_id: Number(actualUpazilaId),
      });
      const updated = [...unions.filter((item) => item.id !== created.id), created]
        .sort((a, b) => a.name.localeCompare(b.name));
      setUnions(updated);
      setUnionId(String(created.id));
      setMouzaId("");
      setDtwNumber("");
      setMouzas([]);
      setDtwMasters([]);
      setMasterDtwCount(null);
      setShowNewUnionForm(false);
      setNewUnionName("");
      setSuccessMessage(`Union "${created.name}" added. Now add or select its Mouza.`);
    } catch (err) {
      setNewUnionError(err instanceof Error ? err.message : "Could not create Union.");
    } finally {
      setSavingNewUnion(false);
    }
  }

  // ==========================================================
  // SECTION 7C: ADD A NEW MOUZA UNDER THE SELECTED UNION
  // ==========================================================
  async function handleCreateMouza(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNewMouzaError("");
    const name = newMouzaName.trim();
    if (!unionId) return setNewMouzaError("Select a Union first.");
    if (!name) return setNewMouzaError("Mouza name is required.");
    if (name !== newMouzaName) return setNewMouzaError("Remove leading or trailing spaces.");

    try {
      setSavingNewMouza(true);
      const created = await createMouza({
        name,
        union_id: Number(unionId),
      });
      const updated = [...mouzas.filter((item) => item.id !== created.id), created]
        .sort((a, b) => a.name.localeCompare(b.name));
      setMouzas(updated);
      setMouzaId(String(created.id));
      setDtwNumber("");
      setDtwMasters([]);
      setMasterDtwCount(0);
      setShowNewMouzaForm(false);
      setNewMouzaName("");
      setSuccessMessage(`Mouza "${created.name}" added. Now add its DTW Number.`);
    } catch (err) {
      setNewMouzaError(err instanceof Error ? err.message : "Could not create Mouza.");
    } finally {
      setSavingNewMouza(false);
    }
  }

  // ==========================================================
  // SECTION 8B: ADD NEW DTW MASTER NUMBER
  // Uses the selected Mouza and refreshes the available dropdown.
  // This does NOT register a Tubewell in Tubewell Management.
  // ==========================================================
  async function handleCreateDtwMaster(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNewDtwError("");

    const number = newDtwNumber.trim();
    if (!mouzaId) {
      setNewDtwError("Select Upazila, Union and Mouza first.");
      return;
    }
    if (!number) {
      setNewDtwError("DTW Number is required.");
      return;
    }
    if (number !== newDtwNumber) {
      setNewDtwError("DTW Number must not start or end with spaces.");
      return;
    }

    try {
      setSavingNewDtw(true);
      const created = await createDtwMaster({
        dtw_number: number,
        mouza_id: Number(mouzaId),
      });

      // Only add it to the selectable list; Tubewell registration
      // still requires the user to press Create Tubewell separately.
      setDtwMasters((current) =>
        [...current.filter((item) => item.id !== created.id), created]
          .sort((a, b) => a.dtw_number.localeCompare(b.dtw_number))
      );
      setMasterDtwCount((current) => (current ?? 0) + 1);
      setDtwNumber(created.dtw_number);
      setSuccessMessage(`${created.dtw_number} added to DTW Master. Now press Create Tubewell separately to register it.`);
      setNewDtwNumber("");
      setShowNewDtwForm(false);
    } catch (err) {
      setNewDtwError(err instanceof Error ? err.message : "Could not add DTW Master record.");
    } finally {
      setSavingNewDtw(false);
    }
  }

  // ==========================================================
  // SECTION 9: CREATE TUBEWELL
  // Preserve the existing backend request and name compatibility.
  // ==========================================================
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccessMessage("");

    if (!managementUnitId) return setError("Management Unit is required.");
    if (!actualUpazilaId) return setError("Upazila is required.");
    if (!unionId) return setError("Union is required.");
    if (!mouzaId) return setError("Mouza is required.");
    if (!dtwNumber) return setError("DTW Number is required.");

    const selectedUpazila = actualUpazilas.find((item) => item.id === Number(actualUpazilaId));
    const selectedUnion = unions.find((item) => item.id === Number(unionId));
    const selectedMouza = mouzas.find((item) => item.id === Number(mouzaId));
    const selectedDtw = dtwMasters.find(
      (item) => item.dtw_number === dtwNumber && item.mouza_id === Number(mouzaId)
    );
    if (!selectedUpazila || !selectedUnion || !selectedMouza || !selectedDtw) {
      setError("Selected location or DTW Number is invalid.");
      return;
    }

    try {
      setSubmitting(true);
      const createdTubewell = await createTubewell({
        tubewell_number: selectedDtw.dtw_number,
        // Keep this legacy backend-required field for compatibility.
        name: selectedDtw.dtw_number,
        management_unit_id: Number(managementUnitId),
        actual_upazila: selectedUpazila.name,
        union_name: selectedUnion.name,
        mouza: selectedMouza.name,
      });
      setSuccessMessage(`${createdTubewell.tubewell_number} successfully created.`);
      ++upazilaRequest.current;
      ++unionRequest.current;
      ++mouzaRequest.current;
      ++dtwRequest.current;
      setManagementUnitId("");
      setActualUpazilaId("");
      setUnionId("");
      setMouzaId("");
      setDtwNumber("");
      setActualUpazilas([]);
      setUnions([]);
      setMouzas([]);
      setDtwMasters([]);
    setMasterDtwCount(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create tubewell.");
    } finally {
      setSubmitting(false);
    }
  }

  // ==========================================================
  // SECTION 10: GREEN-WHITE FORM DISPLAY
  // The original dropdown logic, validations and API calls stay unchanged.
  // ==========================================================
  if (loading) {
    return (
      <div className="bmda-create-tubewell">
        <div className="ctw-card" role="status">Loading management units...</div>
      </div>
    );
  }

  return (
    <main className="bmda-create-tubewell">
      {/* SECTION 11: PAGE HEADER */}
      <header className="ctw-header">
        <div>
          <span className="ctw-eyebrow">BMDA / Tubewells</span>
          <h1>Create Tubewell</h1>
          <p>Register a tubewell from the approved DTW Master list.</p>
        </div>
        <button className="ctw-button ctw-button-secondary" type="button" onClick={() => navigate("/admin/tubewells")}>
          Back to Tubewells
        </button>
      </header>

      {/* SECTION 12: CASCADING REGISTRATION FORM */}
      <section className="ctw-card" aria-labelledby="ctw-form-heading">
        <div className="ctw-card-header">
          <div>
            <h2 id="ctw-form-heading">Tubewell Information</h2>
            <p>Select the location in order, then choose an available DTW Number.</p>
          </div>
          <span className="ctw-step-pill">5 Steps</span>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="ctw-form-grid">
            {/* SECTION 13: MANAGEMENT UNIT */}
            <div className="ctw-field">
              <label htmlFor="managementUnit"><span className="ctw-step">01</span> Management Unit <span className="ctw-required">*</span></label>
              <select
                id="managementUnit"
                value={managementUnitId}
                onChange={(event) => void handleManagementUnitChange(event.target.value)}
                disabled={submitting}
                required
              >
                <option value="" disabled>Select Management Unit</option>
                {managementUnits.map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
            </div>

            {/* SECTION 14: UPAZILA */}
            <div className="ctw-field">
              <label htmlFor="upazila"><span className="ctw-step">02</span> Upazila <span className="ctw-required">*</span></label>
              <select
                id="upazila"
                value={actualUpazilaId}
                onChange={(event) => void handleUpazilaChange(event.target.value)}
                disabled={!managementUnitId || loadingUpazilas || submitting}
                required
              >
                <option value="" disabled>
                  {!managementUnitId ? "Select Management Unit First" : loadingUpazilas ? "Loading Upazilas..." : "Select Upazila"}
                </option>
                {actualUpazilas.map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
            </div>

            {/* SECTION 15: UNION */}
            <div className="ctw-field">
              <label htmlFor="union"><span className="ctw-step">03</span> Union <span className="ctw-required">*</span></label>
              <select
                id="union"
                value={unionId}
                onChange={(event) => void handleUnionChange(event.target.value)}
                disabled={!actualUpazilaId || loadingUnions || submitting}
                required
              >
                <option value="" disabled>
                  {!actualUpazilaId ? "Select Upazila First" : loadingUnions ? "Loading Unions..." : "Select Union"}
                </option>
                {unions.map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
              {actualUpazilaId && (
                <button
                  className="ctw-button ctw-button-secondary ctw-new-dtw-trigger"
                  type="button"
                  onClick={() => {
                    setNewUnionError("");
                    setNewUnionName("");
                    setShowNewUnionForm(true);
                  }}
                  disabled={submitting || loadingUnions}
                >
                  <span aria-hidden="true">＋</span> New Union
                </button>
              )}
            </div>

            {/* SECTION 16: MOUZA */}
            <div className="ctw-field">
              <label htmlFor="mouza"><span className="ctw-step">04</span> Mouza <span className="ctw-required">*</span></label>
              <select
                id="mouza"
                value={mouzaId}
                onChange={(event) => void handleMouzaChange(event.target.value)}
                disabled={!unionId || loadingMouzas || submitting}
                required
              >
                <option value="" disabled>
                  {!unionId ? "Select Union First" : loadingMouzas ? "Loading Mouzas..." : "Select Mouza"}
                </option>
                {/* Hide only the verified empty Chandanbari / Joynanda Barua record (Mouza ID 75). */}
                {mouzas.filter((item) => item.id !== 75).map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
              {unionId && (
                <button
                  className="ctw-button ctw-button-secondary ctw-new-dtw-trigger"
                  type="button"
                  onClick={() => {
                    setNewMouzaError("");
                    setNewMouzaName("");
                    setShowNewMouzaForm(true);
                  }}
                  disabled={submitting || loadingMouzas}
                >
                  <span aria-hidden="true">＋</span> New Mouza
                </button>
              )}
            </div>

            {/* SECTION 17: AVAILABLE DTW NUMBERS */}
            <div className="ctw-field ctw-field-wide">
              <label htmlFor="dtwNumber"><span className="ctw-step">05</span> DTW Number <span className="ctw-required">*</span></label>
              <select
                id="dtwNumber"
                value={dtwNumber}
                onChange={(event) => setDtwNumber(event.target.value)}
                disabled={!mouzaId || loadingDtws || dtwMasters.length === 0 || submitting}
                required
              >
                <option value="" disabled>
                  {!mouzaId ? "Select Mouza First" : loadingDtws ? "Loading DTW Numbers..." : dtwMasters.length === 0 ? (masterDtwCount === 0 ? "No DTW Master Records Found" : "All DTW Numbers Already Registered") : "Select DTW Number"}
                </option>
                {dtwMasters.map((item) => (
                  <option key={item.id} value={item.dtw_number}>{item.dtw_number}</option>
                ))}
              </select>
              {mouzaId && (
                <button
                  className="ctw-button ctw-button-secondary ctw-new-dtw-trigger"
                  type="button"
                  onClick={() => {
                    setNewDtwError("");
                    setNewDtwNumber("");
                    setShowNewDtwForm(true);
                  }}
                  disabled={submitting || loadingDtws}
                >
                  <span aria-hidden="true">＋</span> New DTW
                </button>
              )}
              {mouzaId && !loadingDtws && dtwMasters.length === 0 && !error && (
                <p className="ctw-hint" role="status">
                  {masterDtwCount === 0 ? "No DTW Master Records Found for this Mouza." : "All DTW Numbers Already Registered for this Mouza."}
                </p>
              )}
            </div>
          </div>

          {/* SECTION 18: FEEDBACK AND SUBMISSION */}
          {error && <p className="ctw-alert ctw-alert-error" role="alert">{error}</p>}
          {successMessage && <p className="ctw-alert ctw-alert-success" role="status">{successMessage}</p>}

          <div className="ctw-form-actions">
            <button className="ctw-button ctw-button-primary" type="submit" disabled={submitting || loadingDtws || !dtwNumber}>
              {submitting ? "Creating..." : "Create Tubewell"}
            </button>
          </div>
        </form>
      </section>

      {/* SECTION 19A: NEW UNION MODAL */}
      {showNewUnionForm && (
        <div className="ctw-modal-backdrop" role="presentation">
          <section className="ctw-modal" role="dialog" aria-modal="true" aria-labelledby="ctw-new-union-title">
            <div className="ctw-modal-header">
              <div>
                <span className="ctw-eyebrow">Location Master</span>
                <h2 id="ctw-new-union-title">Add New Union</h2>
                <p>The new Union will belong to the selected Upazila.</p>
              </div>
              <button className="ctw-modal-close" type="button" aria-label="Close"
                onClick={() => setShowNewUnionForm(false)} disabled={savingNewUnion}>×</button>
            </div>
            <div className="ctw-modal-location">
              <div><span>Management Unit</span><strong>{managementUnits.find((item) => item.id === Number(managementUnitId))?.name ?? "—"}</strong></div>
              <div><span>Upazila</span><strong>{actualUpazilas.find((item) => item.id === Number(actualUpazilaId))?.name ?? "—"}</strong></div>
            </div>
            <form onSubmit={handleCreateUnion}>
              <div className="ctw-field">
                <label htmlFor="newUnionName">New Union Name <span className="ctw-required">*</span></label>
                <input id="newUnionName" className="ctw-text-input" value={newUnionName}
                  onChange={(event) => setNewUnionName(event.target.value)} maxLength={150}
                  autoFocus required disabled={savingNewUnion} placeholder="Enter the official Union name" />
              </div>
              {newUnionError && <p className="ctw-alert ctw-alert-error" role="alert">{newUnionError}</p>}
              <div className="ctw-modal-actions">
                <button className="ctw-button ctw-button-secondary" type="button"
                  onClick={() => setShowNewUnionForm(false)} disabled={savingNewUnion}>Cancel</button>
                <button className="ctw-button ctw-button-primary" type="submit"
                  disabled={savingNewUnion || !newUnionName.trim()}>{savingNewUnion ? "Saving..." : "Save Union"}</button>
              </div>
            </form>
          </section>
        </div>
      )}

      {/* SECTION 19B: NEW MOUZA MODAL */}
      {showNewMouzaForm && (
        <div className="ctw-modal-backdrop" role="presentation">
          <section className="ctw-modal" role="dialog" aria-modal="true" aria-labelledby="ctw-new-mouza-title">
            <div className="ctw-modal-header">
              <div>
                <span className="ctw-eyebrow">Location Master</span>
                <h2 id="ctw-new-mouza-title">Add New Mouza</h2>
                <p>The new Mouza will belong to the selected Union.</p>
              </div>
              <button className="ctw-modal-close" type="button" aria-label="Close"
                onClick={() => setShowNewMouzaForm(false)} disabled={savingNewMouza}>×</button>
            </div>
            <div className="ctw-modal-location">
              <div><span>Upazila</span><strong>{actualUpazilas.find((item) => item.id === Number(actualUpazilaId))?.name ?? "—"}</strong></div>
              <div><span>Union</span><strong>{unions.find((item) => item.id === Number(unionId))?.name ?? "—"}</strong></div>
            </div>
            <form onSubmit={handleCreateMouza}>
              <div className="ctw-field">
                <label htmlFor="newMouzaName">New Mouza Name <span className="ctw-required">*</span></label>
                <input id="newMouzaName" className="ctw-text-input" value={newMouzaName}
                  onChange={(event) => setNewMouzaName(event.target.value)} maxLength={150}
                  autoFocus required disabled={savingNewMouza} placeholder="Enter the official Mouza name" />
              </div>
              {newMouzaError && <p className="ctw-alert ctw-alert-error" role="alert">{newMouzaError}</p>}
              <div className="ctw-modal-actions">
                <button className="ctw-button ctw-button-secondary" type="button"
                  onClick={() => setShowNewMouzaForm(false)} disabled={savingNewMouza}>Cancel</button>
                <button className="ctw-button ctw-button-primary" type="submit"
                  disabled={savingNewMouza || !newMouzaName.trim()}>{savingNewMouza ? "Saving..." : "Save Mouza"}</button>
              </div>
            </form>
          </section>
        </div>
      )}

      {/* SECTION 19: NEW DTW MASTER MODAL */}
      {showNewDtwForm && (
        <div
          className="ctw-modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !savingNewDtw) {
              setShowNewDtwForm(false);
            }
          }}
        >
          <section
            className="ctw-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="ctw-new-dtw-title"
          >
            <div className="ctw-modal-header">
              <div>
                <span className="ctw-eyebrow">DTW Master</span>
                <h2 id="ctw-new-dtw-title">Add New DTW Number</h2>
                <p>This saves a Master record only. Tubewell registration is a separate step.</p>
              </div>
              <button
                className="ctw-modal-close"
                type="button"
                aria-label="Close"
                onClick={() => setShowNewDtwForm(false)}
                disabled={savingNewDtw}
              >
                ×
              </button>
            </div>

            <div className="ctw-modal-location">
              <div><span>Upazila</span><strong>{actualUpazilas.find((item) => item.id === Number(actualUpazilaId))?.name ?? "—"}</strong></div>
              <div><span>Union</span><strong>{unions.find((item) => item.id === Number(unionId))?.name ?? "—"}</strong></div>
              <div><span>Mouza</span><strong>{mouzas.find((item) => item.id === Number(mouzaId))?.name ?? "—"}</strong></div>
            </div>

            <form onSubmit={handleCreateDtwMaster}>
              <div className="ctw-field">
                <label htmlFor="newDtwNumber">New DTW Number <span className="ctw-required">*</span></label>
                <input
                  id="newDtwNumber"
                  className="ctw-text-input"
                  type="text"
                  value={newDtwNumber}
                  onChange={(event) => setNewDtwNumber(event.target.value)}
                  maxLength={100}
                  autoFocus
                  required
                  disabled={savingNewDtw}
                  placeholder="Enter the officially assigned DTW number"
                />
                <p className="ctw-modal-note">Use the number approved in the official record. Do not invent a number.</p>
              </div>

              {newDtwError && <p className="ctw-alert ctw-alert-error" role="alert">{newDtwError}</p>}

              <div className="ctw-modal-actions">
                <button
                  className="ctw-button ctw-button-secondary"
                  type="button"
                  onClick={() => setShowNewDtwForm(false)}
                  disabled={savingNewDtw}
                >
                  Cancel
                </button>
                <button
                  className="ctw-button ctw-button-primary"
                  type="submit"
                  disabled={savingNewDtw || !newDtwNumber.trim()}
                >
                  {savingNewDtw ? "Saving..." : "Save to DTW Master"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </main>
  );
}

export default CreateTubewellPage;
