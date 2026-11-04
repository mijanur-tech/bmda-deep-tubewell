import { useEffect, useState } from "react";
import {
  getAEFieldUserCoverage,
  type AEFieldUserCoverageResponse,
} from "../../api/aeFieldUserCoverage.api";
import "./AEFieldUserCoverage.css";

interface Props {
  refreshKey: number;
}

export default function AEFieldUserCoverage({ refreshKey }: Props) {
  const [data, setData] = useState<AEFieldUserCoverageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadCoverage() {
      setLoading(true);
      setError("");

      try {
        const result = await getAEFieldUserCoverage();

        if (!cancelled) {
          setData(result);
        }
      } catch (err) {
        if (!cancelled) {
          setData(null);
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load field user coverage."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadCoverage();

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return (
    <section
      className="bmda-ae-field-coverage"
      aria-labelledby="bmda-ae-field-coverage-title"
    >
      <div className="bmda-ae-field-coverage-heading">
        <div>
          <h2 id="bmda-ae-field-coverage-title">
            Field User-wise Assignment Coverage
          </h2>
          <p>
            Current tubewell assignments by field visitor within your
            management unit.
          </p>
        </div>
      </div>

      {loading && (
        <p role="status">Loading field user coverage...</p>
      )}

      {!loading && error && (
        <p role="alert" className="bmda-ae-field-coverage-error">
          {error}
        </p>
      )}

      {!loading && !error && data && (
        <>
          <div className="bmda-ae-field-coverage-summary">
            <span>Total Tubewells: <strong>{data.total_tubewells}</strong></span>
            <span>Assigned: <strong>{data.assigned_tubewells}</strong></span>
            <span>Unassigned: <strong>{data.unassigned_tubewells}</strong></span>
          </div>

          {data.unmatched_assignments > 0 && (
            <p className="bmda-ae-field-coverage-warning" role="status">
              Unmatched current assignments: {data.unmatched_assignments}
            </p>
          )}

          {data.field_users.length === 0 ? (
            <p>No field visitors found in this management unit.</p>
          ) : (
            <div className="bmda-ae-field-coverage-list">
              {data.field_users.map((item) => {
                const percentage = Math.max(
                  0,
                  Math.min(100, item.coverage_percentage)
                );

                return (
                  <article
                    className="bmda-ae-field-coverage-item"
                    key={item.field_user_id}
                  >
                    <div className="bmda-ae-field-coverage-item-top">
                      <div>
                        <h3>{item.full_name}</h3>
                        <span
                          className={
                            item.is_active
                              ? "bmda-ae-field-status-active"
                              : "bmda-ae-field-status-inactive"
                          }
                        >
                          {item.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>

                      <div className="bmda-ae-field-coverage-numbers">
                        <strong>{item.assigned_tubewells}</strong>
                        <span>Assigned Tubewells</span>
                      </div>
                    </div>

                    <div className="bmda-ae-field-coverage-progress-label">
                      <span>Unit Coverage</span>
                      <strong>{percentage.toFixed(1)}%</strong>
                    </div>

                    <div
                      className="bmda-ae-field-coverage-progress"
                      role="progressbar"
                      aria-label={`${item.full_name} assignment coverage`}
                      aria-valuenow={percentage}
                      aria-valuemin={0}
                      aria-valuemax={100}
                    >
                      <div style={{ width: `${percentage}%` }} />
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </>
      )}
    </section>
  );
}
