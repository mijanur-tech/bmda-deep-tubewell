import { useCallback, useEffect, useState } from "react";
import {
  getSAEPendingRequests,
  reviewSAEReadingCorrection,
  reviewSAEMeterReplacement,
  reviewSAETubewellStatus,
} from "../../api/saePendingRequests.api";
import type {
  SAEPendingRequest,
  SAEReviewAction,
} from "../../api/saePendingRequests.api";
import { getTubewell } from "../../api/tubewells.api";
import type { TubewellItem } from "../../api/tubewells.api";
import "./SAEApprovalWorkspace.css";

interface Props {
  inline?: boolean;
}

type FilterType = "all" | SAEPendingRequest["request_type"];

function requestKey(request: SAEPendingRequest): string {
  return `${request.request_type}-${request.request_id}`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function getRequestLabel(type: SAEPendingRequest["request_type"]): string {
  switch (type) {
    case "reading_correction":
      return "Reading Correction";
    case "meter_replacement":
      return "Meter Replacement";
    case "tubewell_status":
      return "Tubewell Status";
  }
}

export default function SAEApprovalWorkspace({ inline = false }: Props) {
  const [requests, setRequests] = useState<SAEPendingRequest[]>([]);
  const [details, setDetails] = useState<Record<number, TubewellItem>>({});
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [filter, setFilter] = useState<FilterType>("all");
  const [comments, setComments] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<SAEPendingRequest | null>(null);
  const [selectedAction, setSelectedAction] = useState<SAEReviewAction | null>(null);

  const loadRequests = useCallback(async () => {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const data = await getSAEPendingRequests();
      setRequests(data);

      const ids = [...new Set(data.map((item) => item.tubewell_id))];
      const results = await Promise.allSettled(ids.map((id) => getTubewell(id)));
      const nextDetails: Record<number, TubewellItem> = {};

      results.forEach((result, index) => {
        if (result.status === "fulfilled") {
          nextDetails[ids[index]] = result.value;
        }
      });

      setDetails(nextDetails);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load pending requests.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRequests();
  }, [loadRequests]);

  function beginReview(request: SAEPendingRequest, action: SAEReviewAction) {
    if (busyKey !== null) return;

    const comment = (comments[requestKey(request)] ?? "").trim();
    if (action === "rejected" && request.request_type === "reading_correction" && !comment) {
      setError("Rejection reason is required for Reading Correction requests.");
      return;
    }

    setError("");
    setSelected(request);
    setSelectedAction(action);
  }

  async function submitReview(action: SAEReviewAction) {
    if (!selected || selectedAction !== action || busyKey !== null) return;

    const key = requestKey(selected);
    const comment = (comments[key] ?? "").trim();

    if (action === "rejected" && selected.request_type === "reading_correction" && !comment) {
      setError("Rejection reason is required for Reading Correction requests.");
      setSelected(null);
      setSelectedAction(null);
      return;
    }

    if (comment.length > 500) {
      setError("Review comment cannot exceed 500 characters.");
      return;
    }

    setBusyKey(key);
    setError("");
    setMessage("");

    try {
      const payload = {
        action,
        review_comment: comment || null,
      };

      switch (selected.request_type) {
        case "reading_correction":
          await reviewSAEReadingCorrection(selected.request_id, payload);
          break;
        case "meter_replacement":
          await reviewSAEMeterReplacement(selected.request_id, payload);
          break;
        case "tubewell_status":
          await reviewSAETubewellStatus(selected.request_id, payload);
          break;
      }

      setRequests((current) =>
        current.filter((item) => requestKey(item) !== key)
      );
      setSelected(null);
      setSelectedAction(null);
      setMessage(
        `${getRequestLabel(selected.request_type)} #${selected.request_id} ${
          action === "approved" ? "reviewed successfully." : "rejected successfully."
        }`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review action failed.");
      setSelected(null);
      setSelectedAction(null);
    } finally {
      setBusyKey(null);
    }
  }

  const visibleRequests = requests.filter(
    (request) => filter === "all" || request.request_type === filter
  );

  const counts = {
    all: requests.length,
    reading_correction: requests.filter(
      (item) => item.request_type === "reading_correction"
    ).length,
    meter_replacement: requests.filter(
      (item) => item.request_type === "meter_replacement"
    ).length,
    tubewell_status: requests.filter(
      (item) => item.request_type === "tubewell_status"
    ).length,
  };

  return (
    <main className="sae-workspace">
      {!inline && (
        <header className="sae-workspace-header">
          <div>
            <span className="sae-workspace-eyebrow">BMDA · SAE WORKSPACE</span>
            <h1>Pending Review Requests</h1>
            <p>Review field requests assigned to your supervision.</p>
          </div>
          <button type="button" onClick={() => void loadRequests()} disabled={loading || busyKey !== null}>
            Refresh
          </button>
        </header>
      )}

      {inline && (
        <div className="sae-workspace-inline-header">
          <h2>Pending Review Requests</h2>
          <button type="button" onClick={() => void loadRequests()} disabled={loading || busyKey !== null}>
            Refresh
          </button>
        </div>
      )}

      {message && <div className="sae-workspace-success" role="status">{message}</div>}
      {error && <div className="sae-workspace-error" role="alert">{error}</div>}

      <nav className="sae-workspace-filters" aria-label="Request type filters">
        {([
          ["all", "All Requests"],
          ["reading_correction", "Reading Correction"],
          ["meter_replacement", "Meter Replacement"],
          ["tubewell_status", "Tubewell Status"],
        ] as [FilterType, string][]).map(([type, label]) => (
          <button
            key={type}
            type="button"
            className={filter === type ? "active" : ""}
            onClick={() => setFilter(type)}
            disabled={busyKey !== null}
          >
            {label}
            <span>{counts[type]}</span>
          </button>
        ))}
      </nav>

      {loading ? (
        <div className="sae-workspace-empty">Loading pending requests...</div>
      ) : visibleRequests.length === 0 ? (
        <div className="sae-workspace-empty">
          No pending {filter === "all" ? "" : getRequestLabel(filter).toLowerCase() + " "}requests.
        </div>
      ) : (
        <section className="sae-workspace-list">
          {visibleRequests.map((request) => {
            const key = requestKey(request);
            const tubewell = details[request.tubewell_id];

            return (
              <article className="sae-request-card" key={key}>
                <div className="sae-request-top">
                  <div>
                    <span className="sae-request-type">{getRequestLabel(request.request_type)}</span>
                    <h3>{tubewell?.tubewell_number || `Tubewell #${request.tubewell_id}`}</h3>
                    {tubewell && (
                      <p>
                        {tubewell.name} · {tubewell.actual_upazila} ·
                        {" "}{tubewell.union_name} · {tubewell.mouza}
                      </p>
                    )}
                  </div>
                  <span className="sae-pending-badge">Pending</span>
                </div>

                <dl className="sae-request-details">
                  <div>
                    <dt>Request ID</dt>
                    <dd>#{request.request_id}</dd>
                  </div>
                  <div>
                    <dt>Requested by</dt>
                    <dd>#{request.requested_by_user_id}</dd>
                  </div>
                  <div>
                    <dt>Requested at</dt>
                    <dd>{formatDate(request.requested_at)}</dd>
                  </div>
                  {request.reading_id !== null && (
                    <div><dt>Reading ID</dt><dd>#{request.reading_id}</dd></div>
                  )}
                  {request.reading_type && (
                    <div><dt>Reading Type</dt><dd>{request.reading_type}</dd></div>
                  )}
                  {request.old_meter_id !== null && (
                    <div><dt>Old Meter ID</dt><dd>#{request.old_meter_id}</dd></div>
                  )}
                  {request.new_meter_number && (
                    <div><dt>New Meter Number</dt><dd>{request.new_meter_number}</dd></div>
                  )}
                  {request.requested_status && (
                    <div><dt>Requested Status</dt><dd>{request.requested_status}</dd></div>
                  )}
                </dl>

                <div className="sae-request-reason">
                  <strong>Request Reason</strong>
                  <p>{request.reason}</p>
                </div>

                <label htmlFor={`sae-comment-${key}`}>Review comment (required for Reading Correction rejection; maximum 500 characters)</label>
                <textarea
                  id={`sae-comment-${key}`}
                  rows={3}
                  maxLength={500}
                  value={comments[key] ?? ""}
                  onChange={(event) =>
                    setComments((current) => ({ ...current, [key]: event.target.value }))
                  }
                  disabled={busyKey !== null}
                  placeholder="Write your review comment..."
                />

                <div className="sae-request-actions">
                  <button
                    type="button"
                    className="sae-reject-button"
                    disabled={busyKey !== null}
                    onClick={() => beginReview(request, "rejected")}
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    className="sae-approve-button"
                    disabled={busyKey !== null}
                    onClick={() => beginReview(request, "approved")}
                  >
                    Review & Forward / Approve
                  </button>
                </div>
              </article>
            );
          })}
        </section>
      )}

      {selected && selectedAction && (
        <div className="sae-confirm-overlay">
          <section className="sae-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="sae-review-dialog-title">
            <h2 id="sae-review-dialog-title">Confirm Review Decision</h2>
            <p>
              {selectedAction === "rejected" ? "Reject" : "Review and approve/forward"}{" "}
              {getRequestLabel(selected.request_type)} #{selected.request_id}?
            </p>
            <div className="sae-request-actions">
              <button
                type="button"
                onClick={() => { setSelected(null); setSelectedAction(null); }}
                disabled={busyKey !== null}
              >
                Cancel
              </button>
              {selectedAction === "rejected" ? (
                <button
                  type="button"
                  className="sae-reject-button"
                  onClick={() => void submitReview("rejected")}
                  disabled={busyKey !== null}
                >
                  {busyKey !== null ? "Processing..." : "Confirm Rejection"}
                </button>
              ) : (
                <button
                  type="button"
                  className="sae-approve-button"
                  onClick={() => void submitReview("approved")}
                  disabled={busyKey !== null}
                >
                  {busyKey !== null ? "Processing..." : "Confirm Approval / Forward"}
                </button>
              )}
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
