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

export interface MemoryV2SearchResult {
  id: string;
  title: string;
  text: string;
  kind: string;
  source: string;
  similarity: number;
  mode: string;
  metadata: Record<string, any>;
}

export interface MemoryV2SearchResponse {
  results: MemoryV2SearchResult[];
  mode: string;
  count: number;
}

export async function addMemoryV2(
  text: string,
  kind: string,
  source: string,
  metadata: Record<string, any> = {},
): Promise<{ ok: boolean; mode?: string; id?: string } | null> {
  const data = await postJson<any>('/api/memory-v2/add', { text, kind, source, metadata });
  if (!data) return null;
  return {
    ok: data.ok !== false,
    mode: data.mode || data.backend || data.search_mode,
    id: data.id || data.memory_id,
  };
}

export async function searchMemoryV2(query: string, limit = 8): Promise<MemoryV2SearchResponse | null> {
  const q = String(query || '').trim();
  if (!q) return null;
  const data = await getJson<any>(`/api/memory-v2/search?q=${encodeURIComponent(q)}&limit=${encodeURIComponent(String(limit))}`);
  const rawResults = Array.isArray(data?.results) ? data.results : Array.isArray(data?.items) ? data.items : [];
  if (!data || !Array.isArray(rawResults)) return null;
  const mode = data.mode || data.backend || data.search_mode || (data.pgvector_ready ? 'pgvector' : 'keyword');
  return {
    mode,
    count: Number(data.count ?? rawResults.length),
    results: rawResults.map((item: any, index: number): MemoryV2SearchResult => {
      const metadata = item.metadata && typeof item.metadata === 'object' ? item.metadata : {};
      const similarity = Number(item.similarity ?? item.score ?? item.relevance ?? metadata.similarity ?? 0);
      return {
        id: item.id || item.memory_id || item.item_id || `memory-v2-${index}`,
        title: clip(item.title || metadata.title || item.kind || 'Semantic memory', 90),
        text: clip(item.text || item.content || item.snippet || metadata.text || '', 500),
        kind: item.kind || metadata.kind || 'memory',
        source: item.source || metadata.source || 'memory-v2',
        similarity: Number.isFinite(similarity) ? similarity : 0,
        mode: item.mode || item.backend || mode,
        metadata,
      };
    }),
  };
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

export interface StorageStatus {
  backend: string;
  configuredBackend: string;
  collections: number;
  totalDocuments: number;
  postgresReady: boolean;
  redisReady: boolean;
}

export interface LiveWorkflowRun {
  id: string;
  name: string;
  status: string;
  done: number;
  total: number;
}

export interface DurableWorkflowStep {
  id: string;
  name: string;
  actionType: string;
  actionParams: Record<string, any>;
  status: string;
  output: string;
  requiresApproval: boolean;
  approvers: string[];
  approvalProgress: any | null;
}

export interface DurableWorkflowRunDetail {
  id: string;
  name: string;
  status: string;
  cursor: number;
  updatedAt: string;
  steps: DurableWorkflowStep[];
}

export interface DurableWorkflowEffect {
  id: string;
  runId: string;
  stepId: string;
  actionType: string;
  params: Record<string, any>;
  result: Record<string, any>;
  createdAt: string;
}

export interface CodeWriterStatus {
  available: boolean;
  writesEnabled: boolean;
  writesOptInEnv: string;
  pushEnabled: boolean;
  pushOptInEnv: string;
  allowedReposEnv: string;
  allowedRepos: string[];
  allowedGitSubcommands: string[];
  note: string;
}

export interface GitHubWriteStatus {
  available: boolean;
  configured: boolean;
  writesEnabled: boolean;
  supportedWrites: string[];
  note: string;
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

function mapDurableStep(s: any): DurableWorkflowStep {
  return {
    id: s.id || '',
    name: s.name || s.action_type || 'Step',
    actionType: s.action_type || '',
    actionParams: s.action_params && typeof s.action_params === 'object' ? s.action_params : {},
    status: s.status || 'pending',
    output: s.output || '',
    requiresApproval: Boolean(s.requires_approval),
    approvers: Array.isArray(s.approvers) ? s.approvers : [],
    approvalProgress: s.approval_progress || null,
  };
}

function mapDurableRun(r: any): DurableWorkflowRunDetail {
  return {
    id: r.run_id || r.id || '',
    name: r.name || 'Workflow',
    status: r.status || 'unknown',
    cursor: Number(r.cursor ?? 0),
    updatedAt: r.updated_at || r.created_at || '',
    steps: Array.isArray(r.steps) ? r.steps.map(mapDurableStep) : [],
  };
}

export async function fetchCodeChangeRuns(): Promise<DurableWorkflowRunDetail[] | null> {
  const data = await getJson<{ runs: any[] }>('/api/durable-workflows/runs');
  if (!data?.runs) return null;
  return data.runs
    .map(mapDurableRun)
    .filter((run) => run.steps.some((step) => step.actionType === 'write_code_change' || step.actionType === 'open_pull_request'));
}

export async function fetchWorkflowRunDetail(runId: string): Promise<DurableWorkflowRunDetail | null> {
  const data = await getJson<any>(`/api/durable-workflows/runs/${encodeURIComponent(runId)}`);
  if (!data) return null;
  return mapDurableRun(data);
}

export async function approveDurableWorkflowStep(
  runId: string,
  approved: boolean,
  note = '',
  approver = 'EvolveAgent UI',
): Promise<DurableWorkflowRunDetail | null> {
  const data = await postJson<any>(`/api/durable-workflows/runs/${encodeURIComponent(runId)}/approve`, {
    approved,
    note,
    approver,
  });
  if (!data) return null;
  return mapDurableRun(data);
}

export async function fetchWorkflowEffects(runId: string): Promise<DurableWorkflowEffect[] | null> {
  const data = await getJson<any>(`/api/durable-workflows/effects?run_id=${encodeURIComponent(runId)}&limit=50`);
  const raw = Array.isArray(data?.effects) ? data.effects : [];
  if (!data || !Array.isArray(raw)) return null;
  return raw.map((e: any): DurableWorkflowEffect => ({
    id: e.effect_id || e.id || '',
    runId: e.run_id || '',
    stepId: e.step_id || '',
    actionType: e.action_type || '',
    params: e.params && typeof e.params === 'object' ? e.params : {},
    result: e.result && typeof e.result === 'object' ? e.result : {},
    createdAt: e.created_at || '',
  }));
}

export async function fetchCodeWriterStatus(): Promise<CodeWriterStatus | null> {
  const data = await getJson<any>('/api/code-writer/status');
  if (!data) return null;
  return {
    available: Boolean(data.available),
    writesEnabled: Boolean(data.writes_enabled),
    writesOptInEnv: data.writes_opt_in_env || 'CODE_WRITES_ENABLED',
    pushEnabled: Boolean(data.push_enabled),
    pushOptInEnv: data.push_opt_in_env || 'CODE_WRITER_PUSH_ENABLED',
    allowedReposEnv: data.allowed_repos_env || 'CODE_WRITER_ALLOWED_REPOS',
    allowedRepos: Array.isArray(data.allowed_repos) ? data.allowed_repos.map(String) : [],
    allowedGitSubcommands: Array.isArray(data.allowed_git_subcommands) ? data.allowed_git_subcommands.map(String) : [],
    note: data.note || '',
  };
}

export async function fetchGitHubWriteStatus(): Promise<GitHubWriteStatus | null> {
  const data = await getJson<any>('/api/github/status');
  if (!data) return null;
  return {
    available: Boolean(data.available ?? true),
    configured: Boolean(data.configured ?? data.token_configured ?? data.key_configured),
    writesEnabled: Boolean(data.writes_enabled),
    supportedWrites: Array.isArray(data.supported_writes) ? data.supported_writes.map(String) : [],
    note: data.note || '',
  };
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

export async function fetchStorageStatus(): Promise<StorageStatus | null> {
  const data = await getJson<any>('/api/system/storage-status');
  if (!data) return null;
  return {
    backend: data.backend || data.active_backend || 'json',
    configuredBackend: data.configured_backend || data.configuredBackend || data.backend || 'json',
    collections: Number(data.collections ?? data.collection_count ?? 0),
    totalDocuments: Number(data.total_documents ?? data.totalDocuments ?? 0),
    postgresReady: Boolean(data.postgres_ready ?? data.postgresReady),
    redisReady: Boolean(data.redis_ready ?? data.redisReady),
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

// ---- v200 Command Center (unified capability directory) -------------------
export interface CommandCenterSystem {
  label: string;
  route: string;
  active: boolean;
  recordCount: number;
}

export interface CommandCenterDomain {
  domain: string;
  systems: CommandCenterSystem[];
  activeCount: number;
  systemCount: number;
}

export interface CommandCenterSnapshot {
  snapshotId: string;
  activeSystems: number;
  totalSystems: number;
  coveragePct: number;
  overallScore: number;
  overallGrade: string;
  createdAt: string;
}

export interface CommandCenterDashboard {
  version: string;
  title: string;
  domains: CommandCenterDomain[];
  activeSystems: number;
  totalSystems: number;
  coveragePct: number;
  overallScore: number;
  overallGrade: string;
  scoreDimensions: { name: string; score: number; grade: string }[];
  healthStatus: string;
  healthScore: number;
  implementationVersions: number;
  governanceEvents: number;
  workspaces: number;
  safetyBoundaries: string[];
  latestSnapshot: CommandCenterSnapshot | null;
  disclaimer: string;
}

export interface CommandCenterReport {
  reportId: string;
  headline: string;
  overallGrade: string;
  overallScore: number;
  activeSystems: number;
  totalSystems: number;
  coveragePct: number;
  safetyBoundaries: string[];
  disclaimer: string;
  createdAt: string;
}

function mapSnapshot(s: any): CommandCenterSnapshot {
  return {
    snapshotId: s.snapshot_id || '',
    activeSystems: Number(s.active_systems ?? 0),
    totalSystems: Number(s.total_systems ?? 0),
    coveragePct: Number(s.coverage_pct ?? 0),
    overallScore: Number(s.overall_score ?? 0),
    overallGrade: s.overall_grade || '',
    createdAt: s.created_at || '',
  };
}

export async function fetchCommandCenterDashboard(): Promise<CommandCenterDashboard | null> {
  const data = await getJson<any>('/api/os2/dashboard');
  if (!data) return null;
  const cc = data.command_center || {};
  return {
    version: data.version || '',
    title: data.title || '',
    domains: Array.isArray(cc.domains) ? cc.domains.map((d: any): CommandCenterDomain => ({
      domain: d.domain || '',
      systems: Array.isArray(d.systems) ? d.systems.map((s: any): CommandCenterSystem => ({
        label: s.label || '',
        route: s.route || '',
        active: Boolean(s.active),
        recordCount: Number(s.record_count ?? 0),
      })) : [],
      activeCount: Number(d.active_count ?? 0),
      systemCount: Number(d.system_count ?? 0),
    })) : [],
    activeSystems: Number(cc.active_systems ?? 0),
    totalSystems: Number(cc.total_systems ?? 0),
    coveragePct: Number(cc.coverage_pct ?? 0),
    overallScore: Number(data.scorecard?.overall_score ?? 0),
    overallGrade: data.scorecard?.overall_grade || '',
    scoreDimensions: Array.isArray(data.scorecard?.dimensions)
      ? data.scorecard.dimensions.map((d: any) => ({ name: d.name || '', score: Number(d.score ?? 0), grade: d.grade || '' }))
      : [],
    healthStatus: data.health?.status || 'unknown',
    healthScore: Number(data.health?.score ?? 0),
    implementationVersions: Number(data.stats?.implementation_versions ?? 0),
    governanceEvents: Number(data.stats?.governance_events ?? 0),
    workspaces: Number(data.stats?.workspaces ?? 0),
    safetyBoundaries: Array.isArray(data.safety_boundaries) ? data.safety_boundaries.map(String) : [],
    latestSnapshot: data.latest_snapshot ? mapSnapshot(data.latest_snapshot) : null,
    disclaimer: data.disclaimer || '',
  };
}

export async function fetchCommandCenterSnapshots(): Promise<CommandCenterSnapshot[] | null> {
  const data = await getJson<any>('/api/os2/snapshots');
  if (!data?.snapshots) return null;
  return data.snapshots.map(mapSnapshot);
}

export async function createCommandCenterSnapshot(): Promise<CommandCenterSnapshot | null> {
  const data = await postJson<any>('/api/os2/snapshots', {});
  if (!data) return null;
  return mapSnapshot(data);
}

export async function generateCommandCenterReport(): Promise<CommandCenterReport | null> {
  const data = await postJson<any>('/api/os2/report', {});
  if (!data) return null;
  return {
    reportId: data.report_id || '',
    headline: data.headline || '',
    overallGrade: data.overall_grade || '',
    overallScore: Number(data.overall_score ?? 0),
    activeSystems: Number(data.active_systems ?? 0),
    totalSystems: Number(data.total_systems ?? 0),
    coveragePct: Number(data.coverage_pct ?? 0),
    safetyBoundaries: Array.isArray(data.safety_boundaries) ? data.safety_boundaries.map(String) : [],
    disclaimer: data.disclaimer || '',
    createdAt: data.created_at || '',
  };
}

// ---- v180 Personal Chief of Staff -------------------------------------------
export interface ChiefOfStaffStatus {
  available: boolean;
  githubWired: boolean;
  githubReposEnv: string;
  githubReposConfigured: string[];
  note: string;
}

export interface ChiefPriorityItem {
  itemId: string;
  itemType: string;
  title: string;
  priorityScore: number;
  reason: string;
  recommendedAction: string;
  sourceId: string;
}

export interface ChiefFollowup {
  followupId: string;
  workspaceId: string | null;
  title: string;
  description: string;
  sourceType: string;
  dueDate: string;
  priority: string;
  status: string;
  createdAt: string;
}

export interface ChiefDailyPlan {
  planId: string;
  date: string;
  summary: string;
  topPriorities: ChiefPriorityItem[];
  scheduleBlocks: { block: string; itemType: string; title: string; recommendedAction: string }[];
  recommendedNextActions: string[];
  createdAt: string;
}

export interface ChiefWeeklyPlan {
  planId: string;
  weekStart: string;
  summary: string;
  milestones: { title: string; progressPercent: number; riskLevel: string }[];
  priorityThemes: { theme: string; count: number }[];
  blockedItemsCount: number;
  recommendedFocus: string[];
  createdAt: string;
}

export interface ChiefOfStaffDashboard {
  today: string;
  dailyPlan: ChiefDailyPlan | null;
  weeklyPlan: ChiefWeeklyPlan | null;
  priorityItems: ChiefPriorityItem[];
  githubItemsCount: number;
  openFollowups: number;
  overdueFollowups: number;
  blockedItems: number;
  riskSummary: { openRiskCount: number; severityCounts: Record<string, number> };
  recommendedNextAction: string;
}

function mapPriorityItem(item: any): ChiefPriorityItem {
  return {
    itemId: item.item_id || '',
    itemType: item.item_type || '',
    title: item.title || '',
    priorityScore: Number(item.priority_score ?? 0),
    reason: item.reason || '',
    recommendedAction: item.recommended_action || '',
    sourceId: item.source_id || '',
  };
}

function mapDailyPlan(p: any): ChiefDailyPlan {
  return {
    planId: p.plan_id || '',
    date: p.date || '',
    summary: p.summary || '',
    topPriorities: Array.isArray(p.top_priorities) ? p.top_priorities.map(mapPriorityItem) : [],
    scheduleBlocks: Array.isArray(p.schedule_blocks) ? p.schedule_blocks.map((b: any) => ({
      block: b.block || '',
      itemType: b.item_type || '',
      title: b.title || '',
      recommendedAction: b.recommended_action || '',
    })) : [],
    recommendedNextActions: Array.isArray(p.recommended_next_actions) ? p.recommended_next_actions.map(String) : [],
    createdAt: p.created_at || '',
  };
}

function mapWeeklyPlan(p: any): ChiefWeeklyPlan {
  return {
    planId: p.plan_id || '',
    weekStart: p.week_start || '',
    summary: p.summary || '',
    milestones: Array.isArray(p.milestones) ? p.milestones.map((m: any) => ({
      title: m.title || '',
      progressPercent: Number(m.progress_percent ?? 0),
      riskLevel: m.risk_level || 'low',
    })) : [],
    priorityThemes: Array.isArray(p.priority_themes) ? p.priority_themes.map((t: any) => ({
      theme: t.theme || '',
      count: Number(t.count ?? 0),
    })) : [],
    blockedItemsCount: Array.isArray(p.blocked_items) ? p.blocked_items.length : 0,
    recommendedFocus: Array.isArray(p.recommended_focus) ? p.recommended_focus.map(String) : [],
    createdAt: p.created_at || '',
  };
}

export async function fetchChiefOfStaffStatus(): Promise<ChiefOfStaffStatus | null> {
  const data = await getJson<any>('/api/chief-of-staff/status');
  if (!data) return null;
  return {
    available: Boolean(data.available),
    githubWired: Boolean(data.github_wired),
    githubReposEnv: data.github_repos_env || 'CHIEF_OF_STAFF_GITHUB_REPOS',
    githubReposConfigured: Array.isArray(data.github_repos_configured) ? data.github_repos_configured.map(String) : [],
    note: data.note || '',
  };
}

export async function fetchChiefOfStaffDashboard(): Promise<ChiefOfStaffDashboard | null> {
  const data = await getJson<any>('/api/chief-of-staff/dashboard');
  if (!data) return null;
  return {
    today: data.today || '',
    dailyPlan: data.daily_plan ? mapDailyPlan(data.daily_plan) : null,
    weeklyPlan: data.weekly_plan ? mapWeeklyPlan(data.weekly_plan) : null,
    priorityItems: Array.isArray(data.priority_items) ? data.priority_items.map(mapPriorityItem) : [],
    githubItemsCount: Number(data.github_items_count ?? 0),
    openFollowups: Number(data.open_followups ?? 0),
    overdueFollowups: Number(data.overdue_followups ?? 0),
    blockedItems: Number(data.blocked_items ?? 0),
    riskSummary: {
      openRiskCount: Number(data.risk_summary?.open_risk_count ?? 0),
      severityCounts: data.risk_summary?.severity_counts || {},
    },
    recommendedNextAction: data.recommended_next_action || '',
  };
}

export async function generateChiefDailyPlan(): Promise<ChiefDailyPlan | null> {
  const data = await postJson<any>('/api/chief-of-staff/daily-plan', {});
  if (!data) return null;
  return mapDailyPlan(data);
}

export async function generateChiefWeeklyPlan(): Promise<ChiefWeeklyPlan | null> {
  const data = await postJson<any>('/api/chief-of-staff/weekly-plan', {});
  if (!data) return null;
  return mapWeeklyPlan(data);
}

export async function fetchChiefFollowups(): Promise<{ followups: ChiefFollowup[]; overdueCount: number } | null> {
  const data = await getJson<any>('/api/chief-of-staff/followups');
  if (!data?.followups) return null;
  return {
    followups: data.followups.map((f: any): ChiefFollowup => ({
      followupId: f.followup_id || '',
      workspaceId: f.workspace_id ?? null,
      title: f.title || '',
      description: f.description || '',
      sourceType: f.source_type || 'manual',
      dueDate: f.due_date || '',
      priority: f.priority || 'medium',
      status: f.status || 'open',
      createdAt: f.created_at || '',
    })),
    overdueCount: Number(data.overdue_count ?? 0),
  };
}

export async function createChiefFollowup(title: string, dueDate: string, priority: string): Promise<ChiefFollowup | null> {
  const data = await postJson<any>('/api/chief-of-staff/followups', { title, due_date: dueDate, priority });
  if (!data) return null;
  return {
    followupId: data.followup_id || '',
    workspaceId: data.workspace_id ?? null,
    title: data.title || '',
    description: data.description || '',
    sourceType: data.source_type || 'manual',
    dueDate: data.due_date || '',
    priority: data.priority || 'medium',
    status: data.status || 'open',
    createdAt: data.created_at || '',
  };
}

export async function updateChiefFollowupStatus(followupId: string, status: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/api/chief-of-staff/followups/${encodeURIComponent(followupId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  }).catch(() => null);
  return Boolean(res && res.ok);
}

// ---- v160 Agent Marketplace Hub ----------------------------------------------
export interface MarketplaceListing {
  listingId: string;
  kind: string;
  name: string;
  summary: string;
  publisher: string;
  isFeatured: boolean;
  installs: number;
  ratingCount: number;
  averageRating: number;
  createdAt: string;
  manifest: Record<string, any>;
}

export interface MarketplaceRating {
  ratingId: string;
  listingId: string;
  rating: number;
  review: string;
  createdAt: string;
}

export interface MarketplaceInstall {
  installId: string;
  listingId: string;
  kind: string;
  installedName: string;
  createdAt: string;
}

export interface MarketplaceSummary {
  totalListings: number;
  totalInstalls: number;
  listingsByKind: Record<string, number>;
  totalRatings: number;
  kinds: string[];
}

function mapMarketplaceListing(l: any): MarketplaceListing {
  return {
    listingId: l.listing_id || '',
    kind: l.kind || 'agent',
    name: l.name || 'Untitled listing',
    summary: l.summary || '',
    publisher: l.publisher || 'local',
    isFeatured: Boolean(l.is_featured),
    installs: Number(l.installs ?? 0),
    ratingCount: Number(l.rating_count ?? 0),
    averageRating: Number(l.average_rating ?? 0),
    createdAt: l.created_at || '',
    manifest: l.manifest && typeof l.manifest === 'object' ? l.manifest : {},
  };
}

export async function fetchMarketplaceListings(
  kind?: string, sort?: 'featured' | 'popular' | 'top_rated',
): Promise<MarketplaceListing[] | null> {
  const params = new URLSearchParams();
  if (kind) params.set('kind', kind);
  if (sort) params.set('sort', sort);
  const qs = params.toString();
  const data = await getJson<any>(`/api/marketplace-hub/listings${qs ? `?${qs}` : ''}`);
  if (!data?.listings) return null;
  return data.listings.map(mapMarketplaceListing);
}

export async function fetchMarketplaceListing(listingId: string): Promise<MarketplaceListing | null> {
  const data = await getJson<any>(`/api/marketplace-hub/listings/${encodeURIComponent(listingId)}`);
  if (!data) return null;
  return mapMarketplaceListing(data);
}

export async function fetchMarketplaceSummary(): Promise<MarketplaceSummary | null> {
  const data = await getJson<any>('/api/marketplace-hub/summary');
  if (!data) return null;
  return {
    totalListings: Number(data.marketplace_hub_listings ?? 0),
    totalInstalls: Number(data.marketplace_hub_installs ?? 0),
    listingsByKind: data.marketplace_hub_listings_by_kind || {},
    totalRatings: Number(data.marketplace_hub_ratings ?? 0),
    kinds: Array.isArray(data.kinds) ? data.kinds.map(String) : [],
  };
}

export async function fetchMarketplaceRatings(listingId: string): Promise<MarketplaceRating[] | null> {
  const data = await getJson<any>(`/api/marketplace-hub/listings/${encodeURIComponent(listingId)}/ratings`);
  if (!data?.ratings) return null;
  return data.ratings.map((r: any): MarketplaceRating => ({
    ratingId: r.rating_id || '',
    listingId: r.listing_id || '',
    rating: Number(r.rating ?? 0),
    review: r.review || '',
    createdAt: r.created_at || '',
  }));
}

export async function fetchMarketplaceInstalls(): Promise<MarketplaceInstall[] | null> {
  const data = await getJson<any>('/api/marketplace-hub/installs');
  if (!data?.installs) return null;
  return data.installs.map((i: any): MarketplaceInstall => ({
    installId: i.install_id || '',
    listingId: i.listing_id || '',
    kind: i.kind || '',
    installedName: (i.installed && i.installed.name) || '',
    createdAt: i.created_at || '',
  }));
}

export async function installMarketplaceListing(listingId: string): Promise<boolean> {
  const data = await postJson<any>(`/api/marketplace-hub/listings/${encodeURIComponent(listingId)}/install`, {});
  return data !== null;
}

export async function rateMarketplaceListing(listingId: string, rating: number, review: string): Promise<MarketplaceListing | null> {
  const data = await postJson<any>(`/api/marketplace-hub/listings/${encodeURIComponent(listingId)}/rate`, { rating, review });
  if (!data?.listing) return null;
  return mapMarketplaceListing(data.listing);
}

export async function publishMarketplaceListing(
  kind: string, name: string, summary: string, publisher: string,
): Promise<MarketplaceListing | null> {
  const data = await postJson<any>('/api/marketplace-hub/listings', {
    kind, name, summary, publisher, manifest: { name, role: summary },
  });
  if (!data) return null;
  return mapMarketplaceListing(data);
}

// ---- v190 Enterprise AI OS: Compliance Audit Packages -----------------------
export interface AuditPackageSummary {
  packageId: string;
  title: string;
  generatedAt: string;
  governanceEventCount: number;
  blockedActionCount: number;
  sensitiveFindingsCount: number;
  highRiskFindings: number;
  policyCount: number;
  contents: string[];
  disclaimer: string;
}

export interface AuditSensitiveFinding {
  findingId: string;
  label: string;
  secretsDetected: boolean;
  secretTypes: string[];
  piiDetected: boolean;
  piiTypes: string[];
  phiDetected: boolean;
  phiTerms: string[];
  hipaaWarning: boolean;
  riskLevel: string;
  recommendation: string;
}

export interface AuditPolicy {
  policyId: string;
  name: string;
  category: string;
  rules: string[];
  status: string;
}

export interface AuditChecklist {
  checklistId: string;
  title: string;
  framework: string;
  items: { item: string; done: boolean }[];
}

export interface AuditContractReview {
  reviewId: string;
  title: string;
  riskFlags: string[];
  riskLevel: string;
}

export interface AuditPackageDetail extends AuditPackageSummary {
  sensitiveFindings: AuditSensitiveFinding[];
  policies: AuditPolicy[];
  checklists: AuditChecklist[];
  contractReviews: AuditContractReview[];
}

function mapAuditPackageSummary(p: any): AuditPackageSummary {
  return {
    packageId: p.package_id || '',
    title: p.title || 'Untitled package',
    generatedAt: p.generated_at || '',
    governanceEventCount: Number(p.governance_event_count ?? 0),
    blockedActionCount: Number(p.blocked_action_count ?? 0),
    sensitiveFindingsCount: Number(p.sensitive_findings_count ?? 0),
    highRiskFindings: Number(p.high_risk_findings ?? 0),
    policyCount: Number(p.policy_count ?? 0),
    contents: Array.isArray(p.contents) ? p.contents.map(String) : [],
    disclaimer: p.disclaimer || '',
  };
}

export async function fetchAuditPackages(): Promise<AuditPackageSummary[] | null> {
  const data = await getJson<any>('/api/compliance/audit-packages');
  if (!data?.audit_packages) return null;
  return data.audit_packages.map(mapAuditPackageSummary);
}

export async function fetchAuditPackageDetail(packageId: string): Promise<AuditPackageDetail | null> {
  const data = await getJson<any>(`/api/compliance/audit-packages/${encodeURIComponent(packageId)}`);
  if (!data) return null;
  const bundle = data.bundle || {};
  return {
    ...mapAuditPackageSummary(data),
    sensitiveFindings: (Array.isArray(bundle.sensitive_findings) ? bundle.sensitive_findings : []).slice(0, 25).map((f: any): AuditSensitiveFinding => ({
      findingId: f.finding_id || '',
      label: f.label || '',
      secretsDetected: Boolean(f.secrets_detected),
      secretTypes: Array.isArray(f.secret_types) ? f.secret_types.map(String) : [],
      piiDetected: Boolean(f.pii_detected),
      piiTypes: Array.isArray(f.pii_types) ? f.pii_types.map(String) : [],
      phiDetected: Boolean(f.phi_detected),
      phiTerms: Array.isArray(f.phi_terms) ? f.phi_terms.map(String) : [],
      hipaaWarning: Boolean(f.hipaa_warning),
      riskLevel: f.risk_level || 'low',
      recommendation: f.recommendation || '',
    })),
    policies: (Array.isArray(bundle.policies) ? bundle.policies : []).slice(0, 25).map((p: any): AuditPolicy => ({
      policyId: p.policy_id || '',
      name: p.name || '',
      category: p.category || '',
      rules: Array.isArray(p.rules) ? p.rules.map(String) : [],
      status: p.status || 'active',
    })),
    checklists: (Array.isArray(bundle.checklists) ? bundle.checklists : []).slice(0, 15).map((c: any): AuditChecklist => ({
      checklistId: c.checklist_id || '',
      title: c.title || '',
      framework: c.framework || '',
      items: Array.isArray(c.items) ? c.items.map((i: any) => ({ item: String(i.item || ''), done: Boolean(i.done) })) : [],
    })),
    contractReviews: (Array.isArray(bundle.contract_reviews) ? bundle.contract_reviews : []).slice(0, 15).map((r: any): AuditContractReview => ({
      reviewId: r.review_id || '',
      title: r.title || '',
      riskFlags: Array.isArray(r.risk_flags) ? r.risk_flags.map(String) : [],
      riskLevel: r.risk_level || 'low',
    })),
  };
}

export async function createAuditPackage(title: string): Promise<AuditPackageSummary | null> {
  const data = await postJson<any>('/api/compliance/audit-packages', { title });
  if (!data) return null;
  return mapAuditPackageSummary(data);
}

// ---------------------------------------------------------------------------
// v260 Model Serving + v240 GPU Workers + storage retention (Compute Fabric)
// ---------------------------------------------------------------------------

export interface ModelServingBackend {
  backend: string;
  name: string;
  configured: boolean;
  reachable: boolean;
  models: string[];
  note: string;
}

export interface ModelServingDashboard {
  backends: ModelServingBackend[];
  count: number;
  reachableCount: number;
  realExecutionDefault: string;
}

export interface ModelServingDryRunResult {
  accepted: boolean;
  backend: string;
  model: string;
  declinedReason: string;
  nextHumanAction: string;
  availableModels: string[];
}

export async function fetchModelServingDashboard(): Promise<ModelServingDashboard | null> {
  const data = await getJson<any>('/api/model-serving/dashboard');
  if (!data) return null;
  return {
    backends: Array.isArray(data.backends)
      ? data.backends.map((b: any) => ({
          backend: b.backend || '',
          name: b.name || b.backend || '',
          configured: Boolean(b.configured),
          reachable: Boolean(b.reachable),
          models: Array.isArray(b.models) ? b.models.map(String) : [],
          note: b.note || '',
        }))
      : [],
    count: Number(data.count ?? 0),
    reachableCount: Number(data.reachable_count ?? 0),
    realExecutionDefault: data.real_execution_default || 'disabled',
  };
}

export async function runModelServingDryRun(backend: string, model: string): Promise<ModelServingDryRunResult | null> {
  const data = await postJson<any>('/api/model-serving/dry-run', { backend, model });
  if (!data) return null;
  return {
    accepted: Boolean(data.accepted),
    backend: data.backend || backend,
    model: data.model || model,
    declinedReason: data.declined_reason || '',
    nextHumanAction: data.next_human_action || '',
    availableModels: Array.isArray(data.available_models) ? data.available_models.map(String) : [],
  };
}

export interface GpuProvider {
  provider: string;
  name: string;
  enabled: boolean;
  configured: boolean;
  executionEnabled: boolean;
  riskLevel: RiskLevel;
  workerCount: number;
  activeWorkers: number;
  costWarning: string;
  note: string;
}

export interface GpuWorkerDashboard {
  totalGpuWorkers: number;
  activeGpuWorkers: number;
  providers: GpuProvider[];
  approvalRequiredForRealExecution: boolean;
}

export async function fetchGpuWorkerDashboard(): Promise<GpuWorkerDashboard | null> {
  const data = await getJson<any>('/api/worker-registry/gpu/dashboard');
  if (!data) return null;
  return {
    totalGpuWorkers: Number(data.total_gpu_workers ?? 0),
    activeGpuWorkers: Number(data.active_gpu_workers ?? 0),
    providers: Array.isArray(data.providers)
      ? data.providers.map((p: any) => ({
          provider: p.provider || '',
          name: p.name || p.provider || '',
          enabled: Boolean(p.enabled),
          configured: Boolean(p.configured),
          executionEnabled: Boolean(p.execution_enabled),
          riskLevel: (['low', 'medium', 'high'].includes(p.risk_level) ? p.risk_level : 'low') as RiskLevel,
          workerCount: Number(p.worker_count ?? 0),
          activeWorkers: Number(p.active_workers ?? 0),
          costWarning: p.cost_warning || '',
          note: p.note || '',
        }))
      : [],
    approvalRequiredForRealExecution: Boolean(data.approval_required_for_real_execution),
  };
}

export interface PrunableCollections {
  collections: string[];
  minOlderThanDays: number;
  note: string;
}

export interface StoragePruneResult {
  collection: string;
  olderThanDays: number;
  totalRecords?: number;
  recordsToPrune?: number;
  recordsToKeep?: number;
  prunedCount?: number;
  remainingCount?: number;
  archivePath: string | null;
  dryRun: boolean;
}

export async function fetchPrunableCollections(): Promise<PrunableCollections | null> {
  const data = await getJson<any>('/api/system/storage-prune/collections');
  if (!data) return null;
  return {
    collections: Array.isArray(data.collections) ? data.collections.map(String) : [],
    minOlderThanDays: Number(data.min_older_than_days ?? 1),
    note: data.note || '',
  };
}

export async function runStoragePrune(
  collection: string,
  olderThanDays: number,
  dryRun: boolean
): Promise<StoragePruneResult | null> {
  const data = await postJson<any>('/api/system/storage-prune', {
    collection,
    older_than_days: olderThanDays,
    dry_run: dryRun,
  });
  if (!data) return null;
  return {
    collection: data.collection || collection,
    olderThanDays: Number(data.older_than_days ?? olderThanDays),
    totalRecords: data.total_records != null ? Number(data.total_records) : undefined,
    recordsToPrune: data.records_to_prune != null ? Number(data.records_to_prune) : undefined,
    recordsToKeep: data.records_to_keep != null ? Number(data.records_to_keep) : undefined,
    prunedCount: data.pruned_count != null ? Number(data.pruned_count) : undefined,
    remainingCount: data.remaining_count != null ? Number(data.remaining_count) : undefined,
    archivePath: data.archive_path ?? null,
    dryRun: Boolean(data.dry_run),
  };
}

// ---------------------------------------------------------------------------
// v300 Digital Departments
// ---------------------------------------------------------------------------

export interface Department {
  departmentId: string;
  name: string;
  description: string;
  managerAgent: string;
  workerAgents: string[];
  reviewerAgents: string[];
  auditorAgents: string[];
  permissionLevel: string;
  active: boolean;
  createdAt: string;
}

export interface DepartmentTemplate {
  name: string;
  description: string;
  managerAgent: string;
  workerAgents: string[];
  reviewerAgents: string[];
  auditorAgents: string[];
  permissionLevel: string;
}

export interface DepartmentGoal {
  goalId: string;
  title: string;
  description: string;
  status: string;
  progressPercent: number;
}

export interface DepartmentBudget {
  monthlyLimit: number;
  currentMonthCost: number;
  totalEstimatedCost: number;
  budgetStatus: string;
  warning: string | null;
}

export interface DepartmentScorecard {
  department: Department;
  goals: DepartmentGoal[];
  budget: DepartmentBudget | null;
  measurableOutcomes: {
    totalRuns: number;
    planned: number;
    blocked: number;
  };
}

export interface DepartmentRun {
  departmentRunId: string;
  departmentId: string;
  departmentName: string;
  task: string;
  requiresApproval: boolean;
  riskLevel: string;
  status: string;
  blockReason: string | null;
  createdAt: string;
}

export interface DepartmentsOverview {
  totalDepartments: number;
  activeDepartments: number;
  departmentRuns: number;
  collaborationCount: number;
  recentRuns: DepartmentRun[];
}

function mapDepartment(d: any): Department {
  return {
    departmentId: d.department_id || '',
    name: d.name || '',
    description: d.description || '',
    managerAgent: d.manager_agent || '',
    workerAgents: Array.isArray(d.worker_agents) ? d.worker_agents.map(String) : [],
    reviewerAgents: Array.isArray(d.reviewer_agents) ? d.reviewer_agents.map(String) : [],
    auditorAgents: Array.isArray(d.auditor_agents) ? d.auditor_agents.map(String) : [],
    permissionLevel: d.permission_level || 'read_only',
    active: d.active !== false,
    createdAt: d.created_at || '',
  };
}

export async function fetchDepartments(includeArchived = false): Promise<Department[] | null> {
  const data = await getJson<any>(`/api/departments${includeArchived ? '?include_archived=true' : ''}`);
  if (!data || !Array.isArray(data.departments)) return null;
  return data.departments.map(mapDepartment);
}

export async function fetchDepartmentTemplates(): Promise<DepartmentTemplate[] | null> {
  const data = await getJson<any>('/api/departments/templates');
  if (!data || !Array.isArray(data.templates)) return null;
  return data.templates.map((t: any) => ({
    name: t.name || '',
    description: t.description || '',
    managerAgent: t.manager_agent || '',
    workerAgents: Array.isArray(t.worker_agents) ? t.worker_agents.map(String) : [],
    reviewerAgents: Array.isArray(t.reviewer_agents) ? t.reviewer_agents.map(String) : [],
    auditorAgents: Array.isArray(t.auditor_agents) ? t.auditor_agents.map(String) : [],
    permissionLevel: t.permission_level || 'read_only',
  }));
}

export async function seedDepartmentTemplates(): Promise<{ seededCount: number; skippedExisting: number } | null> {
  const data = await postJson<any>('/api/departments/templates/seed', {});
  if (!data) return null;
  return { seededCount: Number(data.seeded_count ?? 0), skippedExisting: Number(data.skipped_existing ?? 0) };
}

export async function createDepartment(
  name: string,
  description: string,
  managerAgent: string,
  permissionLevel: string
): Promise<Department | null> {
  const data = await postJson<any>('/api/departments', {
    name,
    description,
    manager_agent: managerAgent || undefined,
    permission_level: permissionLevel,
  });
  if (!data) return null;
  return mapDepartment(data);
}

export async function fetchDepartmentsOverview(): Promise<DepartmentsOverview | null> {
  const data = await getJson<any>('/api/departments/overview');
  if (!data) return null;
  return {
    totalDepartments: Number(data.total_departments ?? 0),
    activeDepartments: Number(data.active_departments ?? 0),
    departmentRuns: Number(data.department_runs ?? 0),
    collaborationCount: Number(data.collaboration_count ?? 0),
    recentRuns: Array.isArray(data.recent_runs) ? data.recent_runs.map(mapDepartmentRun) : [],
  };
}

function mapDepartmentRun(r: any): DepartmentRun {
  return {
    departmentRunId: r.department_run_id || '',
    departmentId: r.department_id || '',
    departmentName: r.department_name || '',
    task: r.task || '',
    requiresApproval: Boolean(r.requires_approval),
    riskLevel: r.risk_level || 'low',
    status: r.status || 'planned',
    blockReason: r.block_reason ?? null,
    createdAt: r.created_at || '',
  };
}

export async function fetchDepartmentScorecard(departmentId: string): Promise<DepartmentScorecard | null> {
  const data = await getJson<any>(`/api/departments/${encodeURIComponent(departmentId)}/scorecard`);
  if (!data) return null;
  const budget = data.budget;
  return {
    department: mapDepartment(data.department || {}),
    goals: Array.isArray(data.goals)
      ? data.goals.map((g: any) => ({
          goalId: g.goal_id || '',
          title: g.title || g.goal_title || '',
          description: g.description || g.goal_summary || '',
          status: g.status || 'active',
          progressPercent: Number(g.progress_percent ?? 0),
        }))
      : [],
    budget: budget
      ? {
          monthlyLimit: Number(budget.monthly_limit ?? 0),
          currentMonthCost: Number(budget.current_month_cost ?? 0),
          totalEstimatedCost: Number(budget.total_estimated_cost ?? 0),
          budgetStatus: budget.budget_status || 'no_budget',
          warning: budget.warning ?? null,
        }
      : null,
    measurableOutcomes: {
      totalRuns: Number(data.measurable_outcomes?.total_runs ?? 0),
      planned: Number(data.measurable_outcomes?.planned ?? 0),
      blocked: Number(data.measurable_outcomes?.blocked ?? 0),
    },
  };
}

export async function createDepartmentGoal(departmentId: string, title: string, description: string): Promise<DepartmentGoal | null> {
  const data = await postJson<any>(`/api/departments/${encodeURIComponent(departmentId)}/goals`, { title, description });
  if (!data) return null;
  return {
    goalId: data.goal_id || '',
    title: data.title || data.goal_title || title,
    description: data.description || data.goal_summary || description,
    status: data.status || 'active',
    progressPercent: Number(data.progress_percent ?? 0),
  };
}

export async function setDepartmentBudget(departmentId: string, monthlyLimit: number): Promise<boolean> {
  const data = await postJson<any>(`/api/departments/${encodeURIComponent(departmentId)}/budget`, { monthly_limit: monthlyLimit });
  return data !== null;
}

export async function planDepartmentRun(departmentId: string, task: string): Promise<DepartmentRun | null> {
  const data = await postJson<any>(`/api/departments/${encodeURIComponent(departmentId)}/runs`, { task });
  if (!data) return null;
  return mapDepartmentRun(data);
}
