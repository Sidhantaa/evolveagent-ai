import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckSquare,
  FileText,
  Lock,
  Plus,
  RefreshCw,
  Scale,
  ShieldAlert,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { GlassCard } from '../components/shared/GlassCard';
import { RiskBadge } from '../components/shared/RiskBadge';
import {
  AuditPackageDetail,
  AuditPackageSummary,
  createAuditPackage,
  fetchAuditPackageDetail,
  fetchAuditPackages,
} from '../data/api';

const riskTone = (level: string): 'low' | 'medium' | 'high' => {
  if (level === 'high') return 'high';
  if (level === 'medium') return 'medium';
  return 'low';
};

export const CompliancePage: React.FC = () => {
  const { showToast } = useApp();
  const [packages, setPackages] = useState<AuditPackageSummary[] | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [detail, setDetail] = useState<AuditPackageDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [newTitle, setNewTitle] = useState('');

  const refreshList = async () => {
    const data = await fetchAuditPackages();
    setPackages(data);
    if (data && data.length && !data.some((p) => p.packageId === selectedId)) {
      setSelectedId(data[0].packageId);
    }
  };

  useEffect(() => {
    refreshList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    fetchAuditPackageDetail(selectedId).then(setDetail);
  }, [selectedId]);

  const handleCreate = async () => {
    setBusy(true);
    try {
      const created = await createAuditPackage(newTitle.trim() || 'Audit package');
      if (!created) {
        showToast('Could not create audit package', 'warning');
        return;
      }
      setNewTitle('');
      showToast('Audit package generated — a real, immutable point-in-time snapshot.', 'success');
      await refreshList();
      setSelectedId(created.packageId);
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
                v190 Enterprise AI OS
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Compliance</h1>
            <p className="text-xs sm:text-sm text-gray-300 leading-relaxed">
              Real, immutable point-in-time audit bundles: governance events, sensitive-data findings, active policies, and contract reviews. Not legal advice — audit material for human review.
            </p>
          </div>
          <button
            onClick={refreshList}
            className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-200 flex items-center justify-center gap-2 transition-colors self-start lg:self-auto"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <GlassCard className="space-y-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white">Generate audit package</h2>
        </div>
        <div className="flex gap-2">
          <input
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Package title (e.g. Q3 SOC 2 review)"
            className="flex-1 min-w-0 rounded-xl bg-black/40 border border-white/10 px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
          />
          <button
            onClick={handleCreate}
            disabled={busy}
            className="px-4 py-2 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-300 font-bold text-xs flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <Plus className="w-3.5 h-3.5" />
            Generate
          </button>
        </div>
      </GlassCard>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassCard className="lg:col-span-1 space-y-3" padding="none">
          <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
            <h3 className="text-sm font-bold text-white">Packages</h3>
            <span className="text-[11px] font-mono text-gray-500">{packages?.length ?? 0}</span>
          </div>
          <div className="max-h-[600px] overflow-y-auto divide-y divide-white/[0.05]">
            {!packages ? (
              <div className="p-8 text-center text-xs text-gray-500 font-mono">Loading packages...</div>
            ) : packages.length === 0 ? (
              <div className="p-8 text-center text-xs text-gray-500 font-mono">No audit packages yet — generate one above.</div>
            ) : packages.map((p) => (
              <button
                key={p.packageId}
                onClick={() => setSelectedId(p.packageId)}
                className={`w-full text-left p-4 transition-colors ${p.packageId === selectedId ? 'bg-cyan-500/10' : 'hover:bg-white/[0.02]'}`}
              >
                <div className="text-xs font-bold text-white truncate">{p.title}</div>
                <div className="text-[10px] text-gray-500 font-mono mt-0.5">{p.generatedAt ? p.generatedAt.slice(0, 16).replace('T', ' ') : '—'}</div>
                <div className="flex items-center gap-2 mt-1.5">
                  {p.highRiskFindings > 0 && (
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30">
                      {p.highRiskFindings} high-risk
                    </span>
                  )}
                  <span className="text-[10px] font-mono text-gray-500">{p.policyCount} policies</span>
                </div>
              </button>
            ))}
          </div>
        </GlassCard>

        <div className="lg:col-span-2 space-y-6">
          {!detail ? (
            <GlassCard><div className="py-16 text-center text-xs text-gray-500">Select an audit package to inspect.</div></GlassCard>
          ) : (
            <>
              <GlassCard className="space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-extrabold text-white">{detail.title}</h2>
                    <p className="text-[11px] text-gray-500 font-mono mt-0.5">Generated {detail.generatedAt ? detail.generatedAt.slice(0, 19).replace('T', ' ') : '—'}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07]">
                    <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Governance events</div>
                    <div className="text-xl font-extrabold text-white">{detail.governanceEventCount.toLocaleString()}</div>
                  </div>
                  <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07]">
                    <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Blocked actions</div>
                    <div className="text-xl font-extrabold text-amber-400">{detail.blockedActionCount.toLocaleString()}</div>
                  </div>
                  <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07]">
                    <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">Sensitive findings</div>
                    <div className="text-xl font-extrabold text-white">{detail.sensitiveFindingsCount}</div>
                  </div>
                  <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07]">
                    <div className="text-[10px] uppercase font-mono tracking-wider text-gray-500">High-risk findings</div>
                    <div className="text-xl font-extrabold text-rose-400">{detail.highRiskFindings}</div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {detail.contents.map((c) => (
                    <span key={c} className="text-[11px] font-mono px-2 py-1 rounded-lg bg-white/[0.04] border border-white/10 text-gray-300">{c}</span>
                  ))}
                </div>
                <p className="text-[11px] text-gray-500 italic">{detail.disclaimer}</p>
              </GlassCard>

              <GlassCard className="space-y-3">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  <h3 className="text-sm font-bold text-white">Sensitive-data findings</h3>
                  <span className="text-[11px] font-mono text-gray-500">{detail.sensitiveFindings.length}</span>
                </div>
                <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                  {detail.sensitiveFindings.length === 0 && (
                    <div className="text-[11px] text-gray-500 font-mono py-2 text-center">No sensitive-data findings in this bundle.</div>
                  )}
                  {detail.sensitiveFindings.map((f) => (
                    <div key={f.findingId} className="p-2.5 rounded-xl bg-black/20 border border-white/[0.05]">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs text-white font-mono truncate">{f.label}</span>
                        <RiskBadge level={riskTone(f.riskLevel)} size="sm" />
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {f.secretsDetected && f.secretTypes.map((t) => (
                          <span key={t} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 flex items-center gap-1">
                            <Lock className="w-2.5 h-2.5" />{t}
                          </span>
                        ))}
                        {f.piiDetected && f.piiTypes.map((t) => (
                          <span key={t} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">pii:{t}</span>
                        ))}
                        {f.hipaaWarning && (
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 flex items-center gap-1">
                            <AlertTriangle className="w-2.5 h-2.5" />HIPAA
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </GlassCard>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <GlassCard className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Scale className="w-4 h-4 text-blue-400" />
                    <h3 className="text-sm font-bold text-white">Active policies</h3>
                    <span className="text-[11px] font-mono text-gray-500">{detail.policies.length}</span>
                  </div>
                  <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                    {detail.policies.map((p) => (
                      <div key={p.policyId} className="p-2 rounded-lg bg-black/20 border border-white/[0.05]">
                        <div className="text-xs text-white">{p.name}</div>
                        <div className="text-[10px] text-gray-500 font-mono">{p.category} · {p.status}</div>
                      </div>
                    ))}
                  </div>
                </GlassCard>

                <GlassCard className="space-y-3">
                  <div className="flex items-center gap-2">
                    <CheckSquare className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-sm font-bold text-white">Checklists</h3>
                    <span className="text-[11px] font-mono text-gray-500">{detail.checklists.length}</span>
                  </div>
                  <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                    {detail.checklists.map((c) => (
                      <div key={c.checklistId} className="p-2 rounded-lg bg-black/20 border border-white/[0.05]">
                        <div className="text-xs text-white">{c.title}</div>
                        <div className="text-[10px] text-gray-500 font-mono">{c.framework} · {c.items.filter((i) => i.done).length}/{c.items.length} done</div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              </div>

              {detail.contractReviews.length > 0 && (
                <GlassCard className="space-y-3">
                  <h3 className="text-sm font-bold text-white">Contract reviews</h3>
                  <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                    {detail.contractReviews.map((r) => (
                      <div key={r.reviewId} className="p-2.5 rounded-xl bg-black/20 border border-white/[0.05]">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-white">{r.title}</span>
                          <RiskBadge level={riskTone(r.riskLevel)} size="sm" />
                        </div>
                        <ul className="mt-1.5 space-y-0.5">
                          {r.riskFlags.slice(0, 3).map((flag) => (
                            <li key={flag} className="text-[11px] text-gray-500">• {flag}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
