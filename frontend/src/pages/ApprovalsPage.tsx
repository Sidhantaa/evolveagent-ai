import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { GlassCard } from '../components/shared/GlassCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { RiskBadge } from '../components/shared/RiskBadge';
import { 
  ShieldCheck, 
  ShieldAlert, 
  Check, 
  X, 
  Clock, 
  Search, 
  Filter, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  Wrench, 
  Cpu, 
  FileCode, 
  DollarSign, 
  FolderGit2, 
  Sparkles,
  Edit3
} from 'lucide-react';
import { ApprovalRequest } from '../types';

export const ApprovalsPage: React.FC = () => {
  const { approvals, approveRequest, rejectRequest, approveBatchLowRisk, governanceLogs, showToast } = useApp();
  const [selectedId, setSelectedId] = useState<string>(approvals.find(a => a.status === 'pending')?.id || approvals[0]?.id || 'app-01');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');

  const selectedItem = approvals.find(a => a.id === selectedId) || approvals[0];

  const filteredApprovals = approvals.filter(a => {
    const matchesStatus = statusFilter === 'all' ? true : a.status === statusFilter;
    const matchesQuery = a.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                         a.agentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         a.toolName.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesQuery;
  });

  const pendingCount = approvals.filter(a => a.status === 'pending').length;
  const approvedToday = approvals.filter(a => a.status === 'approved').length + 14;
  const rejectedToday = approvals.filter(a => a.status === 'rejected').length + 2;

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* 1. Overview Metrics & Batch Approval Action Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-4 rounded-3xl bg-[#141418] border border-white/10 shadow-xl">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 flex-1">
          {[
            { label: 'Pending Review', value: `${pendingCount}`, sub: 'Requires sign-off', color: 'text-amber-400' },
            { label: 'Approved Today', value: `${approvedToday}`, sub: 'Mock sandbox', color: 'text-emerald-400' },
            { label: 'Rejected Today', value: `${rejectedToday}`, sub: 'Safety blocks', color: 'text-rose-400' },
            { label: 'Blocked Actions', value: '02', sub: 'Destructive shell', color: 'text-rose-400' },
            { label: 'Avg Review Time', value: '42s', sub: 'Fast governance', color: 'text-purple-400' },
            { label: 'High-Risk Tools', value: '01', sub: 'Filesystem write', color: 'text-amber-400' },
          ].map((m, idx) => (
            <div key={idx} className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-0.5">
              <div className="text-[10px] font-mono text-gray-400 uppercase tracking-wider">{m.label}</div>
              <div className={`text-xl font-bold font-mono ${m.color}`}>{m.value}</div>
              <div className="text-[10px] text-gray-500 font-mono truncate">{m.sub}</div>
            </div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 shrink-0">
          <button
            onClick={approveBatchLowRisk}
            className="px-5 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-xs transition-all shadow-lg shadow-purple-500/20 flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            <span>Approve Low-Risk Batch</span>
          </button>
        </div>
      </div>

      {/* 2. Priority Approval Spotlight Card (if pending exists) */}
      {selectedItem && selectedItem.status === 'pending' && (
        <div className="rounded-3xl border border-amber-500/40 bg-gradient-to-br from-[#241c14] via-[#1a1716] to-[#141418] p-6 sm:p-8 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
          
          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6 relative z-10">
            <div className="space-y-4 flex-1">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase font-semibold">
                  Priority Sign-Off Required
                </span>
                <RiskBadge level={selectedItem.riskLevel} />
                <span className="text-xs font-mono text-gray-400">{selectedItem.timestamp}</span>
              </div>

              <div>
                <h2 className="text-2xl font-extrabold text-white tracking-tight">{selectedItem.title}</h2>
                <p className="text-xs sm:text-sm text-gray-300 mt-1">Requested by <strong className="text-white">{selectedItem.agentName}</strong></p>
              </div>

              {/* Intent & Planned Action Box */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-2xl bg-black/40 border border-white/10 font-mono text-xs">
                <div>
                  <span className="text-gray-500 text-[10px] uppercase block mb-1">Agent Intent & Purpose</span>
                  <p className="text-gray-200">{selectedItem.intent}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-[10px] uppercase block mb-1">Exact Planned Tool Action</span>
                  <p className="text-amber-300 font-semibold">{selectedItem.plannedAction}</p>
                </div>
              </div>

              {/* Permission Scope Tags */}
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <span className="text-xs text-gray-400 font-mono">Permission Scopes:</span>
                {selectedItem.permissionScopes.map((scope, i) => (
                  <span key={i} className="text-xs font-mono px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-gray-200">
                    {scope}
                  </span>
                ))}
              </div>
            </div>

            {/* Action buttons on the right */}
            <div className="flex flex-col sm:flex-row lg:flex-col gap-2.5 shrink-0 bg-black/30 p-4 rounded-2xl border border-white/10 w-full lg:w-64">
              <button
                onClick={() => approveRequest(selectedItem.id)}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-black font-extrabold text-xs transition-all shadow-lg flex items-center justify-center gap-2"
              >
                <Check className="w-4 h-4 stroke-[3]" />
                <span>Approve & Execute</span>
              </button>
              <button
                onClick={() => rejectRequest(selectedItem.id)}
                className="w-full py-2.5 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 font-semibold text-xs transition-all flex items-center justify-center gap-2"
              >
                <X className="w-4 h-4" />
                <span>Reject Request</span>
              </button>
              <button
                onClick={() => showToast('Opened scope modification modal...', 'info')}
                className="w-full py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 font-medium text-xs transition-all flex items-center justify-center gap-2"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>Edit Scope / Restrict</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. Split Section: Approval Queue Data Table (Left 2 cols) & Detail Drawer (Right 1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Data Table & Filters */}
        <div className="lg:col-span-2 space-y-4">
          <GlassCard>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/10">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-semibold text-white">Approval Queue ({filteredApprovals.length})</h3>
              </div>

              <div className="flex items-center gap-2">
                {/* Status tabs */}
                <div className="flex items-center p-1 rounded-xl bg-white/[0.03] border border-white/10 text-xs font-mono">
                  {(['pending', 'approved', 'rejected', 'all'] as const).map(s => (
                    <button
                      key={s}
                      onClick={() => setStatusFilter(s)}
                      className={`px-2.5 py-1 rounded-lg capitalize transition-colors ${
                        statusFilter === s ? 'bg-purple-600 text-white font-semibold' : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Search Input */}
            <div className="mt-4 relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by action title, agent name, or MCP tool..."
                className="w-full bg-black/40 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
              />
            </div>

            {/* Table */}
            <div className="mt-4 overflow-x-auto font-mono text-xs">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-white/10 text-gray-400 text-[11px] uppercase">
                    <th className="py-2.5 px-3">Request Title</th>
                    <th className="py-2.5 px-3">Agent</th>
                    <th className="py-2.5 px-3">Risk</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Quick Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredApprovals.map((item) => {
                    const isSel = item.id === selectedId;
                    const isPend = item.status === 'pending';
                    return (
                      <tr
                        key={item.id}
                        onClick={() => setSelectedId(item.id)}
                        className={`cursor-pointer transition-colors ${
                          isSel ? 'bg-purple-900/20 font-medium' : 'hover:bg-white/[0.03]'
                        }`}
                      >
                        <td className="py-3 px-3 font-sans text-white font-semibold truncate max-w-[200px]">{item.title}</td>
                        <td className="py-3 px-3 text-gray-300">{item.agentName}</td>
                        <td className="py-3 px-3"><RiskBadge level={item.riskLevel} size="sm" /></td>
                        <td className="py-3 px-3"><StatusBadge status={item.status} size="sm" /></td>
                        <td className="py-3 px-3 text-right">
                          {isPend ? (
                            <div className="inline-flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                              <button
                                onClick={() => approveRequest(item.id)}
                                title="Approve"
                                className="p-1.5 rounded bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/30"
                              >
                                <Check className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => rejectRequest(item.id)}
                                title="Reject"
                                className="p-1.5 rounded bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 border border-rose-500/30"
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          ) : (
                            <span className="text-[10px] text-gray-500">{item.timestamp}</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </div>

        {/* Right 1 Col: Approval Detail Panel */}
        <div className="space-y-4">
          <GlassCard className="h-full flex flex-col justify-between font-mono">
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-white/10">
                <span className="text-xs font-sans font-semibold text-white">Governance Risk Explanation</span>
                <span className="text-[10px] text-purple-400">{selectedItem.id}</span>
              </div>

              {/* Title & Tool info */}
              <div className="space-y-2">
                <h4 className="text-sm font-sans font-bold text-white">{selectedItem.title}</h4>
                <div className="p-2.5 rounded-xl bg-black/50 border border-white/10 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between text-gray-400">
                    <span>MCP Tool Name:</span>
                    <strong className="text-purple-300">{selectedItem.toolName}</strong>
                  </div>
                  <div className="flex items-center justify-between text-gray-400">
                    <span>Workspace Scope:</span>
                    <strong className="text-white truncate max-w-[150px]">{selectedItem.workspaceScope}</strong>
                  </div>
                  <div className="flex items-center justify-between text-gray-400">
                    <span>Estimated Cost:</span>
                    <strong className="text-emerald-400">{selectedItem.costLimit || '$0.00'}</strong>
                  </div>
                </div>
              </div>

              {/* Governance Automated Checks */}
              <div className="space-y-2">
                <span className="text-[10px] text-gray-500 uppercase block">Automated Governance Checks</span>
                <div className="space-y-2">
                  {selectedItem.governanceChecks.map((chk, i) => (
                    <div key={i} className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
                      <div className="flex items-center justify-between text-xs font-sans font-semibold">
                        <span className="text-gray-200">{chk.label}</span>
                        {chk.passed ? (
                          <span className="text-emerald-400 flex items-center gap-1 text-[11px] font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Passed
                          </span>
                        ) : (
                          <span className="text-amber-400 flex items-center gap-1 text-[11px] font-mono">
                            <AlertTriangle className="w-3.5 h-3.5" /> Required
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] font-sans text-gray-400">{chk.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom action buttons in detail drawer */}
            {selectedItem.status === 'pending' ? (
              <div className="mt-6 pt-4 border-t border-white/10 space-y-2">
                <button
                  onClick={() => approveRequest(selectedItem.id)}
                  className="w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-sans font-bold text-xs transition-all flex items-center justify-center gap-1.5 shadow-lg"
                >
                  <Check className="w-4 h-4 stroke-[3]" />
                  <span>Grant Permission</span>
                </button>
                <button
                  onClick={() => rejectRequest(selectedItem.id)}
                  className="w-full py-2 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 font-sans font-semibold text-xs transition-all"
                >
                  Reject Request
                </button>
              </div>
            ) : (
              <div className="mt-6 pt-4 border-t border-white/10 text-center text-xs font-sans">
                <StatusBadge status={selectedItem.status} />
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
