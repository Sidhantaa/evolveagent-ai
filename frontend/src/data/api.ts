/**
 * Real backend API client for the AI Studio premium UI.
 *
 * Reads live data from the EvolveAgent FastAPI backend and maps it into the UI
 * types. Everything is best-effort: any failure returns null so the caller can
 * keep the mock data (the UI never breaks if the backend is down).
 */

import { Agent, GovernanceEvent, SystemMetric, RiskLevel } from '../types';

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

function riskFromScore(score: number): RiskLevel {
  if (score >= 7) return 'high';
  if (score >= 4) return 'medium';
  return 'low';
}

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

export async function fetchLiveData(): Promise<{
  agents: Agent[] | null;
  governanceLogs: GovernanceEvent[] | null;
  systemMetrics: SystemMetric[] | null;
} | null> {
  const [agents, governanceLogs, systemMetrics] = await Promise.all([
    fetchAgents(),
    fetchGovernance(),
    fetchSystemMetrics(),
  ]);
  if (!agents && !governanceLogs && !systemMetrics) return null; // backend down
  return { agents, governanceLogs, systemMetrics };
}
