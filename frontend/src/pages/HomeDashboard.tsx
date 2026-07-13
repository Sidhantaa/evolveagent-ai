import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { PageId } from '../types';
import { GlassCard } from '../components/shared/GlassCard';
import { MetricCard } from '../components/shared/MetricCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { RiskBadge } from '../components/shared/RiskBadge';
import { 
  Sparkles, 
  Search, 
  ArrowRight, 
  ShieldCheck, 
  CheckCircle2, 
  Clock, 
  Terminal, 
  Users, 
  Wrench, 
  Activity, 
  Check, 
  X, 
  Play, 
  ShieldAlert, 
  Database, 
  Github, 
  FolderGit2, 
  CheckSquare, 
  Layers 
} from 'lucide-react';

export const HomeDashboard: React.FC = () => {
  const { 
    systemMetrics, 
    agents, 
    tasks, 
    approvals, 
    connectors, 
    governanceLogs, 
    setActivePage, 
    setIsCommandModalOpen,
    approveRequest,
    rejectRequest,
    approveBatchLowRisk,
    runMockWorkflowStep,
    showToast 
  } = useApp();

  const [quickPrompt, setQuickPrompt] = useState('');

  const pendingApprovals = approvals.filter(a => a.status === 'pending');
  const activeAgents = agents.filter(a => a.status === 'active' || a.status === 'running');
  const recentTasks = tasks.slice(0, 5);

  const handlePromptSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickPrompt.trim()) return;
    showToast(`Initiating AI workflow for prompt: "${quickPrompt}"...`, 'success');
    setActivePage('chat');
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* 1. AI Command Center Hero Card */}
      <div className="relative rounded-3xl border border-cyan-500/30 bg-gradient-to-br from-[#1c1a29]/90 via-[#15151b]/95 to-[#121217]/90 p-6 sm:p-8 shadow-2xl overflow-hidden">
        {/* Glow backdrop */}
        <div className="absolute -top-20 -right-20 w-80 h-80 bg-cyan-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-xs font-mono mb-4">
            <Sparkles className="w-3.5 h-3.5 animate-spin" style={{ animationDuration: '6s' }} />
            <span>AI Command Center & Multi-Agent OS</span>
          </div>
          
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-white">
            What mission shall we delegate today?
          </h1>
          <p className="mt-2 text-sm sm:text-base text-gray-300">
            EvolveAgent AI routes high-level intents across specialized agents, maintains deep knowledge in Project Brain, and sandboxes every action under strict Governance safety rules.
          </p>

          {/* Quick Prompt Input Bar */}
          <form onSubmit={handlePromptSubmit} className="mt-6 flex flex-col sm:flex-row gap-2.5">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-400" />
              <input
                type="text"
                value={quickPrompt}
                onChange={(e) => setQuickPrompt(e.target.value)}
                placeholder="Ask anything or command agents (e.g. 'Redesign our dashboard cards', 'Scan GitHub repo')..."
                className="w-full bg-black/60 border border-white/15 focus:border-cyan-500/80 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none shadow-inner transition-all"
              />
              <kbd 
                onClick={() => setIsCommandModalOpen(true)}
                className="cursor-pointer absolute right-3 top-1/2 -translate-y-1/2 font-mono text-[11px] px-2 py-0.5 rounded bg-white/10 hover:bg-white/20 text-gray-300 border border-white/10 hidden sm:block"
              >
                ⌘K
              </kbd>
            </div>
            <button
              type="submit"
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-600 via-sky-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center gap-2"
            >
              <span>Launch Mission</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Action Chips */}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs text-gray-400 font-mono">Quick Actions:</span>
            {[
              { label: 'Review my repo', page: 'chat' as const, icon: Github },
              { label: 'Plan mission workflow', page: 'mission-control' as const, icon: CheckSquare },
              { label: 'Verify safety audit', page: 'governance' as const, icon: ShieldCheck },
              { label: 'Inspect Dev trace', page: 'dev-console' as const, icon: Terminal },
            ].map((action, i) => {
              const Icon = action.icon;
              return (
                <button
                  key={i}
                  onClick={() => { setActivePage(action.page); showToast(`Navigated to ${action.label}`, 'info'); }}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/[0.04] hover:bg-white/[0.09] border border-white/10 text-xs text-gray-300 hover:text-white transition-colors"
                >
                  <Icon className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{action.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 2. System Metrics — active ones get full cards, idle/zero ones collapse into one quiet line */}
      {(() => {
        const parseMetricValue = (val: string | number) => {
          const num = parseInt(String(val).replace(/[^0-9]/g, ''), 10);
          return Number.isNaN(num) ? 0 : num;
        };
        const activeMetrics = systemMetrics.filter(m => parseMetricValue(m.value) > 0);
        const idleMetrics = systemMetrics.filter(m => parseMetricValue(m.value) === 0);
        const metricIcons = [
          <Users className="w-4 h-4" />,
          <Activity className="w-4 h-4" />,
          <ShieldAlert className="w-4 h-4" />,
          <Wrench className="w-4 h-4" />,
          <ShieldCheck className="w-4 h-4" />,
        ];
        const metricPages: PageId[] = ['agents', 'mission-control', 'approvals', 'tools', 'governance'];

        return (
          <>
            {activeMetrics.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                {activeMetrics.map((m) => {
                  const originalIdx = systemMetrics.indexOf(m);
                  return (
                    <MetricCard
                      key={originalIdx}
                      label={m.label}
                      value={m.value}
                      trend={m.trend}
                      isPositive={m.isPositive}
                      subtitle={m.subtitle}
                      icon={metricIcons[originalIdx] ?? <Activity className="w-4 h-4" />}
                      onClick={() => setActivePage(metricPages[originalIdx] ?? 'home')}
                    />
                  );
                })}
              </div>
            )}
            {idleMetrics.length > 0 && (
              <div className="text-[11px] text-gray-500 leading-relaxed">
                {idleMetrics.map(m => m.label).join(' · ')} — idle, nothing active
              </div>
            )}
          </>
        );
      })()}

      {/* 3. Main Split Section: Live Activity Log (Left) & Approval Queue (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Live Agent Activity Timeline */}
        <div className="lg:col-span-2 space-y-4">
          <GlassCard className="h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-white/10">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-400 animate-pulse" />
                  <h3 className="text-sm font-semibold text-white">Live Agent Activity Log</h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300">
                    Real-Time Stream
                  </span>
                </div>
                <button
                  onClick={() => { setActivePage('dev-console'); showToast('Viewing full trace inspector', 'info'); }}
                  className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
                >
                  <span>View Full Trace</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Timeline Items */}
              <div className="mt-4 space-y-3">
                {recentTasks.map((t) => (
                  <div key={t.id} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-white/[0.05] border border-white/10 flex items-center justify-center text-sm shrink-0">
                        {t.assignedAgentName.includes('UI') ? '🎨' : t.assignedAgentName.includes('Memory') ? '🧠' : t.assignedAgentName.includes('Impl') ? '⚡' : '🛡️'}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-white">{t.title}</span>
                          <RiskBadge level={t.riskLevel} size="sm" />
                        </div>
                        <p className="text-[11px] text-gray-400 mt-0.5">{t.description}</p>
                        <div className="mt-2 flex items-center gap-3 text-[10px] text-gray-500 font-mono">
                          <span>Agent: <strong className="text-gray-300">{t.assignedAgentName}</strong></span>
                          <span>•</span>
                          <span>Phase: {t.phase}</span>
                          <span>•</span>
                          <span>{t.timestamp}</span>
                        </div>
                      </div>
                    </div>

                    <div className="shrink-0 self-center">
                      <StatusBadge status={t.status} size="sm" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-gray-400">
              <span className="font-mono text-[11px]">Mission #01 Progress: 62%</span>
              <button
                onClick={runMockWorkflowStep}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium text-xs flex items-center gap-1.5 transition-colors"
              >
                <Play className="w-3.5 h-3.5 text-emerald-400" />
                <span>Simulate Next Step</span>
              </button>
            </div>
          </GlassCard>
        </div>

        {/* Right 1 Col: Approval Queue Preview */}
        <div className="space-y-4">
          <GlassCard glow={pendingApprovals.length > 0 ? 'purple' : 'none'} className="h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-white/10">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  <h3 className="text-sm font-semibold text-white">Approval Queue</h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300">
                    {pendingApprovals.length} Pending
                  </span>
                </div>
                <button
                  onClick={() => setActivePage('approvals')}
                  className="text-xs text-cyan-400 hover:text-cyan-300 font-medium"
                >
                  View All
                </button>
              </div>

              {pendingApprovals.length === 0 ? (
                <div className="py-12 text-center text-gray-400">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                  <p className="text-xs font-medium text-white">All Clear!</p>
                  <p className="text-[11px] text-gray-500">No high-risk operations waiting in the sandbox.</p>
                </div>
              ) : (
                <div className="mt-4 space-y-3">
                  {pendingApprovals.map((app) => (
                    <div key={app.id} className="p-3.5 rounded-xl bg-amber-500/[0.04] border border-amber-500/20 space-y-2.5">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h4 className="text-xs font-semibold text-amber-200">{app.title}</h4>
                          <p className="text-[11px] text-gray-400 mt-0.5 line-clamp-2">{app.description}</p>
                        </div>
                        <RiskBadge level={app.riskLevel} size="sm" />
                      </div>

                      <div className="text-[10px] font-mono text-gray-500 flex items-center justify-between">
                        <span>Tool: <strong className="text-gray-300">{app.toolName}</strong></span>
                        <span>{app.timestamp}</span>
                      </div>

                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => approveRequest(app.id)}
                          className="flex-1 px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 font-semibold text-xs border border-emerald-500/30 transition-colors flex items-center justify-center gap-1"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Approve</span>
                        </button>
                        <button
                          onClick={() => rejectRequest(app.id)}
                          className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 font-medium text-xs border border-rose-500/20 transition-colors"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {pendingApprovals.some(a => a.riskLevel === 'low') && (
              <button
                onClick={approveBatchLowRisk}
                className="mt-4 w-full py-2 rounded-xl bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/40 text-cyan-300 font-medium text-xs transition-colors"
              >
                Approve Low-Risk Batch
              </button>
            )}
          </GlassCard>
        </div>
      </div>

      {/* 4. Bottom Split Section: Connected Tools Preview (Left) & Safety Governance Card (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connected Tools Preview */}
        <GlassCard>
          <div className="flex items-center justify-between pb-4 border-b border-white/10">
            <div className="flex items-center gap-2">
              <Wrench className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-white">Connected Tools & MCP Hub</h3>
            </div>
            <button
              onClick={() => setActivePage('tools')}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-medium"
            >
              Manage Hub ({connectors.length})
            </button>
          </div>

          <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
            {connectors.slice(0, 6).map((c) => (
              <div
                key={c.id}
                onClick={() => setActivePage('tools')}
                className="cursor-pointer p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.06] border border-white/5 hover:border-white/15 transition-all flex flex-col justify-between"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-white truncate">{c.name}</span>
                  <span className={`w-2 h-2 rounded-full ${c.status === 'connected' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                </div>
                <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-gray-500">
                  <span>{c.category}</span>
                  <span>{c.callsToday} calls</span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Safety & Governance Card */}
        <GlassCard glow="blue">
          <div className="flex items-center justify-between pb-4 border-b border-white/10">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-white">Safety & Governance Overview</h3>
            </div>
            <button
              onClick={() => setActivePage('governance')}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-medium"
            >
              Policy Matrix
            </button>
          </div>

          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/5">
              <div className="flex items-center gap-2.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <div>
                  <div className="text-xs font-medium text-white">Planning-First Mode Active</div>
                  <div className="text-[11px] text-gray-400">Agents formulate dry-run plans before execution</div>
                </div>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 font-semibold">ENABLED</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/5">
              <div className="flex items-center gap-2.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                <div>
                  <div className="text-xs font-medium text-white">Mock-Safe Sandbox Enforcement</div>
                  <div className="text-[11px] text-gray-400">High-risk filesystem and API operations require sign-off</div>
                </div>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 font-semibold">ENABLED</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/5">
              <div className="flex items-center gap-2.5">
                <div className="w-2 h-2 rounded-full bg-blue-400" />
                <div>
                  <div className="text-xs font-medium text-white">Audit Logging & Telemetry</div>
                  <div className="text-[11px] text-gray-400">{governanceLogs.length} events recorded in tamper-proof log</div>
                </div>
              </div>
              <span className="text-[10px] font-mono text-blue-400 font-semibold">ACTIVE</span>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
