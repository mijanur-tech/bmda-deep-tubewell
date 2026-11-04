// ============================================================
// SECTION 1: IMPORTS
// Existing BMDA API functions handle JWT authentication.
// ============================================================
import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./EditTubewellPage.css";

import { getTubewell, getTubewells, updateTubewell, type TubewellItem } from "../../api/tubewells.api";
import { getManagementUnits, type ManagementUnit } from "../../api/users.api";
import { getActualUpazilas, type ActualUpazila } from "../../api/actualUpazilas.api";
import { getUnions, type UnionItem } from "../../api/unions.api";
import { getMouzas, type MouzaItem } from "../../api/mouzas.api";
import { getDtwMaster, type DtwMasterItem } from "../../api/dtwMaster.api";

// ============================================================
// SECTION 2: EDIT TUBEWELL PAGE
// The existing tubewell ID remains unchanged during editing.
// ============================================================
function EditTubewellPage() {
  const navigate = useNavigate();
  const { tubewellId } = useParams<{ tubewellId: string }>();
  const id = Number(tubewellId);

  const [managementUnits, setManagementUnits] = useState<ManagementUnit[]>([]);
  const [upazilas, setUpazilas] = useState<ActualUpazila[]>([]);
  const [unions, setUnions] = useState<UnionItem[]>([]);
  const [mouzas, setMouzas] = useState<MouzaItem[]>([]);
  const [dtwNumbers, setDtwNumbers] = useState<DtwMasterItem[]>([]);
  const [registeredTubewells, setRegisteredTubewells] = useState<TubewellItem[] | null>(null);
  const [existingTubewell, setExistingTubewell] = useState<TubewellItem | null>(null);
  const [locationWarning, setLocationWarning] = useState("");

  const [managementUnitId, setManagementUnitId] = useState("");
  const [upazilaId, setUpazilaId] = useState("");
  const [unionId, setUnionId] = useState("");
  const [mouzaId, setMouzaId] = useState("");
  const [dtwNumber, setDtwNumber] = useState("");

  const [loading, setLoading] = useState(true);
  const [loadingNext, setLoadingNext] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const requestVersion = useRef(0);

  // ==========================================================
  // SECTION 3: LOAD EXISTING DATA AND LOCATION DROPDOWNS
  // Match stored location names to current master IDs.
  // ==========================================================
  useEffect(() => {
    let cancelled = false;

    async function loadExistingTubewell() {
      if (!Number.isInteger(id) || id <= 0) {
        setError("Invalid tubewell ID.");
        setLoading(false);
        return;
      }

      try {
        // Load the registered numbers before showing selectable DTW numbers.
        // If this request fails, editing is blocked rather than risking a collision.
        const [well, units, registered] = await Promise.all([
          getTubewell(id),
          getManagementUnits(),
          getTubewells(),
        ]);
        if (cancelled) return;
        setExistingTubewell(well);
        setRegisteredTubewells(registered);
        setManagementUnits(units);
        setManagementUnitId(String(well.management_unit_id));

        // A wrongly registered location must not prevent the Admin from
        // opening the edit form and selecting a valid replacement.
        const areaList = await getActualUpazilas(well.management_unit_id);
        if (cancelled) return;
        setUpazilas(areaList);
        const area = areaList.find((item) => item.name === well.actual_upazila);
        if (!area) {
          setLocationWarning("Saved Upazila does not match the current master. Select the correct Upazila to continue.");
          return;
        }
        setUpazilaId(String(area.id));

        const unionList = await getUnions(area.id);
        if (cancelled) return;
        setUnions(unionList);
        const selectedUnion = unionList.find((item) => item.name === well.union_name);
        if (!selectedUnion) {
          setLocationWarning("Saved Union does not match the current master. Select the correct Union to continue.");
          return;
        }
        setUnionId(String(selectedUnion.id));

        const mouzaList = await getMouzas(selectedUnion.id);
        if (cancelled) return;
        setMouzas(mouzaList);
        const selectedMouza = mouzaList.find((item) => item.name === well.mouza);
        if (!selectedMouza) {
          setLocationWarning("Saved Mouza does not match the current master. Select the correct Mouza to continue.");
          return;
        }
        setMouzaId(String(selectedMouza.id));

        const masterNumbers = await getDtwMaster(selectedMouza.id);
        if (cancelled) return;
        const usedByOthers = new Set(
          registered.filter((item) => item.id !== id).map((item) => item.tubewell_number)
        );
        const availableNumbers = masterNumbers.filter((item) => !usedByOthers.has(item.dtw_number));
        setDtwNumbers(availableNumbers);
        if (availableNumbers.some((item) => item.dtw_number === well.tubewell_number)) {
          setDtwNumber(well.tubewell_number);
        } else {
          setLocationWarning("Saved DTW Number does not match an available number under this Mouza. Select the correct DTW Number.");
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load tubewell.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadExistingTubewell();
    return () => { cancelled = true; };
  }, [id]);

  // ==========================================================
  // SECTION 4: CASCADING LOCATION SELECTION
  // Clear all dependent selections when a parent changes.
  // Only the most recent API response is applied.
  // ==========================================================
  async function changeManagementUnit(value: string) {
    const version = ++requestVersion.current;
    setManagementUnitId(value);
    setUpazilaId(""); setUnionId(""); setMouzaId(""); setDtwNumber("");
    setUpazilas([]); setUnions([]); setMouzas([]); setDtwNumbers([]);
    setError(""); setSuccess(""); setLocationWarning("");
    if (!value) return;
    setLoadingNext(true);
    try {
      const result = await getActualUpazilas(Number(value));
      if (version === requestVersion.current) setUpazilas(result);
    } catch (err) {
      if (version === requestVersion.current) setError(err instanceof Error ? err.message : "Unable to load Upazilas.");
    } finally {
      if (version === requestVersion.current) setLoadingNext(false);
    }
  }

  async function changeUpazila(value: string) {
    const version = ++requestVersion.current;
    setUpazilaId(value);
    setUnionId(""); setMouzaId(""); setDtwNumber("");
    setUnions([]); setMouzas([]); setDtwNumbers([]);
    setError(""); setSuccess(""); setLocationWarning("");
    if (!value) return;
    setLoadingNext(true);
    try {
      const result = await getUnions(Number(value));
      if (version === requestVersion.current) setUnions(result);
    } catch (err) {
      if (version === requestVersion.current) setError(err instanceof Error ? err.message : "Unable to load Unions.");
    } finally {
      if (version === requestVersion.current) setLoadingNext(false);
    }
  }

  async function changeUnion(value: string) {
    const version = ++requestVersion.current;
    setUnionId(value);
    setMouzaId(""); setDtwNumber("");
    setMouzas([]); setDtwNumbers([]);
    setError(""); setSuccess(""); setLocationWarning("");
    if (!value) return;
    setLoadingNext(true);
    try {
      const result = await getMouzas(Number(value));
      if (version === requestVersion.current) setMouzas(result);
    } catch (err) {
      if (version === requestVersion.current) setError(err instanceof Error ? err.message : "Unable to load Mouzas.");
    } finally {
      if (version === requestVersion.current) setLoadingNext(false);
    }
  }

  async function changeMouza(value: string) {
    const version = ++requestVersion.current;
    setMouzaId(value);
    setDtwNumber(""); setDtwNumbers([]);
    setError(""); setSuccess(""); setLocationWarning("");
    if (!value) return;
    setLoadingNext(true);
    try {
      if (registeredTubewells === null) {
        throw new Error("Unable to verify registered DTW Numbers. Reload this page before editing.");
      }
      const result = await getDtwMaster(Number(value));
      const usedByOthers = new Set(
        registeredTubewells.filter((item) => item.id !== id).map((item) => item.tubewell_number)
      );
      if (version === requestVersion.current) {
        setDtwNumbers(result.filter((item) => !usedByOthers.has(item.dtw_number)));
      }
    } catch (err) {
      if (version === requestVersion.current) setError(err instanceof Error ? err.message : "Unable to load DTW Numbers.");
    } finally {
      if (version === requestVersion.current) setLoadingNext(false);
    }
  }

  // ==========================================================
  // SECTION 5: SAVE CHANGES
  // The backend enforces master-location and duplicate checks.
  // ==========================================================
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(""); setSuccess(""); setLocationWarning("");

    const area = upazilas.find((item) => item.id === Number(upazilaId));
    const selectedUnion = unions.find((item) => item.id === Number(unionId));
    const selectedMouza = mouzas.find((item) => item.id === Number(mouzaId));
    const selectedNumber = dtwNumbers.find(
      (item) => item.dtw_number === dtwNumber && item.mouza_id === Number(mouzaId)
    );

    if (registeredTubewells === null || !managementUnitId || !area || !selectedUnion || !selectedMouza || !selectedNumber) {
      setError("Please select a valid Management Unit, Upazila, Union, Mouza and DTW Number.");
      return;
    }

    if (registeredTubewells.some((item) => item.id !== id && item.tubewell_number === dtwNumber)) {
      setError("This DTW Number is already registered to another tubewell.");
      return;
    }

    try {
      setSaving(true);
      await updateTubewell(id, {
        tubewell_number: selectedNumber.dtw_number,
        // Preserve the existing backend's required legacy name field.
        name: selectedNumber.dtw_number,
        management_unit_id: Number(managementUnitId),
        actual_upazila: area.name,
        union_name: selectedUnion.name,
        mouza: selectedMouza.name,
      });
      setSuccess("Tubewell updated successfully.");
      setLocationWarning("");
      setExistingTubewell((previous) => previous ? {
        ...previous,
        tubewell_number: selectedNumber.dtw_number,
        name: selectedNumber.dtw_number,
        management_unit_id: Number(managementUnitId),
        actual_upazila: area.name,
        union_name: selectedUnion.name,
        mouza: selectedMouza.name,
      } : previous);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update tubewell.");
    } finally {
      setSaving(false);
    }
  }

  // ==========================================================
  // SECTION 6: EDIT FORM
  // No delete functionality is available on this page.
  // ==========================================================
  if (loading) {
    return <div className="bmda-edit-tubewell"><p className="etw-loading">Loading tubewell details...</p></div>;
  }

  return (
    <main className="bmda-edit-tubewell">
      {/* SECTION 7: PAGE HEADER */}
      <header className="etw-header">
        <div>
          <p className="etw-eyebrow">BMDA / Tubewells Management</p>
          <h1 className="etw-title">Edit Tubewell</h1>
          <p className="etw-subtitle">Update an existing tubewell's registered location and DTW number.</p>
        </div>
        <button className="etw-button etw-button-outline" type="button" onClick={() => navigate("/admin/tubewells")}>
          Back to Tubewells
        </button>
      </header>

      {/* SECTION 8: FEEDBACK MESSAGES */}
      {error && <div className="etw-alert etw-alert-error" role="alert">{error}</div>}
      {success && <div className="etw-alert etw-alert-success" role="status">{success}</div>}
      {locationWarning && <div className="etw-alert etw-alert-error" role="status">{locationWarning}</div>}
      {existingTubewell && (
        <section className="etw-card" aria-label="Previously registered information">
          <p><strong>Previously registered:</strong> {existingTubewell.actual_upazila} / {existingTubewell.union_name} / {existingTubewell.mouza} / {existingTubewell.tubewell_number}</p>
        </section>
      )}

      {/* SECTION 9: EDIT FORM - THE EXISTING FIELD HANDLERS ARE UNCHANGED */}
      {managementUnits.length > 0 && (
        <section className="etw-card" aria-labelledby="etw-form-title">
          <div className="etw-card-heading">
            <h2 id="etw-form-title">Tubewell Information</h2>
            <p>Select the location in order, then save your changes.</p>
          </div>

          <form onSubmit={(event) => void handleSubmit(event)}>
            <div className="etw-grid">
              <div className="etw-field">
                <label htmlFor="managementUnit"><span className="etw-step">1</span> Management Unit</label>
                <select id="managementUnit" value={managementUnitId} disabled={saving || loadingNext}
                  onChange={(event) => void changeManagementUnit(event.target.value)} required>
                  <option value="">Select Management Unit</option>
                  {managementUnits.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </div>

              <div className="etw-field">
                <label htmlFor="upazila"><span className="etw-step">2</span> Upazila</label>
                <select id="upazila" value={upazilaId} disabled={!managementUnitId || saving || loadingNext}
                  onChange={(event) => void changeUpazila(event.target.value)} required>
                  <option value="">Select Upazila</option>
                  {upazilas.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </div>

              <div className="etw-field">
                <label htmlFor="union"><span className="etw-step">3</span> Union</label>
                <select id="union" value={unionId} disabled={!upazilaId || saving || loadingNext}
                  onChange={(event) => void changeUnion(event.target.value)} required>
                  <option value="">Select Union</option>
                  {unions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </div>

              <div className="etw-field">
                <label htmlFor="mouza"><span className="etw-step">4</span> Mouza</label>
                <select id="mouza" value={mouzaId} disabled={!unionId || saving || loadingNext}
                  onChange={(event) => void changeMouza(event.target.value)} required>
                  <option value="">Select Mouza</option>
                  {mouzas.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </div>

              <div className="etw-field etw-field-full">
                <label htmlFor="dtwNumber"><span className="etw-step">5</span> DTW Number</label>
                <select id="dtwNumber" value={dtwNumber} disabled={!mouzaId || saving || loadingNext}
                  onChange={(event) => { setDtwNumber(event.target.value); setSuccess(""); }} required>
                  <option value="">{loadingNext ? "Loading..." : "Select DTW Number"}</option>
                  {dtwNumbers.map((item) => <option key={item.id} value={item.dtw_number}>{item.dtw_number}</option>)}
                </select>
                {mouzaId && !loadingNext && dtwNumbers.length === 0 && (
                  <p className="etw-help">No DTW Numbers found for this Mouza.</p>
                )}
              </div>
            </div>

            {/* SECTION 10: SAVE ACTIONS */}
            <div className="etw-actions">
              <button type="submit" className="etw-button etw-button-primary"
                disabled={saving || loadingNext || !dtwNumber || registeredTubewells === null}>
                {saving ? "Saving..." : "Save Changes"}
              </button>
              <button className="etw-button etw-button-outline" type="button"
                onClick={() => navigate("/admin/tubewells")}>
                Cancel
              </button>
            </div>
          </form>
        </section>
      )}
    </main>
  );
}

export default EditTubewellPage;
