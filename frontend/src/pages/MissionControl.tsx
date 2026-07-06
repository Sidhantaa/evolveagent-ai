import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { fetchWorkflowRuns, LiveWorkflowRun } from '../data/api';
import { GlassCard } from '../components/shared/GlassCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { RiskBadge } from '../components/shared/RiskBadge';
import { 
  Compass, 
  CheckSquare, 
  Users, 
  Sparkles, 
  ArrowRight, 
  Play, 
  ShieldAlert, 
  Activity, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Layers, 
  Check, 
  Cpu 
} from 'lucide-react';
import { TaskStatus } from '../types';

export const MissionControl: React.FC = () => {
  const { mission, tasks, agents, approvals, runMockWorkflowStep, showToast } = useApp();
  const [liveRuns, setLiveRuns] = useState<LiveWorkflowRun[] | null>(null);
  useEffect(() => { fetchWorkflowRuns().then(setLiveRuns); }, []);

  const handleApproveNext = () => {
    runMockWorkflowStep();
    showToast('Next recommended action approved & delegated to agents!', 'success');
  };

  const columns: { id: TaskStatus; label: string; color: string }[] = [
    { id: 'planned', label: 'Planned / Backlog', color: 'border-blue-500/30' },
    { id: 'running', label: 'In Progress / Running', color: 'border-purple-500/40' },
    { id: 'waiting_approval', label: 'Waiting Approval', color: 'border-amber-500/40' },
    { id: 'completed', label: 'Completed', color: 'border-emerald-500/40' }
  ];

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* 1. Active Mission Overview Header Card */}
      <div className="relative rounded-3xl border border-purple-500/30 bg-gradient-to-r from-[#171524] via-[#14141c] to-[#121216] p-6 sm:p-8 shadow-2xl overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 font-semibold uppercase tracking-wider">
                Active Mission #01
              </span>
              <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Running
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">{mission.title}</h1>
            <p className="text-xs sm:text-sm text-gray-300 leading-relaxed">{mission.description}</p>
          </div>

          {/* Assigned Agents Avatars & Progress Radial/Bar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 shrink-0 bg-white/[0.03] p-4 rounded-2xl border border-white/10">
            <div>
              <div className="text-[10px] font-mono uppercase text-gray-400 mb-1.5">Assigned Squad</div>
              <div className="flex items-center -space-x-2">
                {mission.assignedAgents.map((agId, idx) => {
                  const ag = agents.find(a => a.id === agId);
                  return (
                    <div
                      key={idx}
                      title={ag?.name}
                      className="w-9 h-9 rounded-full bg-[#1e1e26] border-2 border-[#121216] flex items-center justify-center text-sm shadow-md"
                    >
                      {ag?.avatar || '🤖'}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="w-full sm:w-44 space-y-1.5">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-gray-400">Total Progress</span>
                <span className="text-purple-300 font-bold">{mission.progress}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-black/60 overflow-hidden p-0.5 border border-white/5">
                <div className="h-full rounded-full bg-gradient-to-r from-purple-500 to-blue-500" style={{ width: `${mission.progress}%` }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Live durable-workflow runs (real backend data) */}
      {liveRuns && liveRuns.length > 0 && (
        <GlassCard>
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <span className="text-sm font-bold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" /> Live Workflow Runs
            </span>
            <span className="text-[11px] font-mono text-gray-400">{liveRuns.length} recent</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-3">
            {liveRuns.map(run => {
              const pct = run.total ? Math.round((run.done / run.total) * 100) : 0;
              const tone = run.status === 'completed' ? 'text-emerald-300' : run.status === 'waiting_approval' ? 'text-amber-300' : run.status === 'cancelled' ? 'text-gray-400' : 'text-purple-300';
              return (
                <div key={run.id} className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-gray-200 truncate">{run.name}</span>
                    <span className={`text-[10px] font-mono ${tone}`}>{run.status.replace('_', ' ')}</span>
                  </div>
                  <div className="mt-2 w-full h-1.5 rounded-full bg-black/50 overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-purple-500 to-blue-500" style={{ width: `${pct}%` }} />
                  </div>
                  <div className="text-[10px] text-gray-500 font-mono mt-1">{run.done}/{run.total} steps</div>
                </div>
              );
            })}
          </div>
        </GlassCard>
      )}

      {/* 2. Next Best Action Recommendation Banner */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-900/30 via-indigo-900/20 to-blue-900/30 border border-purple-500/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-purple-500/20 text-purple-300 shrink-0">
            <Sparkles className="w-5 h-5 animate-spin" style={{ animationDuration: '8s' }} />
          </div>
          <div>
            <div className="text-xs font-semibold text-purple-200 uppercase tracking-wide font-mono">Recommended Next Action</div>
            <p className="text-xs sm:text-sm text-white font-medium mt-0.5">
              UI Design Agent recommends synthesizing the <span className="text-purple-300 font-bold">Agents Overview grid</span> and verifying Mock-Safe permission profiles next.
            </p>
          </div>
        </div>
        <button
          onClick={handleApproveNext}
          className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition-all shadow-lg shadow-purple-500/20 flex items-center justify-center gap-2 shrink-0 self-start sm:self-auto"
        >
          <Check className="w-4 h-4 stroke-[3]" />
          <span>Approve Next Task</span>
        </button>
      </div>

      {/* 3. Mission Phase Tracker (5 Phases Step Bar) */}
      <GlassCard>
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Layers className="w-4 h-4 text-purple-400" />
          <span>Mission Phase Tracker</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {mission.phases.map((phase, idx) => {
            const isDone = phase.status === 'completed';
            const isCurr = phase.status === 'in_progress';
            return (
              <div
                key={phase.id}
                className={`p-3 rounded-xl border transition-all ${
                  isDone ? 'bg-emerald-500/[0.04] border-emerald-500/20 text-emerald-300' :
                  isCurr ? 'bg-purple-500/[0.08] border-purple-500/40 text-purple-200 shadow-md' :
                  'bg-white/[0.01] border-white/5 text-gray-500'
                }`}
              >
                <div className="flex items-center justify-between text-[11px] font-mono mb-1">
                  <span>Phase 0{idx + 1}</span>
                  <StatusBadge status={phase.status} size="sm" showIcon={false} />
                </div>
                <div className="text-xs font-semibold truncate text-white">{phase.title}</div>
                <div className="mt-2 flex items-center justify-between text-[10px] font-mono opacity-80">
                  <span>{phase.completedCount}/{phase.tasksCount} tasks</span>
                  <span>{Math.round((phase.completedCount / phase.tasksCount) * 100)}%</span>
                </div>
              </div>
            );
          })}
        </div>
      </GlassCard>

      {/* 4. Task Graph / Kanban Flow (4 columns) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <CheckSquare className="w-4 h-4 text-purple-400" />
            <span>Task Graph & Execution Pipeline</span>
          </h3>
          <span className="text-xs text-gray-400 font-mono">Showing {tasks.length} atomic operations</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {columns.map(col => {
            const colTasks = tasks.filter(t => t.status === col.id);
            return (
              <div key={col.id} className={`p-4 rounded-2xl bg-[#141418] border ${col.color} flex flex-col min-h-[350px]`}>
                <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-3">
                  <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">{col.label}</span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-white/10 text-gray-300">{colTasks.length}</span>
                </div>

                <div className="flex-1 space-y-3">
                  {colTasks.length === 0 ? (
                    <div className="py-8 text-center text-xs text-gray-500 font-mono">No tasks in this state</div>
                  ) : (
                    colTasks.map(t => (
                      <div
                        key={t.id}
                        className="p-3 rounded-xl bg-[#1a1a20] border border-white/10 hover:border-white/20 transition-all space-y-2 shadow-md"
                      >
                        <div className="flex items-start justify-between gap-1.5">
                          <span className="text-xs font-semibold text-white line-clamp-2">{t.title}</span>
                          <RiskBadge level={t.riskLevel} size="sm" />
                        </div>
                        <p className="text-[11px] text-gray-400 line-clamp-2">{t.description}</p>
                        <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-gray-500">
                          <span className="text-purple-300">{t.assignedAgentName}</span>
                          <span>{t.timestamp}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 5. Mission Intelligence & Health Panel */}
      <GlassCard glow="purple">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-purple-400" />
          <span>Mission Intelligence & Agent Confidence Scores</span>
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
            <div className="text-xs font-mono text-gray-400">Agent Confidence</div>
            <div className="text-2xl font-bold font-mono text-purple-300 mt-1">94%</div>
            <div className="text-[10px] text-emerald-400 mt-1">High predictability</div>
          </div>
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
            <div className="text-xs font-mono text-gray-400">Blockers Detected</div>
            <div className="text-2xl font-bold font-mono text-white mt-1">00</div>
            <div className="text-[10px] text-gray-500 mt-1">Smooth execution</div>
          </div>
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
            <div className="text-xs font-mono text-gray-400">Pending Approvals</div>
            <div className="text-2xl font-bold font-mono text-amber-400 mt-1">{approvals.filter(a => a.status === 'pending').length}</div>
            <div className="text-[10px] text-amber-300/80 mt-1">Gating external writes</div>
          </div>
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
            <div className="text-xs font-mono text-gray-400">Sandboxing Mode</div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">Active</div>
            <div className="text-[10px] text-gray-500 mt-1">Zero unplanned side effects</div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};
