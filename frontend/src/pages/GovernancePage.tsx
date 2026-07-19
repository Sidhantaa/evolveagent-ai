import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { GlassCard } from '../components/shared/GlassCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { RiskBadge } from '../components/shared/RiskBadge';
import { 
  Shield, 
  ShieldCheck, 
  ShieldAlert, 
  Lock, 
  Unlock, 
  CheckCircle2, 
  AlertTriangle, 
  Activity, 
  Sliders, 
  FileText, 
  ToggleLeft, 
  ToggleRight, 
  Search, 
  Cpu, 
  Layers, 
  Wrench, 
  Check, 
  X,
  ArrowRight
} from 'lucide-react';

export const GovernancePage: React.FC = () => {
  const { governanceLogs, safetySettings, toggleSafetySetting, approvals, showToast } = useApp();
  const [searchTerm, setSearchTerm] = useState('');

  const policyMatrix = [
    { action: 'Read workspace memory & vectors', scope: 'Project Brain', risk: 'low' as const, status: 'allowed', autoApprove: true },
    { action: 'Read local source files (/src)', scope: 'Filesystem CLI', risk: 'low' as const, status: 'allowed', autoApprove: true },
    { action: 'Write local source files (/src)', scope: 'Filesystem CLI', risk: 'medium' as const, status: 'approval-gated', autoApprove: false },
    { action: 'Send draft notifications to Slack', scope: 'Slack MCP', risk: 'medium' as const, status: 'approval-gated', autoApprove: false },
    { action: 'Create GitHub issue or draft PR', scope: 'GitHub MCP', risk: 'medium' as const, status: 'approval-gated', autoApprove: false },
    { action: 'Delete or overwrite files (rm -rf)', scope: 'Filesystem CLI', risk: 'high' as const, status: 'blocked', autoApprove: false },
    { action: 'Run arbitrary bash/shell script', scope: 'Terminal CLI', risk: 'high' as const, status: 'blocked', autoApprove: false },
  ];

  const filteredMatrix = policyMatrix.filter(p => 
    p.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.scope.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* 1. Governance Metrics (6 counters) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Governance Score', value: '98%', sub: 'Grade A+ Secure', color: 'text-emerald-400' },
          { label: 'Actions Logged', value: '1,284', sub: 'Tamper-proof audit', color: 'text-white' },
          { label: 'Pending Reviews', value: `${approvals.filter(a => a.status === 'pending').length}`, sub: 'In Approvals queue', color: 'text-amber-400' },
          { label: 'Blocked Actions', value: '12', sub: 'Destructive shell', color: 'text-rose-400' },
          { label: 'Approval Rate', value: '86%', sub: 'Safe execution', color: 'text-cyan-400' },
          { label: 'Safety Incidents', value: '00', sub: 'Zero leaks', color: 'text-emerald-400' },
        ].map((item, idx) => (
          <div key={idx} className="p-3 rounded-2xl bg-[#171717]/80 border border-white/[0.07] backdrop-blur-xl space-y-1">
            <div className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">{item.label}</div>
            <div className={`text-2xl font-bold font-mono tracking-tight ${item.color}`}>{item.value}</div>
            <div className="text-[10px] text-gray-500 font-mono truncate">{item.sub}</div>
          </div>
        ))}
      </div>

      {/* 2. Safety Overview & Active Monitoring Hero Card */}
      <div className="rounded-3xl border border-emerald-500/40 bg-gradient-to-r from-[#14231e] via-[#14181a] to-[#121216] p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold uppercase tracking-wider">
                ● Governance Policy Active
              </span>
              <span className="text-xs font-mono text-gray-400">Monitoring 4 active agent pipelines</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Safety & Compliance Control Plane
            </h1>
            <p className="text-xs sm:text-sm text-gray-300 leading-relaxed">
              Every tool call emitted by an agent is intercepted by our Policy Matrix. Actions are classified by risk and evaluated against your sandbox rules before side effects occur.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <div className="p-3 rounded-2xl bg-black/40 border border-emerald-500/30 flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <div className="text-xs font-mono">
                <div className="font-bold text-white">Mock-Safe Sandbox</div>
                <div className="text-gray-400 text-[10px]">Zero unapproved filesystem writes</div>
              </div>
            </div>
            <div className="p-3 rounded-2xl bg-black/40 border border-cyan-500/30 flex items-center gap-3">
              <Shield className="w-5 h-5 text-cyan-400" />
              <div className="text-xs font-mono">
                <div className="font-bold text-white">Audit Logged</div>
                <div className="text-gray-400 text-[10px]">100% telemetry coverage</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Split Section: Policy Matrix Table (Left 2 cols) & Controls Toggles (Right 1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Permission Policy Matrix Table */}
        <div className="lg:col-span-2 space-y-4">
          <GlassCard>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/10">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-semibold text-white">Global Permission Policy Matrix</h3>
              </div>
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Filter actions or scopes..."
                  className="w-full bg-black/50 border border-white/10 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="mt-4 overflow-x-auto font-mono text-xs">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-white/10 text-gray-400 text-[11px] uppercase">
                    <th className="py-2.5 px-3">Action Type / Intent</th>
                    <th className="py-2.5 px-3">Tool Scope</th>
                    <th className="py-2.5 px-3">Risk Level</th>
                    <th className="py-2.5 px-3">Policy Status</th>
                    <th className="py-2.5 px-3 text-right">Auto-Approve</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredMatrix.map((item, idx) => (
                    <tr key={idx} className="hover:bg-white/[0.02]">
                      <td className="py-3 px-3 font-sans text-white font-semibold">{item.action}</td>
                      <td className="py-3 px-3 text-cyan-300">{item.scope}</td>
                      <td className="py-3 px-3"><RiskBadge level={item.risk} size="sm" /></td>
                      <td className="py-3 px-3"><StatusBadge status={item.status} size="sm" /></td>
                      <td className="py-3 px-3 text-right">
                        <span className={`px-2 py-0.5 rounded text-[10px] ${
                          item.autoApprove ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-white/5 text-gray-400'
                        }`}>
                          {item.autoApprove ? 'YES' : 'REQUIRES QUEUE'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </div>

        {/* Right 1 Col: Governance Controls Toggles & Risk Thresholds */}
        <div className="space-y-4">
          <GlassCard glow="purple">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <span>Real-Time Governance Controls</span>
            </h3>

            <div className="space-y-3">
              {[
                { key: 'planningFirst' as const, title: 'Planning-First Mode', desc: 'Agents formulate dry-run plans before execution.' },
                { key: 'mockSafe' as const, title: 'Mock-Safe Execution', desc: 'Sandbox external filesystem writes and CLI commands.' },
                { key: 'requireApproval' as const, title: 'Require Sign-off on High Risk', desc: 'Route Medium and High risk tools to Approvals.' },
                { key: 'auditLogging' as const, title: 'Tamper-Proof Audit Logging', desc: 'Record every AST evaluation to immutable log.' },
                { key: 'blockDestructive' as const, title: 'Block Destructive Shell', desc: 'Permanently forbid rm -rf, drop table, and git reset.' },
              ].map((ctrl) => {
                const isChecked = safetySettings[ctrl.key];
                return (
                  <div
                    key={ctrl.key}
                    onClick={() => toggleSafetySetting(ctrl.key)}
                    className="cursor-pointer p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.06] border border-white/5 transition-colors flex items-center justify-between gap-3"
                  >
                    <div>
                      <div className="text-xs font-semibold text-white">{ctrl.title}</div>
                      <div className="text-[10px] text-gray-400 leading-tight mt-0.5">{ctrl.desc}</div>
                    </div>
                    <div className="shrink-0">
                      {isChecked ? (
                        <div className="w-9 h-5 rounded-full bg-cyan-600 flex items-center justify-end px-1 shadow-inner transition-all">
                          <div className="w-3.5 h-3.5 rounded-full bg-white shadow" />
                        </div>
                      ) : (
                        <div className="w-9 h-5 rounded-full bg-white/10 flex items-center justify-start px-1 shadow-inner transition-all">
                          <div className="w-3.5 h-3.5 rounded-full bg-gray-400 shadow" />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </GlassCard>

          {/* Risk Threshold Summary */}
          <GlassCard>
            <h4 className="text-xs font-semibold text-white mb-2">Risk Threshold Definitions</h4>
            <div className="space-y-2 font-mono text-xs">
              <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                <span className="font-bold">LOW:</span> Zero state changes (SELECT, read file).
              </div>
              <div className="p-2 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300">
                <span className="font-bold">MEDIUM:</span> Scoped writes, API drafts, issue sync.
              </div>
              <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300">
                <span className="font-bold">HIGH:</span> Core filesystem mutations, shell CLI.
              </div>
            </div>
          </GlassCard>
        </div>
      </div>

      {/* 4. Bottom Section: Recent Audit Log Timeline */}
      <GlassCard>
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span>Recent Audit Log Events ({governanceLogs.length})</span>
          </h3>
          <span className="text-xs font-mono text-gray-400">100% compliance recorded</span>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-xs">
          {governanceLogs.slice(0, 6).map((log) => (
            <div key={log.id} className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1.5">
              <div className="flex items-center justify-between text-gray-400 text-[10px]">
                <span>{log.timestamp}</span>
                <StatusBadge status={log.status} size="sm" showIcon={false} />
              </div>
              <div className="text-white font-bold truncate">{log.action}</div>
              <div className="text-[11px] text-gray-400 font-sans line-clamp-2">{log.details}</div>
              <div className="flex items-center justify-between pt-1 border-t border-white/5 text-[10px] text-cyan-300">
                <span>Agent: {log.agentName}</span>
                <RiskBadge level={log.risk} size="sm" />
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
};
