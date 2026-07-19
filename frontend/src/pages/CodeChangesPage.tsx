import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  Check,
  Code2,
  ExternalLink,
  FileCode2,
  GitBranch,
  GitCommit,
  GitPullRequestArrow,
  RefreshCw,
  ShieldCheck,
  X,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { GlassCard } from '../components/shared/GlassCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { RiskBadge } from '../components/shared/RiskBadge';
import {
  approveDurableWorkflowStep,
  CodeWriterStatus,
  DurableWorkflowEffect,
  DurableWorkflowRunDetail,
  DurableWorkflowStep,
  fetchCodeChangeRuns,
  fetchCodeWriterStatus,
  fetchGitHubWriteStatus,
  fetchWorkflowEffects,
  fetchWorkflowRunDetail,
  GitHubWriteStatus,
} from '../data/api';

type ProposedFile = { file_path: string; content: string };

const isCodeStep = (step: DurableWorkflowStep) =>
  step.actionType === 'write_code_change' || step.actionType === 'open_pull_request';

const clipMiddle = (value: string, max = 72) => {
  if (!value || value.length <= max) return value || '—';
  const left = Math.ceil((max - 3) / 2);
  const right = Math.floor((max - 3) / 2);
  return `${value.slice(0, left)}...${value.slice(-right)}`;
};

const parseFiles = (step: DurableWorkflowStep): ProposedFile[] => {
  const params = step.actionParams || {};
  if (step.actionType === 'open_pull_request') return [];
  if (params.files) {
    try {
      const parsed = JSON.parse(String(params.files));
      if (Array.isArray(parsed)) {
        return parsed
          .map((item) => ({
            file_path: String(item?.file_path || 'untitled.txt'),
            content: String(item?.content || ''),
          }))
          .filter((item) => item.file_path.trim());
      }
    } catch {
      return [{ file_path: 'Invalid files payload', content: String(params.files).slice(0, 4000) }];
    }
  }
  return [{
    file_path: String(params.file_path || 'untitled.txt'),
    content: String(params.content || ''),
  }];
};

const stepTone = (step: DurableWorkflowStep): 'low' | 'medium' | 'high' => {
  if (step.output.includes('[declined]') || step.status === 'skipped') return 'medium';
  if (step.status === 'waiting_approval') return 'high';
  return 'low';
};

const currentCodeStep = (run: DurableWorkflowRunDetail | null) => {
  if (!run) return null;
  return run.steps.find((step) => step.status === 'waiting_approval' && isCodeStep(step))
    || run.steps.find((step) => isCodeStep(step))
    || null;
};

const effectForStep = (effects: DurableWorkflowEffect[] | null, step: DurableWorkflowStep | null) => {
  if (!effects || !step) return null;
  return effects.find((effect) => effect.stepId === step.id) || effects.find((effect) => effect.actionType === step.actionType) || null;
};

const resultReason = (step: DurableWorkflowStep | null, effect: DurableWorkflowEffect | null) => {
  const note = effect?.result?.note;
  if (note) return String(note);
  if (step?.output) return step.output;
  return '';
};

