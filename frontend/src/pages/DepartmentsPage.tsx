import React, { useEffect, useState } from 'react';
import {
  Building2,
  Plus,
  RefreshCw,
  Sparkles,
  Target,
  Wallet,
  X,
  PlayCircle,
  ShieldAlert,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { GlassCard } from '../components/shared/GlassCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { RiskBadge } from '../components/shared/RiskBadge';
import {
  Department,
  DepartmentsOverview,
  DepartmentScorecard,
  fetchDepartments,
  fetchDepartmentsOverview,
  fetchDepartmentScorecard,
  seedDepartmentTemplates,
  createDepartment,
  createDepartmentGoal,
  setDepartmentBudget,
  planDepartmentRun,
} from '../data/api';

export const DepartmentsPage: React.FC = () => {
  const { showToast } = useApp();
  const [departments, setDepartments] = useState<Department[] | null>(null);
  const [overview, setOverview] = useState<DepartmentsOverview | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [scorecard, setScorecard] = useState<DepartmentScorecard | null>(null);
  const [busy, setBusy] = useState(false);

  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newManager, setNewManager] = useState('');
  const [newPermission, setNewPermission] = useState('read_only');

  const [goalTitle, setGoalTitle] = useState('');
  const [goalDescription, setGoalDescription] = useState('');
  const [budgetInput, setBudgetInput] = useState('100');
  const [runTask, setRunTask] = useState('');

  const refreshList = async () => {
    const [depts, ov] = await Promise.all([fetchDepartments(), fetchDepartmentsOverview()]);
    setDepartments(depts);
    setOverview(ov);
    if (depts && depts.length && !depts.some((d) => d.departmentId === selectedId)) {
      setSelectedId(depts[0].departmentId);
    }
  };

  useEffect(() => {
    refreshList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshScorecard = async (id = selectedId) => {
    if (!id) {
      setScorecard(null);
      return;
    }
    setScorecard(await fetchDepartmentScorecard(id));
  };

  useEffect(() => {
    refreshScorecard(selectedId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  const handleSeed = async () => {
    setBusy(true);
    try {
      const result = await seedDepartmentTemplates();
      if (!result) {
        showToast('Seed failed', 'warning');
        return;
      }
      showToast(`Seeded ${result.seededCount} department(s), ${result.skippedExisting} already existed.`, 'success');
      await refreshList();
    } finally {
      setBusy(false);
    }
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setBusy(true);
    try {
      const created = await createDepartment(newName.trim(), newDescription.trim(), newManager.trim(), newPermission);
      if (!created) {
        showToast('Create failed', 'warning');
        return;
      }
      showToast(`Created department "${created.name}".`, 'success');
      setShowCreate(false);
      setNewName('');
      setNewDescription('');
      setNewManager('');
      setNewPermission('read_only');
      await refreshList();
      setSelectedId(created.departmentId);
    } finally {
      setBusy(false);
    }
  };

  const handleCreateGoal = async () => {
    if (!selectedId || !goalTitle.trim()) return;
    setBusy(true);
    try {
      const goal = await createDepartmentGoal(selectedId, goalTitle.trim(), goalDescription.trim());
      if (!goal) {
        showToast('Goal creation declined -- no goal service wired for this department.', 'warning');
        return;
      }
      showToast(`Created goal "${goal.title}".`, 'success');
      setGoalTitle('');
      setGoalDescription('');
      await refreshScorecard();
    } finally {
      setBusy(false);
    }
  };

  const handleSetBudget = async () => {
    const value = Number(budgetInput);
    if (!selectedId || !Number.isFinite(value) || value < 0) return;
    setBusy(true);
    try {
      const ok = await setDepartmentBudget(selectedId, value);
      if (!ok) {
        showToast('Budget update declined -- no usage ledger wired for this department.', 'warning');
        return;
      }
      showToast(`Set monthly budget to $${value}.`, 'success');
      await refreshScorecard();
    } finally {
      setBusy(false);
    }
  };

  const handlePlanRun = async () => {
    if (!selectedId || !runTask.trim()) return;
    setBusy(true);
    try {
      const run = await planDepartmentRun(selectedId, runTask.trim());
      if (!run) {
        showToast('Plan run failed', 'warning');
        return;
      }
      if (run.status === 'blocked') {
        showToast(`Run blocked: ${run.blockReason || 'policy'}.`, 'warning');
      } else {
        showToast('Run planned -- workflow plan, never auto-executed.', 'success');
      }
      setRunTask('');
      await refreshScorecard();
      await refreshList();
    } finally {
      setBusy(false);
    }
  };

  const selectedDept = departments?.find((d) => d.departmentId === selectedId) || null;

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      <div className="rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-[#171524] via-[#14141c] to-[#101018] p-6 sm:p-8 shadow-2xl overflow-hidden relative">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold uppercase tracking-wider">
                v300 Digital Departments
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Departments</h1>
            <p className="text-xs sm:text-sm text-gray-300 leading-relaxed">
              Real, governed departments with goals, budgets, and measurable outcomes. Runs are planned, not
              auto-executed -- every workflow plan stays subject to the department's own permission level.
            </p>
          </div>
          <div className="flex gap-2 self-start lg:self-auto">
            <button
              onClick={handleSeed}
              disabled={busy}
              className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-200 flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              Seed Templates
            </button>
            <button
              onClick={() => setShowCreate(true)}
              className="px-4 py-2.5 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-300 text-xs font-bold flex items-center gap-2 transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Department
            </button>
            <button
              onClick={refreshList}
              className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-200 flex items-center justify-center gap-2 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Departments</div>
          <div className="text-2xl font-extrabold text-white">{overview?.totalDepartments ?? '—'}</div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Active</div>
          <div className="text-2xl font-extrabold text-white">{overview?.activeDepartments ?? '—'}</div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Runs Planned</div>
          <div className="text-2xl font-extrabold text-white">{overview?.departmentRuns ?? '—'}</div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Collaborations</div>
          <div className="text-2xl font-extrabold text-white">{overview?.collaborationCount ?? '—'}</div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <GlassCard className="space-y-0" padding="none">
            <div className="flex items-center gap-2 p-4 border-b border-white/[0.06]">
              <Building2 className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-white">Departments</span>
            </div>
            <div className="max-h-[600px] overflow-y-auto divide-y divide-white/[0.05]">
              {!departments ? (
                <div className="p-8 text-center text-xs text-gray-500 font-mono">Loading departments...</div>
              ) : departments.length === 0 ? (
                <div className="p-8 text-center text-xs text-gray-500 font-mono">
                  No departments yet -- seed templates or create one.
                </div>
              ) : (
                departments.map((d) => (
                  <button
                    key={d.departmentId}
                    onClick={() => setSelectedId(d.departmentId)}
                    className={`w-full text-left p-4 transition-colors ${
                      d.departmentId === selectedId ? 'bg-cyan-500/10' : 'hover:bg-white/[0.02]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <span className="text-sm font-bold text-white truncate block">{d.name}</span>
                        <p className="text-[11px] text-gray-500 truncate">{d.managerAgent}</p>
                      </div>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-gray-400 shrink-0">
                        {d.permissionLevel}
                      </span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </GlassCard>
        </div>

        <div className="lg:col-span-2 space-y-4">
          {!selectedDept ? (
            <GlassCard>
              <div className="py-12 text-center text-xs text-gray-500">Select a department to inspect.</div>
            </GlassCard>
          ) : (
            <>
              <GlassCard className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-sm font-bold text-white">{selectedDept.name}</h2>
                    <p className="text-xs text-gray-400 mt-1">{selectedDept.description}</p>
                  </div>
                  <StatusBadge status={selectedDept.active ? 'connected' : 'disconnected'} size="sm" />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-[11px] font-mono">
                  <div className="p-2 rounded-lg bg-black/30 border border-white/[0.06]">
                    <div className="text-gray-500">Manager</div>
                    <div className="text-white truncate">{selectedDept.managerAgent}</div>
                  </div>
                  <div className="p-2 rounded-lg bg-black/30 border border-white/[0.06]">
                    <div className="text-gray-500">Workers</div>
                    <div className="text-white truncate">{selectedDept.workerAgents.join(', ') || '—'}</div>
                  </div>
                  <div className="p-2 rounded-lg bg-black/30 border border-white/[0.06]">
                    <div className="text-gray-500">Permission</div>
                    <div className="text-white truncate">{selectedDept.permissionLevel}</div>
                  </div>
                </div>
              </GlassCard>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <GlassCard className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider">Goals</h3>
                  </div>
                  <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                    {(scorecard?.goals || []).length === 0 && (
                      <div className="text-[11px] text-gray-500 font-mono py-2 text-center">No goals yet.</div>
                    )}
                    {(scorecard?.goals || []).map((g) => (
                      <div key={g.goalId} className="p-2 rounded-lg bg-black/20 border border-white/[0.05]">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-[11px] text-white truncate">{g.title}</span>
                          <span className="text-[10px] font-mono text-gray-500 shrink-0">{g.progressPercent}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-2 pt-2 border-t border-white/10">
                    <input
                      value={goalTitle}
                      onChange={(e) => setGoalTitle(e.target.value)}
                      placeholder="New goal title"
                      className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-gray-500"
                    />
                    <button
                      onClick={handleCreateGoal}
                      disabled={busy || !goalTitle.trim()}
                      className="w-full px-3 py-2 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 font-bold text-xs transition-colors disabled:opacity-50"
                    >
                      Add Goal
                    </button>
                  </div>
                </GlassCard>

                <GlassCard className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Wallet className="w-4 h-4 text-amber-400" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider">Budget</h3>
                  </div>
                  {scorecard?.budget ? (
                    <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                      <div className="p-2 rounded-lg bg-black/30 border border-white/[0.06]">
                        <div className="text-gray-500">Monthly limit</div>
                        <div className="text-white">${scorecard.budget.monthlyLimit}</div>
                      </div>
                      <div className="p-2 rounded-lg bg-black/30 border border-white/[0.06]">
                        <div className="text-gray-500">This month</div>
                        <div className="text-white">${scorecard.budget.currentMonthCost.toFixed(2)}</div>
                      </div>
                      <div className="col-span-2 p-2 rounded-lg bg-black/30 border border-white/[0.06] flex items-center justify-between">
                        <span className="text-gray-500">Status</span>
                        <span
                          className={
                            scorecard.budget.budgetStatus === 'over'
                              ? 'text-rose-300'
                              : scorecard.budget.budgetStatus === 'near'
                              ? 'text-amber-300'
                              : 'text-emerald-300'
                          }
                        >
                          {scorecard.budget.budgetStatus}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-[11px] text-gray-500 font-mono py-2 text-center">No budget set.</div>
                  )}
                  <div className="space-y-2 pt-2 border-t border-white/10">
                    <input
                      type="number"
                      min={0}
                      value={budgetInput}
                      onChange={(e) => setBudgetInput(e.target.value)}
                      placeholder="Monthly limit ($)"
                      className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-gray-500"
                    />
                    <button
                      onClick={handleSetBudget}
                      disabled={busy}
                      className="w-full px-3 py-2 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 font-bold text-xs transition-colors disabled:opacity-50"
                    >
                      Set Budget
                    </button>
                  </div>
                </GlassCard>
              </div>

              <GlassCard className="space-y-3">
                <div className="flex items-center gap-2">
                  <PlayCircle className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider">Plan a Run</h3>
                </div>
                <p className="text-[11px] text-gray-500">
                  Plans a real workflow across this department's manager/worker/reviewer/auditor agents. Never
                  auto-executed -- blocked automatically if the department is over its monthly budget or its
                  permission level is "blocked".
                </p>
                <div className="flex gap-2">
                  <input
                    value={runTask}
                    onChange={(e) => setRunTask(e.target.value)}
                    placeholder="Task to plan, e.g. 'Draft the Q3 roadmap'"
                    className="flex-1 px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-gray-500"
                  />
                  <button
                    onClick={handlePlanRun}
                    disabled={busy || !runTask.trim()}
                    className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-white font-bold text-xs transition-colors disabled:opacity-50"
                  >
                    Plan Run
                  </button>
                </div>
                <div className="grid grid-cols-3 gap-2 text-[11px] font-mono pt-2 border-t border-white/10">
                  <div className="p-2 rounded-lg bg-black/30 border border-white/[0.06]">
                    <div className="text-gray-500">Total Runs</div>
                    <div className="text-white">{scorecard?.measurableOutcomes.totalRuns ?? '—'}</div>
                  </div>
                  <div className="p-2 rounded-lg bg-black/30 border border-white/[0.06]">
                    <div className="text-gray-500">Planned</div>
                    <div className="text-emerald-300">{scorecard?.measurableOutcomes.planned ?? '—'}</div>
                  </div>
                  <div className="p-2 rounded-lg bg-black/30 border border-white/[0.06] flex items-center gap-1">
                    <ShieldAlert className="w-3 h-3 text-rose-400 shrink-0" />
                    <div>
                      <div className="text-gray-500">Blocked</div>
                      <div className="text-rose-300">{scorecard?.measurableOutcomes.blocked ?? '—'}</div>
                    </div>
                  </div>
                </div>
              </GlassCard>
            </>
          )}
        </div>
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <GlassCard className="w-full max-w-md space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white">New Department</h3>
              <button onClick={() => setShowCreate(false)}>
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Department name"
              className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-gray-500"
            />
            <textarea
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              placeholder="Short description"
              className="w-full min-h-[60px] rounded-xl bg-black/40 border border-white/10 p-3 text-xs text-white placeholder-gray-500"
            />
            <input
              value={newManager}
              onChange={(e) => setNewManager(e.target.value)}
              placeholder="Manager agent (optional)"
              className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-gray-500"
            />
            <select
              value={newPermission}
              onChange={(e) => setNewPermission(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white"
            >
              <option value="read_only">read_only</option>
              <option value="plan_only">plan_only</option>
              <option value="approve_to_edit">approve_to_edit</option>
              <option value="approve_to_run">approve_to_run</option>
              <option value="blocked">blocked</option>
            </select>
            <button
              onClick={handleCreate}
              disabled={busy || !newName.trim()}
              className="w-full px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-white font-bold text-xs transition-colors disabled:opacity-50"
            >
              Create
            </button>
          </GlassCard>
        </div>
      )}
    </div>
  );
};
