import { describe, it, expect, vi, afterEach } from 'vitest';
import {
  fetchAgents,
  fetchGovernance,
  fetchSystemMetrics,
  fetchConnectors,
  fetchApprovals,
  fetchSystemHealth,
  fetchStorageStatus,
  fetchWorkflowRuns,
  addMemoryV2,
  searchMemoryV2,
  routeMessage,
  startDurableRun,
} from './api';

// Helper: stub global fetch to return a given JSON body per-URL.
function stubFetch(routes: Record<string, any>) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const path = url.replace(/^https?:\/\/[^/]+/, '');
    const match = Object.keys(routes).find((k) => path.startsWith(k));
    if (match === undefined) return { ok: false, status: 404, json: async () => ({}) };
    return { ok: true, status: 200, json: async () => routes[match] };
  }) as any);
}

afterEach(() => vi.unstubAllGlobals());

describe('fetchAgents', () => {
  it('maps agent-studio agents to UI Agents and derives risk from guardrails', async () => {
    stubFetch({
      '/api/agent-studio/agents': {
        agents: [
          { agent_id: 'a1', name: 'Sender', role: 'outreach', tools: ['email'], published_local: true,
            evaluation: { score: 88, grade: 'A' }, guardrails: { requires_approval: ['send_email'] },
            memory_scope: { workspace: true }, versions: [{}, {}] },
          { agent_id: 'a2', name: 'Reader', role: 'read', tools: [], guardrails: {} },
        ],
      },
    });
    const agents = await fetchAgents();
    expect(agents).toHaveLength(2);
    expect(agents![0]).toMatchObject({ id: 'a1', name: 'Sender', status: 'active', qualityScore: 88, riskLevel: 'high', permissionLevel: 'approval-gated' });
    expect(agents![1]).toMatchObject({ id: 'a2', status: 'idle', riskLevel: 'low' });
  });

  it('returns null when the endpoint fails', async () => {
    stubFetch({}); // everything 404s
    expect(await fetchAgents()).toBeNull();
  });
});

describe('fetchGovernance', () => {
  it('maps events, classifying blocked/approved and risk score', async () => {
    stubFetch({
      '/api/governance': {
        recent_events: [
          { event_id: 'e1', created_at: '2026-07-06T05:04:46Z', blocked: true, agent_name: 'X', action_type: 'safety_block', risk_score: 8, reason: 'nope' },
          { event_id: 'e2', created_at: '2026-07-06T05:05:00Z', approved: true, agent_name: 'Y', action_type: 'approval_granted', tool_used: 't', risk_score: 2, reason: 'ok' },
        ],
      },
    });
    const gov = await fetchGovernance();
    expect(gov![0]).toMatchObject({ id: 'e1', type: 'safety_block', status: 'blocked', risk: 'high', timestamp: '05:04:46' });
    expect(gov![1]).toMatchObject({ type: 'approval_granted', status: 'allowed', risk: 'low' });
  });
});

describe('fetchSystemMetrics', () => {
  it('turns today metrics into labeled SystemMetric cards', async () => {
    stubFetch({ '/api/today/summary': { metrics: { workflow_runs: 13, learned_items: 3 } } });
    const m = await fetchSystemMetrics();
    const labels = m!.map((x) => x.label);
    expect(labels).toContain('Workflow Runs');
    expect(m!.find((x) => x.label === 'Learned Items')!.value).toBe('03'); // <10 zero-padded
  });
});

describe('fetchConnectors', () => {
  it('maps connectors and derives status/risk', async () => {
    stubFetch({
      '/api/mcp/connectors': {
        connectors: [
          { connector_id: 'c1', name: 'GH', enabled: true, risk_level: 'medium', allowed_actions: ['read'], last_checked_at: '2026-07-06T00:00:00Z' },
          { connector_id: 'c2', name: 'Bad', enabled: false, last_error: 'boom', risk_level: 'high' },
        ],
      },
    });
    const c = await fetchConnectors();
    expect(c![0]).toMatchObject({ id: 'c1', status: 'connected', riskLevel: 'medium', dryCheckPassed: true });
    expect(c![1]).toMatchObject({ id: 'c2', status: 'error', riskLevel: 'high', dryCheckPassed: false });
  });
});

describe('fetchApprovals', () => {
  it('maps approvals pending-first with governance checks', async () => {
    stubFetch({
      '/api/approvals': [
        { approval_id: 'ap1', status: 'approved', action_type: 'deploy', risk_level: 'high', summary: 'ship', created_at: '2026-07-06T01:00:00Z' },
        { approval_id: 'ap2', status: 'pending', action_type: 'send', risk_level: 'medium', summary: 'email', created_at: '2026-07-06T02:00:00Z' },
      ],
    });
    const a = await fetchApprovals();
    expect(a![0].status).toBe('pending'); // pending sorted first
    expect(a![0].governanceChecks.length).toBeGreaterThan(0);
  });
});

