import { useEffect, useMemo, useState } from "react";
import {
  getSAEReadingActivity,
  type SAEReadingActivityResponse,
  type SAEReadingStatus,
  type SAEReadingTubewellActivity,
  type SAEReadingTypeActivity,
} from "../../api/saeReadingActivity.api";
import "./SAEReadingActivityMonitoring.css";

type MeterFilter = "all" | "energy" | "prepaid";
type StatusFilter = "all" | SAEReadingStatus;

const statusLabels: Record<SAEReadingStatus, string> = {
  not_available: "Not available",
  not_started: "Not started",
  up_to_date: "Up to date",
  overdue: "Overdue",
};

function isStatus(value: unknown): value is SAEReadingStatus {
  return value === "not_available" || value === "not_started" || value === "up_to_date" || value === "overdue";
}

function validateResponse(value: SAEReadingActivityResponse): void {
  if (!value || !Array.isArray(value.tubewells) || !Number.isInteger(value.total_assigned_tubewells)) {
    throw new Error("Unexpected Reading Activity response.");
  }
  if (!value.tubewells.every((well) => well && isStatus(well.energy?.status) && isStatus(well.prepaid?.status))) {
    throw new Error("Reading status data could not be verified.");
  }
}

function readableDate(raw: string | null): string {
  if (!raw) return "No reading recorded";
  // ISO yyyy-mm-dd from FastAPI. Format as a local *calendar* date without timezone shifts.
  const date = /^\d{4}-\d{2}-\d{2}$/.test(raw) ? new Date(`${raw}T12:00:00`) : new Date(raw);
  return Number.isNaN(date.getTime()) ? "Date unavailable" : date.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function ReadingPanel({ title, activity }: { title: "Energy" | "Prepaid"; activity: SAEReadingTypeActivity }) {
  const note = activity.note?.trim();
  return (
    <div className="bmda-sae-reading-meter">
      <div className="bmda-sae-reading-meter-title">
        <span className="bmda-sae-reading-meter-name"><span aria-hidden="true">{title === "Energy" ? "⚡" : "▣"}</span> {title}</span>
        <span className={`bmda-sae-reading-status is-${activity.status}`}>{statusLabels[activity.status]}</span>
      </div>
      <dl className="bmda-sae-reading-meta">
        <div><dt>Latest reading</dt><dd>{readableDate(activity.latest_reading_date)}</dd></div>
        <div><dt>Days since</dt><dd>{activity.days_since_last_reading === null ? "—" : `${activity.days_since_last_reading} days`}</dd></div>
        <div><dt>Collected by</dt><dd>{activity.collected_by_field_visitor ?? "Not recorded for this team"}</dd></div>
      </dl>
      {note && <p className="bmda-sae-reading-note">{note}</p>}
    </div>
  );
}

/** Read-only SAE field-team reading monitor; does not add meters or submit readings. */
export default function SAEReadingActivityMonitoring() {
  const [data, setData] = useState<SAEReadingActivityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [meter, setMeter] = useState<MeterFilter>("all");
  const [visitor, setVisitor] = useState("all");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const result = await getSAEReadingActivity();
        validateResponse(result);
        if (!cancelled) setData(result);
      } catch (caught) {
        if (!cancelled) {
          setData(null);
          setError(caught instanceof Error ? caught.message : "Unable to load reading activity.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [refreshKey]);

  const visitors = useMemo(() => {
    const people = new Map<number, string>();
    for (const well of data?.tubewells ?? []) people.set(well.field_user_id, well.field_user_name);
    return [...people.entries()].sort((a, b) => a[1].localeCompare(b[1]) || a[0] - b[0]);
  }, [data]);

  const visible = useMemo(() => {
    const q = search.trim().toLocaleLowerCase();
    return (data?.tubewells ?? []).filter((well) => {
      if (visitor !== "all" && String(well.field_user_id) !== visitor) return false;
      if (q && ![well.tubewell_number, well.tubewell_name, well.field_user_name, String(well.field_user_id)]
        .some((value) => String(value ?? "").toLocaleLowerCase().includes(q))) return false;
      if (status === "all") return true;
      if (meter === "energy") return well.energy.status === status;
      if (meter === "prepaid") return well.prepaid.status === status;
      return well.energy.status === status || well.prepaid.status === status;
    });
  }, [data, search, visitor, meter, status]);

  const notStartedCount = (data?.tubewells ?? []).filter((well) =>
    well.energy.status === "not_started" || well.prepaid.status === "not_started").length;

  const summary = [
    { label: "Assigned tubewells", value: data?.total_assigned_tubewells ?? "—", tone: "default" },
    { label: "Overdue tubewells", value: data?.overdue_tubewells ?? "—", tone: "warn" },
    { label: "Energy overdue", value: data?.energy_overdue ?? "—", tone: "energy" },
    { label: "Prepaid overdue", value: data?.prepaid_overdue ?? "—", tone: "prepaid" },
  ];

  function wellCard(well: SAEReadingTubewellActivity) {
    return (
      <article className="bmda-sae-reading-well" key={well.tubewell_id}>
        <div className="bmda-sae-reading-well-header">
          <div className="bmda-sae-reading-well-info">
            <span className="bmda-sae-reading-well-number">{well.tubewell_number}</span>
            <h3>{well.tubewell_name || "Unnamed tubewell"}</h3>
            <p>Field Visitor: <strong>{well.field_user_name}</strong> <span>(ID {well.field_user_id})</span></p>
          </div>
          <span className={`bmda-sae-reading-well-active ${well.tubewell_is_active ? "is-active" : "is-inactive"}`}>
            {well.tubewell_is_active ? "Active" : "Inactive"}
          </span>
        </div>
        <div className="bmda-sae-reading-meters">
          {(meter === "all" || meter === "energy") && <ReadingPanel title="Energy" activity={well.energy} />}
          {(meter === "all" || meter === "prepaid") && <ReadingPanel title="Prepaid" activity={well.prepaid} />}
        </div>
      </article>
    );
  }

  return (
    <section className="bmda-sae-reading" aria-labelledby="bmda-sae-reading-title">
      <header className="bmda-sae-reading-header">
        <div>
          <span className="bmda-sae-reading-eyebrow">FIELD OPERATIONS / READ-ONLY</span>
          <h2 id="bmda-sae-reading-title">Reading Activity Monitor</h2>
          <p>Monitor Energy and Prepaid readings for tubewells assigned to your field team.</p>
        </div>
        <button type="button" className="bmda-sae-reading-refresh" onClick={() => setRefreshKey((n) => n + 1)} disabled={loading}>
          {loading ? "Refreshing…" : "↻ Refresh readings"}
        </button>
      </header>

      <div className="bmda-sae-reading-summary" aria-label="Reading summary">
        {summary.map((item) => (
          <div className={`bmda-sae-reading-stat is-${item.tone}`} key={item.label}>
            <span>{item.label}</span><strong>{!data && loading ? "…" : item.value}</strong>
          </div>
        ))}
      </div>

      {data && <div className="bmda-sae-reading-context" role="note">
        <span>30-day policy: <strong>{data.warning_threshold_days} days</strong></span>
        <span>Not started (tubewells): <strong>{notStartedCount}</strong></span>
        <span>Unit ID: <strong>{data.management_unit_id}</strong></span>
      </div>}

      <div className="bmda-sae-reading-filters">
        <label>Search tubewell or Field Visitor
          <input type="search" placeholder="Search TT-04, name, visitor..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </label>
        <label>Meter type
          <select value={meter} onChange={(e) => setMeter(e.target.value as MeterFilter)}>
            <option value="all">Energy + Prepaid</option><option value="energy">Energy only</option><option value="prepaid">Prepaid only</option>
          </select>
        </label>
        <label>Reading status
          <select value={status} onChange={(e) => setStatus(e.target.value as StatusFilter)}>
            <option value="all">All statuses</option>
            <option value="overdue">Overdue</option><option value="up_to_date">Up to date</option>
            <option value="not_started">Not started</option><option value="not_available">Not available</option>
          </select>
        </label>
        <label>Field Visitor
          <select value={visitor} onChange={(e) => setVisitor(e.target.value)}>
            <option value="all">All assigned visitors</option>
            {visitors.map(([id, name]) => <option key={id} value={String(id)}>{name} (#{id})</option>)}
          </select>
        </label>
      </div>

      {loading && <div className="bmda-sae-reading-message" role="status">Loading authorized reading activity…</div>}
      {!loading && error && <div className="bmda-sae-reading-error" role="alert">{error} <button type="button" onClick={() => setRefreshKey((n) => n + 1)}>Try again</button></div>}
      {!loading && !error && data && <>
        <div className="bmda-sae-reading-result-count" role="status">Showing {visible.length} of {data.total_assigned_tubewells} assigned tubewells</div>
        {data.tubewells.length === 0 ? (
          <div className="bmda-sae-reading-empty"><strong>No current tubewell assignments</strong><p>Reading activity will appear once a Field Visitor has a current tubewell assignment.</p></div>
        ) : visible.length === 0 ? (
          <div className="bmda-sae-reading-empty"><strong>No matching results</strong><p>Try another search, meter type, status or visitor.</p></div>
        ) : <div className="bmda-sae-reading-list">{visible.map(wellCard)}</div>}
      </>}
      <p className="bmda-sae-reading-footer">Statuses use registered current meters and applicable reading history only. Unregistered meters are “Not available,” not overdue. No readings, meters or requests are modified from this screen.</p>
    </section>
  );
}
