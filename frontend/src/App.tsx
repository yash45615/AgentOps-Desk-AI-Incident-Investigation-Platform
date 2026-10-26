import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Clock3,
  Code2,
  FileText,
  LoaderCircle,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Terminal,
  X,
  Zap,
} from "lucide-react";

import {
  api,
  type Evidence,
  type EvidenceType,
  type Incident,
  type IncidentInput,
  type IncidentStatus,
  type Investigation,
  type Severity,
} from "./api/client";

type Notice = { kind: "success" | "error"; message: string };

const severityOptions: Severity[] = ["low", "medium", "high", "critical"];

const statusOptions: IncidentStatus[] = [
  "open",
  "investigating",
  "resolved",
  "closed",
];

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }

  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function titleCase(value: string) {
  return value.replaceAll("_", " ");
}

function App() {
  // Prevent older API responses from overwriting newer UI state.
  const incidentRequestId = useRef(0);
  const detailRequestId = useRef(0);

  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [activeInvestigation, setActiveInvestigation] =
    useState<Investigation | null>(null);

  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [working, setWorking] = useState(false);

  const [showIncidentForm, setShowIncidentForm] = useState(false);
  const [showEvidenceForm, setShowEvidenceForm] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);

  const selectedIncident =
    incidents.find((incident) => incident.id === selectedId) ?? null;

  const loadIncidents = useCallback(async () => {
    const requestId = ++incidentRequestId.current;

    setLoading(true);

    try {
      const result = await api.listIncidents(search);

      // Ignore stale responses from previous searches or refreshes.
      if (requestId !== incidentRequestId.current) {
        return;
      }

      setIncidents(result.items);

      setSelectedId((current) => {
        if (current && result.items.some((item) => item.id === current)) {
          return current;
        }

        return result.items[0]?.id ?? "";
      });
    } catch (error) {
      if (requestId !== incidentRequestId.current) {
        return;
      }

      setNotice({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not load incidents.",
      });
    } finally {
      if (requestId === incidentRequestId.current) {
        setLoading(false);
      }
    }
  }, [search]);

  const loadDetails = useCallback(async (incidentId: string) => {
    const requestId = ++detailRequestId.current;

    if (!incidentId) {
      setEvidence([]);
      setInvestigations([]);
      setActiveInvestigation(null);
      setDetailLoading(false);
      return;
    }

    setDetailLoading(true);

    try {
      const [evidenceResult, investigationResult] = await Promise.all([
        api.listEvidence(incidentId),
        api.listInvestigations(incidentId),
      ]);

      // Ignore results belonging to an incident that is no longer selected.
      if (requestId !== detailRequestId.current) {
        return;
      }

      setEvidence(evidenceResult.items);
      setInvestigations(investigationResult.items);

      setActiveInvestigation((current) => {
        if (
          current &&
          investigationResult.items.some((item) => item.id === current.id)
        ) {
          return (
            investigationResult.items.find(
              (item) => item.id === current.id,
            ) ?? null
          );
        }

        return investigationResult.items[0] ?? null;
      });
    } catch (error) {
      if (requestId !== detailRequestId.current) {
        return;
      }

      setNotice({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not load incident details.",
      });
    } finally {
      if (requestId === detailRequestId.current) {
        setDetailLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void loadIncidents();
  }, [loadIncidents]);

  useEffect(() => {
    void loadDetails(selectedId);
  }, [selectedId, loadDetails]);

  const filteredIncidents = useMemo(
    () =>
      incidents.filter((incident) => {
        const matchesSeverity =
          severityFilter === "all" ||
          incident.severity === severityFilter;

        const matchesStatus =
          statusFilter === "all" ||
          incident.status === statusFilter;

        return matchesSeverity && matchesStatus;
      }),
    [incidents, severityFilter, statusFilter],
  );

  const stats = useMemo(
    () => ({
      total: incidents.length,

      open: incidents.filter(
        (item) =>
          item.status === "open" ||
          item.status === "investigating",
      ).length,

      critical: incidents.filter(
        (item) =>
          item.severity === "critical" &&
          item.status !== "resolved" &&
          item.status !== "closed",
      ).length,

      resolved: incidents.filter(
        (item) => item.status === "resolved",
      ).length,
    }),
    [incidents],
  );

  async function createIncident(input: IncidentInput) {
    setWorking(true);

    try {
      const created = await api.createIncident(input);

      await loadIncidents();

      setSelectedId(created.id);
      setShowIncidentForm(false);

      setNotice({
        kind: "success",
        message: "Incident created.",
      });
    } catch (error) {
      setNotice({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not create incident.",
      });
    } finally {
      setWorking(false);
    }
  }

  async function createEvidence(input: {
    evidence_type: EvidenceType;
    title: string;
    content: string;
    source: string;
  }) {
    if (!selectedId) {
      return;
    }

    const incidentId = selectedId;

    setWorking(true);

    try {
      await api.createEvidence(incidentId, {
        ...input,
        metadata: {},
      });

      await loadDetails(incidentId);

      setShowEvidenceForm(false);

      setNotice({
        kind: "success",
        message: "Evidence added.",
      });
    } catch (error) {
      setNotice({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not add evidence.",
      });
    } finally {
      setWorking(false);
    }
  }

  async function runInvestigation() {
    if (!selectedId) {
      return;
    }

    const incidentId = selectedId;

    setWorking(true);

    try {
      const result = await api.runInvestigation(incidentId);

      await loadDetails(incidentId);

      // Show the investigation that was just created.
      setActiveInvestigation(result);

      setNotice({
        kind: "success",
        message: "Investigation completed.",
      });
    } catch (error) {
      setNotice({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Investigation failed.",
      });
    } finally {
      setWorking(false);
    }
  }

  async function updateStatus(status: IncidentStatus) {
    if (!selectedIncident) {
      return;
    }

    const incidentId = selectedIncident.id;

    setWorking(true);

    try {
      const updated = await api.updateIncident(incidentId, {
        status,
      });

      setIncidents((items) =>
        items.map((item) =>
          item.id === updated.id ? updated : item,
        ),
      );

      setNotice({
        kind: "success",
        message: "Incident status updated.",
      });
    } catch (error) {
      setNotice({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not update status.",
      });
    } finally {
      setWorking(false);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          aria-label="AgentOps Desk home"
        >
          <span className="brand-mark">
            <Activity size={21} />
          </span>

          <span>
            <strong>agentops</strong>
            <small>INVESTIGATION DESK</small>
          </span>
        </a>

        <div className="workspace-label">WORKSPACE</div>

        <button className="nav-item active" type="button">
          <CircleDot size={17} />
          <span>Incidents</span>
          <span className="nav-count">{stats.total}</span>
        </button>

        <div className="nav-item muted">
          <ShieldCheck size={17} />
          <span>Evidence &amp; signals</span>
        </div>

        <div className="nav-item muted">
          <Zap size={17} />
          <span>Investigations</span>
        </div>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot" />

            <span>
              <strong>Workspace</strong>
              <small>Local development</small>
            </span>
          </div>

          <div className="sidebar-version">
            AGENTOPS DESK · v0.1.0
          </div>
        </div>
      </aside>

      <section className="main-area">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>Incidents</strong>
          </div>

          <div className="topbar-right">
            <span className="environment-pill">
              <span className="status-dot" />
              API workspace
            </span>

            <button
              className="icon-button"
              type="button"
              aria-label="Refresh incidents"
              onClick={() => void loadIncidents()}
              title="Refresh"
            >
              <RefreshCw size={16} />
            </button>
          </div>
        </header>

        <div className="page-content">
          <section className="page-heading">
            <div>
              <div className="eyebrow">
                <span className="eyebrow-line" />
                OPERATIONS OVERVIEW
              </div>

              <h1>
                Incident command center<span>.</span>
              </h1>

              <p>
                Turn raw signals into evidence-backed investigations.
              </p>
            </div>

            <button
              className="primary-button"
              type="button"
              onClick={() => setShowIncidentForm(true)}
            >
              <Plus size={17} />
              New incident
            </button>
          </section>

          {notice && (
            <div
              className={`notice ${notice.kind}`}
              role="status"
              aria-live="polite"
            >
              {notice.kind === "success" ? (
                <CheckCircle2 size={17} />
              ) : (
                <AlertCircle size={17} />
              )}

              <span>{notice.message}</span>

              <button
                className="notice-close"
                type="button"
                onClick={() => setNotice(null)}
                aria-label="Dismiss notification"
              >
                <X size={15} />
              </button>
            </div>
          )}

          <section className="stats-grid">
            <StatCard
              label="Total incidents"
              value={stats.total}
              icon={<Activity size={17} />}
              tone="violet"
            />

            <StatCard
              label="Active incidents"
              value={stats.open}
              icon={<Clock3 size={17} />}
              tone="blue"
            />

            <StatCard
              label="Critical severity"
              value={stats.critical}
              icon={<AlertTriangle size={17} />}
              tone="red"
            />

            <StatCard
              label="Resolved"
              value={stats.resolved}
              icon={<CheckCircle2 size={17} />}
              tone="green"
            />
          </section>

          <section className="workspace-grid">
            <div className="panel incident-panel">
              <div className="panel-heading">
                <div>
                  <h2>
                    Incidents{" "}
                    <span className="subtle-count">
                      {filteredIncidents.length}
                    </span>
                  </h2>

                  <p>Monitor and triage incoming issues</p>
                </div>

                <button
                  className="icon-button small"
                  type="button"
                  onClick={() => void loadIncidents()}
                  aria-label="Refresh incident list"
                  title="Refresh list"
                >
                  <RefreshCw size={15} />
                </button>
              </div>

              <div className="incident-filters">
                <label className="search-box">
                  <Search size={15} />

                  <input
                    type="search"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search incidents..."
                    aria-label="Search incidents"
                  />
                </label>

                <select
                  value={severityFilter}
                  onChange={(event) =>
                    setSeverityFilter(event.target.value)
                  }
                  aria-label="Filter by severity"
                >
                  <option value="all">All severities</option>

                  {severityOptions.map((item) => (
                    <option key={item} value={item}>
                      {titleCase(item)}
                    </option>
                  ))}
                </select>

                <select
                  value={statusFilter}
                  onChange={(event) =>
                    setStatusFilter(event.target.value)
                  }
                  aria-label="Filter by status"
                >
                  <option value="all">All statuses</option>

                  {statusOptions.map((item) => (
                    <option key={item} value={item}>
                      {titleCase(item)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="incident-list" aria-live="polite">
                {loading ? (
                  <LoadingState label="Loading incidents..." />
                ) : filteredIncidents.length === 0 ? (
                  <EmptyState
                    title="No incidents found"
                    description="Create an incident or adjust your filters."
                  />
                ) : (
                  filteredIncidents.map((incident) => (
                    <button
                      className={`incident-row ${
                        selectedId === incident.id ? "selected" : ""
                      }`}
                      key={incident.id}
                      type="button"
                      aria-pressed={selectedId === incident.id}
                      onClick={() => setSelectedId(incident.id)}
                    >
                      <span
                        className={`severity-marker ${incident.severity}`}
                      />

                      <span className="incident-row-content">
                        <span className="incident-row-title">
                          {incident.title}
                        </span>

                        <span className="incident-row-meta">
                          {incident.service_name}
                          <span> · </span>
                          {formatDate(incident.created_at)}
                        </span>

                        <span
                          className={`status-pill ${incident.status}`}
                        >
                          {titleCase(incident.status)}
                        </span>
                      </span>

                      <ChevronRight
                        size={16}
                        className="row-chevron"
                      />
                    </button>
                  ))
                )}
              </div>

              <div className="panel-footer">
                <span>
                  Showing {filteredIncidents.length} of {incidents.length}{" "}
                  incidents
                </span>

                <span className="live-label">
                  <span className="status-dot" />
                  Synced on refresh
                </span>
              </div>
            </div>

            <div className="detail-column">
              {!selectedIncident ? (
                <div className="panel empty-detail">
                  <Activity size={30} />

                  <h2>Select an incident</h2>

                  <p>
                    Choose an incident to inspect its signals and
                    investigation history.
                  </p>
                </div>
              ) : (
                <>
                  <div className="panel incident-detail">
                    <div className="detail-kicker">
                      <span>INCIDENT DETAIL</span>

                      <span
                        className={`severity-tag ${selectedIncident.severity}`}
                      >
                        {selectedIncident.severity}
                      </span>
                    </div>

                    <h2>{selectedIncident.title}</h2>

                    <p className="detail-description">
                      {selectedIncident.description ||
                        "No description provided."}
                    </p>

                    <div className="detail-facts">
                      <Fact
                        label="SERVICE"
                        value={selectedIncident.service_name}
                      />

                      <Fact
                        label="ENVIRONMENT"
                        value={selectedIncident.environment}
                      />

                      <Fact
                        label="CREATED"
                        value={formatDate(selectedIncident.created_at)}
                      />
                    </div>

                    <div className="status-update">
                      <label htmlFor="incident-status">
                        Incident status
                      </label>

                      <select
                        id="incident-status"
                        value={selectedIncident.status}
                        disabled={working}
                        onChange={(event) =>
                          void updateStatus(
                            event.target.value as IncidentStatus,
                          )
                        }
                      >
                        {statusOptions.map((item) => (
                          <option key={item} value={item}>
                            {titleCase(item)}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="panel evidence-panel">
                    <div className="panel-heading">
                      <div>
                        <h2>
                          <FileText size={17} /> Evidence{" "}
                          <span className="subtle-count">
                            {evidence.length}
                          </span>
                        </h2>

                        <p>Signals associated with this incident</p>
                      </div>

                      <button
                        className="secondary-button compact"
                        type="button"
                        disabled={working}
                        onClick={() => setShowEvidenceForm(true)}
                      >
                        <Plus size={15} />
                        Add evidence
                      </button>
                    </div>

                    {detailLoading ? (
                      <LoadingState label="Loading evidence..." />
                    ) : evidence.length === 0 ? (
                      <EmptyState
                        title="No evidence yet"
                        description="Add a log, metric, event, or stack trace to start an investigation."
                      />
                    ) : (
                      <div className="evidence-list">
                        {evidence.map((item) => (
                          <EvidenceRow
                            key={item.id}
                            evidence={item}
                          />
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="panel investigation-panel">
                    <div className="panel-heading">
                      <div>
                        <h2>
                          <Zap size={17} /> Investigation
                        </h2>

                        <p>
                          Rule-based analysis of available evidence
                        </p>
                      </div>

                      <button
                        className="primary-button compact"
                        type="button"
                        disabled={working || detailLoading}
                        onClick={() => void runInvestigation()}
                      >
                        {working ? (
                          <LoaderCircle size={15} className="spin" />
                        ) : (
                          <Zap size={15} />
                        )}
                        Run analysis
                      </button>
                    </div>

                    {detailLoading ? (
                      <LoadingState label="Loading investigation history..." />
                    ) : activeInvestigation ? (
                      <div className="investigation-result">
                        <div className="result-summary">
                          <div className="result-icon">
                            <CheckCircle2 size={18} />
                          </div>

                          <div className="result-copy">
                            <strong>Analysis completed</strong>

                            <span>
                              {activeInvestigation.engine_version}
                              {" · "}
                              {formatDate(activeInvestigation.created_at)}
                            </span>
                          </div>

                          <span className="finding-count">
                            {activeInvestigation.findings.length} finding
                            {activeInvestigation.findings.length === 1
                              ? ""
                              : "s"}
                          </span>
                        </div>

                        {activeInvestigation.summary && (
                          <p className="analysis-summary">
                            {activeInvestigation.summary}
                          </p>
                        )}

                        {activeInvestigation.confidence !== null && (
                          <div className="confidence-row">
                            <span>Heuristic confidence</span>

                            <strong>
                              {Math.round(
                                activeInvestigation.confidence * 100,
                              )}
                              %
                            </strong>
                          </div>
                        )}

                        <div
                          className="confidence-track"
                          aria-label={`Heuristic confidence ${
                            Math.round(
                              (activeInvestigation.confidence ?? 0) * 100,
                            )
                          } percent`}
                        >
                          <span
                            style={{
                              width: `${Math.max(
                                0,
                                Math.min(
                                  100,
                                  (activeInvestigation.confidence ?? 0) *
                                    100,
                                ),
                              )}%`,
                            }}
                          />
                        </div>

                        <p className="confidence-note">
                          This score is a heuristic indicator, not a
                          calibrated probability that a root cause is
                          correct.
                        </p>

                        {activeInvestigation.findings.length === 0 ? (
                          <div className="no-findings">
                            <ShieldCheck size={18} />

                            <span>
                              No rule-based findings were detected in the
                              available evidence.
                            </span>
                          </div>
                        ) : (
                          <div className="finding-list">
                            {activeInvestigation.findings.map(
                              (finding, index) => (
                                <div
                                  className="finding-card"
                                  key={`${finding.rule_id}-${finding.evidence_id}-${index}`}
                                >
                                  <div className="finding-title-row">
                                    <span className="finding-icon">
                                      <AlertTriangle size={15} />
                                    </span>

                                    <strong>{finding.title}</strong>

                                    <span className="rule-id">
                                      {finding.rule_id}
                                    </span>
                                  </div>

                                  <p>{finding.description}</p>

                                  <div className="evidence-reference">
                                    <FileText size={13} />

                                    <span>
                                      {finding.evidence_title}
                                    </span>

                                    <span> · </span>

                                    <span>{finding.source}</span>
                                  </div>

                                  {finding.excerpt && (
                                    <blockquote>
                                      {finding.excerpt}
                                    </blockquote>
                                  )}
                                </div>
                              ),
                            )}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="analysis-empty">
                        <div className="analysis-empty-icon">
                          <Terminal size={21} />
                        </div>

                        <strong>Ready to investigate</strong>

                        <p>
                          Run the rules engine to identify patterns in
                          the evidence linked to this incident.
                        </p>
                      </div>
                    )}

                    {investigations.length > 1 && (
                      <div className="history-row">
                        <label htmlFor="investigation-history">
                          Previous investigations
                        </label>

                        <select
                          id="investigation-history"
                          value={activeInvestigation?.id ?? ""}
                          onChange={(event) => {
                            const selected = investigations.find(
                              (item) =>
                                item.id === event.target.value,
                            );

                            setActiveInvestigation(selected ?? null);
                          }}
                        >
                          {investigations.map((item) => (
                            <option key={item.id} value={item.id}>
                              {formatDate(item.created_at)}
                              {" · "}
                              {item.findings.length} findings
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </section>

          <footer className="page-footer">
            <span>
              <Code2 size={14} /> AgentOps Desk · Evidence-driven incident
              response
            </span>

            <span>
              Built for inspectable investigations{" "}
              <ArrowUpRight size={13} />
            </span>
          </footer>
        </div>
      </section>

      {showIncidentForm && (
        <Modal
          title="Create incident"
          onClose={() => setShowIncidentForm(false)}
        >
          <IncidentForm
            busy={working}
            onCancel={() => setShowIncidentForm(false)}
            onSubmit={(input) => void createIncident(input)}
          />
        </Modal>
      )}

      {showEvidenceForm && (
        <Modal
          title="Add evidence"
          onClose={() => setShowEvidenceForm(false)}
        >
          <EvidenceForm
            busy={working}
            onCancel={() => setShowEvidenceForm(false)}
            onSubmit={(input) => void createEvidence(input)}
          />
        </Modal>
      )}
    </main>
  );
}

function StatCard({
  label,
  value,
  icon,
  tone,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  tone: string;
}) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${tone}`}>{icon}</div>

      <div className="stat-label">{label}</div>

      <div className="stat-bottom">
        <strong>{value.toString().padStart(2, "0")}</strong>

        <span className="stat-trend">
          <ArrowUpRight size={13} /> Live data
        </span>
      </div>
    </div>
  );
}

function Fact({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="detail-fact">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EvidenceRow({ evidence }: { evidence: Evidence }) {
  const Icon =
    evidence.evidence_type === "metric"
      ? Activity
      : evidence.evidence_type === "event"
        ? Zap
        : evidence.evidence_type === "stack_trace"
          ? Code2
          : Terminal;

  return (
    <details className="evidence-item">
      <summary>
        <span
          className={`evidence-type-icon ${evidence.evidence_type}`}
        >
          <Icon size={15} />
        </span>

        <span className="evidence-item-copy">
          <strong>{evidence.title}</strong>

          <small>
            {titleCase(evidence.evidence_type)}
            {" · "}
            {evidence.source}
          </small>
        </span>

        <span className="evidence-date">
          {formatDate(evidence.created_at)}
        </span>

        <ChevronRight
          size={15}
          className="evidence-chevron"
        />
      </summary>

      <pre className="evidence-content">{evidence.content}</pre>
    </details>
  );
}

function LoadingState({ label }: { label: string }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <LoaderCircle size={19} className="spin" />
      <span>{label}</span>
    </div>
  );
}

function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">
        <FileText size={19} />
      </div>

      <strong>{title}</strong>

      <p>{description}</p>
    </div>
  );
}

function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="modal-header">
          <h2>{title}</h2>

          <button
            className="icon-button"
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
          >
            <X size={17} />
          </button>
        </div>

        {children}
      </section>
    </div>
  );
}

function IncidentForm({
  busy,
  onSubmit,
  onCancel,
}: {
  busy: boolean;
  onSubmit: (input: IncidentInput) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [serviceName, setServiceName] = useState("");
  const [environment, setEnvironment] = useState("development");
  const [severity, setSeverity] = useState<Severity>("medium");

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    onSubmit({
      title: title.trim(),
      description: description.trim(),
      service_name: serviceName.trim(),
      environment: environment.trim(),
      severity,
    });
  }

  return (
    <form className="modal-form" onSubmit={submit}>
      <label>
        Incident title

        <input
          required
          minLength={3}
          maxLength={200}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="e.g. Checkout API latency spike"
        />
      </label>

      <label>
        Description

        <textarea
          maxLength={10000}
          rows={3}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="What is happening?"
        />
      </label>

      <div className="form-row">
        <label>
          Service name

          <input
            required
            value={serviceName}
            onChange={(event) => setServiceName(event.target.value)}
            placeholder="checkout-api"
          />
        </label>

        <label>
          Environment

          <input
            required
            value={environment}
            onChange={(event) => setEnvironment(event.target.value)}
            placeholder="development"
          />
        </label>
      </div>

      <label>
        Severity

        <select
          value={severity}
          onChange={(event) =>
            setSeverity(event.target.value as Severity)
          }
        >
          {severityOptions.map((item) => (
            <option key={item} value={item}>
              {titleCase(item)}
            </option>
          ))}
        </select>
      </label>

      <div className="modal-actions">
        <button
          type="button"
          className="secondary-button"
          onClick={onCancel}
          disabled={busy}
        >
          Cancel
        </button>

        <button
          type="submit"
          className="primary-button"
          disabled={busy}
        >
          {busy ? (
            <LoaderCircle size={15} className="spin" />
          ) : (
            <Plus size={15} />
          )}

          Create incident
        </button>
      </div>
    </form>
  );
}

function EvidenceForm({
  busy,
  onSubmit,
  onCancel,
}: {
  busy: boolean;
  onSubmit: (input: {
    evidence_type: EvidenceType;
    title: string;
    content: string;
    source: string;
  }) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [type, setType] = useState<EvidenceType>("log");
  const [source, setSource] = useState("manual");
  const [content, setContent] = useState("");

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    onSubmit({
      title: title.trim(),
      evidence_type: type,
      source: source.trim(),
      content: content.trim(),
    });
  }

  return (
    <form className="modal-form" onSubmit={submit}>
      <label>
        Evidence title

        <input
          required
          maxLength={200}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="e.g. API timeout logs"
        />
      </label>

      <div className="form-row">
        <label>
          Evidence type

          <select
            value={type}
            onChange={(event) =>
              setType(event.target.value as EvidenceType)
            }
          >
            <option value="log">Log</option>
            <option value="stack_trace">Stack trace</option>
            <option value="metric">Metric</option>
            <option value="event">Event</option>
          </select>
        </label>

        <label>
          Source

          <input
            required
            value={source}
            onChange={(event) => setSource(event.target.value)}
            placeholder="manual"
          />
        </label>
      </div>

      <label>
        Content

        <textarea
          required
          minLength={1}
          maxLength={100000}
          rows={7}
          value={content}
          onChange={(event) => setContent(event.target.value)}
          placeholder="Paste relevant logs, stack trace, or metric details..."
        />
      </label>

      <div className="modal-actions">
        <button
          type="button"
          className="secondary-button"
          onClick={onCancel}
          disabled={busy}
        >
          Cancel
        </button>

        <button
          type="submit"
          className="primary-button"
          disabled={busy}
        >
          {busy ? (
            <LoaderCircle size={15} className="spin" />
          ) : (
            <Plus size={15} />
          )}

          Add evidence
        </button>
      </div>
    </form>
  );
}

export default App;