import React from 'react';
import { useApp } from '../../context/AppContext';
import { PageId } from '../../types';
import { 
  Search, 
  Menu, 
  Sparkles, 
  ShieldAlert, 
  Bell, 
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';

export const TopBar: React.FC<{ setMobileOpen: (open: boolean) => void }> = ({ setMobileOpen }) => {
  const { activePage, setActivePage, setIsCommandModalOpen, approvals, safetySettings, toggleSafetySetting, showToast, liveConnected, refreshLive } = useApp();

  const pendingApprovalsCount = approvals.filter(a => a.status === 'pending').length;

  const pageTitles: Record<PageId, { title: string; subtitle: string }> = {
    'home': { title: 'Home Dashboard', subtitle: 'AI command center & multi-agent system overview' },
    'instructions': { title: 'Instructions & Getting Started', subtitle: 'How EvolveAgent AI works, and how to use it safely' },
    'chat': { title: 'Simple Mode Chat', subtitle: 'ChatGPT-style agent interface with live orchestration' },
    'dev-console': { title: 'Developer Mode Console', subtitle: 'System health, workflow trace inspector & tool call logs' },
    'mission-control': { title: 'Mission Control', subtitle: 'Active mission tracker, phase graph & next best action recommendations' },
    'agents': { title: 'Agents Overview', subtitle: 'Manage specialized agents, permission profiles & safety rules' },
    'approvals': { title: 'Approvals Queue', subtitle: 'Review risk explanations, governance checks & cost limits' },
    'project-brain': { title: 'Project Brain', subtitle: 'Workspace memory search, knowledge graph & decision records' },
    'tools': { title: 'Tools / MCP Hub', subtitle: 'Manage connected tools, MCP connectors & global permission modes' },
    'governance': { title: 'Governance & Safety', subtitle: 'Safety policy matrix, audit logs & risk threshold controls' },
    'settings': { title: 'Workspace Settings', subtitle: 'AI model routing, safety defaults, memory indexing & appearance' },
    'design-system': { title: 'Design System Tokens', subtitle: 'Brand palette, typography scale, core components & interaction rules' }
  };

  const currentInfo = pageTitles[activePage] || { title: 'EvolveAgent AI', subtitle: 'Local-first multi-agent operating system' };

  return (
    <header className="sticky top-0 z-40 h-16 shrink-0 bg-[#0a0a0c]/80 backdrop-blur-xl border-b border-white/[0.08] px-4 sm:px-6 flex items-center justify-between gap-4">
      {/* Left side: Mobile menu + Page Title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-xl bg-white/[0.04] border border-white/10 text-gray-300 hover:text-white lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h2 className="text-sm sm:text-base font-bold text-white tracking-tight truncate">{currentInfo.title}</h2>
            {pendingApprovalsCount > 0 && activePage !== 'approvals' && (
              <button
                onClick={() => setActivePage('approvals')}
                className="hidden sm:inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30 transition-colors"
              >
                <ShieldAlert className="w-3 h-3" />
                <span>{pendingApprovalsCount} Action{pendingApprovalsCount > 1 ? 's' : ''} Need Review</span>
              </button>
            )}
          </div>
          <p className="text-[11px] text-gray-400 truncate hidden sm:block">{currentInfo.subtitle}</p>
        </div>
      </div>

      {/* Center/Right: Command Bar Trigger + Quick Mode Tabs + Safety Badge */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Command K input button */}
        <button
          onClick={() => setIsCommandModalOpen(true)}
          className="flex items-center justify-between gap-3 px-3 py-1.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/10 text-gray-400 hover:text-gray-200 text-xs transition-all w-36 sm:w-56"
        >
          <div className="flex items-center gap-2 truncate">
            <Search className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <span className="truncate">Search or ⌘ K</span>
          </div>
          <kbd className="hidden sm:inline-block font-mono text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-gray-400 border border-white/10">
            ⌘K
          </kbd>
        </button>

        {/* Live/Mock data indicator — reflects real backend connection */}
        <button
          onClick={() => { refreshLive(); showToast(liveConnected ? 'Refreshed live data from backend' : 'Backend offline — showing sample data', liveConnected ? 'success' : 'warning'); }}
          title={liveConnected ? 'Connected to the local backend — click to refresh' : 'Backend offline (showing sample data) — click to retry'}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border text-xs font-mono transition-colors shrink-0 ${
            liveConnected
              ? 'bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/20 text-emerald-300'
              : 'bg-white/[0.04] hover:bg-white/[0.08] border-white/10 text-gray-400'
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${liveConnected ? 'bg-emerald-400 animate-pulse' : 'bg-gray-500'}`} />
          <span className="hidden md:inline">{liveConnected ? 'Live Data' : 'Sample Data'}</span>
        </button>

        {/* Safety-mode badge — reflects Mock-Safe and toggles it on click */}
        <button
          onClick={() => toggleSafetySetting('mockSafe')}
          title={safetySettings.mockSafe
            ? 'Mock-Safe ON: risky actions are simulated & held for approval. Click to allow real (non-risky) execution.'
            : 'Real Actions ON: non-risky intents execute for real; risky ones are still approval-gated by the backend. Click to re-enable Mock-Safe.'}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border text-xs font-mono transition-colors shrink-0 ${
            safetySettings.mockSafe
              ? 'bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/20 text-emerald-300'
              : 'bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/30 text-amber-300'
          }`}
        >
          {safetySettings.mockSafe
            ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            : <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />}
          <span className="hidden md:inline">{safetySettings.mockSafe ? 'Mock-Safe' : 'Real Actions'}</span>
        </button>
      </div>
    </header>
  );
};