describe('fetchSystemHealth', () => {
  it('merges health + governance + today into a health object', async () => {
    stubFetch({
      '/health': { status: 'ok' },
      '/api/governance': { total_events: 120, blocked_actions: 4, approvals: 30 },
      '/api/today/summary': { metrics: { workflow_runs: 13, learned_items: 3 } },
    });
    const h = await fetchSystemHealth();
    expect(h).toMatchObject({ online: true, totalEvents: 120, blocked: 4, approvals: 30, workflowRuns: 13 });
  });
});

describe('fetchStorageStatus', () => {
  it('maps the v100 storage status endpoint', async () => {
    stubFetch({
      '/api/system/storage-status': {
        backend: 'postgres',
        configured_backend: 'postgres',
        collections: 197,
        total_documents: 105817,
        postgres_ready: true,
        redis_ready: true,
      },
    });
    const status = await fetchStorageStatus();
    expect(status).toMatchObject({
      backend: 'postgres',
      configuredBackend: 'postgres',
      collections: 197,
      totalDocuments: 105817,
      postgresReady: true,
      redisReady: true,
    });
  });

  it('returns null when storage status is unavailable', async () => {
    stubFetch({});
    expect(await fetchStorageStatus()).toBeNull();
  });
});

describe('fetchWorkflowRuns', () => {
  it('computes done/total per run', async () => {
    stubFetch({
      '/api/durable-workflows/runs': {
        runs: [{ run_id: 'r1', name: 'Weekly', status: 'waiting_approval', steps: [{ status: 'done' }, { status: 'skipped' }, { status: 'pending' }] }],
      },
    });
    const r = await fetchWorkflowRuns();
    expect(r![0]).toMatchObject({ id: 'r1', done: 2, total: 3, status: 'waiting_approval' });
  });
});

describe('Memory v2 helpers', () => {
  it('POSTs new semantic memory items', async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ ok: true, memory_id: 'm1', mode: 'pgvector' }) }));
    vi.stubGlobal('fetch', fetchMock as any);
    const result = await addMemoryV2('Remember this', 'Decision', 'test', { title: 'ADR' });
    expect(result).toMatchObject({ ok: true, id: 'm1', mode: 'pgvector' });
    expect(fetchMock.mock.calls[0][0]).toContain('/api/memory-v2/add');
    expect(JSON.parse((fetchMock.mock.calls[0][1] as any).body)).toMatchObject({
      text: 'Remember this',
      kind: 'Decision',
      source: 'test',
      metadata: { title: 'ADR' },
    });
  });

  it('maps semantic search results with pgvector mode and similarity', async () => {
    stubFetch({
      '/api/memory-v2/search': {
        mode: 'pgvector',
        count: 1,
        results: [
          {
            memory_id: 'm2',
            title: 'Storage migration decision',
            text: 'Keep JSON as fallback while Postgres comes online.',
            kind: 'Decision',
            source: 'project_brain',
            similarity: 0.91,
            metadata: { created_at: '2026-07-07' },
          },
        ],
      },
    });
    const response = await searchMemoryV2('storage migration', 5);
    expect(response).toMatchObject({ mode: 'pgvector', count: 1 });
    expect(response!.results[0]).toMatchObject({
      id: 'm2',
      title: 'Storage migration decision',
      kind: 'Decision',
      source: 'project_brain',
      similarity: 0.91,
      mode: 'pgvector',
    });
  });

  it('returns null for blank or unavailable semantic search', async () => {
    expect(await searchMemoryV2('   ')).toBeNull();
    stubFetch({});
    expect(await searchMemoryV2('missing')).toBeNull();
  });
});

describe('startDurableRun', () => {
  it('POSTs name + steps and returns true on success', async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ run_id: 'r9', status: 'running' }) }));
    vi.stubGlobal('fetch', fetchMock as any);
    const ok = await startDurableRun('My run', [{ name: 'step 1' }]);
    expect(ok).toBe(true);
    const call = fetchMock.mock.calls[0];
    expect(call[0]).toContain('/api/durable-workflows/runs');
    expect(JSON.parse((call[1] as any).body)).toMatchObject({ name: 'My run', steps: [{ name: 'step 1' }] });
  });

  it('returns false when the backend is offline', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('offline'); }) as any);
    expect(await startDurableRun('x', [])).toBe(false);
  });
});

describe('routeMessage', () => {
  it('passes execute and returns the answer + flags', async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ answer: 'hello', requires_approval: true, blocked_execution: false, suggested_workflow: 'wf' }) }));
    vi.stubGlobal('fetch', fetchMock as any);
    const res = await routeMessage('do a thing', true);
    expect(res).toMatchObject({ answer: 'hello', requiresApproval: true, suggestedWorkflow: 'wf' });
    const body = JSON.parse((fetchMock.mock.calls[0][1] as any).body);
    expect(body).toMatchObject({ text: 'do a thing', execute: true });
  });
});
