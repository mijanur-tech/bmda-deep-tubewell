import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getAEPendingRequests,
  getSupervisorPendingRequests,
  reviewAERequest,
  reviewSupervisorRequest,
} from "../../api/tubewellStatus.api";
import type {
  ApprovalAction,
  TubewellStatusRequest,
} from "../../api/tubewellStatus.api";
import { getTubewell } from "../../api/tubewells.api";
import type { TubewellItem } from "../../api/tubewells.api";
import "./ApprovalPage.css";

// SECTION 1: Role-specific configuration.
interface ApprovalPageProps {
  role: "supervisor" | "assistant_engineer";
  inline?: boolean;
}

export default function ApprovalPage({ role, inline = false }: ApprovalPageProps) {
  const navigate = useNavigate();
  const isAE = role === "assistant_engineer";
  const [requests, setRequests] = useState<TubewellStatusRequest[]>([]);
  const [tubewellDetails, setTubewellDetails] = useState<Record<number, TubewellItem>>({});
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [comments, setComments] = useState<Record<number, string>>({});
  const [selected, setSelected] = useState<{
    id: number;
    action: ApprovalAction;
  } | null>(null);

  // SECTION 2: Load only requests permitted by the backend.
  async function loadRequests() {
    setLoading(true);
    setError("");
    try {
      const data = isAE
        ? await getAEPendingRequests()
        : await getSupervisorPendingRequests();
      setRequests(data);

      // Load only details permitted by the existing backend security.
      const ids = [...new Set(data.map((item) => item.tubewell_id))];
      const results = await Promise.allSettled(ids.map((id) => getTubewell(id)));
      const details: Record<number, TubewellItem> = {};

      results.forEach((result, index) => {
        if (result.status === "fulfilled") {
          details[ids[index]] = result.value;
        }
      });

      setTubewellDetails(details);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load requests.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadRequests();
    // Reload whenever the workspace role changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role]);

  // SECTION 3: Submit a confirmed review decision.
  async function submitReview() {
    if (!selected || busyId !== null) return;

    const { id, action } = selected;
    const comment = (comments[id] ?? "").trim();

    if (comment.length > 500) {
      setError("Review comment must be 500 characters or fewer.");
      return;
    }

    setBusyId(id);
    setError("");
    setMessage("");

    try {
      const payload = { action, review_comment: comment || null };

      if (isAE) {
        await reviewAERequest(id, payload);
      } else {
        await reviewSupervisorRequest(id, payload);
      }

      setSelected(null);
      setMessage(
        action === "rejected"
          ? `Request #${id} rejected successfully.`
          : isAE
            ? `Request #${id} finally approved.`
            : `Request #${id} forwarded to the Assistant Engineer.`
      );

      // Remove the reviewed request from the pending list.
      setRequests((current) => current.filter((item) => item.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review failed.");
      setSelected(null);
    } finally {
      setBusyId(null);
    }
  }

  // SECTION 4: User interface.
  return (
    <main className="bmda-approval-page">
      {!inline && (
      <header className="bmda-approval-header">
        <div>
          <p className="bmda-approval-eyebrow">BMDA · Approval Management</p>
          <h1>{isAE ? "Final Approval Requests" : "Sub-Assistant Engineer Review Requests"}</h1>
          <p>
            {isAE
              ? "Review requests forwarded by Sub-Assistant Engineers and make the final decision."
              : "Review field requests and forward approved requests to the Assistant Engineer."}
          </p>
        </div>
        <div className="bmda-approval-header-actions">
          {!inline && (
          <button
            type="button"
            onClick={() => navigate(isAE ? "/ae/dashboard" : "/supervisor/dashboard")}
            disabled={busyId !== null}
          >
            ← Back to Dashboard
          </button>
          )}
          <button
            type="button"
            onClick={() => void loadRequests()}
            disabled={loading || busyId !== null}
          >
            Refresh
          </button>
        </div>
      </header>
      )}

      {inline && (
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
          <button type="button" onClick={() => void loadRequests()} disabled={loading || busyId !== null}>
            Refresh Requests
          </button>
        </div>
      )}

      {message && <div className="bmda-approval-success" role="status">{message}</div>}
      {error && <div className="bmda-approval-error" role="alert">{error}</div>}

      {loading ? (
        <p className="bmda-approval-empty">Loading pending requests...</p>
      ) : requests.length === 0 ? (
        <div className="bmda-approval-empty">No pending requests at this time.</div>
      ) : (
        <div className="bmda-approval-list">
          {requests.map((request) => (
            <article className="bmda-approval-card" key={request.id}>
              <div className="bmda-approval-card-top">
                <div>
                  <span className="bmda-approval-request-id">Request #{request.id}</span>
                  <h2>{tubewellDetails[request.tubewell_id]?.tubewell_number || `Tubewell #${request.tubewell_id}`}</h2>
                  {tubewellDetails[request.tubewell_id] && (
                    <p>
                      {tubewellDetails[request.tubewell_id].name} ·
                      {` ${tubewellDetails[request.tubewell_id].actual_upazila}`} ·
                      {` ${tubewellDetails[request.tubewell_id].union_name}`} ·
                      {` ${tubewellDetails[request.tubewell_id].mouza}`}
                    </p>
                  )}
                </div>
                <span className="bmda-approval-status">
                  {request.requested_status === "active" ? "Activate" : "Deactivate"}
                </span>
              </div>

              <dl className="bmda-approval-details">
                <div><dt>Requested by User</dt><dd>#{request.requested_by_user_id}</dd></div>
                <div><dt>Requested at</dt><dd>{new Date(request.requested_at).toLocaleString()}</dd></div>
                <div><dt>Current Stage</dt><dd>{request.status.replaceAll("_", " ")}</dd></div>
              </dl>

              <div className="bmda-approval-reason">
                <strong>Reason</strong>
                <p>{request.reason}</p>
              </div>

              {isAE && request.review_comment && (
                <div className="bmda-approval-reason">
                  <strong>Sub-Assistant Engineer Comment</strong>
                  <p>{request.review_comment}</p>
                </div>
              )}

              <label className="bmda-approval-label" htmlFor={`comment-${request.id}`}>
                Review comment (optional, maximum 500 characters)
              </label>
              <textarea
                id={`comment-${request.id}`}
                maxLength={500}
                rows={3}
                value={comments[request.id] ?? ""}
                onChange={(event) =>
                  setComments((current) => ({
                    ...current,
                    [request.id]: event.target.value,
                  }))
                }
                disabled={busyId !== null}
                placeholder="Write a review comment..."
              />

              <div className="bmda-approval-actions">
                <button
                  className="bmda-approval-reject"
                  type="button"
                  disabled={busyId !== null}
                  onClick={() => setSelected({ id: request.id, action: "rejected" })}
                >
                  Reject
                </button>
                <button
                  className="bmda-approval-approve"
                  type="button"
                  disabled={busyId !== null}
                  onClick={() => setSelected({ id: request.id, action: "approved" })}
                >
                  {isAE ? "Final Approve" : "Forward to AE"}
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {selected && (
        <div className="bmda-approval-overlay">
          <div
            className="bmda-approval-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="bmda-approval-dialog-title"
          >
            <h2 id="bmda-approval-dialog-title">Confirm Decision</h2>
            <p>
              {selected.action === "rejected"
                ? `Reject Request #${selected.id}?`
                : isAE
                  ? `Give final approval to Request #${selected.id}? This may change the tubewell status.`
                  : `Forward Request #${selected.id} to the Assistant Engineer?`}
            </p>
            <div className="bmda-approval-actions">
              <button type="button" disabled={busyId !== null} onClick={() => setSelected(null)}>
                Cancel
              </button>
              <button
                className={selected.action === "rejected" ? "bmda-approval-reject" : "bmda-approval-approve"}
                type="button"
                disabled={busyId !== null}
                onClick={() => void submitReview()}
              >
                {busyId !== null ? "Processing..." : "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
