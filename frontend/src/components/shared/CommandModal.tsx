import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Search, 
  Terminal, 
  Sparkles, 
  ArrowRight, 
  ShieldAlert, 
  Brain, 
  Bot, 
  CheckSquare, 
  Settings, 
  X,
  Play,
  FileCode,
  Sliders,
  Layers
} from 'lucide-react';
import { PageId } from '../../types';

export const CommandModal: React.FC = () => {
  const { 
    isCommandModalOpen, 
    setIsCommandModalOpen, 
    setActivePage, 
    agents, 
    memories, 
    approvals,
    runMockWorkflowStep,
    approveBatchLowRisk,
    showToast
  } = useApp();
  const [query, setQuery] = useState('');

  useEffect(() => {
    if (isCommandModalOpen) {
      setQuery('');
    }
  }, [isCommandModalOpen]);

  if (!isCommandModalOpen) return null;

  const handleClose = () => setIsCommandModalOpen(false);

  const navigateTo = (page: PageId) => {
    setActivePage(page);
    handleClose();
    showToast(`Navigated to ${page.toUpperCase().replace('-', ' ')}`, 'info');
  };

  const executeAction = (action: () => void, msg: string) => {
    action();
    handleClose();
    if (msg) showToast(msg, 'success');
  };

  const quickActions = [
    { title: 'Review my repo & suggest UI architecture', icon: Sparkles, action: () => navigateTo('chat'), tag: 'Agent Workflow' },
    { title: 'Plan workflow for Mission #01', icon: CheckSquare, action: () => navigateTo('mission-control'), tag: 'Mission Chief' },
    { title: 'Approve pending low-risk tool batch', icon: ShieldAlert, action: () => executeAction(approveBatchLowRisk, ''), tag: 'Governance' },
    { title: 'Simulate next workflow trace step', icon: Play, action: () => executeAction(runMockWorkflowStep, ''), tag: 'Dev Console' },
    { title: 'Search Project Brain memories for tokens', icon: Brain, action: () => navigateTo('project-brain'), tag: 'Knowledge' },
    { title: 'Inspect UI Design Agent live tokens', icon: Bot, action: () => navigateTo('agents'), tag: 'Agent Profile' },
  ];

  const filteredActions = quickActions.filter(a => a.title.toLowerCase().includes(query.toLowerCase()));
  const filteredAgents = agents.filter(a => a.name.toLowerCase().includes(query.toLowerCase()) || a.role.toLowerCase().includes(query.toLowerCase()));
  const filteredMemories = memories.filter(m => m.title.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 px-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="w-full max-w-2xl rounded-2xl border border-white/15 bg-[#141418] shadow-2xl overflow-hidden relative">
        {/* Top Search bar */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-white/10 bg-[#1a1a20]/60">
          <Search className="w-5 h-5 text-purple-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search EvolveAgent AI (e.g. 'repo', 'approve', 'brain')..."
            className="flex-1 bg-transparent text-sm text-white placeholder-gray-500 focus:outline-none"
            autoFocus
          />
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/10 text-gray-400 border border-white/10">ESC</span>
            <button onClick={handleClose} className="p-1 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content list */}
        <div className="max-h-[65vh] overflow-y-auto p-3 space-y-4">
          {/* Quick Actions */}
          <div>
            <div className="text-[10px] font-mono uppercase tracking-wider text-gray-400 px-2 mb-1.5">Quick Commands & Actions</div>
            <div className="space-y-1">
              {filteredActions.map((item, idx) => {
                const Icon = item.icon;
                return (
                  <button
                    key={idx}
                    onClick={item.action}
                    className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-white/[0.06] text-left transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 group-hover:bg-purple-500/20 group-hover:text-purple-300 transition-colors">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-medium text-white group-hover:text-purple-200 transition-colors">{item.title}</div>
                        <div className="text-[11px] text-gray-500">{item.tag}</div>
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-white transition-colors" />
                  </button>
                );
              })}
            </div>
          </div>

          {/* Navigation Pages */}
          {query && (
            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-gray-400 px-2 mb-1.5">Navigate to Screen</div>
              <div className="grid grid-cols-2 gap-1.5">
                {(['home', 'chat', 'dev-console', 'mission-control', 'agents', 'approvals', 'project-brain', 'tools', 'governance', 'settings', 'design-system'] as PageId[]).map((page) => (
                  <button
                    key={page}
                    onClick={() => navigateTo(page)}
                    className="flex items-center gap-2 p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.08] border border-white/5 text-xs text-gray-300 capitalize transition-colors"
                  >
                    <Layers className="w-3.5 h-3.5 text-purple-400" />
                    <span>{page.replace('-', ' ')}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Agents */}
          {filteredAgents.length > 0 && (
            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-gray-400 px-2 mb-1.5">Active Agents ({filteredAgents.length})</div>
              <div className="space-y-1">
                {filteredAgents.map(agent => (
                  <button
                    key={agent.id}
                    onClick={() => navigateTo('agents')}
                    className="w-full flex items-center justify-between p-2 rounded-xl hover:bg-white/[0.06] text-left transition-colors"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="text-base">{agent.avatar}</span>
                      <div>
                        <div className="text-xs font-medium text-white">{agent.name}</div>
                        <div className="text-[11px] text-gray-400">{agent.role}</div>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/5 text-gray-300 border border-white/10 capitalize">
                      {agent.status}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Project Brain Matches */}
          {filteredMemories.length > 0 && (
            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-gray-400 px-2 mb-1.5">Project Brain ({filteredMemories.length})</div>
              <div className="space-y-1">
                {filteredMemories.slice(0, 3).map(mem => (
                  <button
                    key={mem.id}
                    onClick={() => navigateTo('project-brain')}
                    className="w-full flex items-center justify-between p-2 rounded-xl hover:bg-white/[0.06] text-left transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <Brain className="w-3.5 h-3.5 text-indigo-400" />
                      <span className="text-xs text-gray-300 truncate max-w-md">{mem.title}</span>
                    </div>
                    <span className="text-[10px] font-mono text-purple-400">{mem.relevance}% Match</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-white/10 bg-[#121215] flex items-center justify-between text-[11px] text-gray-500 font-mono">
          <div className="flex items-center gap-3">
            <span>↑↓ to navigate</span>
            <span>ENTER to select</span>
            <span>ESC to close</span>
          </div>
          <div className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Mock-Safe Environment</span>
          </div>
        </div>
      </div>
    </div>
  );
};
