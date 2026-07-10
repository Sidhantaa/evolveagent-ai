import React from 'react';
import { useApp } from '../../context/AppContext';
import { PageId } from '../../types';
import {
  LayoutDashboard,
  MessageSquare,
  Terminal,
  GitPullRequestArrow,
  Compass,
  Users,
  ShieldCheck,
  Brain,
  Wrench,
  Shield,
  Settings,
  Palette,
  Sparkles,
  ChevronRight,
  ShieldAlert,
  Activity,
  Gauge,
  Target
} from 'lucide-react';

interface NavItem {
  id: PageId;
  label: string;
  icon: React.ElementType;
  badge?: string | number;
  badgeColor?: 'purple' | 'amber' | 'emerald';
}

export const Sidebar: React.FC<{ mobileOpen?: boolean; setMobileOpen?: (open: boolean) => void }> = ({
  mobileOpen = false,
  setMobileOpen
}) => {
  const { activePage, setActivePage, approvals, agents, memories, safetySettings } = useApp();

  const pendingApprovalsCount = approvals.filter(a => a.status === 'pending').length;
  const activeAgentsCount = agents.filter(a => a.status === 'active' || a.status === 'running').length;

  const navItems: NavItem[] = [
    { id: 'home', label: 'Home Dashboard', icon: LayoutDashboard },
    { id: 'chat', label: 'Simple Mode Chat', icon: MessageSquare, badge: 'Live', badgeColor: 'purple' },
    { id: 'dev-console', label: 'Dev Mode Console', icon: Terminal, badge: 'Trace', badgeColor: 'emerald' },
    { id: 'code-changes', label: 'Code Changes', icon: GitPullRequestArrow, badge: 'v150', badgeColor: 'amber' },
    { id: 'mission-control', label: 'Mission Control', icon: Compass, badge: '62%', badgeColor: 'purple' },
    { id: 'agents', label: 'Agents', icon: Users, badge: activeAgentsCount, badgeColor: 'emerald' },
    { id: 'approvals', label: 'Approvals', icon: ShieldCheck, badge: pendingApprovalsCount > 0 ? pendingApprovalsCount : undefined, badgeColor: 'amber' },
    { id: 'project-brain', label: 'Project Brain', icon: Brain, badge: memories.length, badgeColor: 'purple' },
    { id: 'tools', label: 'Tools / MCP Hub', icon: Wrench, badge: '07', badgeColor: 'emerald' },
    { id: 'governance', label: 'Governance', icon: Shield, badge: '98%', badgeColor: 'emerald' },
    { id: 'command-center', label: 'Command Center', icon: Gauge, badge: 'v200', badgeColor: 'purple' },
    { id: 'chief-of-staff', label: 'Chief of Staff', icon: Target, badge: 'v180', badgeColor: 'amber' },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'design-system', label: 'Design System', icon: Palette }
  ];

  const handleNav = (id: PageId) => {
    setActivePage(id);
    if (setMobileOpen) setMobileOpen(false);
  };

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen && setMobileOpen(false)}
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:sticky top-0 left-0 z-50 h-screen w-64 shrink-0 bg-[#0d0d10] border-r border-white/[0.08] flex flex-col justify-between transition-transform duration-300 lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="p-4 border-b border-white/[0.08]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-blue-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
                  EvolveAgent <span className="text-purple-400 font-mono text-xs">AI</span>
                </h1>
                <div className="flex items-center gap-1.5 text-[10px] text-gray-400 font-mono">
                  <span>vNext 2.4.0</span>
                  <span className="w-1 h-1 rounded-full bg-emerald-400" />
                  <span className="text-emerald-400">Local-First</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation items */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="text-[10px] font-mono uppercase tracking-wider text-gray-500 px-3 py-1">Operating System</div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            
            let badgeBg = 'bg-white/10 text-gray-300 border-white/10';
            if (item.badgeColor === 'purple') badgeBg = 'bg-purple-500/20 text-purple-300 border-purple-500/30';
            if (item.badgeColor === 'amber') badgeBg = 'bg-amber-500/20 text-amber-300 border-amber-500/30 animate-pulse';
            if (item.badgeColor === 'emerald') badgeBg = 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';

            return (
              <button
                key={item.id}
                onClick={() => handleNav(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-gradient-to-r from-purple-600/20 to-blue-600/10 text-white border border-purple-500/30 shadow-[0_0_15px_-3px_rgba(160,120,255,0.15)] font-semibold'
                    : 'text-gray-400 hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 shrink-0 transition-colors ${isActive ? 'text-purple-400' : 'text-gray-500 group-hover:text-gray-300'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && (
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${badgeBg}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* System Health / Safety Footer */}
        <div className="p-3 border-t border-white/[0.08] bg-[#0a0a0c]">
          <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-emerald-400" /> System Health
              </span>
              <span className="font-mono font-semibold text-emerald-400">98% A+</span>
            </div>
            
            <div className="w-full h-1.5 rounded-full bg-black/60 overflow-hidden p-0.5">
              <div className="h-full w-[98%] rounded-full bg-gradient-to-r from-emerald-500 to-purple-500" />
            </div>

            <div className="flex items-center justify-between text-[10px] font-mono text-gray-500 pt-1 border-t border-white/5">
              <span>Mode: {safetySettings.planningFirst ? 'Planning-First' : 'Direct'}</span>
              <span className="text-purple-400">Mock-Safe</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
