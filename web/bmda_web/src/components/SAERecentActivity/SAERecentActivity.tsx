import { useMemo } from "react";
import type { SAEReadingActivityResponse, SAEReadingStatus } from "../../api/saeReadingActivity.api";
import "./SAERecentActivity.css";

type ActivityItem = {
  key: string;
  tubewellNumber: string;
  tubewellName: string;
  fieldVisitor: string;
  collector: string | null;
  readingType: "Energy" | "Prepaid";
  readingDate: string;
  status: SAEReadingStatus;
  daysSince: number | null;
};

const STATUS_LABEL: Record<SAEReadingStatus, string> = {
  overdue: "Overdue",
  up_to_date: "Up to date",
  not_started: "Not started",
  not_available: "Not available",
};

/**
 * Shows the most recent reading per tubewell and reading type, not a full
 * event history. Never invents submissions or activity timestamps.
 */
export default function SAERecentActivity({
  data,
  loading,
  error,
  onViewAll,
}: {
  data: SAEReadingActivityResponse | null;
  loading: boolean;
  error: string;
  onViewAll: () => void;
}) {
  const recent = useMemo(() => {
    const items: ActivityItem[] = [];
    for (const tubewell of data?.tubewells ?? []) {
      for (const readingType of ["energy", "prepaid"] as const) {
        const reading = tubewell[readingType];
        // A missing date is not a completed reading, even if a status is present.
        if (!reading.latest_reading_date ||
            !/^\d{4}-\d{2}-\d{2}$/.test(reading.latest_reading_date)) continue;
        items.push({
          key: `${tubewell.tubewell_id}-${readingType}`,
          tubewellNumber: tubewell.tubewell_number,
          tubewellName: tubewell.tubewell_name,
          fieldVisitor: tubewell.field_user_name,
          collector: reading.collected_by_field_visitor,
          readingType: readingType === "energy" ? "Energy" : "Prepaid",
          readingDate: reading.latest_reading_date,
          status: reading.status,
          daysSince: reading.days_since_last_reading,
        });
      }
    }
    // ISO date strings sort chronologically; ties have deterministic order.
    items.sort((a, b) => b.readingDate.localeCompare(a.readingDate) ||
      a.tubewellNumber.localeCompare(b.tubewellNumber) ||
      a.readingType.localeCompare(b.readingType));
    return items.slice(0, 8);
  }, [data]);

  return (
    <section className="bmda-sae-recent" aria-label="Latest field reading activity">
      <header className="bmda-sae-recent__header">
        <div>
          <p className="bmda-sae-recent__eyebrow">FIELD OPERATIONS · LATEST READINGS</p>
          <h2>Recent Field Activity</h2>
          <p>Latest Energy and Prepaid readings from your assigned field team.</p>
        </div>
        <button type="button" className="bmda-sae-recent__link" onClick={onViewAll}>
          View reading monitoring <span aria-hidden="true">→</span>
        </button>
      </header>
      {loading ? (
        <div className="bmda-sae-recent__state" role="status">Loading latest readings…</div>
      ) : error || !data ? (
        <div className="bmda-sae-recent__state bmda-sae-recent__state--error" role="alert">
          Recent activity is unavailable. Use Refresh overview to retry.
        </div>
      ) : recent.length === 0 ? (
        <div className="bmda-sae-recent__state">
          <strong>No submitted readings yet</strong>
          <span>Recent readings will appear here when your assigned team submits Energy or Prepaid readings.</span>
        </div>
      ) : (
        <>
          <div className="bmda-sae-recent__list">
            {recent.map((item) => (
              <article className="bmda-sae-recent__item" key={item.key}>
                <span className={`bmda-sae-recent__type ${item.readingType === "Energy" ? "is-energy" : "is-prepaid"}`}>
                  {item.readingType === "Energy" ? "E" : "P"}
                </span>
                <div className="bmda-sae-recent__details">
                  <div className="bmda-sae-recent__mainline">
                    <strong>{item.tubewellNumber || item.tubewellName || "Tubewell"}</strong>
                    <span className="bmda-sae-recent__kind">{item.readingType}</span>
                    <span className={`bmda-sae-recent__status is-${item.status}`}>{STATUS_LABEL[item.status] ?? "Status unavailable"}</span>
                  </div>
                  {item.tubewellName && item.tubewellName !== item.tubewellNumber && (
                    <span className="bmda-sae-recent__name">{item.tubewellName}</span>
                  )}
                  <span className="bmda-sae-recent__meta">
                    Assigned: {item.fieldVisitor || "Unavailable"} · Collected by: {item.collector || "Not recorded"}
                  </span>
                </div>
                <div className="bmda-sae-recent__date">
                  <strong>{item.readingDate}</strong>
                  {item.daysSince !== null && item.daysSince >= 0 && (
                    <span>{item.daysSince === 0 ? "Today" : `${item.daysSince} days ago`}</span>
                  )}
                </div>
              </article>
            ))}
          </div>
          <p className="bmda-sae-recent__footnote">
            Showing up to 8 latest readings by date. Each tubewell contributes at most one Energy and one Prepaid reading; this is not a complete submission history.
          </p>
        </>
      )}
    </section>
  );
}
