/**
 * Real backend API client for the AI Studio premium UI.
 *
 * Reads live data from the EvolveAgent FastAPI backend and maps it into the UI
 * types. Everything is best-effort: any failure returns null so the caller can
 * keep the mock data (the UI never breaks if the backend is down).
 */

import {
  Agent,
  GovernanceEvent,
  SystemMetric,
  RiskLevel,
  MemoryItem,
  ToolConnector,
  ApprovalRequest,
} from '../types';

export const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || 'http://127.0.0.1:8000';

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

async function postJson<T>(path: string, body: any): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

// ---- Actions ---------------------------------------------------------------
/** Route a chat message through the Master Agent. Returns the reply + metadata.
 *  `execute` is only honored by the backend for NON-risky intents; risky actions
 *  are always held for approval regardless. */
export async function routeMessage(
  text: string,
  execute = false,
): Promise<
  { answer: string; requiresApproval: boolean; blockedExecution: boolean; intent: string; suggestedWorkflow: string | null } | null
> {
  const d = await postJson<any>('/api/master-agent/route', { text, execute });
  if (!d) return null;
  return {
    answer: d.answer || d.route_explanation || 'Routed your request.',
    requiresApproval: Boolean(d.requires_approval),
    blockedExecution: Boolean(d.blocked_execution),
    intent: d.intent || '',
    suggestedWorkflow: d.suggested_workflow || null,
  };
}

/** Dry-run (plan) a connector action — real preview, NO execution. Mock-safe. */
export async function planConnectorAction(
  connectorId: string,
  actionName: string,
): Promise<
  { allowed: boolean; requiresApproval: boolean; riskLevel: string; plan: string[]; blockedReason: string | null; actionName: string } | null
> {
  const d = await postJson<any>(`/api/mcp/connectors/${connectorId}/plan-action`, { action_name: actionName, payload: {} });
  if (!d) return null;
  return {
    allowed: Boolean(d.allowed),
    requiresApproval: Boolean(d.requires_approval),
    riskLevel: d.risk_level || 'medium',
    plan: Array.isArray(d.plan) ? d.plan : [],
    blockedReason: d.blocked_reason || null,
    actionName,
  };
}

// ---- MCP execute → approve → run (approval-gated, mock-safe) ----------------
export interface McpExecutionRequest {
  requestId: string;
  status: string; // pending_approval | approved | executed | blocked | rejected
  requiresApproval: boolean;
  riskLevel: string;
  blockedReason: string | null;
  actionName: string;
}

export interface McpExecutionResult {
  status: string;
  executionMode: string; // mock | real_read_only
  success: boolean;
  realCallMade: boolean;
  secretsUsed: boolean;
  output: any;
  note: string;
}

/** Request a real execution of a connector action. Returns a request_id.
 *  Risky/approval-gated actions come back as `pending_approval` and never auto-run.
 *  Returns null for sample/mock connectors (backend 404s). */
export async function requestConnectorExecution(
  connectorId: string,
  actionName: string,
): Promise<McpExecutionRequest | null> {
  const d = await postJson<any>(`/api/mcp/connectors/${connectorId}/execute`, { action_name: actionName, payload: {} });
  if (!d) return null;
  return {
    requestId: d.request_id,
    status: d.status || 'pending_approval',
    requiresApproval: Boolean(d.requires_approval),
    riskLevel: d.risk_level || 'medium',
    blockedReason: d.blocked_reason || null,
    actionName,
  };
}

/** Approve a pending execution request (explicit human sign-off). */
export async function approveConnectorExecution(requestId: string): Promise<McpExecutionRequest | null> {
  const d = await postJson<any>(`/api/mcp/executions/${requestId}/approve`, {});
  if (!d) return null;
  return {
    requestId: d.request_id,
    status: d.status || 'approved',
    requiresApproval: Boolean(d.requires_approval),
    riskLevel: d.risk_level || 'medium',
    blockedReason: d.blocked_reason || null,
    actionName: d.action_name || '',
  };
}

