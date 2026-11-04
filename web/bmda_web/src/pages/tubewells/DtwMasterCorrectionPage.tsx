import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { apiRequest } from "../../api/client";
import { correctDtwMaster, type DtwMasterItem } from "../../api/dtwMaster.api";
import { getManagementUnits, type ManagementUnit } from "../../api/users.api";
import { getActualUpazilas, type ActualUpazila } from "../../api/actualUpazilas.api";
import { getUnions, type UnionItem } from "../../api/unions.api";
import { getMouzas, type MouzaItem } from "../../api/mouzas.api";
import "./EditTubewellPage.css";

// Requires backend GET /dtw-master/search?dtw_number=...
// Response must include master fields plus registered and current_location.
type SearchResult = DtwMasterItem & { registered: boolean; current_location: string };

export default function DtwMasterCorrectionPage() {
  const [number, setNumber] = useState("");
  const [record, setRecord] = useState<SearchResult | null>(null);
  const [units, setUnits] = useState<ManagementUnit[]>([]);
  const [areas, setAreas] = useState<ActualUpazila[]>([]);
  const [unions, setUnions] = useState<UnionItem[]>([]);
  const [mouzas, setMouzas] = useState<MouzaItem[]>([]);
  const [unitId, setUnitId] = useState("");
  const [areaId, setAreaId] = useState("");
  const [unionId, setUnionId] = useState("");
  const [mouzaId, setMouzaId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let active = true;
    getManagementUnits().then(data => { if (active) setUnits(data); })
      .catch((err: unknown) => { if (active) setError(err instanceof Error ? err.message : "Failed to load units"); });
    return () => { active = false; };
  }, []);

  const clearSelection = () => {
    setUnitId(""); setAreaId(""); setUnionId(""); setMouzaId("");
    setAreas([]); setUnions([]); setMouzas([]);
  };
  const fail = (err: unknown) => setError(err instanceof Error ? err.message : "Request failed");

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setSuccess(""); setRecord(null); clearSelection();
    if (!number.trim()) return;
    setBusy(true);
    try {
      const data = await apiRequest(`/dtw-master/search?dtw_number=${encodeURIComponent(number.trim())}`, { method: "GET" }) as SearchResult;
      if (!data || !Number.isInteger(data.id) || !Number.isInteger(data.mouza_id) ||
          typeof data.registered !== "boolean" || typeof data.current_location !== "string") {
        throw new Error("Unexpected search response");
      }
      setRecord(data);
    } catch (err) { fail(err); } finally { setBusy(false); }
  }

  async function changeUnit(value: string) {
    clearSelection(); setUnitId(value); setError(""); setSuccess("");
    if (!value) return;
    setBusy(true);
    try { setAreas(await getActualUpazilas(Number(value))); }
    catch (err) { fail(err); } finally { setBusy(false); }
  }
  async function changeArea(value: string) {
    setAreaId(value); setUnionId(""); setMouzaId(""); setUnions([]); setMouzas([]); setError("");
    if (!value) return;
    setBusy(true);
    try { setUnions(await getUnions(Number(value))); }
    catch (err) { fail(err); } finally { setBusy(false); }
  }
  async function changeUnion(value: string) {
    setUnionId(value); setMouzaId(""); setMouzas([]); setError("");
    if (!value) return;
    setBusy(true);
    try { setMouzas(await getMouzas(Number(value))); }
    catch (err) { fail(err); } finally { setBusy(false); }
  }

  const unit = units.find(x => x.id === Number(unitId));
  const area = areas.find(x => x.id === Number(areaId));
  const union = unions.find(x => x.id === Number(unionId));
  const mouza = mouzas.find(x => x.id === Number(mouzaId));
  const same = record?.mouza_id === mouza?.id;

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!record || !unit || !area || !union || !mouza || busy || same) return;
    if (!window.confirm(`Correct ${record.dtw_number}?\nFROM: ${record.current_location}\nTO: ${unit.name} / ${area.name} / ${union.name} / ${mouza.name}`)) return;
    setBusy(true); setError(""); setSuccess("");
    try {
      await correctDtwMaster(record.id, { mouza_id: mouza.id, management_unit_id: unit.id });
      setRecord(null); clearSelection();
      setSuccess("Correction saved. Search again to verify the updated location.");
    } catch (err) { fail(err); } finally { setBusy(false); }
  }

  return <main className="bmda-edit-tubewell">
    <header className="etw-header"><div>
      <p className="etw-eyebrow">BMDA / Admin / DTW Master</p>
      <h1 className="etw-title">DTW Master Correction</h1>
      <p className="etw-subtitle">Correct location without changing the DTW number or record ID.</p>
    </div></header>
    {error && <div className="etw-alert etw-alert-error" role="alert">{error}</div>}
    {success && <div className="etw-alert etw-alert-success" role="status">{success}</div>}
    <section className="etw-card"><h2>Search DTW Number</h2>
      <form onSubmit={event => void search(event)}>
        <div className="etw-field"><label htmlFor="dtw-search">Exact DTW Number</label>
          <input id="dtw-search" value={number} onChange={event => setNumber(event.target.value)}
            placeholder="e.g. OLD-66" disabled={busy} required /></div>
        <div className="etw-actions"><button type="submit" className="etw-button etw-button-primary" disabled={busy}>
          {busy ? "Loading..." : "Search"}</button></div>
      </form>
    </section>
    {record && <>
      <section className="etw-card"><h2>Current Information</h2>
        <p><strong>DTW Number:</strong> {record.dtw_number}</p>
        <p><strong>Master ID:</strong> {record.id}</p>
        <p><strong>Current Location:</strong> {record.current_location}</p>
        <p><strong>Status:</strong> {record.registered ? "Registered" : "Not registered"}</p>
      </section>
      <section className="etw-card"><h2>New Location</h2>
        <form onSubmit={event => void save(event)}><div className="etw-grid">
          <div className="etw-field"><label htmlFor="dtw-unit">Management Unit</label>
            <select id="dtw-unit" value={unitId} onChange={event => void changeUnit(event.target.value)} disabled={busy} required>
              <option value="">Select Management Unit</option>{units.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}
            </select></div>
          <div className="etw-field"><label htmlFor="dtw-area">Upazila</label>
            <select id="dtw-area" value={areaId} onChange={event => void changeArea(event.target.value)} disabled={!unitId || busy} required>
              <option value="">Select Upazila</option>{areas.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}
            </select></div>
          <div className="etw-field"><label htmlFor="dtw-union">Union</label>
            <select id="dtw-union" value={unionId} onChange={event => void changeUnion(event.target.value)} disabled={!areaId || busy} required>
              <option value="">Select Union</option>{unions.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}
            </select></div>
          <div className="etw-field"><label htmlFor="dtw-mouza">Mouza</label>
            <select id="dtw-mouza" value={mouzaId} onChange={event => { setMouzaId(event.target.value); setError(""); }} disabled={!unionId || busy} required>
              <option value="">Select Mouza</option>{mouzas.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}
            </select></div>
        </div>
        {mouza && <p className="etw-help"><strong>Preview:</strong> {record.current_location} → {unit?.name} / {area?.name} / {union?.name} / {mouza.name}</p>}
        {same && <p className="etw-help">This Mouza is already assigned in the master.</p>}
        <div className="etw-actions"><button type="submit" className="etw-button etw-button-primary"
          disabled={busy || !unit || !area || !union || !mouza || same}>{busy ? "Saving..." : "Save Correction"}</button></div>
        </form>
      </section>
    </>}
  </main>;
}
