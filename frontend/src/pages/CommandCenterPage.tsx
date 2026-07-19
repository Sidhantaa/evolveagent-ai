import React, { useEffect, useState } from 'react';
import {
  Activity,
  CheckCircle2,
  Circle,
  FileText,
  Gauge,
  History,
  Layers,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { GlassCard } from '../components/shared/GlassCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import {
  CommandCenterDashboard,
  CommandCenterReport,
  CommandCenterSnapshot,
  createCommandCenterSnapshot,
  fetchCommandCenterDashboard,
  fetchCommandCenterSnapshots,
  generateCommandCenterReport,
} from '../data/api';

const gradeTone = (grade: string) => {
  if (grade === 'A') return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
  if (grade === 'B') return 'text-blue-400 border-blue-500/30 bg-blue-500/10';
  if (grade === 'C') return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
  return 'text-rose-400 border-rose-500/30 bg-rose-500/10';
};

export const CommandCenterPage: React.FC = () => {
  const { showToast } = useApp();
  const [dashboard, setDashboard] = useState<CommandCenterDashboard | null>(null);
  const [snapshots, setSnapshots] = useState<CommandCenterSnapshot[] | null>(null);
  const [report, setReport] = useState<CommandCenterReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [openDomains, setOpenDomains] = useState<Record<string, boolean>>({});

  const refreshAll = async () => {
    const [dash, snaps] = await Promise.all([fetchCommandCenterDashboard(), fetchCommandCenterSnapshots()]);
    setDashboard(dash);
    setSnapshots(snaps);
  };

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleDomain = (domain: string) => {
    setOpenDomains((prev) => ({ ...prev, [domain]: !prev[domain] }));
  };

  const handleSnapshot = async () => {
    setBusy(true);
    try {
      const snap = await createCommandCenterSnapshot();
      if (!snap) {
        showToast('Snapshot endpoint unavailable', 'warning');
        return;
      }
      showToast(`Snapshot created — grade ${snap.overallGrade}, ${snap.activeSystems}/${snap.totalSystems} systems active.`, 'success');
      await refreshAll();
    } finally {
      setBusy(false);
    }
  };

  const handleReport = async () => {
    setBusy(true);
    try {
      const rep = await generateCommandCenterReport();
      if (!rep) {
        showToast('Report endpoint unavailable', 'warning');
        return;
      }
      setReport(rep);
      showToast('Final platform report generated.', 'success');
      await refreshAll();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      <div className="rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-[#171524] via-[#14141c] to-[#101018] p-6 sm:p-8 shadow-2xl overflow-hidden relative">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold uppercase tracking-wider">
                {dashboard?.version || 'v200.0'} Capstone
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Command Center</h1>
            <p className="text-xs sm:text-sm text-gray-300 leading-relaxed">
              A live capability directory across every system this platform has built — which ones are wired to
              real data right now, and which are still dormant. {dashboard?.disclaimer}
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

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard className="space-y-1">
          <div className="flex items-center gap-2 text-gray-400"><Layers className="w-4 h-4" /><span className="text-[10px] uppercase font-mono tracking-wider">Systems active</span></div>
          <div className="text-2xl font-extrabold text-white">{dashboard?.activeSystems ?? '—'}<span className="text-sm text-gray-500">/{dashboard?.totalSystems ?? '—'}</span></div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="flex items-center gap-2 text-gray-400"><Gauge className="w-4 h-4" /><span className="text-[10px] uppercase font-mono tracking-wider">Coverage</span></div>
          <div className="text-2xl font-extrabold text-white">{dashboard?.coveragePct ?? '—'}%</div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="flex items-center gap-2 text-gray-400"><Sparkles className="w-4 h-4" /><span className="text-[10px] uppercase font-mono tracking-wider">Overall grade</span></div>
          <div className={`inline-flex text-2xl font-extrabold px-2 rounded-lg border ${gradeTone(dashboard?.overallGrade || '')}`}>
            {dashboard?.overallGrade || '—'}
          </div>
        </GlassCard>
        <GlassCard className="space-y-1">
          <div className="flex items-center gap-2 text-gray-400"><Activity className="w-4 h-4" /><span className="text-[10px] uppercase font-mono tracking-wider">Health</span></div>
          <StatusBadge status={dashboard?.healthStatus || 'unknown'} size="sm" />
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          {!dashboard ? (
            <GlassCard><div className="text-xs text-gray-500 font-mono py-8 text-center">Loading command center...</div></GlassCard>
          ) : dashboard.domains.map((d) => (
            <GlassCard key={d.domain} className="space-y-0" padding="none">
              <button
                onClick={() => toggleDomain(d.domain)}
                className="w-full flex items-center justify-between p-4 hover:bg-white/[0.02] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-white">{d.domain}</span>
                  <span className="text-[11px] font-mono text-gray-500">{d.activeCount}/{d.systemCount} active</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-1.5 rounded-full bg-white/10 overflow-hidden">
                    <div
                      className={`h-full ${d.activeCount === d.systemCount ? 'bg-emerald-400' : d.activeCount === 0 ? 'bg-rose-400' : 'bg-amber-400'}`}
                      style={{ width: `${d.systemCount ? (d.activeCount / d.systemCount) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              </button>
              {openDomains[d.domain] !== false && (
                <div className="px-4 pb-4 space-y-1.5 border-t border-white/[0.06] pt-3">
                  {d.systems.map((s) => (
                    <div key={s.route + s.label} className="flex items-center justify-between gap-2 p-2 rounded-xl bg-black/20 border border-white/[0.05]">
                      <div className="flex items-center gap-2 min-w-0">
                        {s.active ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" /> : <Circle className="w-3.5 h-3.5 text-gray-600 shrink-0" />}
                        <span className="text-xs text-white truncate">{s.label}</span>
                        <span className="text-[10px] font-mono text-gray-500 truncate hidden sm:inline">{s.route}</span>
                      </div>
                      <span className="text-[11px] font-mono text-gray-400 shrink-0">{s.recordCount.toLocaleString()} rec.</span>
                    </div>
                  ))}
                </div>
              )}
            </GlassCard>
          ))}
        </div>

        <div className="space-y-6">
          <GlassCard className="space-y-3">
            <div className="flex items-center gap-2">
              <Gauge className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-white">Scorecard dimensions</h3>
            </div>
            <div className="space-y-2">
              {(dashboard?.scoreDimensions || []).map((dim) => (
                <div key={dim.name} className="space-y-1">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="text-gray-400 capitalize">{dim.name.replace(/_/g, ' ')}</span>
                    <span className={`px-1.5 rounded ${gradeTone(dim.grade)}`}>{dim.grade} · {dim.score}</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                    <div className="h-full bg-cyan-400" style={{ width: `${dim.score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard className="space-y-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white">Safety boundaries</h3>
            </div>
            <ul className="space-y-1.5">
              {(dashboard?.safetyBoundaries || []).map((b) => (
                <li key={b} className="text-[11px] text-gray-400 leading-relaxed flex gap-1.5">
                  <span className="text-emerald-400">•</span><span>{b}</span>
                </li>
              ))}
            </ul>
          </GlassCard>

          <GlassCard className="space-y-3">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-bold text-white">Snapshots</h3>
              <span className="text-[11px] font-mono text-gray-500">{snapshots?.length ?? 0}</span>
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <button
                onClick={handleSnapshot}
                disabled={busy}
                className="flex-1 px-3 py-2 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-300 font-bold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
              >
                Create snapshot
              </button>
              <button
                onClick={handleReport}
                disabled={busy}
                className="flex-1 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-gray-200 font-bold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
              >
                <FileText className="w-3.5 h-3.5" />
                Generate report
              </button>
            </div>
            <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
              {(snapshots || []).slice(0, 10).map((s) => (
                <div key={s.snapshotId} className="flex items-center justify-between text-[11px] font-mono p-2 rounded-lg bg-black/20 border border-white/[0.05]">
                  <span className="text-gray-400">{s.createdAt ? s.createdAt.slice(0, 16).replace('T', ' ') : '—'}</span>
                  <span className={`px-1.5 rounded ${gradeTone(s.overallGrade)}`}>{s.overallGrade} · {s.coveragePct}%</span>
                </div>
              ))}
              {snapshots && snapshots.length === 0 && (
                <div className="text-[11px] text-gray-500 font-mono py-2 text-center">No snapshots yet.</div>
              )}
            </div>
          </GlassCard>

          {report && (
            <GlassCard className="space-y-2 border-emerald-500/20">
              <div className="text-[10px] uppercase tracking-wider font-mono text-emerald-300">Latest report</div>
              <p className="text-xs text-white leading-relaxed">{report.headline}</p>
              <p className="text-[11px] text-gray-500 italic">{report.disclaimer}</p>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
