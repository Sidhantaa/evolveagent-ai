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
  fetchCodeChangeRuns,
  fetchWorkflowRunDetail,
  approveDurableWorkflowStep,
  fetchWorkflowEffects,
  fetchCodeWriterStatus,
  fetchGitHubWriteStatus,
  addMemoryV2,
  searchMemoryV2,
  routeMessage,
  startDurableRun,
  fetchModelServingDashboard,
  runModelServingDryRun,
  fetchGpuWorkerDashboard,
  fetchPrunableCollections,
  runStoragePrune,
  fetchDepartments,
  fetchDepartmentTemplates,
  seedDepartmentTemplates,
  createDepartment,
  fetchDepartmentsOverview,
  fetchDepartmentScorecard,
  createDepartmentGoal,
  setDepartmentBudget,
  planDepartmentRun,
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

describe('v150 code-change workflow helpers', () => {
  it('filters durable workflow runs to code-write and pull-request runs', async () => {
    stubFetch({
      '/api/durable-workflows/runs': {
        runs: [
          { run_id: 'r1', name: 'Code write', status: 'waiting_approval', cursor: 0, steps: [{ id: 's1', action_type: 'write_code_change', status: 'waiting_approval', action_params: { file_path: 'x.ts', content: 'ok' } }] },
          { run_id: 'r2', name: 'Notify', status: 'completed', steps: [{ id: 's2', action_type: 'notify', status: 'done' }] },
          { run_id: 'r3', name: 'Open PR', status: 'waiting_approval', steps: [{ id: 's3', action_type: 'open_pull_request', status: 'waiting_approval', action_params: { github_repo: 'manit/repo' } }] },
        ],
      },
    });
    const runs = await fetchCodeChangeRuns();
    expect(runs!.map((run) => run.id)).toEqual(['r1', 'r3']);
    expect(runs![0].steps[0]).toMatchObject({ id: 's1', actionType: 'write_code_change', status: 'waiting_approval' });
  });

  it('fetches one durable workflow run detail', async () => {
    stubFetch({
      '/api/durable-workflows/runs/r1': {
        run_id: 'r1',
        name: 'Code write',
        status: 'waiting_approval',
        steps: [{ id: 's1', action_type: 'write_code_change', status: 'waiting_approval', output: '' }],
      },
    });
    const run = await fetchWorkflowRunDetail('r1');
    expect(run).toMatchObject({ id: 'r1', name: 'Code write', status: 'waiting_approval' });
    expect(run!.steps[0].actionType).toBe('write_code_change');
  });

  it('approves or rejects the current gated durable workflow step', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ run_id: 'r1', name: 'Code write', status: 'completed', steps: [{ id: 's1', status: 'done', action_type: 'write_code_change' }] }),
    }));
    vi.stubGlobal('fetch', fetchMock as any);
    const run = await approveDurableWorkflowStep('r1', true, 'looks good', 'tester');
    expect(run).toMatchObject({ id: 'r1', status: 'completed' });
    expect(fetchMock.mock.calls[0][0]).toContain('/api/durable-workflows/runs/r1/approve');
    expect(JSON.parse((fetchMock.mock.calls[0][1] as any).body)).toMatchObject({
      approved: true,
      note: 'looks good',
      approver: 'tester',
    });
  });

  it('maps durable workflow effects for declined-safe output and PR links', async () => {
    stubFetch({
      '/api/durable-workflows/effects': {
        effects: [
          {
            effect_id: 'e1',
            run_id: 'r1',
            step_id: 's1',
            action_type: 'open_pull_request',
            result: { pushed: true, wrote: true, pull_request: { url: 'https://github.com/x/y/pull/1', number: 1 } },
            created_at: '2026-07-09T01:00:00Z',
          },
        ],
      },
    });
    const effects = await fetchWorkflowEffects('r1');
    expect(effects![0]).toMatchObject({ id: 'e1', actionType: 'open_pull_request' });
    expect(effects![0].result.pull_request.url).toContain('/pull/1');
  });

  it('maps code-writer and GitHub write status without secret values', async () => {
    stubFetch({
      '/api/code-writer/status': {
        available: true,
        writes_enabled: false,
        writes_opt_in_env: 'CODE_WRITES_ENABLED',
        push_enabled: false,
        push_opt_in_env: 'CODE_WRITER_PUSH_ENABLED',
        allowed_repos_env: 'CODE_WRITER_ALLOWED_REPOS',
        allowed_repos: [],
        allowed_git_subcommands: ['add', 'commit'],
        note: 'off by default',
      },
      '/api/github/status': {
        available: true,
        configured: true,
        writes_enabled: false,
        supported_writes: [],
        note: 'safe',
      },
    });
    const code = await fetchCodeWriterStatus();
    const github = await fetchGitHubWriteStatus();
    expect(code).toMatchObject({ writesEnabled: false, writesOptInEnv: 'CODE_WRITES_ENABLED' });
    expect(github).toMatchObject({ configured: true, writesEnabled: false });
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

describe('v260 model serving + v240 GPU workers + storage retention (Compute Fabric)', () => {
  it('maps the model-serving dashboard', async () => {
    stubFetch({
      '/api/model-serving/dashboard': {
        backends: [
          { backend: 'ollama', name: 'Ollama', configured: true, reachable: true, models: ['llama3'], note: '' },
          { backend: 'vllm', name: 'vLLM', configured: false, reachable: false, models: [], note: 'not configured' },
        ],
        count: 2,
        reachable_count: 1,
        real_execution_default: 'disabled',
      },
    });
    const dash = await fetchModelServingDashboard();
    expect(dash).toMatchObject({ count: 2, reachableCount: 1, realExecutionDefault: 'disabled' });
    expect(dash!.backends[0]).toMatchObject({ backend: 'ollama', configured: true, reachable: true, models: ['llama3'] });
  });

  it('runs a model-serving dry-run', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true, status: 200,
      json: async () => ({ accepted: false, backend: 'ollama', model: 'llama3', declined_reason: 'not reachable', next_human_action: 'start it yourself', available_models: [] }),
    }));
    vi.stubGlobal('fetch', fetchMock as any);
    const result = await runModelServingDryRun('ollama', 'llama3');
    expect(result).toMatchObject({ accepted: false, backend: 'ollama', declinedReason: 'not reachable' });
    expect(fetchMock.mock.calls[0][0]).toContain('/api/model-serving/dry-run');
  });

  it('maps the GPU worker dashboard with risk levels', async () => {
    stubFetch({
      '/api/worker-registry/gpu/dashboard': {
        total_gpu_workers: 3,
        active_gpu_workers: 1,
        approval_required_for_real_execution: true,
        providers: [
          { provider: 'kaggle', name: 'Kaggle GPU Worker', enabled: true, configured: true, execution_enabled: true, risk_level: 'high', worker_count: 2, active_workers: 1, cost_warning: 'uses account quota', note: '' },
          { provider: 'local', name: 'Local GPU Workers', enabled: true, configured: false, execution_enabled: false, risk_level: 'low', worker_count: 0, active_workers: 0, cost_warning: '', note: '' },
        ],
      },
    });
    const dash = await fetchGpuWorkerDashboard();
    expect(dash).toMatchObject({ totalGpuWorkers: 3, activeGpuWorkers: 1, approvalRequiredForRealExecution: true });
    expect(dash!.providers[0]).toMatchObject({ provider: 'kaggle', riskLevel: 'high', executionEnabled: true });
  });

  it('falls back to low risk for an unrecognized risk_level value', async () => {
    stubFetch({
      '/api/worker-registry/gpu/dashboard': {
        total_gpu_workers: 0, active_gpu_workers: 0,
        providers: [{ provider: 'x', name: 'X', enabled: false, configured: false, execution_enabled: false, risk_level: 'not-a-real-level', worker_count: 0, active_workers: 0 }],
      },
    });
    const dash = await fetchGpuWorkerDashboard();
    expect(dash!.providers[0].riskLevel).toBe('low');
  });

  it('fetches prunable collections', async () => {
    stubFetch({
      '/api/system/storage-prune/collections': {
        collections: ['governance_log.json', 'chat_sessions.json'],
        min_older_than_days: 1,
        note: 'archive-then-delete',
      },
    });
    const result = await fetchPrunableCollections();
    expect(result).toMatchObject({ collections: ['governance_log.json', 'chat_sessions.json'], minOlderThanDays: 1 });
  });

  it('runs a storage-prune preview (dry_run) and a real prune', async () => {
    const fetchMock = vi.fn(async (url: string, opts: any) => {
      const body = JSON.parse(opts.body);
      if (body.dry_run) {
        return { ok: true, status: 200, json: async () => ({ collection: body.collection, older_than_days: body.older_than_days, total_records: 10, records_to_prune: 3, records_to_keep: 7, dry_run: true }) };
      }
      return { ok: true, status: 200, json: async () => ({ collection: body.collection, older_than_days: body.older_than_days, pruned_count: 3, remaining_count: 7, archive_path: '/data/archives/x.json', dry_run: false }) };
    });
    vi.stubGlobal('fetch', fetchMock as any);

    const preview = await runStoragePrune('governance_log.json', 90, true);
    expect(preview).toMatchObject({ dryRun: true, recordsToPrune: 3, recordsToKeep: 7 });

    const real = await runStoragePrune('governance_log.json', 90, false);
    expect(real).toMatchObject({ dryRun: false, prunedCount: 3, remainingCount: 7, archivePath: '/data/archives/x.json' });
  });
});

