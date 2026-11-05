import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { removeAccessToken } from "../../auth/session";
import { useCurrentUser } from "../../auth/useCurrentUser";
import { getTubewells, type TubewellItem } from "../../api/tubewells.api";
import { getSAEFieldVisitorSummary, type SAEFieldVisitorSummaryResponse } from "../../api/saeFieldVisitorSummary.api";
import { getSAEReadingActivity, type SAEReadingActivityResponse } from "../../api/saeReadingActivity.api";
import { getSAEPendingRequests } from "../../api/saePendingRequests.api";
import { getAEPersonnelSummary, type AEPersonnelSummary } from "../../api/aePersonnelSummary.api";
import { getAEPendingTubewellStatusRequests } from "../../api/aePendingRequests.api";
import { getAEReadingWarnings, type AEReadingWarnings } from "../../api/aeReadingWarnings.api";
import { getAssignments, type AssignmentItem } from "../../api/assignments.api";
import {
  getAEPendingMeterReplacements,
  getAEMeterReplacementDetail,
  reviewAEMeterReplacement,
  type AEMeterReplacementRequest,
} from "../../api/meterReplacementAE.api";
import { calculateAEAssignmentCoverage } from "../../api/aeAssignmentCoverage";
import AEFieldUserCoverage from "../AEFieldUserCoverage/AEFieldUserCoverage";
import SAEReadingActivityMonitoring from "../SAEReadingActivityMonitoring/SAEReadingActivityMonitoring";
import SAERecentActivity from "../SAERecentActivity/SAERecentActivity";
import SAETubewellAssignmentMonitoring from "../SAETubewellAssignmentMonitoring/SAETubewellAssignmentMonitoring";
import SAEFieldVisitorMonitoring from "../SAEFieldVisitorMonitoring/SAEFieldVisitorMonitoring";
import bmdaLogo from "../../assets/bmda-logo.png";
import ApprovalPage from "../../pages/approvals/ApprovalPage";
import "./RoleDashboard.css";
import "./SAEPremiumDashboard.css";
import "./SAESectionDropdown.css";

type Role = "ae" | "supervisor";

const menus = {
  ae: [
    ["overview", "Overview", "▦"],
    ["responsibilities", "Management Scope", "◫"],
    ["tubewells", "Tubewell List", "◫"],
    ["assignments", "Tubewell Assignments", "◫"],
    ["workflow", "Approval Workflow", "✓"],
    ["approvals", "Approval Requests", "✓"],
    ["account", "My Profile", "◉"],
  ],
  supervisor: [
    ["overview", "Overview", "▦"],
    ["responsibilities", "Field Operations", "◫"],
    ["tubewells", "Tubewell List", "◫"],
    ["workflow", "Review Workflow", "✓"],
    ["approvals", "Approval Requests", "✓"],
    ["account", "My Profile", "◉"],
  ],
} as const;

// SAE-only section choices. Single-section tabs remain accessible consistently.
const saeSections: Record<string, { id: string; label: string; detail: string }[]> = {
  overview: [
    { id: "summary", label: "Dashboard Summary", detail: "Your operational status and key figures" },
    { id: "welcome", label: "Welcome & Management Unit", detail: "Your workspace and management unit" },
    { id: "quick", label: "Quick Actions", detail: "Go directly to an available work area" },
  ],
  responsibilities: [
    { id: "visitors", label: "Field Visitor Monitoring", detail: "Monitor field visitors in your team" },
    { id: "readings", label: "Reading Activity Monitoring", detail: "Check Energy and Prepaid reading activity" },
    { id: "duties", label: "Field Responsibilities", detail: "Your day-to-day operational duties" },
  ],
  tubewells: [
    { id: "list", label: "Tubewell List", detail: "Search and filter assigned tubewells" },
    { id: "assignments", label: "Field Visitor-wise Assignments", detail: "See who is responsible for each tubewell" },
  ],
  workflow: [
    { id: "review", label: "Review Workflow", detail: "Read the current review workflow guidance" },
  ],
  approvals: [
    { id: "requests", label: "Approval Requests", detail: "Work with your authorized request queue" },
  ],
  account: [
    { id: "profile", label: "Profile Information", detail: "View your account and management unit" },
  ],
};

const pageSizes = [10, 25, 50] as const;
const cellStyle = {
  padding: "12px 13px",
  borderBottom: "1px solid #e2ede5",
  textAlign: "left" as const,
  verticalAlign: "top" as const,
  whiteSpace: "nowrap" as const,
};

