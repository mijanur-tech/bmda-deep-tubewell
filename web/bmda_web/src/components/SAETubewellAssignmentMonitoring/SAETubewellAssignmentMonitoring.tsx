import { useEffect, useMemo, useState } from "react";
import {
  getSAETubewellAssignments,
  type SAETubewellAssignmentItem,
  type SAETubewellAssignmentsResponse,
} from "../../api/saeTubewellAssignments.api";
import "./SAETubewellAssignmentMonitoring.css";

type StatusFilter = "all" | "active" | "inactive";

type VisitorGroup = {
  id: number;
  name: string;
  isActive: boolean;
  assignments: SAETubewellAssignmentItem[];
};

/** Read-only, server-scoped SAE assignment monitoring. */
export default function SAETubewellAssignmentMonitoring() {
  const [data, setData] = useState<SAETubewellAssignmentsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [visitor, setVisitor] = useState("all");
  const [expanded, setExpanded] = useState<number[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const response = await getSAETubewellAssignments();
        if (!Array.isArray(response.assignments) || typeof response.total_assignments !== "number") {
          throw new Error("Unexpected assignment response.");
        }
        if (!cancelled) {
          setData(response);
          setExpanded([]);
        }
      } catch (caught) {
        if (!cancelled) {
          setData(null);
          setError(caught instanceof Error ? caught.message : "Unable to load assignments.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [revision]);

  const visitors = useMemo(() => {
    const groups = new Map<number, VisitorGroup>();
    for (const assignment of data?.assignments ?? []) {
      let group = groups.get(assignment.field_user_id);
      if (!group) {
        group = {
          id: assignment.field_user_id,
          name: assignment.field_user_name,
          isActive: assignment.field_user_is_active,
          assignments: [],
        };
        groups.set(group.id, group);
      }
      group.assignments.push(assignment);
    }
    return Array.from(groups.values()).sort((a, b) => a.name.localeCompare(b.name) || a.id - b.id);
  }, [data]);

  const matches = useMemo(() => {
    const q = search.trim().toLocaleLowerCase();
    return visitors.map((group) => ({
      ...group,
      assignments: group.assignments.filter((item) => {
        if (status === "active" && !item.tubewell_is_active) return false;
        if (status === "inactive" && item.tubewell_is_active) return false;
        if (visitor !== "all" && String(item.field_user_id) !== visitor) return false;
        if (!q) return true;
        return [
          item.field_user_name, String(item.field_user_id), item.tubewell_number,
          item.tubewell_name, item.actual_upazila, item.union_name, item.mouza,
        ].some((value) => String(value ?? "").toLocaleLowerCase().includes(q));
      }),
    })).filter((group) => group.assignments.length > 0);
  }, [visitors, status, visitor, search]);

  const visibleCount = matches.reduce((sum, group) => sum + group.assignments.length, 0);
  const activeCount = (data?.assignments ?? []).filter((item) => item.tubewell_is_active).length;
  const inactiveCount = (data?.assignments ?? []).filter((item) => !item.tubewell_is_active).length;

  function toggle(id: number) {
    setExpanded((previous) => previous.includes(id) ? previous.filter((value) => value !== id) : [...previous, id]);
  }

  return (
    <section className="bmda-sae-assign" aria-labelledby="bmda-sae-assign-title">
      <div className="bmda-sae-assign-heading">
        <div>
          <span className="bmda-sae-assign-eyebrow">FIELD OPERATIONS / OWN TEAM</span>
          <h2 id="bmda-sae-assign-title">Field Visitor-wise Tubewell Assignments</h2>
          <p>Current tubewell responsibilities for Field Visitors in your authorized team.</p>
        </div>
        <button type="button" onClick={() => setRevision((value) => value + 1)} disabled={loading} className="bmda-sae-assign-refresh">
          {loading ? "Loading..." : "Refresh assignments"}
        </button>
      </div>

      {loading && <p role="status" className="bmda-sae-assign-message">Loading current assignments...</p>}
      {error && <p role="alert" className="bmda-sae-assign-error">{error}</p>}

      {!loading && !error && data && (
        <>
          <div className="bmda-sae-assign-stats" aria-label="Current assignment summary">
            <div><span>Current assignments</span><strong>{data.total_assignments}</strong></div>
            <div><span>Active tubewells</span><strong>{activeCount}</strong></div>
            <div><span>Inactive tubewells</span><strong>{inactiveCount}</strong></div>
            <div><span>Visitors with assignments</span><strong>{visitors.length}</strong></div>
          </div>

          <div className="bmda-sae-assign-controls">
            <label><span>Search assignments</span><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Number, name, visitor, location" /></label>
            <label><span>Field Visitor</span><select value={visitor} onChange={(event) => setVisitor(event.target.value)}>
              <option value="all">All assigned visitors</option>
              {visitors.map((item) => <option value={String(item.id)} key={item.id}>{item.name} (ID {item.id})</option>)}
            </select></label>
            <label><span>Tubewell status</span><select value={status} onChange={(event) => setStatus(event.target.value as StatusFilter)}>
              <option value="all">All statuses</option><option value="active">Active only</option><option value="inactive">Inactive only</option>
            </select></label>
          </div>

          <p className="bmda-sae-assign-count" aria-live="polite">Showing <strong>{visibleCount}</strong> of {data.total_assignments} current assignments · {matches.length} Field Visitors</p>

          <div className="bmda-sae-assign-groups">
            {matches.map((group) => {
              const isExpanded = expanded.includes(group.id);
              return (
                <article className="bmda-sae-assign-group" key={group.id}>
                  <button type="button" className="bmda-sae-assign-group-button" onClick={() => toggle(group.id)} aria-expanded={isExpanded} aria-controls={`bmda-sae-assign-person-${group.id}`}>
                    <span className="bmda-sae-assign-avatar" aria-hidden="true">{group.name.trim().charAt(0).toUpperCase() || "F"}</span>
                    <span className="bmda-sae-assign-person"><strong>{group.name}</strong><small>Field Visitor · ID {group.id} · {group.isActive ? "Active" : "Inactive"} account</small></span>
                    <span className="bmda-sae-assign-pill">{group.assignments.length} tubewell{group.assignments.length === 1 ? "" : "s"}</span>
                    <span className="bmda-sae-assign-caret" aria-hidden="true">{isExpanded ? "−" : "+"}</span>
                  </button>
                  {isExpanded && (
                    <div id={`bmda-sae-assign-person-${group.id}`} className="bmda-sae-assign-records">
                      {group.assignments.map((item) => (
                        <div key={item.assignment_id} className="bmda-sae-assign-record">
                          <div className="bmda-sae-assign-record-top"><strong>{item.tubewell_number || `Tubewell #${item.tubewell_id}`}</strong><span className={item.tubewell_is_active ? "is-active" : "is-inactive"}>{item.tubewell_is_active ? "Active" : "Inactive"}</span></div>
                          <div className="bmda-sae-assign-record-name">{item.tubewell_name || "Name unavailable"}</div>
                          <div className="bmda-sae-assign-record-meta">{[item.actual_upazila, item.union_name, item.mouza].filter(Boolean).join(" · ") || "Location unavailable"}</div>
                          <div className="bmda-sae-assign-record-date">Assigned: {item.assigned_at || "Date not recorded"} · Assignment #{item.assignment_id}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </article>
              );
            })}
          </div>
          {matches.length === 0 && <p className="bmda-sae-assign-empty">{data.total_assignments === 0 ? "No current tubewell assignments for your team." : "No assignments match the selected filters."}</p>}
          <p className="bmda-sae-assign-footnote">Read-only monitoring. Historical assignments are not included; inactive tubewells remain visible while their current assignment exists.</p>
        </>
      )}
    </section>
  );
}