describe('v300 Digital Departments', () => {
  it('maps the departments list', async () => {
    stubFetch({
      '/api/departments': {
        departments: [
          { department_id: 'd1', name: 'Engineering', description: 'Builds things', manager_agent: 'Eng Mgr', worker_agents: ['Coder'], permission_level: 'approve_to_run', active: true, created_at: '2026-07-20T00:00:00Z' },
        ],
        total_departments: 1,
      },
    });
    const depts = await fetchDepartments();
    expect(depts).toHaveLength(1);
    expect(depts![0]).toMatchObject({ departmentId: 'd1', name: 'Engineering', managerAgent: 'Eng Mgr', permissionLevel: 'approve_to_run', active: true });
  });

  it('maps department templates', async () => {
    stubFetch({
      '/api/departments/templates': {
        templates: [{ name: 'Research', description: 'Gathers evidence', manager_agent: 'Research Mgr', worker_agents: [], permission_level: 'read_only' }],
        count: 1,
      },
    });
    const templates = await fetchDepartmentTemplates();
    expect(templates![0]).toMatchObject({ name: 'Research', managerAgent: 'Research Mgr', permissionLevel: 'read_only' });
  });

  it('seeds department templates', async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ seeded_count: 6, skipped_existing: 0, departments: [] }) }));
    vi.stubGlobal('fetch', fetchMock as any);
    const result = await seedDepartmentTemplates();
    expect(result).toMatchObject({ seededCount: 6, skippedExisting: 0 });
    expect(fetchMock.mock.calls[0][0]).toContain('/api/departments/templates/seed');
  });

  it('creates a department', async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ department_id: 'd2', name: 'Finance', manager_agent: 'Finance Mgr', permission_level: 'read_only', active: true }) }));
    vi.stubGlobal('fetch', fetchMock as any);
    const dept = await createDepartment('Finance', 'Estimates costs', 'Finance Mgr', 'read_only');
    expect(dept).toMatchObject({ departmentId: 'd2', name: 'Finance' });
    const body = JSON.parse((fetchMock.mock.calls[0][1] as any).body);
    expect(body).toMatchObject({ name: 'Finance', manager_agent: 'Finance Mgr', permission_level: 'read_only' });
  });

  it('maps the departments overview', async () => {
    stubFetch({
      '/api/departments/overview': {
        total_departments: 3, active_departments: 3, department_runs: 5, collaboration_count: 1,
        recent_runs: [{ department_run_id: 'r1', department_id: 'd1', department_name: 'Engineering', task: 'ship it', requires_approval: true, risk_level: 'medium', status: 'planned', created_at: '2026-07-20T00:00:00Z' }],
      },
    });
    const overview = await fetchDepartmentsOverview();
    expect(overview).toMatchObject({ totalDepartments: 3, activeDepartments: 3, departmentRuns: 5, collaborationCount: 1 });
    expect(overview!.recentRuns[0]).toMatchObject({ departmentRunId: 'r1', task: 'ship it', riskLevel: 'medium' });
  });

  it('maps the department scorecard, including a null budget when none is set', async () => {
    stubFetch({
      '/api/departments/d1/scorecard': {
        department: { department_id: 'd1', name: 'Engineering', active: true },
        goals: [{ goal_id: 'g1', title: 'Ship v1', status: 'active', progress_percent: 40 }],
        budget: null,
        measurable_outcomes: { total_runs: 2, planned: 1, blocked: 1 },
      },
    });
    const scorecard = await fetchDepartmentScorecard('d1');
    expect(scorecard!.department).toMatchObject({ departmentId: 'd1', name: 'Engineering' });
    expect(scorecard!.goals[0]).toMatchObject({ goalId: 'g1', title: 'Ship v1', progressPercent: 40 });
    expect(scorecard!.budget).toBeNull();
    expect(scorecard!.measurableOutcomes).toMatchObject({ totalRuns: 2, planned: 1, blocked: 1 });
  });

  it('maps a scorecard with a real budget', async () => {
    stubFetch({
      '/api/departments/d1/scorecard': {
        department: { department_id: 'd1', name: 'Engineering', active: true },
        goals: [],
        budget: { monthly_limit: 100, current_month_cost: 42.5, total_estimated_cost: 200, budget_status: 'near', warning: 'Approaching the monthly budget.' },
        measurable_outcomes: { total_runs: 0, planned: 0, blocked: 0 },
      },
    });
    const scorecard = await fetchDepartmentScorecard('d1');
    expect(scorecard!.budget).toMatchObject({ monthlyLimit: 100, currentMonthCost: 42.5, budgetStatus: 'near' });
  });

  it('creates a department goal', async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ goal_id: 'g2', goal_title: 'New goal', goal_summary: '', status: 'active' }) }));
    vi.stubGlobal('fetch', fetchMock as any);
    const goal = await createDepartmentGoal('d1', 'New goal', '');
    expect(goal).toMatchObject({ goalId: 'g2', title: 'New goal' });
    expect(fetchMock.mock.calls[0][0]).toContain('/api/departments/d1/goals');
  });

  it('sets a department budget', async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ budget_id: 'b1', monthly_limit: 50 }) }));
    vi.stubGlobal('fetch', fetchMock as any);
    const ok = await setDepartmentBudget('d1', 50);
    expect(ok).toBe(true);
    const body = JSON.parse((fetchMock.mock.calls[0][1] as any).body);
    expect(body).toMatchObject({ monthly_limit: 50 });
  });

  it('plans a department run and reports a blocked status', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true, status: 200,
      json: async () => ({ department_run_id: 'r2', department_id: 'd1', department_name: 'Engineering', task: 'x', requires_approval: true, risk_level: 'high', status: 'blocked', block_reason: 'budget_exceeded' }),
    }));
    vi.stubGlobal('fetch', fetchMock as any);
    const run = await planDepartmentRun('d1', 'x');
    expect(run).toMatchObject({ departmentRunId: 'r2', status: 'blocked', blockReason: 'budget_exceeded' });
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
