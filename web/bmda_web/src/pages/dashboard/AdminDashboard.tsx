import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getUsers } from "../../api/users.api";
import type { UserItem } from "../../api/users.api";
import { getTubewells } from "../../api/tubewells.api";
import type { TubewellItem } from "../../api/tubewells.api";
import { getMeters } from "../../api/meters.api";
import type { MeterItem } from "../../api/meters.api";
import { getAssignments } from "../../api/assignments.api";
import type { AssignmentItem } from "../../api/assignments.api";
import { useCurrentUser } from "../../auth/useCurrentUser";

import "./AdminDashboard.css";
import "./AdminDashboardStats.css";

// ============================================================
// SECTION 1: STATISTICS DATA TYPES
// ============================================================

interface UserStatistics {
  total: number;
  active: number;
  inactive: number;
  assistantEngineers: number;
  supervisors: number;
  fieldUsers: number;
}

interface TubewellStatistics {
  registered: number;
  active: number;
  inactive: number;
}

interface MeterStatistics {
  registered: number;
  installed: number;
  removed: number;
}

interface AssignmentStatistics {
  current: number;
  unassigned: number;
  totalRecords: number;
}

// ============================================================
// SECTION 2: STATISTICS CALCULATIONS
// ============================================================

function calculateUserStatistics(
  users: UserItem[]
): UserStatistics {
  return {
    total: users.length,
    active: users.filter((item) => item.is_active).length,
    inactive: users.filter((item) => !item.is_active).length,
    assistantEngineers: users.filter(
      (item) => item.role === "assistant_engineer"
    ).length,
    supervisors: users.filter(
      (item) => item.role === "supervisor"
    ).length,
    fieldUsers: users.filter(
      (item) => item.role === "field_user"
    ).length,
  };
}

function calculateTubewellStatistics(
  tubewells: TubewellItem[]
): TubewellStatistics {
  const active = tubewells.filter(
    (item) => item.is_active === true
  ).length;

  return {
    registered: tubewells.length,
    active,
    inactive: tubewells.length - active,
  };
}

function calculateMeterStatistics(
  meters: MeterItem[]
): MeterStatistics {
  const removed = meters.filter(
    (item) => item.removed_at !== null
  ).length;

  return {
    registered: meters.length,
    installed: meters.length - removed,
    removed,
  };
}

function calculateAssignmentStatistics(
  assignments: AssignmentItem[],
  tubewells: TubewellItem[]
): AssignmentStatistics {
  const currentAssignments = assignments.filter(
    (item) => item.ended_at === null
  );

  const registeredTubewellIds = new Set(
    tubewells.map((item) => item.id)
  );

  const assignedTubewellIds = new Set(
    currentAssignments
      .map((item) => item.tubewell_id)
      .filter((id) => registeredTubewellIds.has(id))
  );

  return {
    current: currentAssignments.length,
    unassigned: tubewells.length - assignedTubewellIds.size,
    totalRecords: assignments.length,
  };
}

// ============================================================
// SECTION 3: STATISTICS CARD DEFINITIONS
// ============================================================

const statisticCards: {
  key: keyof UserStatistics;
  title: string;
  description: string;
}[] = [
  {
    key: "total",
    title: "Total Users",
    description: "All registered system accounts",
  },
  {
    key: "active",
    title: "Active Users",
    description: "Currently enabled accounts",
  },
  {
    key: "inactive",
    title: "Inactive Users",
    description: "Currently disabled accounts",
  },
  {
    key: "assistantEngineers",
    title: "Assistant Engineers",
    description: "Registered AE accounts",
  },
  {
    key: "supervisors",
    title: "Sub-Assistant Engineers",
    description: "Registered Sub-Assistant Engineer accounts",
  },
  {
    key: "fieldUsers",
    title: "Field Users",
    description: "Registered Field Visitor accounts",
  },
];

const tubewellCards: {
  key: keyof TubewellStatistics;
  title: string;
  description: string;
}[] = [
  {
    key: "registered",
    title: "Registered Tubewells",
    description: "Tubewells registered in the system",
  },
  {
    key: "active",
    title: "Active Tubewells",
    description: "Currently active registered tubewells",
  },
  {
    key: "inactive",
    title: "Inactive Tubewells",
    description: "Currently inactive registered tubewells",
  },
];