export default function RoleDashboard({ role }: { role: Role }) {
  const navigate = useNavigate();
  const { user, loading, error } = useCurrentUser();
  const [menuOpen, setMenuOpen] = useState(false);
  const [active, setActive] = useState("overview");
  const [saeSection, setSaeSection] = useState("summary");
  const [tubewells, setTubewells] = useState<TubewellItem[]>([]);
  const [tubewellsLoading, setTubewellsLoading] = useState(false);
  const [tubewellsError, setTubewellsError] = useState("");
  const [personnel, setPersonnel] = useState<AEPersonnelSummary | null>(null);
  const [personnelLoading, setPersonnelLoading] = useState(false);
  const [personnelError, setPersonnelError] = useState("");
  const [aePendingCount, setAePendingCount] = useState<number | null>(null);
  const [aePendingLoading, setAePendingLoading] = useState(false);
  const [aePendingError, setAePendingError] = useState("");
  const [readingWarnings, setReadingWarnings] = useState<AEReadingWarnings | null>(null);
  const [readingWarningsLoading, setReadingWarningsLoading] = useState(false);
  const [readingWarningsError, setReadingWarningsError] = useState("");
  const [assignments, setAssignments] = useState<AssignmentItem[]>([]);
  const [assignmentsLoading, setAssignmentsLoading] = useState(false);
  const [assignmentsError, setAssignmentsError] = useState("");
  const [aeMeterRequests, setAeMeterRequests] = useState<AEMeterReplacementRequest[]>([]);
  const [activeMeterType, setActiveMeterType] = useState<"energy" | "prepaid">("energy");
  const [aeMeterRequestsLoading, setAeMeterRequestsLoading] = useState(false);
  const [aeMeterRequestsError, setAeMeterRequestsError] = useState("");
  const [selectedMeterRequest, setSelectedMeterRequest] = useState<AEMeterReplacementRequest | null>(null);
  const [meterRequestDetailLoading, setMeterRequestDetailLoading] = useState(false);
  const [meterReviewComment, setMeterReviewComment] = useState("");
  const [meterReviewBusy, setMeterReviewBusy] = useState(false);
  const [meterReviewMessage, setMeterReviewMessage] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  // SAE-only live overview. Keep AE data loading and permissions unchanged.
  const [saeTeam, setSaeTeam] = useState<SAEFieldVisitorSummaryResponse | null>(null);
  const [saeTeamLoading, setSaeTeamLoading] = useState(false);
  const [saeTeamError, setSaeTeamError] = useState("");
  const [saeActivity, setSaeActivity] = useState<SAEReadingActivityResponse | null>(null);
  const [saeActivityLoading, setSaeActivityLoading] = useState(false);
  const [saeActivityError, setSaeActivityError] = useState("");
  const [saePendingCount, setSaePendingCount] = useState<number | null>(null);
  const [saePendingLoading, setSaePendingLoading] = useState(false);
  const [saePendingError, setSaePendingError] = useState("");
  const [search, setSearch] = useState("");
  const [saeTubewellStatus, setSaeTubewellStatus] = useState<"all" | "active" | "inactive">("all");
  const [pageSize, setPageSize] = useState<number>(10);
  const [page, setPage] = useState(1);

  const isAE = role === "ae";
  const roleTitle = isAE ? "Assistant Engineer" : "Sub-Assistant Engineer";
  const unitName = user?.upazila_name?.trim() ||
    (user?.upazila_id == null ? "No Management Unit assigned" : "Management Unit unavailable");

  useEffect(() => {
    if (loading || error || !user) return;
    let cancelled = false;
    async function loadTubewells() {
      setTubewellsLoading(true);
      setTubewellsError("");
      try {
        const data = await getTubewells();
        if (!cancelled) {
          if (!Array.isArray(data)) throw new Error("Unexpected tubewell response.");
          setTubewells(data);
        }
      } catch (err) {
        if (!cancelled) {
          setTubewells([]);
          setTubewellsError(err instanceof Error ? err.message : "Unable to load tubewells.");
        }
      } finally {
        if (!cancelled) setTubewellsLoading(false);
      }
    }
    void loadTubewells();
    return () => { cancelled = true; };
  }, [user, loading, error, refreshKey]);

  useEffect(() => {
    if (!isAE || loading || error || !user) return;
    let cancelled = false;

    async function loadPersonnel() {
      setPersonnelLoading(true);
      setPersonnelError("");
      try {
        const data = await getAEPersonnelSummary();
        if (!cancelled) setPersonnel(data);
      } catch (err) {
        if (!cancelled) {
          setPersonnel(null);
          setPersonnelError(err instanceof Error ? err.message : "Unable to load personnel.");
        }
      } finally {
        if (!cancelled) setPersonnelLoading(false);
      }
    }

    void loadPersonnel();
    return () => { cancelled = true; };
  }, [isAE, user, loading, error, refreshKey]);

  useEffect(() => {
    if (!isAE || loading || error || !user) return;
    let cancelled = false;

    async function loadAEPending() {
      setAePendingLoading(true);
      setAePendingError("");
      try {
        const requests = await getAEPendingTubewellStatusRequests();
        if (!cancelled) setAePendingCount(requests.length);
      } catch (err) {
        if (!cancelled) {
          setAePendingCount(null);
          setAePendingError(err instanceof Error ? err.message : "Unable to load AE pending requests.");
        }
      } finally {
        if (!cancelled) setAePendingLoading(false);
      }
    }

    void loadAEPending();
    return () => { cancelled = true; };
  }, [isAE, user, loading, error, refreshKey]);

  useEffect(() => {
    if (!isAE || loading || error || !user) return;
    let cancelled = false;

    async function loadAEMeterRequests() {
      setAeMeterRequestsLoading(true);
      setAeMeterRequestsError("");
      try {
        const data = await getAEPendingMeterReplacements();
        if (!cancelled) setAeMeterRequests(data);
      } catch (err) {
        if (!cancelled) {
          setAeMeterRequests([]);
          setAeMeterRequestsError(
            err instanceof Error ? err.message : "Unable to load meter replacement approvals."
          );
        }
      } finally {
        if (!cancelled) setAeMeterRequestsLoading(false);
      }
    }

    void loadAEMeterRequests();
    return () => { cancelled = true; };
  }, [isAE, user, loading, error, refreshKey]);

  useEffect(() => {
    if (!isAE || loading || error || !user) return;
    let cancelled = false;

    async function loadReadingWarnings() {
      setReadingWarningsLoading(true);
      setReadingWarningsError("");
      try {
        const data = await getAEReadingWarnings();
        if (!cancelled) setReadingWarnings(data);
      } catch (err) {
        if (!cancelled) {
          setReadingWarnings(null);
          setReadingWarningsError(
            err instanceof Error ? err.message : "Unable to load reading warnings."
          );
        }
      } finally {
        if (!cancelled) setReadingWarningsLoading(false);
      }
    }

    void loadReadingWarnings();
    return () => { cancelled = true; };
  }, [isAE, user, loading, error, refreshKey]);
  useEffect(() => {
    if (!isAE || loading || error || !user) return;

    let cancelled = false;

    async function loadAssignments() {
      setAssignmentsLoading(true);
      setAssignmentsError("");

      try {
        const data = await getAssignments(true);

        if (!Array.isArray(data)) {
          throw new Error("Unexpected assignment response.");
        }

        if (!cancelled) {
          setAssignments(data);
        }
      } catch (err) {
        if (!cancelled) {
          setAssignments([]);
          setAssignmentsError(
            err instanceof Error
              ? err.message
              : "Unable to load assignments."
          );
        }
      } finally {
        if (!cancelled) {
          setAssignmentsLoading(false);
        }
      }
    }

    void loadAssignments();

    return () => {
      cancelled = true;
    };
  }, [isAE, user, loading, error, refreshKey]);
  // The backend scopes each endpoint to the authenticated SAE/team.
  // Separate requests prevent one failing card from hiding healthy cards.
  useEffect(() => {
    if (isAE || loading || error || !user) return;
    let cancelled = false;
    setSaeTeamLoading(true);
    setSaeTeamError("");
    getSAEFieldVisitorSummary()
      .then((data) => {
        if (cancelled) return;
        if (!Number.isSafeInteger(data.total_field_visitors) || data.total_field_visitors < 0 ||
            !Number.isSafeInteger(data.assigned_tubewells) || data.assigned_tubewells < 0) {
          throw new Error("Invalid SAE field visitor summary response.");
        }
        setSaeTeam(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setSaeTeam(null);
          setSaeTeamError(err instanceof Error ? err.message : "Unable to load field visitor statistics.");
        }
      })
      .finally(() => { if (!cancelled) setSaeTeamLoading(false); });
    return () => { cancelled = true; };
  }, [isAE, loading, error, user, refreshKey]);

  useEffect(() => {
    if (isAE || loading || error || !user) return;
    let cancelled = false;
    setSaeActivityLoading(true);
    setSaeActivityError("");
    getSAEReadingActivity()
      .then((data) => {
        if (cancelled) return;
        if (![data.overdue_tubewells, data.energy_overdue, data.prepaid_overdue].every(
          (count) => Number.isSafeInteger(count) && count >= 0
        )) {
          throw new Error("Invalid SAE reading warning response.");
        }
        setSaeActivity(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setSaeActivity(null);
          setSaeActivityError(err instanceof Error ? err.message : "Unable to load reading warnings.");
        }
      })
      .finally(() => { if (!cancelled) setSaeActivityLoading(false); });
    return () => { cancelled = true; };
  }, [isAE, loading, error, user, refreshKey]);

  useEffect(() => {
    if (isAE || loading || error || !user) return;
    let cancelled = false;
    setSaePendingLoading(true);
    setSaePendingError("");
    getSAEPendingRequests()
      .then((data) => {
        if (cancelled) return;
        setSaePendingCount(data.length);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setSaePendingCount(null);
          setSaePendingError(err instanceof Error ? err.message : "Unable to load pending reviews.");
        }
      })
      .finally(() => { if (!cancelled) setSaePendingLoading(false); });
    return () => { cancelled = true; };
  }, [isAE, loading, error, user, refreshKey]);

  const filtered = useMemo(() => {
    const q = search.trim().toLocaleLowerCase();
    return tubewells.filter((item) => {
      if (!isAE && saeTubewellStatus !== "all" &&
          item.is_active !== (saeTubewellStatus === "active")) {
        return false;
      }
      return !q ||
        [item.tubewell_number, item.name, item.actual_upazila, item.union_name, item.mouza]
          .some((value) => String(value ?? "").toLocaleLowerCase().includes(q));
    });
  }, [tubewells, search, isAE, saeTubewellStatus]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const visible = filtered.slice((safePage - 1) * pageSize, safePage * pageSize);
  const assignmentCoverage = useMemo(() => {
    if (!isAE || tubewellsLoading || assignmentsLoading ||
        tubewellsError || assignmentsError) {
      return null;
    }

    return calculateAEAssignmentCoverage(
      tubewells.map((item) => item.id),
      assignments
    );
  }, [
    isAE,
    tubewells,
    assignments,
    tubewellsLoading,
    assignmentsLoading,
    tubewellsError,
    assignmentsError,
  ]);
  // Never infer a missing meter type from the meter number or request ID.
  const typedMeterRequests = aeMeterRequests.filter(
    (request) => request.meter_type === activeMeterType
  );
  const unclassifiedMeterRequests = aeMeterRequests.filter(
    (request) => request.meter_type !== "energy" && request.meter_type !== "prepaid"
  );
  const energyMeterCount = aeMeterRequests.filter((request) => request.meter_type === "energy").length;
  const prepaidMeterCount = aeMeterRequests.filter((request) => request.meter_type === "prepaid").length;

  const activeTubewells = tubewells.filter((item) => item.is_active).length;
  const inactiveTubewells = tubewells.length - activeTubewells;

  async function openMeterReplacementDetail(requestId: number) {
    setMeterRequestDetailLoading(true);
    setMeterReviewMessage("");
    setMeterReviewComment("");
    try {
      const detail = await getAEMeterReplacementDetail(requestId);
      if (detail.meter_type !== "energy" && detail.meter_type !== "prepaid") {
        setSelectedMeterRequest(null);
        setMeterReviewMessage("Meter type is not available from the backend. Final review is blocked until it is verified.");
        return;
      }
      if (detail.meter_type !== activeMeterType) {
        setSelectedMeterRequest(null);
        setMeterReviewMessage("Request meter type does not match the selected tab. Review was blocked.");
        return;
      }
      setSelectedMeterRequest(detail);
    } catch (err) {
      setMeterReviewMessage(
        err instanceof Error ? err.message : "Unable to load request details."
      );
    } finally {
      setMeterRequestDetailLoading(false);
    }
  }

  async function submitMeterReplacementReview(action: "approved" | "rejected") {
    if (!selectedMeterRequest || meterReviewBusy) return;
    if (selectedMeterRequest.meter_type !== activeMeterType) {
      setMeterReviewMessage("Meter type mismatch. Final approval is blocked.");
      return;
    }
    const actionLabel = action === "approved" ? "approve" : "reject";
    if (!window.confirm(`Are you sure you want to ${actionLabel} this meter replacement request?`)) return;

    setMeterReviewBusy(true);
    setMeterReviewMessage("");
    try {
      await reviewAEMeterReplacement(
        selectedMeterRequest.id,
        action,
        meterReviewComment.trim() || undefined
      );
      setMeterReviewMessage(
        action === "approved"
          ? "Meter replacement approved. The new meter has been created."
          : "Meter replacement rejected. Meter records remain unchanged."
      );
      setSelectedMeterRequest(null);
      setMeterReviewComment("");
      const updated = await getAEPendingMeterReplacements();
      setAeMeterRequests(updated);
      setRefreshKey((value) => value + 1);
    } catch (err) {
      setMeterReviewMessage(
        err instanceof Error ? err.message : "Unable to submit final review."
      );
    } finally {
      setMeterReviewBusy(false);
    }
  }

  function logout() {
    removeAccessToken();
    navigate("/login", { replace: true });
  }
  function goToSection(id: string) {
    if (isAE && id === "assignments") {
      setMenuOpen(false);
      navigate("/ae/assignments");
      return;
    }
    setActive(id);
    if (!isAE) setSaeSection(saeSections[id]?.[0]?.id ?? "summary");
    setMenuOpen(false);
    if (isAE) {
      document.getElementById(`bmda-role-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  if (loading) return <main className="bmda-role-state" role="status">Loading your workspace...</main>;
  if (error || !user) return <main className="bmda-role-state" role="alert">{error || "Unable to load your account."}</main>;

  const selectedSaeSection = saeSections[active]?.find((section) => section.id === saeSection);

  const tasks = isAE
    ? ["Monitor tubewells within your management unit", "Coordinate Sub-Assistant Engineers and field visitors", "Review eligible requests after authorization is enabled", "Review readings, warnings and reports"]
    : ["Coordinate your assigned field visitors", "Monitor assigned field activities and readings", "Review requests from your own field visitors", "Follow up on missing readings and warnings"];

  return (
    <div className={`bmda-role-shell ${isAE ? "" : "bmda-sae-theme"}`} data-sae-view={isAE ? undefined : active}>
      <button className="bmda-role-mobile-toggle" type="button" aria-controls="bmda-role-sidebar" aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}>
        {menuOpen ? "✕ Close navigation" : "☰ Open navigation"}
      </button>
      {menuOpen && <button type="button" className="bmda-role-overlay" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
      <aside id="bmda-role-sidebar" className={`bmda-role-sidebar ${menuOpen ? "is-open" : ""}`} aria-label={`${roleTitle} navigation`}>
        <div className="bmda-role-brand">
          <img src={bmdaLogo} alt="BMDA logo" />
          <div><strong>BMDA PANCHAGARH</strong><span>Deep Tubewell Management</span></div>
        </div>
        <div className="bmda-role-side-heading">{roleTitle} Workspace</div>
        <nav aria-label="Workspace sections">
          {menus[role].map(([id, label, symbol]) => (
            <button key={id} type="button" className={`bmda-role-nav-item ${active === id ? "active" : ""}`} aria-current={active === id ? "page" : undefined} onClick={() => goToSection(id)}>
              <span aria-hidden="true">{symbol}</span>{label}
            </button>
          ))}
        </nav>
        <div className="bmda-role-sidebar-bottom">
          <div className="bmda-role-side-user"><strong>{user.full_name}</strong><span>{roleTitle}</span></div>
          <button className="bmda-role-signout" type="button" onClick={logout}>↪ Sign out</button>
        </div>
      </aside>
      <main className="bmda-role-main">
        <header className="bmda-role-topbar"><span>BMDA / {roleTitle} / Dashboard</span><span className="bmda-role-topbar-chip">● Signed in</span></header>
        <div className="bmda-role-content">
          {!isAE && (
            <nav className="bmda-sae-top-tabs" aria-label="Field operations work areas">
              {[
                { id: "overview", label: "Overview" },
                { id: "responsibilities", label: "Field Operations" },
                { id: "tubewells", label: "Tubewells" },
                { id: "workflow", label: "Review Workflow" },
                { id: "approvals", label: "Approval Requests" },
                { id: "account", label: "My Profile" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  className={`bmda-sae-tab ${active === tab.id ? "is-active" : ""}`}
                  aria-current={active === tab.id ? "page" : undefined}
                  onClick={() => goToSection(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          )}
          {!isAE && (
            <div className="bmda-sae-section-picker" role="group" aria-label="Choose a section within the selected work area">
              <div className="bmda-sae-section-picker-copy">
                <span className="bmda-sae-section-picker-eyebrow">SECTION NAVIGATION</span>
                <strong>{menus.supervisor.find(([id]) => id === active)?.[1] ?? "Workspace"}</strong>
                <small>{selectedSaeSection?.detail ?? "Choose a section to view"}</small>
              </div>
              <label className="bmda-sae-section-select-label">
                <span>Go to section</span>
                <select aria-label="Select section in current tab" value={saeSection} onChange={(event) => setSaeSection(event.target.value)}>
                  {(saeSections[active] ?? []).map((section) => (
                    <option key={section.id} value={section.id}>{section.label}</option>
                  ))}
                </select>
              </label>
            </div>
          )}
          <section id="bmda-role-overview" className="bmda-role-hero" hidden={!isAE && saeSection !== "welcome"}>
            <div><p className="bmda-role-eyebrow">{roleTitle} Dashboard</p><h1>Welcome, {user.full_name}</h1><p>Your workspace for day-to-day BMDA responsibilities.</p></div>
            <div className="bmda-role-unit"><span>Management Unit</span><strong>{unitName}</strong></div>
          </section>
          <section className="bmda-role-section" aria-label="Workspace status" hidden={!isAE && saeSection !== "summary"}>
            <div className="bmda-role-section-heading"><h2>Workspace overview</h2><p>{isAE ? "AE dashboard statistics use authorized management-unit APIs for tubewells, personnel, pending approvals, assignments and reading warnings." : "Your field operations workspace for assigned tubewells, field visitors, pending reviews and reading follow-ups."}</p></div>
            {!isAE && (
              <button
                type="button"
                onClick={() => setRefreshKey((value) => value + 1)}
                disabled={saeTeamLoading || saePendingLoading || saeActivityLoading}
                style={{ marginBottom: 14, padding: "9px 14px", border: "1px solid #b9d7cc", borderRadius: 9, background: "#fff", color: "#165c4b", fontWeight: 700, cursor: "pointer" }}
              >
                Refresh overview
              </button>
            )}
            <div className="bmda-role-cards bmda-role-cards-premium">
              {(isAE
                ? ["Unit Tubewells", "Field Personnel", "Pending Requests", "Reading Warnings"]
                : ["Assigned Field Visitors", "Assigned Tubewells", "Pending Reviews", "Reading Warnings"]
              ).map((name, i) => {
                const isTubewellCard = isAE ? i === 0 : i === 1;
                const isPersonnelCard = isAE && i === 1;
                const isAEPendingCard = isAE && i === 2;
                const isAEReadingCard = isAE && i === 3;

                const personnelTotal = personnel
                  ? personnel.sub_assistant_engineers.total + personnel.field_visitors.total
                  : null;

                const value = !isAE
                  ? i === 0
                    ? (saeTeamLoading ? "Loading..." : saeTeamError || !saeTeam ? "Unavailable" : saeTeam.total_field_visitors)
                    : i === 1
                      ? (saeTeamLoading ? "Loading..." : saeTeamError || !saeTeam ? "Unavailable" : saeTeam.assigned_tubewells)
                      : i === 2
                        ? (saePendingLoading ? "Loading..." : saePendingError || saePendingCount === null ? "Unavailable" : saePendingCount)
                        : (saeActivityLoading ? "Loading..." : saeActivityError || !saeActivity ? "Unavailable" : saeActivity.overdue_tubewells)
                  : isTubewellCard
                    ? (tubewellsLoading ? "Loading..." : tubewellsError ? "Unavailable" : tubewells.length)
                    : isPersonnelCard
                      ? (personnelLoading ? "Loading..." : personnelError || personnelTotal === null ? "Unavailable" : personnelTotal)
                      : isAEPendingCard
                        ? ((aePendingLoading || aeMeterRequestsLoading) ? "Loading..." : (aePendingError || aeMeterRequestsError || aePendingCount === null) ? "Unavailable" : aePendingCount + aeMeterRequests.length)
                        : isAEReadingCard
                          ? (readingWarningsLoading ? "Loading..." : readingWarningsError || !readingWarnings ? "Unavailable" : readingWarnings.overdue_tubewells)
                          : "—";

                const icons = ["◫", "♙", "✓", "!"];

                return (
                  <article className="bmda-role-premium-card" key={name}>
                    <div className="bmda-role-premium-top">
                      <span className="bmda-role-premium-icon" aria-hidden="true">{icons[i]}</span>
                      <span className="bmda-role-premium-indicator">
                        LIVE
                      </span>
                    </div>

                    <div className="bmda-role-premium-number">{value}</div>
                    <h3 className="bmda-role-premium-title">{name}</h3>

                    {isPersonnelCard && !personnelLoading && !personnelError && personnel ? (
                      <div className="bmda-role-premium-personnel">
                        <span>Sub-Assistant Engineers: <strong>{personnel.sub_assistant_engineers.total}</strong> (Active {personnel.sub_assistant_engineers.active}, Inactive {personnel.sub_assistant_engineers.inactive})</span>
                        <span>Field Visitors: <strong>{personnel.field_visitors.total}</strong> (Active {personnel.field_visitors.active}, Inactive {personnel.field_visitors.inactive})</span>
                      </div>
                    ) : isAEReadingCard && !readingWarningsLoading && !readingWarningsError && readingWarnings ? (
                      <div className="bmda-role-premium-reading">
                        <div><span>Energy</span><strong>{readingWarnings.energy_warnings}</strong></div>
                        <div><span>Prepaid</span><strong>{readingWarnings.prepaid_warnings}</strong></div>
                        <div><span>Not started</span><strong>{readingWarnings.reading_not_started}</strong></div>
                        <p>{readingWarnings.warning_threshold_days}-day warning threshold</p>
                      </div>
                    ) : !isAE && i === 0 && !saeTeamLoading && !saeTeamError && saeTeam ? (
                      <div className="bmda-role-premium-personnel">
                        <span>Active: <strong>{saeTeam.active_field_visitors}</strong></span>
                        <span>Inactive: <strong>{saeTeam.inactive_field_visitors}</strong></span>
                      </div>
                    ) : !isAE && i === 3 && !saeActivityLoading && !saeActivityError && saeActivity ? (
                      <div className="bmda-role-premium-reading">
                        <div><span>Energy</span><strong>{saeActivity.energy_overdue}</strong></div>
                        <div><span>Prepaid</span><strong>{saeActivity.prepaid_overdue}</strong></div>
                        <p>{saeActivity.warning_threshold_days}-day warning threshold · distinct tubewells</p>
                      </div>
                    ) : (
                      <p className="bmda-role-premium-description">
                        {!isAE
                          ? i === 0
                            ? (saeTeamError ? "Unable to load assigned field visitors" : "Field visitors under your supervision")
                            : i === 1
                              ? (saeTeamError ? "Unable to load team assignments" : "Currently assigned tubewells in your field team")
                              : i === 2
                                ? (saePendingError ? "Unable to load pending reviews" : "Requests awaiting your review")
                                : (saeActivityError ? "Unable to load reading warnings" : "Overdue Energy / Prepaid readings in your team")
                          : isTubewellCard
                            ? (tubewellsError ? "Unable to load authorized tubewells" : "Registered within authorized scope")
                            : isPersonnelCard
                              ? (personnelError ? "Unable to load personnel" : "Authorized personnel summary")
                              : isAEPendingCard
                                ? (aePendingError ? "Unable to load approval queue" : "Tubewell status and meter replacement requests awaiting AE approval")
                                : isAEReadingCard
                                  ? (readingWarningsError ? "Unable to load reading warnings" : "Authorized reading warning summary")
                                  : "Verified data integration pending"}
                      </p>
                    )}
                    {!isAE && (
                      <button
                        type="button"
                        aria-label={`Open ${[
                          "Field Visitor Monitoring",
                          "Field Visitor-wise Assignments",
                          "Approval Requests",
                          "Reading Activity Monitoring",
                        ][i]}`}
                        onClick={() => {
                          const target = [
                            { tab: "responsibilities", section: "visitors" },
                            { tab: "tubewells", section: "assignments" },
                            { tab: "approvals", section: "requests" },
                            { tab: "responsibilities", section: "readings" },
                          ][i];
                          if (!target) return;
                          goToSection(target.tab);
                          setSaeSection(target.section);
                        }}
                        style={{
                          alignSelf: "flex-start",
                          marginTop: 14,
                          padding: "10px 13px",
                          border: "1px solid #bcded8",
                          borderRadius: 10,
                          background: "#f0faf7",
                          color: "#087562",
                          font: "inherit",
                          fontSize: 13,
                          fontWeight: 700,
                          cursor: "pointer",
                        }}
                      >
                        {[
                          "View field visitors",
                          "View assignments",
                          "Review requests",
                          "View reading activity",
                        ][i]} ↗
                      </button>
                    )}
                  </article>
                );
              })}
            </div>
          </section>
          {!isAE && saeSection === "summary" && (
            <SAERecentActivity
              data={saeActivity}
              loading={saeActivityLoading}
              error={saeActivityError}
              onViewAll={() => {
                goToSection("responsibilities");
                setSaeSection("readings");
              }}
            />
          )}
          {isAE && (
            <section
              className="bmda-role-section bmda-role-panel"
              aria-label="Tubewell Assignment Coverage"
            >
              <div className="bmda-role-section-heading">
                <h2>Tubewell Assignment Coverage</h2>
                <p>
                  Current Field Visitor assignment coverage within
                  your authorized management unit.
                </p>
              </div>

              <div className="bmda-role-cards">
                {[
                  ["Total Tubewells", assignmentCoverage?.total],
                  ["Assigned", assignmentCoverage?.assigned],
                  ["Unassigned", assignmentCoverage?.unassigned],
                  [
                    "Coverage",
                    assignmentCoverage
                      ? `${assignmentCoverage.coveragePercentage}%`
                      : null,
                  ],
                ].map(([label, value]) => (
                  <div className="bmda-role-stat" key={String(label)}>
                    <span>{label}</span>
                    <strong>
                      {tubewellsLoading || assignmentsLoading
                        ? "Loading..."
                        : value ?? "Unavailable"}
                    </strong>
                  </div>
                ))}
              </div>

              {(tubewellsError || assignmentsError) && (
                <p role="alert">
                  Assignment coverage could not be loaded.
                </p>
              )}
            </section>
          )}
          {isAE && (
            <AEFieldUserCoverage refreshKey={refreshKey} />
          )}
          {!isAE && (
            <section
              className="bmda-role-section bmda-role-panel bmda-sae-quick-actions"
              aria-label="Field operations quick actions"
              hidden={saeSection !== "quick"}
            >
              <div className="bmda-role-section-heading">
                <h2>Field Operations — Quick Access</h2>
                <p>Jump directly to the work areas available in your dashboard.</p>
              </div>
              <div className="bmda-sae-quick-grid">
                {[
                  { id: "tubewells", icon: "◫", title: "Tubewell List", desc: "Find and review tubewells" },
                  { id: "approvals", icon: "✓", title: "Approval Requests", desc: "Open your request review area" },
                  { id: "workflow", icon: "≡", title: "Review Workflow", desc: "Access the review workflow" },
                  { id: "account", icon: "●", title: "My Profile", desc: "View your account information" },
                ].map((action) => (
                  <button
                    key={action.id}
                    type="button"
                    className="bmda-sae-quick-action"
                    onClick={() => goToSection(action.id)}
                  >
                    <span className="bmda-sae-quick-icon" aria-hidden="true">
                      {action.icon}
                    </span>
                    <span className="bmda-sae-quick-copy">
                      <strong>{action.title}</strong>
                      <small>{action.desc}</small>
                    </span>
                    <span className="bmda-sae-quick-chevron" aria-hidden="true">›</span>
                  </button>
                ))}
              </div>
            </section>
          )}
          <section id="bmda-role-responsibilities" className="bmda-role-section bmda-role-panel">
            <div className="bmda-role-section-heading"><h2>{isAE ? "Management scope" : "Field operations"}</h2><p>{isAE ? "Responsibilities within your assigned management unit." : "Responsibilities within your authorized team."}</p></div>
            {!isAE && <div hidden={saeSection !== "visitors"}><SAEFieldVisitorMonitoring /></div>}
            <div hidden={!isAE && saeSection !== "duties"}>
              <ul className="bmda-role-task-list">{tasks.map((task) => <li key={task}><span aria-hidden="true">✓</span>{task}</li>)}</ul>
            </div>
            {!isAE && <div hidden={saeSection !== "readings"}><SAEReadingActivityMonitoring /></div>}
          </section>

          {/* Read-only tubewell list; server enforces the role scope. */}
          <section id="bmda-role-tubewells" className="bmda-role-section bmda-role-panel">
            {!isAE && <div hidden={saeSection !== "assignments"}><SAETubewellAssignmentMonitoring /></div>}
            <div hidden={!isAE && saeSection !== "list"}>
            <div className="bmda-role-section-heading">
              <h2>Tubewell List</h2>
              <p>{isAE ? "Tubewells within your authorized management unit." : "Tubewells assigned within your authorized field team."}</p>
            </div>
            <div className="bmda-role-cards" style={{ marginBottom: 18 }}>
              <div className="bmda-role-stat"><span>Total Tubewells</span><strong>{tubewellsLoading ? "..." : tubewellsError ? "—" : tubewells.length}</strong></div>
              <div className="bmda-role-stat"><span>Active Tubewells</span><strong>{tubewellsLoading ? "..." : tubewellsError ? "—" : activeTubewells}</strong></div>
              <div className="bmda-role-stat"><span>Inactive Tubewells</span><strong>{tubewellsLoading ? "..." : tubewellsError ? "—" : inactiveTubewells}</strong></div>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center", marginBottom: 16 }}>
              <input
                type="search" aria-label="Search tubewells" placeholder="Search number, name, upazila, union or mouza"
                value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }}
                style={{ flex: "1 1 270px", minWidth: 0, padding: "11px 12px", border: "1px solid #cfe3d3", borderRadius: 9, background: "#fff", color: "#183c2b" }}
              />
              {!isAE && (
                <label style={{ display: "flex", gap: 7, alignItems: "center", fontSize: 13 }}>
                  Status
                  <select
                    aria-label="Filter tubewells by status"
                    value={saeTubewellStatus}
                    onChange={(event) => {
                      setSaeTubewellStatus(event.target.value as "all" | "active" | "inactive");
                      setPage(1);
                    }}
                    style={{ padding: "10px", border: "1px solid #cfe3d3", borderRadius: 9, background: "#fff", color: "#183c2b" }}
                  >
                    <option value="all">All tubewells</option>
                    <option value="active">Active only</option>
                    <option value="inactive">Inactive only</option>
                  </select>
                </label>
              )}
              <label style={{ display: "flex", gap: 7, alignItems: "center", fontSize: 13 }}>
                Rows
                <select aria-label="Rows per page" value={pageSize} onChange={(event) => { setPageSize(Number(event.target.value)); setPage(1); }} style={{ padding: "10px", border: "1px solid #cfe3d3", borderRadius: 9, background: "#fff", color: "#183c2b" }}>
                  {pageSizes.map((size) => <option key={size} value={size}>{size}</option>)}
                </select>
              </label>
              <button type="button" disabled={tubewellsLoading} onClick={() => setRefreshKey((value) => value + 1)} style={{ padding: "11px 15px", border: "1px solid #167c43", borderRadius: 9, color: "#176d3e", background: "#fff", fontWeight: 700, cursor: tubewellsLoading ? "not-allowed" : "pointer" }}>
                {tubewellsLoading ? "Loading..." : "Refresh Tubewells"}
              </button>
            </div>
            {tubewellsLoading && <p role="status">Loading tubewell information...</p>}
            {tubewellsError && <p role="alert" style={{ color: "#b42318" }}>{tubewellsError}</p>}
            {!tubewellsLoading && !tubewellsError && (
              <>
                <div style={{ width: "100%", overflowX: "auto", border: "1px solid #dcece0", borderRadius: 12 }}>
                  <table style={{ width: "100%", minWidth: 800, borderCollapse: "collapse", fontSize: 13, color: "#254c34" }}>
                    <thead style={{ background: "#e8f5eb", color: "#205437" }}>
                      <tr>{["SL", "DTW Number", "Name", "Upazila", "Union", "Mouza", "Status"].map((head) => <th key={head} scope="col" style={{ ...cellStyle, fontWeight: 750 }}>{head}</th>)}</tr>
                    </thead>
                    <tbody>
                      {visible.map((item, index) => (
                        <tr key={item.id} style={{ background: index % 2 === 0 ? "#fff" : "#f7fbf8" }}>
                          <td style={cellStyle}>{(safePage - 1) * pageSize + index + 1}</td>
                          <td style={{ ...cellStyle, fontWeight: 700 }}>{item.tubewell_number || "—"}</td>
                          <td style={cellStyle}>{item.name || "—"}</td>
                          <td style={cellStyle}>{item.actual_upazila || "—"}</td>
                          <td style={cellStyle}>{item.union_name || "—"}</td>
                          <td style={cellStyle}>{item.mouza || "—"}</td>
                          <td style={cellStyle}><span style={{ color: item.is_active ? "#176d3e" : "#b42318", fontWeight: 700 }}>{item.is_active ? "Active" : "Inactive"}</span></td>
                        </tr>
                      ))}
                      {visible.length === 0 && <tr><td colSpan={7} style={{ padding: 22, textAlign: "center" }}>{tubewells.length === 0 ? "No tubewells found within your authorized scope." : "No tubewells match your search."}</td></tr>}
                    </tbody>
                  </table>
                </div>
                <div style={{ marginTop: 14, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12, fontSize: 13 }}>
                  <span>Showing {filtered.length === 0 ? 0 : (safePage - 1) * pageSize + 1}–{Math.min(safePage * pageSize, filtered.length)} of {filtered.length}</span>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <button type="button" disabled={safePage <= 1} onClick={() => setPage(safePage - 1)} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #cfe3d3", background: "#fff", color: "#176d3e", cursor: safePage <= 1 ? "not-allowed" : "pointer" }}>Previous</button>
                    <span>Page {safePage} of {totalPages}</span>
                    <button type="button" disabled={safePage >= totalPages} onClick={() => setPage(safePage + 1)} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #cfe3d3", background: "#fff", color: "#176d3e", cursor: safePage >= totalPages ? "not-allowed" : "pointer" }}>Next</button>
                  </div>
                </div>
              </>
            )}
            </div>
          </section>

          <section id="bmda-role-workflow" className="bmda-role-section bmda-role-panel">
            <div className="bmda-role-section-heading"><h2>{isAE ? "Approval workflow" : "Review workflow"}</h2><p>{isAE ? "Review authorized approval requests within your management unit. Meter replacement requests are handled separately by meter type." : "Review Reading Corrections with final SAE authority. Recommend Meter Replacement and Tubewell Status requests for AE final authorization."}</p></div>
            <div className="bmda-role-notice"><strong>{isAE ? "Final Approval Workflow" : "Sub-Assistant Engineer Review Workflow"}</strong><p>{isAE ? "Review requests forwarded by Sub-Assistant Engineers. Final approval applies the authorized change." : "Review requests from your assigned Field Visitors. SAE decides Reading Corrections; Meter Replacement and Tubewell Status require AE final authorization."}</p></div>
          </section>
          {isAE && (
            <section id="bmda-role-meter-replacements" className="bmda-role-section bmda-role-panel">
              <div className="bmda-role-section-heading">
                <h2>Meter Replacement — Final Approval</h2>
                <p>Review meter replacement requests recommended by Sub-Assistant Engineers. A new meter is created only after your final approval.</p>
              </div>
              <div className="bmda-role-cards" style={{ marginBottom: 18 }}>
                <div className="bmda-role-stat">
                  <span>Awaiting AE Approval</span>
                  <strong>{aeMeterRequestsLoading ? "Loading..." : aeMeterRequestsError ? "Unavailable" : aeMeterRequests.length}</strong>
                </div>
                <div className="bmda-role-stat">
                  <span>Approval authority</span>
                  <strong>Assistant Engineer</strong>
                </div>
              </div>
              <div className="bmda-meter-type-tabs" role="group" aria-label="Meter replacement type">
                <button type="button" className={activeMeterType === "energy" ? "is-active" : ""} aria-pressed={activeMeterType === "energy"} onClick={() => { setActiveMeterType("energy"); setSelectedMeterRequest(null); setMeterReviewMessage(""); }}>
                  Energy Meter <span>{aeMeterRequestsLoading ? "…" : aeMeterRequestsError ? "—" : energyMeterCount}</span>
                </button>
                <button type="button" className={activeMeterType === "prepaid" ? "is-active" : ""} aria-pressed={activeMeterType === "prepaid"} onClick={() => { setActiveMeterType("prepaid"); setSelectedMeterRequest(null); setMeterReviewMessage(""); }}>
                  Prepaid Meter <span>{aeMeterRequestsLoading ? "…" : aeMeterRequestsError ? "—" : prepaidMeterCount}</span>
                </button>
              </div>
              {!aeMeterRequestsLoading && !aeMeterRequestsError && unclassifiedMeterRequests.length > 0 && (
                <p role="alert" className="bmda-meter-type-warning">
                  {unclassifiedMeterRequests.length} request(s) have no verified Energy/Prepaid type in the API response. They are excluded from both tabs and cannot be approved here until the backend provides meter_type.
                </p>
              )}
              {aeMeterRequestsError && <p role="alert" style={{ color: "#b42318" }}>{aeMeterRequestsError}</p>}
              {meterReviewMessage && <p role="status" style={{ color: meterReviewMessage.toLowerCase().includes("unable") ? "#b42318" : "#176d3e", background: "#f2faf4", borderRadius: 9, padding: 12 }}>{meterReviewMessage}</p>}
              {aeMeterRequestsLoading ? (
                <p role="status">Loading SAE-recommended meter replacement requests...</p>
              ) : !aeMeterRequestsError && typedMeterRequests.length === 0 ? (
                <div className="bmda-role-notice"><strong>No pending {activeMeterType === "energy" ? "Energy" : "Prepaid"} Meter approvals</strong><p>Only requests with a verified meter type appear in this tab.</p></div>
              ) : (
                <div style={{ display: "grid", gap: 12 }}>
                  {typedMeterRequests.map((request) => (
                    <article key={request.id} style={{ border: "1px solid #dcece0", borderRadius: 12, padding: 16, background: "#fbfefc" }}>
                      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 10, alignItems: "center" }}>
                        <div>
                          <strong style={{ color: "#174b2e" }}>{request.meter_type === "energy" ? "Energy" : "Prepaid"} · Request #{request.id} · Tubewell #{request.tubewell_id}</strong>
                          <p style={{ margin: "6px 0 0", color: "#607966", fontSize: 13 }}>New meter: {request.new_meter_number} · Old meter ID: {request.old_meter_id}</p>
                        </div>
                        <button type="button" onClick={() => void openMeterReplacementDetail(request.id)} disabled={meterRequestDetailLoading || meterReviewBusy} style={{ padding: "9px 13px", border: "1px solid #167c43", borderRadius: 8, background: "#fff", color: "#176d3e", fontWeight: 700, cursor: "pointer" }}>Review details</button>
                      </div>
                      <p style={{ margin: "10px 0 0", color: "#526f5b", fontSize: 13 }}><strong>Reason:</strong> {request.reason}</p>
                      <p style={{ margin: "7px 0 0", color: "#526f5b", fontSize: 12 }}><strong>SAE recommendation:</strong> {request.review_comment || "No recommendation comment supplied."}</p>
                    </article>
                  ))}
                </div>
              )}
              {meterRequestDetailLoading && <p role="status">Loading request details...</p>}
              {selectedMeterRequest && (
                <div style={{ marginTop: 18, border: "1px solid #b9dcc4", borderRadius: 14, padding: 18, background: "#f5fbf6" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                    <h3 style={{ margin: 0, color: "#174b2e" }}>Final review · Request #{selectedMeterRequest.id}</h3>
                    <button type="button" onClick={() => setSelectedMeterRequest(null)} style={{ border: 0, background: "transparent", color: "#52705d", cursor: "pointer" }}>Close</button>
                  </div>
                  <dl className="bmda-role-profile" style={{ marginTop: 14 }}>
                    <div><dt>Meter Type</dt><dd>{selectedMeterRequest.meter_type === "energy" ? "Energy" : "Prepaid"}</dd></div>
                    <div><dt>Tubewell ID</dt><dd>{selectedMeterRequest.tubewell_id}</dd></div>
                    <div><dt>Old Meter ID</dt><dd>{selectedMeterRequest.old_meter_id}</dd></div>
                    <div><dt>Proposed New Meter</dt><dd>{selectedMeterRequest.new_meter_number}</dd></div>
                    <div><dt>Requested by Field Visitor ID</dt><dd>{selectedMeterRequest.requested_by_user_id}</dd></div>
                    <div><dt>Request Date</dt><dd>{new Date(selectedMeterRequest.requested_at).toLocaleString()}</dd></div>
                    <div><dt>SAE Reviewed</dt><dd>{selectedMeterRequest.reviewed_at ? new Date(selectedMeterRequest.reviewed_at).toLocaleString() : "—"}</dd></div>
                  </dl>
                  <div className="bmda-role-notice" style={{ marginTop: 14 }}>
                    <strong>Replacement reason</strong><p>{selectedMeterRequest.reason}</p>
                    <strong>SAE recommendation</strong><p>{selectedMeterRequest.review_comment || "No recommendation comment supplied."}</p>
                  </div>
                  <label style={{ display: "block", marginTop: 16, color: "#315a3e", fontSize: 13, fontWeight: 700 }}>
                    AE review comment (optional)
                    <textarea value={meterReviewComment} onChange={(event) => setMeterReviewComment(event.target.value)} maxLength={500} rows={3} placeholder="Add your final review comment..." style={{ display: "block", width: "100%", marginTop: 7, padding: 11, border: "1px solid #cfe3d3", borderRadius: 9, resize: "vertical", font: "inherit" }} />
                  </label>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 14 }}>
                    <button type="button" disabled={meterReviewBusy} onClick={() => void submitMeterReplacementReview("approved")} style={{ padding: "11px 17px", border: 0, borderRadius: 9, background: "#167c43", color: "#fff", fontWeight: 750, cursor: meterReviewBusy ? "wait" : "pointer" }}>{meterReviewBusy ? "Submitting..." : "Final Approve"}</button>
                    <button type="button" disabled={meterReviewBusy} onClick={() => void submitMeterReplacementReview("rejected")} style={{ padding: "11px 17px", border: "1px solid #b42318", borderRadius: 9, background: "#fff", color: "#b42318", fontWeight: 750, cursor: meterReviewBusy ? "wait" : "pointer" }}>Reject</button>
                  </div>
                  <p style={{ margin: "12px 0 0", color: "#718a78", fontSize: 11, lineHeight: 1.5 }}>Final approval creates the replacement meter and closes the old meter. Rejection leaves meter records unchanged.</p>
                </div>
              )}
            </section>
          )}

          <section id="bmda-role-approvals" className="bmda-role-section bmda-role-panel">
            <div className="bmda-role-section-heading"><h2>Approval Requests</h2><p>Review pending requests within your authorized management scope.</p></div>
            <div className="bmda-role-inline-approvals"><ApprovalPage role={isAE ? "assistant_engineer" : "supervisor"} inline /></div>
          </section>
          <section id="bmda-role-account" className="bmda-role-section bmda-role-panel">
            <div className="bmda-role-section-heading"><h2>My profile</h2><p>Account information from your authenticated session.</p></div>
            <dl className="bmda-role-profile"><div><dt>Officer</dt><dd>{user.full_name}</dd></div><div><dt>Role</dt><dd>{roleTitle}</dd></div><div><dt>Management Unit</dt><dd>{unitName}</dd></div></dl>
          </section>
          <footer className="bmda-role-footer">BMDA Panchagarh · Deep Tubewell Management System</footer>
        </div>
      </main>
    </div>
  );
}



