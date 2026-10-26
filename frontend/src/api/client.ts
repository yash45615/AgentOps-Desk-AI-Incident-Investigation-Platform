
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export type Severity = "low" | "medium" | "high" | "critical";
export type IncidentStatus = "open" | "investigating" | "resolved" | "closed";
export type EvidenceType = "log" | "stack_trace" | "metric" | "event";

export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  status: IncidentStatus;
  service_name: string;
  environment: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentList {
  items: Incident[];
  total: number;
  limit: number;
  offset: number;
}

export interface Evidence {
  id: string;
  incident_id: string;
  evidence_type: EvidenceType;
  title: string;
  content: string;
  source: string;
  metadata: Record<string, unknown>;
  observed_at: string | null;
  created_at: string;
}

export interface EvidenceList {
  items: Evidence[];
  total: number;
}

export interface Finding {
  rule_id: string;
  title: string;
  description: string;
  evidence_id: string;
  evidence_title: string;
  evidence_type: string;
  source: string;
  excerpt: string;
}

export interface Investigation {
  id: string;
  incident_id: string;
  status: string;
  summary: string | null;
  findings: Finding[];
  confidence: number | null;
  engine_version: string;
  created_at: string;
  completed_at: string | null;
}

export interface InvestigationList {
  items: Investigation[];
  total: number;
}

export interface IncidentInput {
  title: string;
  description: string;
  severity: Severity;
  service_name: string;
  environment: string;
}

export interface EvidenceInput {
  evidence_type: EvidenceType;
  title: string;
  content: string;
  source: string;
  metadata: Record<string, unknown>;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;

    try {
      const body = await response.json();
      message =
        body?.error?.message ??
        body?.detail ??
        message;
    } catch {
      // Keep the HTTP status message when the response is not JSON.
    }

    throw new Error(
      typeof message === "string" ? message : JSON.stringify(message),
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  listIncidents: (search = "") => {
    const params = new URLSearchParams({ limit: "100", offset: "0" });

    if (search.trim()) {
      params.set("search", search.trim());
    }

    return request<IncidentList>(`/incidents?${params}`);
  },

  createIncident: (input: IncidentInput) =>
    request<Incident>("/incidents", {
      method: "POST",
      body: JSON.stringify({ ...input, status: "open" }),
    }),

  updateIncident: (
    id: string,
    input: Partial<Pick<Incident, "status" | "severity" | "title" | "description">>,
  ) =>
    request<Incident>(`/incidents/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    }),

  listEvidence: (incidentId: string) =>
    request<EvidenceList>(
      `/incidents/${encodeURIComponent(incidentId)}/evidence?limit=100&offset=0`,
    ),

  createEvidence: (incidentId: string, input: EvidenceInput) =>
    request<Evidence>(
      `/incidents/${encodeURIComponent(incidentId)}/evidence`,
      {
        method: "POST",
        body: JSON.stringify(input),
      },
    ),

  listInvestigations: (incidentId: string) =>
    request<InvestigationList>(
      `/incidents/${encodeURIComponent(incidentId)}/investigations?limit=100&offset=0`,
    ),

  runInvestigation: (incidentId: string) =>
    request<Investigation>(
      `/incidents/${encodeURIComponent(incidentId)}/investigations`,
      { method: "POST" },
    ),
};