const meterCards: {
  key: keyof MeterStatistics;
  title: string;
  description: string;
}[] = [
  {
    key: "registered",
    title: "Registered Meters",
    description: "All registered meter records",
  },
  {
    key: "installed",
    title: "Installed Meters",
    description: "Records without a removal date",
  },
  {
    key: "removed",
    title: "Removed Meters",
    description: "Records with a removal date",
  },
];

const assignmentCards: {
  key: keyof AssignmentStatistics;
  title: string;
  description: string;
}[] = [
  {
    key: "current",
    title: "Current Assignments",
    description: "Assignment records without an end date",
  },
  {
    key: "unassigned",
    title: "Unassigned Tubewells",
    description: "Registered tubewells without a current assignment",
  },
  {
    key: "totalRecords",
    title: "Total Assignment Records",
    description: "All current and historical assignment records",
  },
];

// ============================================================
// SECTION 4: ADMIN DASHBOARD
// ============================================================

function AdminDashboard() {
  const navigate = useNavigate();
  const { user, loading, error } = useCurrentUser();

  const [statistics, setStatistics] =
    useState<UserStatistics | null>(null);
  const [statisticsLoading, setStatisticsLoading] =
    useState(true);
  const [statisticsError, setStatisticsError] =
    useState<string | null>(null);
  const [statisticsRequest, setStatisticsRequest] =
    useState(0);

  const [tubewellStatistics, setTubewellStatistics] =
    useState<TubewellStatistics | null>(null);
  const [tubewellsLoading, setTubewellsLoading] =
    useState(true);
  const [tubewellsError, setTubewellsError] =
    useState<string | null>(null);
  const [tubewellsRequest, setTubewellsRequest] =
    useState(0);

  const [meterStatistics, setMeterStatistics] =
    useState<MeterStatistics | null>(null);
  const [metersLoading, setMetersLoading] =
    useState(true);
  const [metersError, setMetersError] =
    useState<string | null>(null);
  const [metersRequest, setMetersRequest] =
    useState(0);

  const [assignmentStatistics, setAssignmentStatistics] =
    useState<AssignmentStatistics | null>(null);
  const [assignmentsLoading, setAssignmentsLoading] =
    useState(true);
  const [assignmentsError, setAssignmentsError] =
    useState<string | null>(null);
  const [assignmentsRequest, setAssignmentsRequest] =
    useState(0);

  const isAdmin = user?.role === "admin";

  // ==========================================================
  // SECTION 5: LOAD USER STATISTICS
  // ==========================================================

  useEffect(() => {
    if (!isAdmin) return;

    let cancelled = false;

    async function loadStatistics() {
      setStatisticsLoading(true);
      setStatisticsError(null);
      setStatistics(null);

      try {
        const users = await getUsers();

        if (!Array.isArray(users)) {
          throw new Error("Invalid users response.");
        }

        if (!cancelled) {
          setStatistics(calculateUserStatistics(users));
        }
      } catch {
        if (!cancelled) {
          setStatisticsError(
            "User statistics could not be loaded. Please try again."
          );
        }
      } finally {
        if (!cancelled) {
          setStatisticsLoading(false);
        }
      }
    }

    void loadStatistics();

    return () => {
      cancelled = true;
    };
  }, [isAdmin, statisticsRequest]);

  // ==========================================================
  // SECTION 6: LOAD TUBEWELL STATISTICS
  // ==========================================================

  useEffect(() => {
    if (!isAdmin) return;

    let cancelled = false;

    async function loadTubewellStatistics() {
      setTubewellsLoading(true);
      setTubewellsError(null);
      setTubewellStatistics(null);

      try {
        const tubewells = await getTubewells();

        if (!Array.isArray(tubewells)) {
          throw new Error("Invalid tubewells response.");
        }

        if (!cancelled) {
          setTubewellStatistics(
            calculateTubewellStatistics(tubewells)
          );
        }
      } catch {
        if (!cancelled) {
          setTubewellsError(
            "Tubewell statistics could not be loaded. Please try again."
          );
        }
      } finally {
        if (!cancelled) {
          setTubewellsLoading(false);
        }
      }
    }

    void loadTubewellStatistics();

    return () => {
      cancelled = true;
    };
  }, [isAdmin, tubewellsRequest]);

  // ==========================================================
  // SECTION 7: LOAD METER STATISTICS
  // ==========================================================

  useEffect(() => {
    if (!isAdmin) return;

    let cancelled = false;

    async function loadMeterStatistics() {
      setMetersLoading(true);
      setMetersError(null);
      setMeterStatistics(null);

      try {
        const meters = await getMeters();

        if (!Array.isArray(meters)) {
          throw new Error("Invalid meters response.");
        }

        if (
          !meters.every(
            (item) =>
              item !== null &&
              typeof item === "object" &&
              (item.removed_at === null ||
                typeof item.removed_at === "string")
          )
        ) {
          throw new Error("Invalid meter status data.");
        }

        if (!cancelled) {
          setMeterStatistics(
            calculateMeterStatistics(meters)
          );
        }
      } catch {
        if (!cancelled) {
          setMetersError(
            "Meter statistics could not be loaded. Please try again."
          );
        }
      } finally {
        if (!cancelled) {
          setMetersLoading(false);
        }
      }
    }

    void loadMeterStatistics();

    return () => {
      cancelled = true;
    };
  }, [isAdmin, metersRequest]);

  // ==========================================================
  // SECTION 8: LOAD ASSIGNMENT STATISTICS
  // Read-only: GET assignments and GET tubewells.
  // ==========================================================

  useEffect(() => {
    if (!isAdmin) return;

    let cancelled = false;

    async function loadAssignmentStatistics() {
      setAssignmentsLoading(true);
      setAssignmentsError(null);
      setAssignmentStatistics(null);

      try {
        const [assignments, tubewells] = await Promise.all([
          getAssignments(false),
          getTubewells(),
        ]);

        if (
          !Array.isArray(assignments) ||
          !Array.isArray(tubewells)
        ) {
          throw new Error("Invalid assignment response.");
        }

        if (
          !assignments.every(
            (item) =>
              item !== null &&
              typeof item === "object" &&
              Number.isInteger(item.tubewell_id) &&
              (item.ended_at === null ||
                typeof item.ended_at === "string")
          ) ||
          !tubewells.every(
            (item) =>
              item !== null &&
              typeof item === "object" &&
              Number.isInteger(item.id)
          )
        ) {
          throw new Error("Invalid assignment data.");
        }

        if (!cancelled) {
          setAssignmentStatistics(
            calculateAssignmentStatistics(
              assignments,
              tubewells
            )
          );
        }
      } catch {
        if (!cancelled) {
          setAssignmentsError(
            "Assignment statistics could not be loaded. Please try again."
          );
        }
      } finally {
        if (!cancelled) {
          setAssignmentsLoading(false);
        }
      }
    }

    void loadAssignmentStatistics();

    return () => {
      cancelled = true;
    };
  }, [isAdmin, assignmentsRequest]);

  // ==========================================================
  // SECTION 9: RETRY AND NAVIGATION HANDLERS
  // ==========================================================

  function retryStatistics() {
    setStatisticsRequest((previous) => previous + 1);
  }

  function retryTubewells() {
    setTubewellsRequest((previous) => previous + 1);
  }

  function retryMeters() {
    setMetersRequest((previous) => previous + 1);
  }

  function retryAssignments() {
    setAssignmentsRequest((previous) => previous + 1);
  }

  function goToUsers() {
    navigate("/admin/users");
  }

  function goToTubewells() {
    navigate("/admin/tubewells");
  }

  function goToAssignments() {
    navigate("/admin/assignments");
  }

  function goToMeters() {
    navigate("/admin/meters");
  }

  // ==========================================================
  // SECTION 10: AUTHENTICATION STATES
  // ==========================================================

  if (loading) {
    return (
      <main className="bmda-admin-dashboard">
        <div className="admin-dash-notice" role="status">
          Loading user...
        </div>
      </main>
    );
  }

  if (error || !user) {
    return (
      <main className="bmda-admin-dashboard">
        <div
          className="admin-dash-notice admin-dash-error"
          role="alert"
        >
          {error || "Unable to load current user."}
        </div>
      </main>
    );
  }

  // ==========================================================
  // SECTION 11: DASHBOARD INTERFACE
  // ==========================================================

  return (
    <main className="bmda-admin-dashboard">
      <div className="admin-dash-container">
        <header className="admin-dash-header">
          <div>
            <p className="admin-dash-eyebrow">
              BMDA · Deep Tubewell Management System
            </p>
            <h1 className="admin-dash-title">
              Admin Dashboard
            </h1>
            <p className="admin-dash-subtitle">
              Manage system users and tubewell records from one place.
            </p>
          </div>
        </header>

        <section
          className="admin-dash-welcome"
          aria-label="Current user"
        >
          <div
            className="admin-dash-avatar"
            aria-hidden="true"
          >
            {(user.full_name?.trim()?.[0] || "A").toUpperCase()}
          </div>

          <div className="admin-dash-welcome-copy">
            <p className="admin-dash-welcome-label">
              Welcome back
            </p>
            <h2 className="admin-dash-user-name">
              {user.full_name || "Administrator"}
            </h2>
            <span className="admin-dash-role">
              Executive Engineer, Panchagarh Region
            </span>
          </div>
        </section>

        {/* User Overview */}
        <section
          className="admin-stats-section"
          aria-labelledby="admin-stats-heading"
          aria-busy={statisticsLoading}
        >
          <div className="admin-dash-section-heading">
            <h2 id="admin-stats-heading">User Overview</h2>
            <p>
              Current registered users by account status and role.
            </p>
          </div>

          {statisticsLoading ? (
            <div className="admin-stats-notice" role="status">
              Loading live user statistics...
            </div>
          ) : statisticsError ? (
            <div
              className="admin-stats-notice admin-stats-error"
              role="alert"
            >
              <p>{statisticsError}</p>
              <button
                type="button"
                className="admin-stats-retry"
                onClick={retryStatistics}
              >
                Retry
              </button>
            </div>
          ) : statistics ? (
            <div className="admin-stats-grid">
              {statisticCards.map((card) => (
                <article className="admin-stats-card" key={card.key}>
                  <p className="admin-stats-title">{card.title}</p>
                  <p className="admin-stats-value">
                    {statistics[card.key].toLocaleString("en-US")}
                  </p>
                  <p className="admin-stats-description">
                    {card.description}
                  </p>
                </article>
              ))}
            </div>
          ) : null}
        </section>

        {/* Tubewell Overview */}
        <section
          className="admin-stats-section"
          aria-labelledby="admin-tubewell-stats-heading"
          aria-busy={tubewellsLoading}
        >
          <div className="admin-dash-section-heading">
            <h2 id="admin-tubewell-stats-heading">
              Tubewell Overview
            </h2>
            <p>
              Live statistics for tubewells registered in the system.
            </p>
          </div>

          {tubewellsLoading ? (
            <div className="admin-stats-notice" role="status">
              Loading live tubewell statistics...
            </div>
          ) : tubewellsError ? (
            <div
              className="admin-stats-notice admin-stats-error"
              role="alert"
            >
              <p>{tubewellsError}</p>
              <button
                type="button"
                className="admin-stats-retry"
                onClick={retryTubewells}
              >
                Retry
              </button>
            </div>
          ) : tubewellStatistics ? (
            <div className="admin-stats-grid">
              {tubewellCards.map((card) => (
                <article className="admin-stats-card" key={card.key}>
                  <p className="admin-stats-title">{card.title}</p>
                  <p className="admin-stats-value">
                    {tubewellStatistics[card.key].toLocaleString("en-US")}
                  </p>
                  <p className="admin-stats-description">
                    {card.description}
                  </p>
                </article>
              ))}
            </div>
          ) : null}
        </section>

        {/* Meter Overview */}
        <section
          className="admin-stats-section"
          aria-labelledby="admin-meter-stats-heading"
          aria-busy={metersLoading}
        >
          <div className="admin-dash-section-heading">
            <h2 id="admin-meter-stats-heading">
              Meter Overview
            </h2>
            <p>
              Live meter registration and removal-date statistics.
            </p>
          </div>

          {metersLoading ? (
            <div className="admin-stats-notice" role="status">
              Loading live meter statistics...
            </div>
          ) : metersError ? (
            <div
              className="admin-stats-notice admin-stats-error"
              role="alert"
            >
              <p>{metersError}</p>
              <button
                type="button"
                className="admin-stats-retry"
                onClick={retryMeters}
              >
                Retry
              </button>
            </div>
          ) : meterStatistics ? (
            <div className="admin-stats-grid">
              {meterCards.map((card) => (
                <article className="admin-stats-card" key={card.key}>
                  <p className="admin-stats-title">{card.title}</p>
                  <p className="admin-stats-value">
                    {meterStatistics[card.key].toLocaleString("en-US")}
                  </p>
                  <p className="admin-stats-description">
                    {card.description}
                  </p>
                </article>
              ))}
            </div>
          ) : null}
        </section>

        {/* Assignment Overview */}
        <section
          className="admin-stats-section"
          aria-labelledby="admin-assignment-stats-heading"
          aria-busy={assignmentsLoading}
        >
          <div className="admin-dash-section-heading">
            <h2 id="admin-assignment-stats-heading">
              Assignment Overview
            </h2>
            <p>
              Live current assignments and assignment history.
            </p>
          </div>

          {assignmentsLoading ? (
            <div className="admin-stats-notice" role="status">
              Loading live assignment statistics...
            </div>
          ) : assignmentsError ? (
            <div
              className="admin-stats-notice admin-stats-error"
              role="alert"
            >
              <p>{assignmentsError}</p>
              <button
                type="button"
                className="admin-stats-retry"
                onClick={retryAssignments}
              >
                Retry
              </button>
            </div>
          ) : assignmentStatistics ? (
            <div className="admin-stats-grid">
              {assignmentCards.map((card) => (
                <article
                  className="admin-stats-card"
                  key={card.key}
                >
                  <p className="admin-stats-title">
                    {card.title}
                  </p>
                  <p className="admin-stats-value">
                    {assignmentStatistics[card.key].toLocaleString("en-US")}
                  </p>
                  <p className="admin-stats-description">
                    {card.description}
                  </p>
                </article>
              ))}
            </div>
          ) : null}
        </section>

        {/* Management Workspace */}
        <section
          className="admin-dash-workspace"
          aria-labelledby="admin-dash-workspace-title"
        >
          <div className="admin-dash-section-heading">
            <h2 id="admin-dash-workspace-title">
              Management Workspace
            </h2>
            <p>Choose an area to continue your work.</p>
          </div>

          <div className="admin-dash-grid">
            <article className="admin-dash-card">
              <div
                className="admin-dash-card-icon"
                aria-hidden="true"
              >
                👥
              </div>
              <h3>Users Management</h3>
              <p>
                View and manage system users and their access.
              </p>
              <button
                className="admin-dash-btn admin-dash-btn-primary"
                type="button"
                onClick={goToUsers}
              >
                Open Users Management
                <span aria-hidden="true">→</span>
              </button>
            </article>

            <article className="admin-dash-card">
              <div
                className="admin-dash-card-icon"
                aria-hidden="true"
              >
                🌿
              </div>
              <h3>Tubewells Management</h3>
              <p>
                View, search and manage registered tubewells.
              </p>
              <button
                className="admin-dash-btn admin-dash-btn-primary"
                type="button"
                onClick={goToTubewells}
              >
                Open Tubewells Management
                <span aria-hidden="true">→</span>
              </button>
            </article>

            <article className="admin-dash-card">
              <div
                className="admin-dash-card-icon"
                aria-hidden="true"
              >
                📋
              </div>
              <h3>Tubewell Assignments</h3>
              <p>
                View and monitor existing tubewell assignments
                without changing assignment records.
              </p>
              <button
                className="admin-dash-btn admin-dash-btn-primary"
                type="button"
                onClick={goToAssignments}
              >
                Open Assignment Monitoring
                <span aria-hidden="true">→</span>
              </button>
            </article>

            <article className="admin-dash-card">
              <div
                className="admin-dash-card-icon"
                aria-hidden="true"
              >
                ⚡
              </div>
              <h3>Meter Monitoring</h3>
              <p>
                View registered meter records and their
                installation history.
              </p>
              <button
                className="admin-dash-btn admin-dash-btn-primary"
                type="button"
                onClick={goToMeters}
              >
                Open Meter Monitoring
                <span aria-hidden="true">→</span>
              </button>
            </article>
          </div>
        </section>

        {/* System Overview */}
        <aside className="admin-dash-info">
          <h2>System Overview</h2>
          <p>
            This system also covers Meters, Assignments, Readings,
            Requests, Warnings and Reports. These areas will be linked
            here as their frontend pages become available.
          </p>
        </aside>
      </div>
    </main>
  );
}

export default AdminDashboard;