/** Run an approved execution request. Mock-by-default; a real read-only call
 *  only happens when the backend adapter's opt-in is set. Surfaces the result. */
export async function runConnectorExecution(requestId: string): Promise<McpExecutionResult | null> {
  const d = await postJson<any>(`/api/mcp/executions/${requestId}/run`, {});
  if (!d) return null;
  const result = d.result || {};
  return {
    status: d.status || 'executed',
    executionMode: result.execution_mode || 'mock',
    success: Boolean(result.success),
    realCallMade: Boolean(result.real_call_made),
    secretsUsed: Boolean(result.secrets_used),
    output: result.output ?? {},
    note: result.note || '',
  };
}

/** Enable/disable a real MCP connector. Best-effort; false if it 404s (sample item). */
export async function setConnectorEnabled(connectorId: string, enabled: boolean): Promise<boolean> {
  const d = await postJson<any>(`/api/mcp/connectors/${connectorId}/${enabled ? 'enable' : 'disable'}`, {});
  return d !== null;
}

/** Approve or reject a REAL backend approval. Best-effort; null if it 404s (mock item). */
export async function decideApproval(
  approvalId: string,
  decision: 'approve' | 'reject',
  comment?: string,
): Promise<boolean> {
  const d = await postJson<any>(`/api/approvals/${approvalId}/decision`, { decision, comment });
  return d !== null;
}

function riskFromScore(score: number): RiskLevel {
  if (score >= 7) return 'high';
  if (score >= 4) return 'medium';
  return 'low';
}

function riskFromLevel(level: string): RiskLevel {
  const l = String(level || '').toLowerCase();
  if (l === 'high' || l === 'critical') return 'high';
  if (l === 'medium' || l === 'moderate') return 'medium';
  if (l === 'low') return 'low';
  return 'medium';
}

const clip = (s: any, n: number) => String(s ?? '').slice(0, n);

// ---- Agents (Agent Studio) --------------------------------------------------
export async function fetchAgents(): Promise<Agent[] | null> {
  const data = await getJson<{ agents: any[] }>('/api/agent-studio/agents');
  if (!data?.agents) return null;
  return data.agents.map((a): Agent => {
    const requiresApproval = (a.guardrails?.requires_approval || []).length > 0;
    return {
      id: a.agent_id,
      name: a.name || 'Untitled Agent',
      role: a.role || '',
      description: a.description || a.role || '',
      avatar: '🤖',
      status: a.published_local ? 'active' : 'idle',
      qualityScore: a.evaluation?.score ?? 0,
      riskLevel: requiresApproval ? 'high' : 'low',
      memoryAccess: a.memory_scope?.workspace ? 'Full Workspace' : 'Scoped Project',
      permissionLevel: requiresApproval ? 'approval-gated' : 'planning-only',
      connectedTools: a.tools || [],
      currentTask: a.evaluation?.grade ? `Last eval grade: ${a.evaluation.grade}` : undefined,
      tasksCompletedToday: (a.versions?.length ?? 0),
      tokensUsed: '—',
    };
  });
}

// ---- Governance -------------------------------------------------------------
export async function fetchGovernance(): Promise<GovernanceEvent[] | null> {
  const data = await getJson<{ recent_events: any[] }>('/api/governance');
  if (!data?.recent_events) return null;
  return data.recent_events.slice(0, 40).map((e, i): GovernanceEvent => {
    const type: GovernanceEvent['type'] = e.blocked
      ? 'safety_block'
      : String(e.action_type || '').includes('approv')
        ? 'approval_granted'
        : e.tool_used
          ? 'tool_call'
          : 'audit_log';
    return {
      id: e.event_id || `gov-${i}`,
      timestamp: (e.created_at || '').slice(11, 19) || '—',
      type,
      agentName: e.agent_name || 'Governance',
      action: e.action_type || e.tool_used || 'event',
      status: e.blocked ? 'blocked' : e.approved ? 'allowed' : 'mock_executed',
      risk: riskFromScore(e.risk_score || 0),
      details: e.reason || '',
    };
  });
}

