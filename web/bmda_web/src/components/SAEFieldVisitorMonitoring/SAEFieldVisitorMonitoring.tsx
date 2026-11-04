import { useEffect, useMemo, useState } from "react";
import {
  getSAEFieldVisitorSummary,
  type SAEFieldVisitorSummaryResponse,
} from "../../api/saeFieldVisitorSummary.api";
import "./SAEFieldVisitorMonitoring.css";

/** Read-only monitoring panel. Server owns all SAE scope checks. */
export default function SAEFieldVisitorMonitoring() {
  const [summary, setSummary] = useState<SAEFieldVisitorSummaryResponse | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"all" | "active" | "inactive">("all");
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setBusy(true);
      setError("");
      try {
        const result = await getSAEFieldVisitorSummary();
        if (!cancelled) {
          if (!Array.isArray(result.field_visitors)) {
            throw new Error("Unexpected Field Visitor response.");
          }
          setSummary(result);
        }
      } catch (caught) {
        if (!cancelled) {
          setSummary(null);
          setError(caught instanceof Error ? caught.message : "Unable to load Field Visitors.");
        }
      } finally {
        if (!cancelled) setBusy(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [revision]);

  const visitors = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    return (summary?.field_visitors ?? []).filter((visitor) => {
      if (status === "active" && !visitor.is_active) return false;
      if (status === "inactive" && visitor.is_active) return false;
      return !normalized || visitor.full_name.toLocaleLowerCase().includes(normalized)
        || String(visitor.field_user_id).includes(normalized);
    });
  }, [summary, query, status]);

  return (
    <section className="bmda-sae-monitor" aria-labelledby="bmda-sae-monitor-title">
      <div className="bmda-sae-monitor-heading">
        <div>
          <span className="bmda-sae-monitor-kicker">TEAM OPERATIONS</span>
          <h2 id="bmda-sae-monitor-title">Field Visitor Monitoring</h2>
          <p>Current team members and tubewell assignments within your authorized scope.</p>
        </div>
        <button type="button" className="bmda-sae-monitor-refresh"
          onClick={() => setRevision((value) => value + 1)} disabled={busy}>
          {busy ? "Loading..." : "Refresh data"}
        </button>
      </div>

      {error && <p className="bmda-sae-monitor-error" role="alert">{error}</p>}
      {busy && <p className="bmda-sae-monitor-info" role="status">Loading Field Visitor information...</p>}

      {!busy && !error && summary && (
        <>
          <div className="bmda-sae-monitor-stats" aria-label="Field Visitor summary">
            {[
              { label: "Total visitors", value: summary.total_field_visitors, style: "navy" },
              { label: "Active visitors", value: summary.active_field_visitors, style: "emerald" },
              { label: "Assigned tubewells", value: summary.assigned_tubewells, style: "teal" },
              { label: "Without assignments", value: summary.visitors_without_assignments, style: "amber" },
            ].map((card) => (
              <div className={`bmda-sae-monitor-stat bmda-sae-monitor-stat--${card.style}`} key={card.label}>
                <span>{card.label}</span><strong>{card.value}</strong>
              </div>
            ))}
          </div>

          <div className="bmda-sae-monitor-toolbar">
            <label className="bmda-sae-monitor-search">
              <span>Search visitors</span>
              <input type="search" placeholder="Name or visitor ID" value={query}
                onChange={(event) => setQuery(event.target.value)} />
            </label>
            <label className="bmda-sae-monitor-filter">
              <span>Status</span>
              <select value={status} onChange={(event) => setStatus(event.target.value as typeof status)}>
                <option value="all">All visitors</option>
                <option value="active">Active only</option>
                <option value="inactive">Inactive only</option>
              </select>
            </label>
          </div>

          <div className="bmda-sae-monitor-results" aria-live="polite">
            Showing {visitors.length} of {summary.total_field_visitors} Field Visitors
            <span>{summary.inactive_field_visitors} inactive</span>
          </div>
          <div className="bmda-sae-monitor-grid">
            {visitors.map((visitor) => (
              <article className="bmda-sae-monitor-person" key={visitor.field_user_id}>
                <div className="bmda-sae-monitor-person-top">
                  <div className="bmda-sae-monitor-avatar" aria-hidden="true">
                    {visitor.full_name.trim().slice(0, 1).toUpperCase() || "F"}
                  </div>
                  <span className={`bmda-sae-monitor-status ${visitor.is_active ? "is-active" : "is-inactive"}`}>
                    {visitor.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
                <h3>{visitor.full_name}</h3>
                <p>Field Visitor · ID {visitor.field_user_id}</p>
                <div className="bmda-sae-monitor-assigned">
                  <span>Current tubewell assignments</span>
                  <strong>{visitor.assigned_tubewells}</strong>
                </div>
              </article>
            ))}
          </div>
          {visitors.length === 0 && (
            <p className="bmda-sae-monitor-empty">
              {summary.total_field_visitors === 0
                ? "No Field Visitors are currently assigned to your team."
                : "No Field Visitors match your search or filter."}
            </p>
          )}
        </>
      )}
    </section>
  );
}
