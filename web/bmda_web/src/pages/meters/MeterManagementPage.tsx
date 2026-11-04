import { useEffect, useState } from "react";

import { getMeters } from "../../api/meters.api";
import type { MeterItem } from "../../api/meters.api";

import "./MeterManagementPage.css";

function formatDate(value: string | null): string {
  if (!value) return "—";

  const date = new Date(`${value}T00:00:00`);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-GB");
}

export default function MeterManagementPage() {
  const [meters, setMeters] = useState<MeterItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [request, setRequest] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadMeters() {
      setLoading(true);
      setError(null);

      try {
        const result = await getMeters();

        if (!Array.isArray(result)) {
          throw new Error("Invalid meter response.");
        }

        if (!cancelled) {
          setMeters(result);
        }
      } catch {
        if (!cancelled) {
          setError(
            "Meter information could not be loaded. Please try again."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadMeters();

    return () => {
      cancelled = true;
    };
  }, [request]);

  return (
    <main className="bmda-meter-page">
      <header className="bmda-meter-header">
        <div>
          <p className="bmda-meter-eyebrow">
            BMDA · Operational Management
          </p>
          <h1>Meter Management</h1>
          <p>
            View registered meters and their installation history.
          </p>
        </div>
      </header>

      <section
        className="bmda-meter-panel"
        aria-labelledby="meter-list-heading"
        aria-busy={loading}
      >
        <div className="bmda-meter-panel-heading">
          <div>
            <h2 id="meter-list-heading">Registered Meters</h2>
            <p>
              Current meter records from the BMDA system.
            </p>
          </div>
          <span className="bmda-meter-count">
            {loading || error ? "—" : meters.length}
          </span>
        </div>

        {loading ? (
          <p className="bmda-meter-message" role="status">
            Loading meter records...
          </p>
        ) : error ? (
          <div className="bmda-meter-message" role="alert">
            <p>{error}</p>
            <button
              type="button"
              onClick={() => setRequest((value) => value + 1)}
            >
              Retry
            </button>
          </div>
        ) : meters.length === 0 ? (
          <p className="bmda-meter-message">
            No meter records found.
          </p>
        ) : (
          <div className="bmda-meter-table-scroll">
            <table className="bmda-meter-table">
              <thead>
                <tr>
                  <th scope="col">Meter ID</th>
                  <th scope="col">Tubewell ID</th>
                  <th scope="col">Meter Number</th>
                  <th scope="col">Installed At</th>
                  <th scope="col">Removed At</th>
                </tr>
              </thead>
              <tbody>
                {meters.map((meter) => (
                  <tr key={meter.id}>
                    <td>{meter.id}</td>
                    <td>{meter.tubewell_id}</td>
                    <td>{meter.meter_number || "—"}</td>
                    <td>{formatDate(meter.installed_at)}</td>
                    <td>{formatDate(meter.removed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