// ---- System metrics (Today dashboard) --------------------------------------
export async function fetchSystemMetrics(): Promise<SystemMetric[] | null> {
  const data = await getJson<{ metrics: Record<string, number> }>('/api/today/summary');
  if (!data?.metrics) return null;
  const m = data.metrics;
  const label = (k: string) => k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  return Object.entries(m).map(([k, v]): SystemMetric => ({
    label: label(k),
    value: typeof v === 'number' && v < 10 ? `0${v}` : v,
    subtitle: 'live',
  }));
}

// ---- Project Brain memories (task memory) ----------------------------------
export async function fetchMemories(): Promise<MemoryItem[] | null> {
  const data = await getJson<any[]>('/api/memory');
  if (!Array.isArray(data)) return null;
  return data
    .slice(-40)
    .reverse()
    .map((m, i): MemoryItem => ({
      id: m.task_id || `mem-${i}`,
      title: clip(m.user_input || m.task_type || 'Memory', 80),
      snippet: clip(m.final_output_summary || '', 240),
      type: 'Memory',
      relevance: Math.min(100, Math.round(Number(m.judge_score) || 90)),
      tier: 'hot',
      source: Array.isArray(m.agents_used) ? m.agents_used.join(', ') : String(m.agents_used || 'Task Memory'),
      timestamp: clip(m.created_at, 10) || '—',
      tags: [m.task_type].filter(Boolean),
      pinned: false,
    }));
}

// ---- Tools / MCP connectors -------------------------------------------------
export async function fetchConnectors(): Promise<ToolConnector[] | null> {
  const data = await getJson<{ connectors: any[] }>('/api/mcp/connectors');
  const list = data?.connectors;
  if (!Array.isArray(list)) return null;
  return list.slice(0, 48).map((c): ToolConnector => ({
    id: c.connector_id,
    name: c.name || c.slug || 'Connector',
    category: 'MCP',
    status: c.last_error ? 'error' : c.enabled ? 'connected' : 'disconnected',
    riskLevel: riskFromLevel(c.risk_level),
    description: clip(c.description || '', 160),
    icon: '🔌',
    permissions: (c.allowed_actions || []).slice(0, 8),
    dryCheckPassed: !c.last_error,
    activeAgentsCount: 0,
    callsToday: 0,
    lastUsed: clip(c.last_checked_at, 10) || '—',
  }));
}

// ---- Approvals --------------------------------------------------------------
export async function fetchApprovals(): Promise<ApprovalRequest[] | null> {
  const data = await getJson<any[]>('/api/approvals');
  if (!Array.isArray(data)) return null;
  const mapStatus = (s: string): ApprovalRequest['status'] => {
    const v = String(s || '').toLowerCase();
    if (v === 'approved' || v === 'completed' || v === 'allowed') return 'approved';
    if (v === 'rejected' || v === 'blocked' || v === 'denied') return 'rejected';
    return 'pending';
  };
  // Pending first, then most recent; cap the list.
  const sorted = [...data].sort((a, b) => {
    const ap = mapStatus(a.status) === 'pending' ? 0 : 1;
    const bp = mapStatus(b.status) === 'pending' ? 0 : 1;
    return ap - bp || String(b.created_at).localeCompare(String(a.created_at));
  });
  return sorted.slice(0, 24).map((a, i): ApprovalRequest => ({
    id: a.approval_id || `apr-${i}`,
    title: clip(a.summary || a.action_type || 'Approval request', 80),
    description: clip(a.summary || '', 240),
    agentId: '',
    agentName: clip(a.task_type || 'Agent', 40),
    riskLevel: riskFromLevel(a.risk_level),
    timestamp: clip(a.created_at, 10) || '—',
    status: mapStatus(a.status),
    intent: clip(a.action_type || '', 80),
    plannedAction: clip(a.action_type || a.summary || '', 120),
    permissionScopes: [],
    toolName: clip(a.action_type || 'action', 40),
    workspaceScope: a.workspace_id || 'default',
    governanceChecks: [
      { label: 'Approval-gated', passed: true, detail: 'Held for explicit human approval' },
      { label: 'Mock-safe', passed: true, detail: 'No real external mutation without approval' },
    ],
  }));
}

