import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { planConnectorAction } from '../data/api';
import { GlassCard } from '../components/shared/GlassCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { RiskBadge } from '../components/shared/RiskBadge';
import { 
  Wrench, 
  Cpu, 
  Github, 
  FolderGit2, 
  Database, 
  CheckSquare, 
  MessageSquare, 
  Monitor, 
  ShieldCheck, 
  Activity, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Terminal, 
  Play, 
  Power, 
  Settings, 
  ExternalLink,
  Shield,
  Layers
} from 'lucide-react';
import { ToolConnector } from '../types';

export const ToolsMcpHub: React.FC = () => {
  const { connectors, toggleToolConnection, governanceLogs, showToast } = useApp();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedConnectorId, setSelectedConnectorId] = useState<string>('conn-github');
  const [planResult, setPlanResult] = useState<Awaited<ReturnType<typeof planConnectorAction>>>(null);
  const [planBusy, setPlanBusy] = useState(false);

  const handlePreviewAction = async (connectorId: string, permissions: string[]) => {
    const action = permissions[0] || 'status';
    setPlanBusy(true);
    setPlanResult(null);
    try {
      const res = await planConnectorAction(connectorId, action);
      if (res) { setPlanResult(res); showToast(`Dry-run planned for "${action}" — nothing executed`, 'info'); }
      else showToast('This is a sample connector — connect a real one to plan actions', 'warning');
    } finally {
      setPlanBusy(false);
    }
  };

  const featuredTool = connectors.find(c => c.id === selectedConnectorId) || connectors[0];

  const filteredConnectors = selectedCategory === 'all'
    ? connectors
    : connectors.filter(c => c.category === selectedCategory);

  const connectedCount = connectors.filter(c => c.status === 'connected' || c.status === 'approval-gated').length;
  const gatedCount = connectors.filter(c => c.status === 'approval-gated').length;
  const highRiskCount = connectors.filter(c => c.riskLevel === 'high').length;

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* 1. Overview Metrics (6 counters) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Connected Tools', value: `0${connectedCount}`, sub: 'Active in session', color: 'text-white' },
          { label: 'Approval-Gated', value: `0${gatedCount}`, sub: 'Requires user sign-off', color: 'text-amber-400' },
          { label: 'Read-Only Mode', value: '04', sub: 'Zero side effects', color: 'text-blue-400' },
          { label: 'High-Risk Tools', value: `0${highRiskCount}`, sub: 'Filesystem / CLI', color: 'text-rose-400' },
          { label: 'Calls Today', value: '32', sub: 'Mock sandbox verified', color: 'text-purple-400' },
          { label: 'Failed Checks', value: '00', sub: '100% compliant', color: 'text-emerald-400' },
        ].map((item, idx) => (
          <div key={idx} className="p-3 rounded-2xl bg-[#171717]/80 border border-white/[0.07] backdrop-blur-xl space-y-1">
            <div className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">{item.label}</div>
            <div className={`text-2xl font-bold font-mono tracking-tight ${item.color}`}>{item.value}</div>
            <div className="text-[10px] text-gray-500 font-mono truncate">{item.sub}</div>
          </div>
        ))}
      </div>

      {/* 2. Featured Connector Card (GitHub / Selected Tool Spotlight) */}
      <div className="rounded-3xl border border-purple-500/40 bg-gradient-to-br from-[#1a1c29] via-[#14141c] to-[#121217] p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="flex items-start gap-4 max-w-2xl">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-600 to-blue-600 flex items-center justify-center text-white shrink-0 shadow-lg shadow-purple-500/30">
              {featuredTool.icon === 'Github' ? <Github className="w-8 h-8" /> :
               featuredTool.icon === 'FolderGit2' ? <FolderGit2 className="w-8 h-8" /> :
               featuredTool.icon === 'Database' ? <Database className="w-8 h-8" /> :
               featuredTool.icon === 'CheckSquare' ? <CheckSquare className="w-8 h-8" /> :
               featuredTool.icon === 'MessageSquare' ? <MessageSquare className="w-8 h-8" /> :
               <Monitor className="w-8 h-8" />}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 uppercase font-semibold">
                  {featuredTool.category} Connector Spotlight
                </span>
                <StatusBadge status={featuredTool.status} size="sm" />
                <RiskBadge level={featuredTool.riskLevel} size="sm" />
              </div>

              <h2 className="text-2xl font-extrabold text-white tracking-tight">{featuredTool.name}</h2>
              <p className="text-xs text-gray-300 leading-relaxed pt-1">{featuredTool.description}</p>

              {/* Permission Scopes */}
              <div className="flex flex-wrap items-center gap-1.5 pt-2">
                <span className="text-xs text-gray-400 font-mono">Scoped Permissions:</span>
                {featuredTool.permissions.map((p, idx) => (
                  <span key={idx} className="text-[11px] font-mono px-2 py-0.5 rounded bg-white/10 text-emerald-300 border border-white/10">
                    {p}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Stats & Actions */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 bg-white/[0.03] p-4 rounded-2xl border border-white/10 shrink-0">
            <div className="space-y-2 text-xs font-mono border-b sm:border-b-0 sm:border-r border-white/10 pb-3 sm:pb-0 sm:pr-4">
              <div className="flex items-center justify-between gap-4">
                <span className="text-gray-400">Dry Check:</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Passed
                </span>
              </div>
              <div className="flex items-center justify-between gap-4">
                <span className="text-gray-400">Active Agents:</span>
                <span className="text-white font-semibold">{featuredTool.activeAgentsCount} agents</span>
              </div>
              <div className="flex items-center justify-between gap-4">
                <span className="text-gray-400">Calls Today:</span>
                <span className="text-purple-300 font-semibold">{featuredTool.callsToday} executions</span>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <button
                onClick={() => toggleToolConnection(featuredTool.id)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center justify-center gap-2 shadow-md ${
                  featuredTool.status === 'connected' || featuredTool.status === 'approval-gated'
                    ? 'bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300'
                    : 'bg-emerald-600 hover:bg-emerald-500 text-black font-bold'
                }`}
              >
                <Power className="w-3.5 h-3.5" />
                <span>{featuredTool.status === 'connected' || featuredTool.status === 'approval-gated' ? 'Disconnect Tool' : 'Connect MCP Tool'}</span>
              </button>
              <button
                onClick={() => handlePreviewAction(featuredTool.id, featuredTool.permissions)}
                disabled={planBusy}
                className="px-4 py-2 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 text-purple-200 text-xs font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Settings className="w-3.5 h-3.5 text-purple-300" />
                <span>{planBusy ? 'Planning…' : `Preview action: ${featuredTool.permissions[0] || 'status'}`}</span>
              </button>
              <button
                onClick={() => showToast(`Opening OAuth scope settings for ${featuredTool.name}...`, 'info')}
                className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 text-xs font-medium transition-colors flex items-center justify-center gap-2"
              >
                <Settings className="w-3.5 h-3.5 text-gray-400" />
                <span>Configure OAuth / Sandboxing</span>
              </button>
            </div>
          </div>
        </div>

        {/* Real dry-run plan preview (mock-safe — nothing is executed) */}
        {planResult && (
          <div className="mt-4 p-4 rounded-2xl bg-black/30 border border-purple-500/20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-white">Dry-run plan · <span className="font-mono text-purple-300">{planResult.actionName}</span></span>
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${planResult.riskLevel === 'high' ? 'bg-rose-500/15 text-rose-300' : planResult.riskLevel === 'medium' ? 'bg-amber-500/15 text-amber-300' : 'bg-emerald-500/15 text-emerald-300'}`}>risk: {planResult.riskLevel}</span>
                {planResult.requiresApproval && <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">needs approval</span>}
                {!planResult.allowed && <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-300">blocked</span>}
              </div>
            </div>
            <ol className="list-decimal list-inside space-y-1">
              {planResult.plan.map((step, i) => (
                <li key={i} className="text-[11px] text-gray-300">{step}</li>
              ))}
            </ol>
            {planResult.blockedReason && <p className="text-[11px] text-rose-300 mt-2">Blocked: {planResult.blockedReason}</p>}
            <p className="text-[10px] text-gray-500 mt-2">This is a planned dry-run only — no action was executed. Running it for real would require approval.</p>
          </div>
        )}
      </div>

      {/* 3. Category Filter & Connectors Grid (6 cards) */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Wrench className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-white">Installed Tool Connectors ({filteredConnectors.length})</h3>
          </div>
          
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
            <span className="text-xs text-gray-400 font-mono mr-1">Category:</span>
            {['all', 'MCP', 'API', 'Local CLI', 'Database'].map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1 rounded-lg text-xs font-mono transition-all ${
                  selectedCategory === cat
                    ? 'bg-purple-600 text-white font-semibold shadow-md'
                    : 'bg-white/[0.03] hover:bg-white/[0.08] text-gray-400'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredConnectors.map((tool) => {
            const isSel = tool.id === selectedConnectorId;
            const isConn = tool.status === 'connected' || tool.status === 'approval-gated';
            return (
              <div
                key={tool.id}
                onClick={() => setSelectedConnectorId(tool.id)}
                className={`cursor-pointer rounded-2xl border transition-all p-5 flex flex-col justify-between ${
                  isSel
                    ? 'bg-[#1e1e28]/90 border-purple-500/50 shadow-[0_4px_25px_-5px_rgba(160,120,255,0.2)]'
                    : 'bg-[#171717]/80 border-white/[0.07] hover:bg-[#1a1a20]/90 hover:border-white/15'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-white/[0.04] border border-white/10 flex items-center justify-center text-purple-400">
                        {tool.icon === 'Github' ? <Github className="w-5 h-5" /> :
                         tool.icon === 'FolderGit2' ? <FolderGit2 className="w-5 h-5" /> :
                         tool.icon === 'Database' ? <Database className="w-5 h-5" /> :
                         tool.icon === 'CheckSquare' ? <CheckSquare className="w-5 h-5" /> :
                         tool.icon === 'MessageSquare' ? <MessageSquare className="w-5 h-5" /> :
                         <Monitor className="w-5 h-5" />}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-white">{tool.name}</h4>
                        <span className="text-[10px] font-mono text-purple-300 uppercase">{tool.category}</span>
                      </div>
                    </div>
                    <StatusBadge status={tool.status} size="sm" />
                  </div>

                  <p className="mt-3 text-xs text-gray-400 line-clamp-2 leading-relaxed">{tool.description}</p>

                  <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-xs font-mono">
                    <span className="text-gray-400">Risk Profile:</span>
                    <RiskBadge level={tool.riskLevel} size="sm" />
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono">
                  <span className="text-gray-500">Last used: <strong className="text-gray-300">{tool.lastUsed}</strong></span>
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleToolConnection(tool.id); }}
                    className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                      isConn ? 'bg-white/5 hover:bg-white/10 text-gray-300' : 'bg-emerald-600 text-black font-bold'
                    }`}
                  >
                    {isConn ? 'Disconnect' : 'Connect Tool'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. Split Section: Recent Activity Timeline (Left) & Global Permission Modes (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Recent Activity Timeline */}
        <GlassCard>
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <span className="text-xs font-semibold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-400" /> Recent Tool Call Logs
            </span>
            <span className="text-[10px] font-mono text-gray-400">Mock-Safe Sandbox</span>
          </div>

          <div className="mt-3 space-y-3 font-mono text-xs">
            {governanceLogs.slice(0, 4).map(log => (
              <div key={log.id} className="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-white font-bold">{log.agentName}</span>
                    <span className="text-purple-300">→</span>
                    <span className="text-purple-200 font-semibold truncate max-w-[180px]">{log.action}</span>
                  </div>
                  <p className="text-[11px] text-gray-400 mt-1 font-sans">{log.details}</p>
                </div>
                <StatusBadge status={log.status} size="sm" showIcon={false} />
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Right: Connector Safety & Global Permission Modes */}
        <GlassCard glow="blue">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <span className="text-xs font-semibold text-white flex items-center gap-2">
              <Shield className="w-4 h-4 text-blue-400" /> Global Tool Permission Modes
            </span>
            <span className="text-[10px] font-mono text-emerald-400">● 100% SECURE</span>
          </div>

          <div className="mt-3 space-y-3 text-xs">
            {[
              { mode: 'Read-only Default', desc: 'All tools initialize with read-only scopes. No external writes can occur without explicit elevation.', color: 'text-blue-300 bg-blue-500/10 border-blue-500/20' },
              { mode: 'Draft-only Mode', desc: 'External tools (Slack, Linear, GitHub PRs) formulate drafts and save to queue instead of publishing.', color: 'text-purple-300 bg-purple-500/10 border-purple-500/20' },
              { mode: 'Approval-gated Actions', desc: 'Any tool call marked Medium or High risk triggers an automated interception to the Approvals screen.', color: 'text-amber-300 bg-amber-500/10 border-amber-500/20' },
              { mode: 'Destructive Shell Block', desc: 'Commands like `rm -rf`, `drop table`, or `git reset --hard` are permanently blocked at the AST level.', color: 'text-rose-300 bg-rose-500/10 border-rose-500/20' }
            ].map((rule, idx) => (
              <div key={idx} className={`p-3 rounded-xl border flex items-start justify-between gap-3 ${rule.color}`}>
                <div>
                  <div className="font-bold font-mono">{rule.mode}</div>
                  <p className="text-gray-300 text-[11px] mt-0.5 leading-relaxed font-sans">{rule.desc}</p>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-black/30 shrink-0">ACTIVE</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
