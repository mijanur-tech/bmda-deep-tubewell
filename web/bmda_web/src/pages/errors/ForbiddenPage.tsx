import { useNavigate } from "react-router-dom";
import "./ForbiddenPage.css";

function ForbiddenPage() {
  const navigate = useNavigate();

  function handleBack() {
    navigate(-1);
  }

  return (
    <main className="bmda-forbidden-page">
      <section
        className="bmda-forbidden-card"
        aria-labelledby="bmda-forbidden-title"
      >
        <div className="bmda-forbidden-icon" aria-hidden="true">
          <svg
            width="34"
            height="34"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="4" y="10" width="16" height="11" rx="2" />
            <path d="M8 10V7a4 4 0 0 1 8 0v3" />
            <circle cx="12" cy="15.5" r="1" />
            <path d="M12 16.5v1.5" />
          </svg>
        </div>

        <span className="bmda-forbidden-code">ERROR 403</span>

        <h1 id="bmda-forbidden-title">
          Access Denied
        </h1>

        <p className="bmda-forbidden-description">
          আপনার এই পেজে প্রবেশ করার অনুমতি নেই।
        </p>

        <p className="bmda-forbidden-help">
          You do not have permission to access this page.
        </p>

        <button
          type="button"
          className="bmda-forbidden-back"
          onClick={handleBack}
        >
          <span aria-hidden="true">←</span>
          Back
        </button>

        <div className="bmda-forbidden-footer">
          BMDA · Deep Tubewell Management System
        </div>
      </section>
    </main>
  );
}

export default ForbiddenPage;