// ---- Provider / settings status (secret-safe) ------------------------------
export interface ProviderStatus {
  totalProviders: number;
  readyProviders: number;
  capabilityModes: Record<string, string>;
  fallbackEnabled: boolean;
  providers: { provider: string; ready: boolean; keys: { name: string; isSet: boolean }[] }[];
}

export async function fetchProviderStatus(): Promise<ProviderStatus | null> {
  const [summary, keyCheck] = await Promise.all([
    getJson<any>('/api/provider-control/summary'),
    getJson<any>('/api/provider-control/key-check'),
  ]);
  if (!summary && !keyCheck) return null;
  return {
    totalProviders: summary?.total_providers ?? 0,
    readyProviders: summary?.ready_providers ?? 0,
    capabilityModes: summary?.capability_modes ?? {},
    fallbackEnabled: Boolean(summary?.fallback_enabled),
    providers: (keyCheck?.checks || []).map((c: any) => ({
      provider: c.provider,
      ready: Boolean(c.ready),
      keys: (c.keys || []).map((k: any) => ({ name: k.key_name, isSet: Boolean(k.is_set) })),
    })),
  };
}

// ---- System health (Dev Console) ------------------------------------------
export interface SystemHealth {
  online: boolean;
  totalEvents: number;
  blocked: number;
  approvals: number;
  workflowRuns: number;
  learnedItems: number;
}

export interface LiveWorkflowRun {
  id: string;
  name: string;
  status: string;
  done: number;
  total: number;
}

/** Start a REAL durable-workflow run. Risky/action steps stay approval-gated by the backend. */
export async function startDurableRun(name: string, steps: any[]): Promise<boolean> {
  const d = await postJson<any>('/api/durable-workflows/runs', { name, steps });
  return d !== null;
}

export async function fetchWorkflowRuns(): Promise<LiveWorkflowRun[] | null> {
  const data = await getJson<{ runs: any[] }>('/api/durable-workflows/runs');
  if (!data?.runs) return null;
  return data.runs.slice(0, 8).map((r): LiveWorkflowRun => ({
    id: r.run_id,
    name: r.name || 'Workflow',
    status: r.status || 'unknown',
    done: (r.steps || []).filter((s: any) => s.status === 'done' || s.status === 'skipped').length,
    total: (r.steps || []).length,
  }));
}

export async function fetchSystemHealth(): Promise<SystemHealth | null> {
  const [health, gov, today] = await Promise.all([
    getJson<any>('/health'),
    getJson<any>('/api/governance'),
    getJson<any>('/api/today/summary'),
  ]);
  if (!health && !gov && !today) return null;
  return {
    online: health?.status === 'ok',
    totalEvents: gov?.total_events ?? 0,
    blocked: gov?.blocked_actions ?? 0,
    approvals: gov?.approvals ?? 0,
    workflowRuns: today?.metrics?.workflow_runs ?? 0,
    learnedItems: today?.metrics?.learned_items ?? 0,
  };
}

export async function fetchLiveData(): Promise<{
  agents: Agent[] | null;
  governanceLogs: GovernanceEvent[] | null;
  systemMetrics: SystemMetric[] | null;
  memories: MemoryItem[] | null;
  connectors: ToolConnector[] | null;
  approvals: ApprovalRequest[] | null;
} | null> {
  const [agents, governanceLogs, systemMetrics, memories, connectors, approvals] = await Promise.all([
    fetchAgents(),
    fetchGovernance(),
    fetchSystemMetrics(),
    fetchMemories(),
    fetchConnectors(),
    fetchApprovals(),
  ]);
  if (!agents && !governanceLogs && !systemMetrics && !memories && !connectors && !approvals) return null;
  return { agents, governanceLogs, systemMetrics, memories, connectors, approvals };
}
