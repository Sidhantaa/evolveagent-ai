import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import {
  fetchStorageStatus, fetchSystemHealth, StorageStatus, SystemHealth,
  fetchModelServingDashboard, runModelServingDryRun, ModelServingDashboard,
  fetchGpuWorkerDashboard, GpuWorkerDashboard,
  fetchPrunableCollections, runStoragePrune, PrunableCollections, StoragePruneResult,
  fetchSchedulerTickStatus, SchedulerTickStatus,
} from '../data/api';
import { GlassCard } from '../components/shared/GlassCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { RiskBadge } from '../components/shared/RiskBadge';
import {
  Terminal,
  Play,
  Pause,
  Download,
  Search,
  Filter,
  Code2,
  ShieldCheck,
  Cpu,
  Database,
  Activity,
  CheckCircle2,
  Clock,
  ArrowRight,
  Layers,
  Sparkles,
  ChevronRight,
  Server,
  Trash2,
  Archive,
  Zap
} from 'lucide-react';

export const DevModeConsole: React.FC = () => {
  const { traceSteps, runMockWorkflowStep, governanceLogs, agents, connectors, approvals, showToast } = useApp();
  const [isPaused, setIsPaused] = useState(false);
  const [selectedStep, setSelectedStep] = useState(traceSteps[traceSteps.length - 1]?.step || 1);
  const [logFilter, setLogFilter] = useState('');
  const [activeTab, setActiveTab] = useState<'trace' | 'json' | 'tools'>('trace');

  const currentStepData = traceSteps.find(s => s.step === selectedStep) || traceSteps[0];

  const handleExport = () => {
    const jsonStr = JSON.stringify({ trace: traceSteps, governance: governanceLogs }, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evolve-agent-trace-TR-9942-AX-${Date.now()}.json`;
    a.click();
    showToast('Exported trace & governance logs to JSON', 'success');
  };

  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [storageStatus, setStorageStatus] = useState<StorageStatus | null>(null);
  useEffect(() => {
    fetchSystemHealth().then(setHealth);
    fetchStorageStatus().then(setStorageStatus);
  }, []);

  // v260 model serving + v240 GPU workers (Compute Fabric)
  const [modelServing, setModelServing] = useState<ModelServingDashboard | null>(null);
  const [gpuDashboard, setGpuDashboard] = useState<GpuWorkerDashboard | null>(null);
  useEffect(() => {
    fetchModelServingDashboard().then(setModelServing);
    fetchGpuWorkerDashboard().then(setGpuDashboard);
  }, []);
  const refreshComputeFabric = async () => {
    const [ms, gpu] = await Promise.all([fetchModelServingDashboard(), fetchGpuWorkerDashboard()]);
    setModelServing(ms);
    setGpuDashboard(gpu);
    showToast(ms || gpu ? 'Compute Fabric status refreshed' : 'Compute Fabric endpoints unavailable', ms || gpu ? 'success' : 'info');
  };

  // v120 scheduler tick + v280 target 2 auto-dispatch (opt-in, off by default)
  const [tickStatus, setTickStatus] = useState<SchedulerTickStatus | null>(null);
  useEffect(() => {
    fetchSchedulerTickStatus().then(setTickStatus);
  }, []);
  const refreshTickStatus = async () => {
    const status = await fetchSchedulerTickStatus();
    setTickStatus(status);
    showToast(status ? 'Scheduler tick status refreshed' : 'Scheduler tick status unavailable', status ? 'success' : 'info');
  };

  // Storage retention (manual, archive-then-delete; dry_run defaults true)
  const [prunable, setPrunable] = useState<PrunableCollections | null>(null);
  const [pruneCollection, setPruneCollection] = useState<string>('');
  const [pruneOlderThanDays, setPruneOlderThanDays] = useState<number>(90);
  const [prunePreview, setPrunePreview] = useState<StoragePruneResult | null>(null);
  const [pruneBusy, setPruneBusy] = useState(false);
  useEffect(() => {
    fetchPrunableCollections().then(data => {
      setPrunable(data);
      if (data && data.collections.length > 0) setPruneCollection(data.collections[0]);
    });
  }, []);
  const handlePreviewPrune = async () => {
    if (!pruneCollection) return;
    setPruneBusy(true);
    const result = await runStoragePrune(pruneCollection, pruneOlderThanDays, true);
    setPruneBusy(false);
    setPrunePreview(result);
    showToast(result ? `Preview: ${result.recordsToPrune ?? 0} record(s) would be pruned` : 'Preview failed', result ? 'info' : 'warning');
  };
  const handleRealPrune = async () => {
    if (!pruneCollection || !prunePreview) return;
    const confirmed = window.confirm(
      `Permanently prune ${prunePreview.recordsToPrune ?? 0} record(s) older than ${pruneOlderThanDays} day(s) from ${pruneCollection}? They will be archived first, then removed from the live collection.`
    );
    if (!confirmed) return;
    setPruneBusy(true);
    const result = await runStoragePrune(pruneCollection, pruneOlderThanDays, false);
    setPruneBusy(false);
    setPrunePreview(result);
    showToast(result ? `Pruned ${result.prunedCount ?? 0} record(s)` : 'Prune failed', result ? 'success' : 'warning');
  };

  const filteredLogs = governanceLogs.filter(l =>
    l.agentName.toLowerCase().includes(logFilter.toLowerCase()) || 
    l.action.toLowerCase().includes(logFilter.toLowerCase()) ||
    l.type.toLowerCase().includes(logFilter.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* 1. System Health Bar (6 counters) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Backend', value: health ? (health.online ? 'Online' : 'Down') : '—', sub: health ? 'health :8000' : 'checking…', color: health?.online ? 'text-emerald-400' : 'text-gray-400' },
          { label: 'Gov Events', value: health ? `${health.totalEvents}` : `${governanceLogs.length}`, sub: 'Tamper-proof log', color: 'text-sky-400' },
          { label: 'Blocked', value: health ? `${health.blocked}` : '0', sub: 'Safety blocks', color: 'text-rose-400' },
          { label: 'Approvals', value: health ? `${health.approvals}` : '0', sub: 'Granted', color: 'text-emerald-400' },
          { label: 'Active Agents', value: `${agents.filter(a => a.status !== 'idle').length}/${agents.length}`, sub: 'Orchestrating', color: 'text-cyan-400' },
          { label: 'Workflow Runs', value: health ? `${health.workflowRuns}` : '0', sub: 'Durable', color: 'text-amber-400' },
        ].map((item, idx) => (
          <div key={idx} className="p-3 rounded-2xl bg-[#171717]/80 border border-white/[0.07] backdrop-blur-xl space-y-1">
            <div className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">{item.label}</div>
            <div className={`text-2xl font-bold font-mono tracking-tight ${item.color}`}>{item.value}</div>
            <div className="text-[10px] text-gray-500 font-mono truncate">{item.sub}</div>
          </div>
        ))}
      </div>

      {/* 2. v100 Storage foundation status */}
      <GlassCard className="space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-300 border border-blue-500/20">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-sm font-bold text-white">Storage</h3>
                <StatusBadge status={storageStatus ? 'connected' : 'waiting'} size="sm" showIcon={false} />
                <span className={`text-[11px] font-mono px-2 py-0.5 rounded-full border ${
                  (storageStatus?.backend || 'json').toLowerCase() === 'postgres'
                    ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                    : 'bg-blue-500/15 text-blue-300 border-blue-500/30'
                }`}>
                  {(storageStatus?.backend || 'json').toUpperCase()}
                </span>
              </div>
              <p className="text-xs text-gray-400 font-mono mt-1">
                v100 storage backend readiness. JSON fallback remains safe when Postgres or Redis are unavailable.
              </p>
            </div>
          </div>

          <button
            onClick={async () => {
              const latest = await fetchStorageStatus();
              setStorageStatus(latest);
              showToast(latest ? 'Storage status refreshed' : 'Storage status endpoint unavailable', latest ? 'success' : 'info');
            }}
            className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-300 flex items-center gap-1.5 transition-colors self-start"
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Refresh Storage</span>
          </button>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            {
              label: 'Collections',
              value: storageStatus ? storageStatus.collections.toLocaleString() : '—',
              sub: 'Storage collections',
              color: 'text-cyan-300',
            },
            {
              label: 'Documents',
              value: storageStatus ? storageStatus.totalDocuments.toLocaleString() : '—',
              sub: 'Total records',
              color: 'text-emerald-300',
            },
            {
              label: 'Postgres',
              value: storageStatus?.postgresReady ? 'Ready' : 'Offline',
              sub: `Configured: ${storageStatus?.configuredBackend || 'json'}`,
              color: storageStatus?.postgresReady ? 'text-emerald-300' : 'text-amber-300',
            },
            {
              label: 'Redis',
              value: storageStatus?.redisReady ? 'Ready' : 'Optional',
              sub: 'Read-through cache',
              color: storageStatus?.redisReady ? 'text-emerald-300' : 'text-gray-400',
            },
          ].map(item => (
            <div key={item.label} className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
              <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">{item.label}</div>
              <div className={`text-xl font-bold font-mono tracking-tight ${item.color}`}>{item.value}</div>
              <div className="text-[10px] text-gray-500 font-mono truncate">{item.sub}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-[11px] font-mono text-gray-300">
          <div className="flex items-center gap-2 rounded-xl bg-white/[0.025] border border-white/[0.06] px-3 py-2">
            <span className={`w-2 h-2 rounded-full ${storageStatus ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            <span>{storageStatus ? 'Live backend status loaded' : 'Using safe loading state'}</span>
          </div>
          <div className="flex items-center gap-2 rounded-xl bg-white/[0.025] border border-white/[0.06] px-3 py-2">
            <span className={`w-2 h-2 rounded-full ${storageStatus?.postgresReady ? 'bg-emerald-400' : 'bg-gray-500'}`} />
            <span>Postgres JSONB backend is {storageStatus?.postgresReady ? 'reachable' : 'not required'}</span>
          </div>
          <div className="flex items-center gap-2 rounded-xl bg-white/[0.025] border border-white/[0.06] px-3 py-2">
            <span className={`w-2 h-2 rounded-full ${storageStatus?.redisReady ? 'bg-emerald-400' : 'bg-gray-500'}`} />
            <span>Redis cache is {storageStatus?.redisReady ? 'reachable' : 'optional'}</span>
          </div>
        </div>

        {/* Storage retention -- manual, archive-then-delete; dry_run defaults true */}
        <div className="pt-4 mt-2 border-t border-white/10 space-y-3">
          <div className="flex items-center gap-2">
            <Archive className="w-3.5 h-3.5 text-amber-400" />
            <h4 className="text-xs font-bold text-white">Storage Retention</h4>
            <span className="text-[10px] font-mono text-gray-500">Manual only — nothing runs automatically</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={pruneCollection}
              onChange={(e) => { setPruneCollection(e.target.value); setPrunePreview(null); }}
              className="bg-black/50 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none"
            >
              {(prunable?.collections || []).map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <input
              type="number"
              min={prunable?.minOlderThanDays ?? 1}
              value={pruneOlderThanDays}
              onChange={(e) => { setPruneOlderThanDays(Number(e.target.value)); setPrunePreview(null); }}
              className="w-24 bg-black/50 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none"
            />
            <span className="text-[11px] text-gray-400">days or older</span>
            <button
              onClick={handlePreviewPrune}
              disabled={pruneBusy || !pruneCollection}
              className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-300 flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Preview</span>
            </button>
            <button
              onClick={handleRealPrune}
              disabled={pruneBusy || !prunePreview || (prunePreview.recordsToPrune ?? 0) === 0}
              className="px-3 py-1.5 rounded-xl bg-rose-600/80 hover:bg-rose-500 text-white text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-40"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Prune for real</span>
            </button>
          </div>
          {prunePreview && (
            <div className="text-[11px] font-mono text-gray-300 bg-black/30 border border-white/[0.07] rounded-xl px-3 py-2">
              {prunePreview.dryRun ? (
                <span>Preview: {prunePreview.recordsToPrune ?? 0} of {prunePreview.totalRecords ?? 0} record(s) would be pruned ({prunePreview.recordsToKeep ?? 0} kept).</span>
              ) : (
                <span className="text-emerald-300">
                  Pruned {prunePreview.prunedCount ?? 0} record(s), {prunePreview.remainingCount ?? 0} remaining.
                  {prunePreview.archivePath ? ` Archived to ${prunePreview.archivePath}.` : ''}
                </span>
              )}
            </div>
          )}
        </div>
      </GlassCard>

      {/* v240 GPU Workers + v260 Model Serving (Compute Fabric) */}
      <GlassCard className="space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-300 border border-purple-500/20">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-sm font-bold text-white">Compute Fabric</h3>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full border bg-amber-500/15 text-amber-300 border-amber-500/30">
                  {gpuDashboard ? 'Real execution disabled by default' : 'Loading'}
                </span>
              </div>
              <p className="text-xs text-gray-400 font-mono mt-1">
                v240 GPU workers + v260 local model-serving readiness. Every real execution path stays approval-gated.
              </p>
            </div>
          </div>
          <button
            onClick={refreshComputeFabric}
            className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-300 flex items-center gap-1.5 transition-colors self-start"
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Refresh Compute Fabric</span>
          </button>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">GPU Workers</div>
            <div className="text-xl font-bold font-mono tracking-tight text-cyan-300">{gpuDashboard ? gpuDashboard.totalGpuWorkers : '—'}</div>
            <div className="text-[10px] text-gray-500 font-mono truncate">{gpuDashboard ? `${gpuDashboard.activeGpuWorkers} active` : 'checking…'}</div>
          </div>
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">GPU Providers</div>
            <div className="text-xl font-bold font-mono tracking-tight text-emerald-300">{gpuDashboard ? gpuDashboard.providers.length : '—'}</div>
            <div className="text-[10px] text-gray-500 font-mono truncate">local, kaggle, runpod, …</div>
          </div>
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">Model Backends</div>
            <div className="text-xl font-bold font-mono tracking-tight text-cyan-300">{modelServing ? modelServing.count : '—'}</div>
            <div className="text-[10px] text-gray-500 font-mono truncate">ollama, vllm, openai-compat</div>
          </div>
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">Reachable</div>
            <div className={`text-xl font-bold font-mono tracking-tight ${modelServing && modelServing.reachableCount > 0 ? 'text-emerald-300' : 'text-gray-400'}`}>
              {modelServing ? modelServing.reachableCount : '—'}
            </div>
            <div className="text-[10px] text-gray-500 font-mono truncate">local model servers</div>
          </div>
        </div>

        {gpuDashboard && gpuDashboard.providers.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-white">GPU Providers</h4>
            <div className="overflow-x-auto font-mono text-xs">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-white/10 text-gray-400 text-[11px] uppercase">
                    <th className="py-2 px-3">Provider</th>
                    <th className="py-2 px-3">Enabled</th>
                    <th className="py-2 px-3">Configured</th>
                    <th className="py-2 px-3">Execution</th>
                    <th className="py-2 px-3">Risk</th>
                    <th className="py-2 px-3">Workers</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {gpuDashboard.providers.map(p => (
                    <tr key={p.provider} className="hover:bg-white/[0.02]">
                      <td className="py-2 px-3 font-semibold text-white">{p.name}</td>
                      <td className="py-2 px-3"><StatusBadge status={p.enabled ? 'connected' : 'disconnected'} size="sm" showIcon={false} /></td>
                      <td className="py-2 px-3">{p.configured ? 'Yes' : 'No'}</td>
                      <td className="py-2 px-3">{p.executionEnabled ? <span className="text-amber-300">Enabled</span> : <span className="text-gray-500">Disabled</span>}</td>
                      <td className="py-2 px-3"><RiskBadge level={p.riskLevel} size="sm" /></td>
                      <td className="py-2 px-3">{p.activeWorkers}/{p.workerCount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {modelServing && modelServing.backends.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-white">Local Model-Serving Backends</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {modelServing.backends.map(b => (
                <div key={b.backend} className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-white">{b.name}</span>
                    <span className={`w-2 h-2 rounded-full ${b.reachable ? 'bg-emerald-400' : b.configured ? 'bg-amber-400' : 'bg-gray-500'}`} />
                  </div>
                  <div className="text-[10px] font-mono text-gray-500">
                    {b.reachable ? `${b.models.length} model(s) loaded` : b.configured ? 'Configured, not reachable' : 'Not configured'}
                  </div>
                  {b.note && <div className="text-[10px] font-mono text-gray-600 truncate">{b.note}</div>}
                </div>
              ))}
            </div>
            <p className="text-[10px] font-mono text-gray-500">
              Read-only readiness. No model server is ever started by this app.
            </p>
          </div>
        )}
      </GlassCard>

      {/* v120 Scheduler tick + v280 target 2 auto-dispatch (opt-in, off by default) */}
      <GlassCard className="space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-sm font-bold text-white">Scheduler Tick</h3>
                <StatusBadge status={tickStatus?.enabled ? 'connected' : 'disconnected'} size="sm" />
                <span className={`text-[11px] font-mono px-2 py-0.5 rounded-full border flex items-center gap-1 ${
                  tickStatus?.autoDispatchEnabled
                    ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                    : 'bg-white/5 text-gray-400 border-white/10'
                }`}>
                  <Zap className="w-3 h-3" />
                  Auto-dispatch {tickStatus?.autoDispatchEnabled ? 'ON' : 'off (default)'}
                </span>
              </div>
              <p className="text-xs text-gray-400 font-mono mt-1">
                v120 background tick + v280 concurrent job dispatch. Both off by default; nothing runs automatically
                unless explicitly enabled via env flags.
              </p>
            </div>
          </div>
          <button
            onClick={refreshTickStatus}
            className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-300 flex items-center gap-1.5 transition-colors self-start"
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Refresh Tick Status</span>
          </button>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">Interval</div>
            <div className="text-xl font-bold font-mono tracking-tight text-cyan-300">{tickStatus ? `${tickStatus.intervalSeconds}s` : '—'}</div>
          </div>
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">Tasks Fired</div>
            <div className="text-xl font-bold font-mono tracking-tight text-emerald-300">{tickStatus ? tickStatus.lastFiredCount : '—'}</div>
          </div>
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">Stale Jobs Failed</div>
            <div className="text-xl font-bold font-mono tracking-tight text-rose-300">{tickStatus ? tickStatus.lastStaleJobsFailedCount : '—'}</div>
          </div>
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">Kaggle Polled</div>
            <div className="text-xl font-bold font-mono tracking-tight text-cyan-300">{tickStatus ? tickStatus.lastKaggleJobsPolledCount : '—'}</div>
          </div>
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-1">
            <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">Auto-Dispatched</div>
            <div className={`text-xl font-bold font-mono tracking-tight ${tickStatus?.autoDispatchEnabled ? 'text-amber-300' : 'text-gray-500'}`}>
              {tickStatus ? tickStatus.lastAutoDispatchedCount : '—'}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] font-mono text-gray-300">
          <div className="flex items-center gap-2 rounded-xl bg-white/[0.025] border border-white/[0.06] px-3 py-2">
            <span className={`w-2 h-2 rounded-full ${tickStatus?.lastTickAt ? 'bg-emerald-400' : 'bg-gray-500'}`} />
            <span>Last tick: {tickStatus?.lastTickAt || 'never (tick disabled or not yet run)'}</span>
          </div>
          <div className="flex items-center gap-2 rounded-xl bg-white/[0.025] border border-white/[0.06] px-3 py-2">
            <span className={`w-2 h-2 rounded-full ${tickStatus?.lastError ? 'bg-rose-400' : 'bg-emerald-400'}`} />
            <span>{tickStatus?.lastError ? `Last error: ${tickStatus.lastError}` : 'No errors on the last tick'}</span>
          </div>
        </div>
      </GlassCard>

      {/* 2. Header & Control Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-[#141418] border border-white/10">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-white">Current Workflow Trace</h2>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold">
                Trace ID: TR-9942-AX
              </span>
            </div>
            <p className="text-xs text-gray-400 font-mono">Real-time inspection of AST parsing, LLM routing, and MCP tool payloads</p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <button
            onClick={() => {
              setIsPaused(!isPaused);
              showToast(isPaused ? 'Resumed trace stream' : 'Paused trace stream', 'info');
            }}
            className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-300 flex items-center gap-1.5 transition-colors"
          >
            {isPaused ? <Play className="w-3.5 h-3.5 text-emerald-400" /> : <Pause className="w-3.5 h-3.5 text-amber-400" />}
            <span>{isPaused ? 'Resume Trace' : 'Pause Execution'}</span>
          </button>
          <button
            onClick={runMockWorkflowStep}
            className="px-3 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium flex items-center gap-1.5 transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Step Into Next</span>
          </button>
          <button
            onClick={handleExport}
            className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-300 flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Log</span>
          </button>
        </div>
      </div>

      {/* 3. Main Console Tabs (Trace vs JSON vs Tools) */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 border-b border-white/10 pb-2">
          {[
            { id: 'trace' as const, label: 'Workflow Trace Steps', icon: Activity, count: traceSteps.length },
            { id: 'tools' as const, label: 'Tool Call Inspector', icon: Cpu, count: connectors.length },
            { id: 'json' as const, label: 'Raw State JSON', icon: Code2 },
          ].map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-cyan-600/20 text-white border border-cyan-500/40 shadow-md'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="w-3.5 h-3.5 text-cyan-400" />
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-gray-300">
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Tab 1: Workflow Trace Inspector Split */}
        {activeTab === 'trace' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Step List */}
            <div className="lg:col-span-2 space-y-3">
              {traceSteps.map((s) => {
                const isSelected = s.step === selectedStep;
                return (
                  <div
                    key={s.id}
                    onClick={() => setSelectedStep(s.step)}
                    className={`cursor-pointer p-4 rounded-2xl border transition-all ${
                      isSelected
                        ? 'bg-cyan-900/20 border-cyan-500/50 shadow-[0_0_20px_-5px_rgba(34,211,238,0.2)]'
                        : 'bg-[#171717]/60 border-white/5 hover:bg-[#1a1a20]/80 hover:border-white/15'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono text-xs font-bold ${
                          isSelected ? 'bg-cyan-600 text-white' : 'bg-white/10 text-gray-300'
                        }`}>
                          #{s.step}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-white">{s.action}</span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-cyan-300 border border-white/10">
                              {s.agent}
                            </span>
                          </div>
                          {s.toolUsed && (
                            <div className="mt-1 text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                              <span>⚡ Tool invoked:</span>
                              <strong className="underline">{s.toolUsed}</strong>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 font-mono text-xs shrink-0">
                        <span className="text-gray-400">{s.durationMs}ms</span>
                        <span className="text-gray-500">{s.timestamp}</span>
                        <StatusBadge status={s.status} size="sm" showIcon={false} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Right 1 Col: Step Detail & Raw IO */}
            <GlassCard className="h-fit sticky top-20 space-y-4 font-mono">
              <div className="flex items-center justify-between pb-3 border-b border-white/10 text-xs font-sans font-semibold text-white">
                <span>Step #{currentStepData?.step} Inspector</span>
                <span className="text-cyan-400 font-mono">{currentStepData?.id}</span>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-gray-500 text-[10px] uppercase">Executing Agent</span>
                  <div className="text-white font-semibold mt-0.5">{currentStepData?.agent}</div>
                </div>

                <div>
                  <span className="text-gray-500 text-[10px] uppercase">Action Name</span>
                  <div className="text-cyan-300 mt-0.5">{currentStepData?.action}</div>
                </div>

                {currentStepData?.toolUsed && (
                  <div>
                    <span className="text-gray-500 text-[10px] uppercase">MCP Tool Connection</span>
                    <div className="text-emerald-400 font-semibold mt-0.5">{currentStepData?.toolUsed}</div>
                  </div>
                )}

                <div className="pt-2 border-t border-white/10">
                  <span className="text-gray-500 text-[10px] uppercase">Input Payload Snippet</span>
                  <pre className="mt-1 p-2.5 rounded-xl bg-black/60 border border-white/10 text-gray-300 text-[11px] overflow-x-auto whitespace-pre-wrap">
                    {currentStepData?.inputSnippet || 'No input arguments'}
                  </pre>
                </div>

                <div>
                  <span className="text-gray-500 text-[10px] uppercase">Output Response Snippet</span>
                  <pre className="mt-1 p-2.5 rounded-xl bg-black/60 border border-white/10 text-emerald-300 text-[11px] overflow-x-auto whitespace-pre-wrap">
                    {currentStepData?.outputSnippet || 'No output emitted'}
                  </pre>
                </div>
              </div>
            </GlassCard>
          </div>
        )}

        {/* Tab 2: Tool Call Inspector Table */}
        {activeTab === 'tools' && (
          <GlassCard>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/10">
              <h3 className="text-sm font-semibold text-white">Connected Tools & Execution Logs</h3>
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                <input
                  type="text"
                  value={logFilter}
                  onChange={(e) => setLogFilter(e.target.value)}
                  placeholder="Filter tool calls..."
                  className="w-full bg-black/50 border border-white/10 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="mt-4 overflow-x-auto font-mono text-xs">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-white/10 text-gray-400 text-[11px] uppercase">
                    <th className="py-2 px-3">Timestamp</th>
                    <th className="py-2 px-3">Agent</th>
                    <th className="py-2 px-3">Tool / Command</th>
                    <th className="py-2 px-3">Risk Level</th>
                    <th className="py-2 px-3">Sandbox Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-white/[0.02]">
                      <td className="py-3 px-3 text-gray-400">{log.timestamp}</td>
                      <td className="py-3 px-3 font-semibold text-white">{log.agentName}</td>
                      <td className="py-3 px-3 text-cyan-300 font-semibold">{log.action}</td>
                      <td className="py-3 px-3"><RiskBadge level={log.risk} size="sm" /></td>
                      <td className="py-3 px-3"><StatusBadge status={log.status} size="sm" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        )}

        {/* Tab 3: Raw State JSON Inspector */}
        {activeTab === 'json' && (
          <GlassCard>
            <div className="flex items-center justify-between pb-3 border-b border-white/10 font-mono text-xs">
              <span className="text-white font-semibold flex items-center gap-2">
                <Code2 className="w-4 h-4 text-cyan-400" /> Real-time Operating System State Dump
              </span>
              <span className="text-gray-400">Updated automatically</span>
            </div>
            <pre className="mt-3 p-4 rounded-xl bg-black/80 border border-white/10 text-emerald-400 text-xs font-mono max-h-[500px] overflow-y-auto">
              {JSON.stringify({
                systemVersion: "EvolveAgent AI vNext 2.4.0",
                activeAgentsCount: agents.length,
                pendingApprovalsCount: approvals.filter(a => a.status === 'pending').length,
                traceCount: traceSteps.length,
                lastStep: traceSteps[traceSteps.length - 1],
                activeAgents: agents.map(a => ({ name: a.name, status: a.status, currentTask: a.currentTask }))
              }, null, 2)}
            </pre>
          </GlassCard>
        )}
      </div>

      {/* 4. Live Agent Execution Progress Bars */}
      <GlassCard>
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <span>Active Agent Resource Consumption & Pipeline Health</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {agents.slice(0, 4).map(agent => (
            <div key={agent.id} className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-white flex items-center gap-1.5">
                  <span>{agent.avatar}</span>
                  <span className="truncate">{agent.name}</span>
                </span>
                <span className="text-[10px] font-mono text-cyan-400">{agent.qualityScore}% Q-Score</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-black/60 overflow-hidden">
                <div className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500" style={{ width: `${agent.qualityScore}%` }} />
              </div>
              <div className="flex items-center justify-between text-[10px] font-mono text-gray-500">
                <span>Tokens: {agent.tokensUsed}</span>
                <span>{agent.tasksCompletedToday} tasks today</span>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
};
