import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Calendar,
  Check,
  Github,
  ListChecks,
  Plus,
  RefreshCw,
  Sparkles,
  Target,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { GlassCard } from '../components/shared/GlassCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { RiskBadge } from '../components/shared/RiskBadge';
import {
  ChiefFollowup,
  ChiefOfStaffDashboard,
  ChiefOfStaffStatus,
  createChiefFollowup,
  fetchChiefFollowups,
  fetchChiefOfStaffDashboard,
  fetchChiefOfStaffStatus,
  generateChiefDailyPlan,
  generateChiefWeeklyPlan,
  updateChiefFollowupStatus,
} from '../data/api';

const priorityTone = (priority: string): 'low' | 'medium' | 'high' => {
  if (priority === 'high') return 'high';
  if (priority === 'low') return 'low';
  return 'medium';
};

export const ChiefOfStaffPage: React.FC = () => {
  const { showToast } = useApp();
  const [status, setStatus] = useState<ChiefOfStaffStatus | null>(null);
  const [dashboard, setDashboard] = useState<ChiefOfStaffDashboard | null>(null);
  const [followups, setFollowups] = useState<ChiefFollowup[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDue, setNewDue] = useState('');
  const [newPriority, setNewPriority] = useState('medium');

  const refreshAll = async () => {
    const [s, d, f] = await Promise.all([
      fetchChiefOfStaffStatus(),
      fetchChiefOfStaffDashboard(),
      fetchChiefFollowups(),
    ]);
    setStatus(s);
    setDashboard(d);
    setFollowups(f?.followups ?? null);
  };

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleDailyPlan = async () => {
    setBusy(true);
    try {
      const plan = await generateChiefDailyPlan();
      if (!plan) {
        showToast('Daily-plan endpoint unavailable', 'warning');
        return;
      }
      showToast('Daily plan generated.', 'success');
      await refreshAll();
    } finally {
      setBusy(false);
    }
  };

  const handleWeeklyPlan = async () => {
    setBusy(true);
    try {
      const plan = await generateChiefWeeklyPlan();
      if (!plan) {
        showToast('Weekly-plan endpoint unavailable', 'warning');
        return;
      }
      showToast('Weekly plan generated.', 'success');
      await refreshAll();
    } finally {
      setBusy(false);
    }
  };

  const handleAddFollowup = async () => {
    if (!newTitle.trim()) return;
    setBusy(true);
    try {
      const created = await createChiefFollowup(newTitle.trim(), newDue, newPriority);
      if (!created) {
        showToast('Could not create follow-up', 'warning');
        return;
      }
      setNewTitle('');
      setNewDue('');
      setNewPriority('medium');
      showToast('Follow-up added.', 'success');
      await refreshAll();
    } finally {
      setBusy(false);
    }
  };

  const handleMarkDone = async (followupId: string) => {
    setBusy(true);
    try {
      const ok = await updateChiefFollowupStatus(followupId, 'done');
      if (!ok) {
        showToast('Could not update follow-up', 'warning');
        return;
      }
      await refreshAll();
    } finally {
      setBusy(false);
    }
  };

  const openFollowups = (followups || []).filter((f) => f.status === 'open');

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      <div className="rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-[#171524] via-[#14141c] to-[#101018] p-6 sm:p-8 shadow-2xl overflow-hidden relative">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold uppercase tracking-wider">
                v180 Personal Chief of Staff
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Chief of Staff</h1>
            <p className="text-xs sm:text-sm text-gray-300 leading-relaxed">
              Real priority ranking across goals, tasks, leads, risks, approvals, follow-ups — and open GitHub
              PRs/issues when configured.
            </p>
          </div>
          <button
            onClick={refreshAll}
            className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-200 flex items-center justify-center gap-2 transition-colors self-start lg:self-auto"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <GlassCard className="space-y-3">
        <div className="flex items-center gap-2">
          <Github className="w-4 h-4 text-gray-300" />
          <h2 className="text-sm font-bold text-white">GitHub signal</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] uppercase tracking-wider font-mono text-gray-500">Wired</div>
            <StatusBadge status={status?.githubWired ? 'connected' : 'disconnected'} size="sm" />
          </div>
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] uppercase tracking-wider font-mono text-gray-500">Repos configured</div>
            <div className="text-xs text-white font-mono">
              {status?.githubReposConfigured.length ? status.githubReposConfigured.join(', ') : `none — set ${status?.githubReposEnv || 'CHIEF_OF_STAFF_GITHUB_REPOS'}`}
            </div>
          </div>
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] uppercase tracking-wider font-mono text-gray-500">Items folded into priorities</div>
            <div className="text-xl font-extrabold text-white">{dashboard?.githubItemsCount ?? 0}</div>
          </div>
        </div>
      </GlassCard>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Open follow-ups</div>
          <div className="text-2xl font-extrabold text-white">{dashboard?.openFollowups ?? '—'}</div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Overdue</div>
          <div className="text-2xl font-extrabold text-amber-400">{dashboard?.overdueFollowups ?? '—'}</div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Blocked items</div>
          <div className="text-2xl font-extrabold text-rose-400">{dashboard?.blockedItems ?? '—'}</div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Open risks</div>
          <div className="text-2xl font-extrabold text-white">{dashboard?.riskSummary.openRiskCount ?? '—'}</div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <GlassCard className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-bold text-white">Today's plan</h2>
              </div>
              <button
                onClick={handleDailyPlan}
                disabled={busy}
                className="px-3 py-2 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-300 font-bold text-xs flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Generate daily plan
              </button>
            </div>
            {dashboard?.dailyPlan ? (
              <>
                <p className="text-xs text-gray-300">{dashboard.dailyPlan.summary}</p>
                <div className="space-y-2">
                  {dashboard.dailyPlan.topPriorities.map((item) => (
                    <div key={item.itemId} className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-gray-400 uppercase">{item.itemType}</span>
                          <span className="text-xs font-bold text-white truncate">{item.title}</span>
                        </div>
                        <p className="text-[11px] text-gray-500">{item.reason}</p>
                        <p className="text-[11px] text-cyan-300 mt-0.5">{item.recommendedAction}</p>
                      </div>
                      <span className="text-xs font-mono text-gray-400 shrink-0">{item.priorityScore}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="py-8 text-center text-xs text-gray-500 font-mono">No daily plan yet — generate one.</div>
            )}
          </GlassCard>

          <GlassCard className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-blue-400" />
                <h2 className="text-sm font-bold text-white">This week</h2>
              </div>
              <button
                onClick={handleWeeklyPlan}
                disabled={busy}
                className="px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-gray-200 font-bold text-xs flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                Generate weekly plan
              </button>
            </div>
            {dashboard?.weeklyPlan ? (
              <>
                <p className="text-xs text-gray-300">{dashboard.weeklyPlan.summary}</p>
                <div className="flex flex-wrap gap-2">
                  {dashboard.weeklyPlan.priorityThemes.map((t) => (
                    <span key={t.theme} className="text-[11px] font-mono px-2 py-1 rounded-lg bg-white/[0.04] border border-white/10 text-gray-300">
                      {t.theme}: {t.count}
                    </span>
                  ))}
                </div>
              </>
            ) : (
              <div className="py-6 text-center text-xs text-gray-500 font-mono">No weekly plan yet — generate one.</div>
            )}
          </GlassCard>
        </div>

        <div className="space-y-6">
          <GlassCard className="space-y-3">
            <div className="flex items-center gap-2">
              <ListChecks className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white">Follow-ups</h3>
            </div>
            <div className="flex gap-2">
              <input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="New follow-up..."
                className="flex-1 min-w-0 rounded-xl bg-black/40 border border-white/10 px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              />
              <button
                onClick={handleAddFollowup}
                disabled={busy || !newTitle.trim()}
                className="px-3 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 disabled:opacity-50"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-1.5 max-h-96 overflow-y-auto pr-1">
              {openFollowups.length === 0 && (
                <div className="text-[11px] text-gray-500 font-mono py-2 text-center">No open follow-ups.</div>
              )}
              {openFollowups.map((f) => (
                <div key={f.followupId} className="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-black/20 border border-white/[0.05]">
                  <div className="min-w-0">
                    <div className="text-xs text-white truncate">{f.title}</div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <RiskBadge level={priorityTone(f.priority)} size="sm" />
                      {f.dueDate && <span className="text-[10px] font-mono text-gray-500">{f.dueDate}</span>}
                    </div>
                  </div>
                  <button
                    onClick={() => handleMarkDone(f.followupId)}
                    disabled={busy}
                    className="p-1.5 rounded-lg bg-white/5 hover:bg-emerald-500/20 border border-white/10 text-gray-300 hover:text-emerald-300 transition-colors shrink-0"
                  >
                    <Check className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </GlassCard>

          {dashboard?.recommendedNextAction && (
            <GlassCard className="space-y-2 border-amber-500/20">
              <div className="flex items-center gap-2 text-amber-300">
                <AlertTriangle className="w-4 h-4" />
                <h3 className="text-xs font-bold uppercase tracking-wider">Recommended next action</h3>
              </div>
              <p className="text-xs text-white">{dashboard.recommendedNextAction}</p>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