export const CodeChangesPage: React.FC = () => {
  const { showToast } = useApp();
  const [runs, setRuns] = useState<DurableWorkflowRunDetail[] | null>(null);
  const [selectedRunId, setSelectedRunId] = useState('');
  const [selectedRun, setSelectedRun] = useState<DurableWorkflowRunDetail | null>(null);
  const [effects, setEffects] = useState<DurableWorkflowEffect[] | null>(null);
  const [codeStatus, setCodeStatus] = useState<CodeWriterStatus | null>(null);
  const [githubStatus, setGithubStatus] = useState<GitHubWriteStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState('');

  const loadRuns = async () => {
    const latest = await fetchCodeChangeRuns();
    setRuns(latest);
    const nextId = selectedRunId || latest?.[0]?.id || '';
    if (nextId) setSelectedRunId(nextId);
    return nextId;
  };

  const loadSelected = async (runId: string) => {
    if (!runId) return;
    const [detail, fx] = await Promise.all([
      fetchWorkflowRunDetail(runId),
      fetchWorkflowEffects(runId),
    ]);
    setSelectedRun(detail);
    setEffects(fx);
  };

  const refreshAll = async () => {
    const [nextId] = await Promise.all([
      loadRuns(),
      fetchCodeWriterStatus().then(setCodeStatus),
      fetchGitHubWriteStatus().then(setGithubStatus),
    ]);
    if (nextId) await loadSelected(nextId);
  };

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedRunId) loadSelected(selectedRunId);
  }, [selectedRunId]);

  const selectedStep = currentCodeStep(selectedRun);
  const selectedEffect = effectForStep(effects, selectedStep);
  const proposedFiles = useMemo(() => selectedStep ? parseFiles(selectedStep) : [], [selectedStep]);
  const declinedSafely = Boolean(selectedStep?.output.includes('[declined]') || selectedEffect?.result?.wrote === false);
  const pr = selectedEffect?.result?.pull_request;

  const decide = async (approved: boolean) => {
    if (!selectedRun?.id) return;
    setBusy(true);
    try {
      const updated = await approveDurableWorkflowStep(selectedRun.id, approved, note, 'EvolveAgent UI');
      if (!updated) {
        showToast('Approval endpoint unavailable', 'warning');
        return;
      }
      setSelectedRun(updated);
      const latestEffects = await fetchWorkflowEffects(selectedRun.id);
      setEffects(latestEffects);
      await loadRuns();
      showToast(approved ? 'Code-change step approved. Result refreshed.' : 'Code-change step rejected.', approved ? 'success' : 'info');
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
                v150 Autonomous Software Team
              </span>
              <RiskBadge level="high" size="sm" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Code Changes</h1>
            <p className="text-xs sm:text-sm text-gray-300 leading-relaxed">
              Human approval gate for real local commits, branch pushes, and GitHub pull requests. Declined writes are shown as safe outcomes, not hidden errors.
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

      <GlassCard className="space-y-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-bold text-white">Write + PR Configuration</h2>
          <span className="text-[11px] font-mono text-gray-500">secret-safe status only</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-2">
            <div className="text-[10px] uppercase tracking-wider font-mono text-gray-500">Code writer</div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-white">Local commits</span>
              <StatusBadge status={codeStatus?.writesEnabled ? 'connected' : 'waiting'} size="sm" />
            </div>
            <p className="text-[11px] text-gray-400 font-mono">
              {codeStatus?.writesEnabled ? 'Enabled' : `Enable with ${codeStatus?.writesOptInEnv || 'CODE_WRITES_ENABLED'}`}
            </p>
          </div>
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-2">
            <div className="text-[10px] uppercase tracking-wider font-mono text-gray-500">Push gate</div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-white">Branch push</span>
              <StatusBadge status={codeStatus?.pushEnabled ? 'connected' : 'waiting'} size="sm" />
            </div>
            <p className="text-[11px] text-gray-400 font-mono">
              {codeStatus?.pushEnabled ? 'Enabled' : `Enable with ${codeStatus?.pushOptInEnv || 'CODE_WRITER_PUSH_ENABLED'}`}
            </p>
          </div>
          <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07] space-y-2">
            <div className="text-[10px] uppercase tracking-wider font-mono text-gray-500">GitHub writes</div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-white">Pull requests</span>
              <StatusBadge status={githubStatus?.writesEnabled ? 'connected' : 'waiting'} size="sm" />
            </div>
            <p className="text-[11px] text-gray-400 font-mono">
              {githubStatus?.writesEnabled ? 'Enabled' : 'GitHub writes disabled or not configured'}
            </p>
          </div>
        </div>
        <div className="p-3 rounded-2xl bg-white/[0.025] border border-white/[0.06]">
          <div className="text-[10px] uppercase tracking-wider font-mono text-gray-500 mb-2">Allowed repos</div>
          <div className="flex flex-wrap gap-2">
            {(codeStatus?.allowedRepos || []).length ? codeStatus!.allowedRepos.map((repo) => (
              <span key={repo} className="text-[11px] font-mono px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                {clipMiddle(repo, 86)}
              </span>
            )) : (
              <span className="text-xs text-amber-300 font-mono">
                No repos exposed. Set {codeStatus?.allowedReposEnv || 'CODE_WRITER_ALLOWED_REPOS'} after choosing a disposable target repo.
              </span>
            )}
          </div>
        </div>
      </GlassCard>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassCard className="lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-cyan-400" />
              Runs
            </h2>
            <span className="text-[11px] font-mono text-gray-500">{runs?.length ?? 0} code workflow(s)</span>
          </div>
          <div className="space-y-2 max-h-[720px] overflow-y-auto pr-1">
            {!runs ? (
              <div className="text-xs text-gray-500 font-mono">Loading durable workflows...</div>
            ) : runs.length === 0 ? (
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 text-xs text-gray-400">
                No durable workflow has a `write_code_change` or `open_pull_request` step yet.
              </div>
            ) : runs.map((run) => {
              const step = currentCodeStep(run);
              const active = run.id === selectedRunId;
              return (
                <button
                  key={run.id}
                  onClick={() => setSelectedRunId(run.id)}
                  className={`w-full text-left p-3 rounded-2xl border transition-all ${
                    active ? 'bg-cyan-500/10 border-cyan-500/40' : 'bg-white/[0.02] border-white/[0.06] hover:border-white/20'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="text-xs font-bold text-white truncate">{run.name}</div>
                      <div className="text-[10px] text-gray-500 font-mono truncate">{run.id}</div>
                    </div>
                    <StatusBadge status={run.status} size="sm" />
                  </div>
                  <div className="mt-2 flex items-center justify-between gap-2">
                    <span className="text-[11px] font-mono text-cyan-300">{step?.actionType || 'code step'}</span>
                    {step && <RiskBadge level={stepTone(step)} size="sm" />}
                  </div>
                </button>
              );
            })}
          </div>
        </GlassCard>

        <div className="lg:col-span-2 space-y-6">
          <GlassCard className="space-y-4">
            {!selectedRun || !selectedStep ? (
              <div className="py-16 text-center text-sm text-gray-400">Select a code-change workflow to inspect.</div>
            ) : (
              <>
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-white/10 pb-4">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge status={selectedStep.status} />
                      {declinedSafely && (
                        <span className="inline-flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          Declined safely
                        </span>
                      )}
                      {pr?.url && (
                        <a
                          href={pr.url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/25"
                        >
                          <GitPullRequestArrow className="w-3.5 h-3.5" />
                          PR #{pr.number || 'open'}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    <h2 className="text-xl font-extrabold text-white">{selectedStep.name}</h2>
                    <p className="text-xs text-gray-400 font-mono">{selectedStep.actionType}</p>
                  </div>
                  <div className="text-right text-[11px] font-mono text-gray-500">
                    <div>Run: {selectedRun.id}</div>
                    <div>Updated: {selectedRun.updatedAt ? selectedRun.updatedAt.slice(0, 19) : '—'}</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07]">
                    <div className="text-[10px] uppercase tracking-wider font-mono text-gray-500">Target repo</div>
                    <div className="text-xs text-white font-mono mt-1 break-all">
                      {selectedStep.actionParams.repo_path || selectedStep.actionParams.github_repo || '—'}
                    </div>
                  </div>
                  <div className="p-3 rounded-2xl bg-black/30 border border-white/[0.07]">
                    <div className="text-[10px] uppercase tracking-wider font-mono text-gray-500">Commit / PR intent</div>
                    <div className="text-xs text-white font-mono mt-1">
                      {selectedStep.actionParams.commit_message || selectedStep.actionParams.title || '—'}
                    </div>
                  </div>
                </div>

                {selectedStep.approvers.length > 0 && (
                  <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 space-y-2">
                    <div className="text-[10px] uppercase tracking-wider font-mono text-amber-300">Approval progress</div>
                    <div className="flex flex-wrap gap-2">
                      {selectedStep.approvalProgress?.steps?.length ? selectedStep.approvalProgress.steps.map((item: any, idx: number) => (
                        <span key={`${item.title}-${idx}`} className="text-[11px] font-mono px-2 py-1 rounded-lg bg-black/30 border border-white/10 text-gray-200">
                          {item.title}: {item.status}
                        </span>
                      )) : selectedStep.approvers.map((name) => (
                        <span key={name} className="text-[11px] font-mono px-2 py-1 rounded-lg bg-black/30 border border-white/10 text-gray-200">
                          {name}: pending
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {resultReason(selectedStep, selectedEffect) && (
                  <div className={`p-3 rounded-2xl border ${
                    declinedSafely ? 'bg-amber-500/10 border-amber-500/30 text-amber-200' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200'
                  }`}>
                    <div className="text-[10px] uppercase tracking-wider font-mono mb-1">
                      {declinedSafely ? 'Safe decline reason' : 'Backend result'}
                    </div>
                    <p className="text-xs font-mono break-words">{resultReason(selectedStep, selectedEffect)}</p>
                  </div>
                )}

                {selectedEffect?.result && Object.keys(selectedEffect.result).length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="p-3 rounded-2xl bg-white/[0.025] border border-white/[0.06]">
                      <GitBranch className="w-4 h-4 text-cyan-300 mb-2" />
                      <div className="text-[10px] text-gray-500 uppercase font-mono">Branch</div>
                      <div className="text-xs text-white font-mono break-all">{selectedEffect.result.branch || selectedStep.actionParams.branch_name || '—'}</div>
                    </div>
                    <div className="p-3 rounded-2xl bg-white/[0.025] border border-white/[0.06]">
                      <GitCommit className="w-4 h-4 text-emerald-300 mb-2" />
                      <div className="text-[10px] text-gray-500 uppercase font-mono">Commit</div>
                      <div className="text-xs text-white font-mono">{selectedEffect.result.commit_sha ? String(selectedEffect.result.commit_sha).slice(0, 12) : '—'}</div>
                    </div>
                    <div className="p-3 rounded-2xl bg-white/[0.025] border border-white/[0.06]">
                      <GitPullRequestArrow className="w-4 h-4 text-blue-300 mb-2" />
                      <div className="text-[10px] text-gray-500 uppercase font-mono">Pull request</div>
                      {pr?.url ? (
                        <a className="text-xs text-blue-300 font-mono hover:underline" href={pr.url} target="_blank" rel="noreferrer">
                          #{pr.number || 'open'}
                        </a>
                      ) : (
                        <div className="text-xs text-white font-mono">—</div>
                      )}
                    </div>
                  </div>
                )}

                {selectedStep.actionType === 'write_code_change' && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <FileCode2 className="w-4 h-4 text-cyan-400" />
                      <h3 className="text-sm font-bold text-white">Proposed file content</h3>
                    </div>
                    {proposedFiles.map((file, index) => (
                      <div key={`${file.file_path}-${index}`} className="rounded-2xl border border-white/[0.08] overflow-hidden bg-black/40">
                        <div className="flex items-center justify-between px-4 py-2 border-b border-white/[0.08] bg-white/[0.03]">
                          <span className="text-xs text-white font-mono break-all">{file.file_path}</span>
                          <span className="text-[10px] text-gray-500 font-mono">{file.content.length.toLocaleString()} chars</span>
                        </div>
                        <pre className="p-4 max-h-80 overflow-auto text-[11px] leading-relaxed text-gray-200 font-mono whitespace-pre-wrap">
                          {file.content || '// empty file'}
                        </pre>
                      </div>
                    ))}
                  </div>
                )}

                {selectedStep.actionType === 'open_pull_request' && (
                  <div className="p-4 rounded-2xl bg-black/30 border border-white/[0.07] space-y-3">
                    <div className="flex items-center gap-2 text-white font-bold text-sm">
                      <GitPullRequestArrow className="w-4 h-4 text-blue-300" />
                      Pull request plan
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                      <div><span className="text-gray-500">GitHub repo:</span> <span className="text-white">{selectedStep.actionParams.github_repo || '—'}</span></div>
                      <div><span className="text-gray-500">Head:</span> <span className="text-white">{selectedStep.actionParams.branch_name || '—'}</span></div>
                      <div><span className="text-gray-500">Base:</span> <span className="text-white">{selectedStep.actionParams.base || 'main'}</span></div>
                      <div><span className="text-gray-500">Title:</span> <span className="text-white">{selectedStep.actionParams.title || '—'}</span></div>
                    </div>
                    {selectedStep.actionParams.body && (
                      <pre className="p-3 rounded-xl bg-black/40 border border-white/[0.06] text-[11px] text-gray-300 font-mono whitespace-pre-wrap max-h-48 overflow-auto">
                        {selectedStep.actionParams.body}
                      </pre>
                    )}
                  </div>
                )}

                {selectedStep.status === 'waiting_approval' && (
                  <div className="p-4 rounded-2xl bg-[#111116] border border-amber-500/30 space-y-3">
                    <div className="flex items-center gap-2 text-amber-300 font-bold text-sm">
                      <AlertTriangle className="w-4 h-4" />
                      Human approval required
                    </div>
                    <textarea
                      value={note}
                      onChange={(event) => setNote(event.target.value)}
                      placeholder="Optional approval note"
                      className="w-full min-h-[72px] rounded-xl bg-black/40 border border-white/10 p-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                    />
                    <div className="flex flex-col sm:flex-row gap-2">
                      <button
                        onClick={() => decide(true)}
                        disabled={busy}
                        className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                      >
                        <Check className="w-4 h-4" />
                        Approve gated step
                      </button>
                      <button
                        onClick={() => decide(false)}
                        disabled={busy}
                        className="px-5 py-2.5 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 font-bold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                      >
                        <X className="w-4 h-4" />
                        Reject step
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </GlassCard>

          <GlassCard className="space-y-3">
            <div className="flex items-center gap-2">
              <Code2 className="w-4 h-4 text-gray-300" />
              <h3 className="text-sm font-bold text-white">Raw action params</h3>
            </div>
            <pre className="p-4 rounded-2xl bg-black/40 border border-white/[0.06] text-[11px] text-gray-300 font-mono whitespace-pre-wrap max-h-72 overflow-auto">
              {selectedStep ? JSON.stringify(selectedStep.actionParams, null, 2) : '{}'}
            </pre>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
