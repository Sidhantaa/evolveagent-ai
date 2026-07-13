import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  PlayCircle, 
  PauseCircle, 
  StopCircle, 
  CheckCircle2, 
  Clock, 
  ShieldAlert, 
  Edit3, 
  Check, 
  Sparkles,
  ArrowRight
} from 'lucide-react';

export const LiveWorkingCard: React.FC = () => {
  const { approvals, approveRequest, mission, showToast } = useApp();
  const [isPaused, setIsPaused] = useState(false);
  const [isStopped, setIsStopped] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [customInstruction, setCustomInstruction] = useState('');

  const pendingApproval = approvals.find(a => a.status === 'pending');

  const handlePause = () => {
    setIsPaused(prev => !prev);
    showToast(isPaused ? 'Resumed orchestration pipeline' : 'Paused live agent orchestration', 'info');
  };

  const handleStop = () => {
    setIsStopped(true);
    showToast('Orchestration stopped. All agents returned to idle state.', 'warning');
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customInstruction.trim()) return;
    showToast(`Updated instruction sent to Master Orchestrator: "${customInstruction}"`, 'success');
    setCustomInstruction('');
    setIsEditing(false);
  };

  if (isStopped) {
    return (
      <div className="rounded-xl border border-white/10 bg-[#171717]/90 p-4 text-gray-400 text-sm flex items-center justify-between">
        <span className="flex items-center gap-2">
          <StopCircle className="w-4 h-4 text-rose-400" /> Orchestration stopped by user.
        </span>
        <button 
          onClick={() => setIsStopped(false)} 
          className="text-xs text-cyan-400 hover:text-cyan-300 underline"
        >
          Restart Pipeline
        </button>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-2xl border border-cyan-500/30 bg-[#141418] p-5 shadow-2xl relative overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute -top-10 -right-10 w-40 h-40 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/10 relative z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Sparkles className={`w-4 h-4 text-white ${isPaused ? '' : 'animate-spin'}`} style={{ animationDuration: '4s' }} />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              EvolveAgent is working…
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                {isPaused ? 'PAUSED' : 'LIVE ORCHESTRATION'}
              </span>
            </h4>
            <p className="text-xs text-gray-400">Mission: {mission.title}</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 self-end sm:self-auto">
          <button
            onClick={handlePause}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-300 transition-colors"
          >
            {isPaused ? <PlayCircle className="w-3.5 h-3.5 text-emerald-400" /> : <PauseCircle className="w-3.5 h-3.5 text-amber-400" />}
            <span>{isPaused ? 'Resume' : 'Pause'}</span>
          </button>
          <button
            onClick={() => setIsEditing(prev => !prev)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-300 transition-colors"
          >
            <Edit3 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Edit</span>
          </button>
          <button
            onClick={handleStop}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-xs text-rose-300 transition-colors"
          >
            <StopCircle className="w-3.5 h-3.5" />
            <span>Stop</span>
          </button>
        </div>
      </div>

      {/* Edit Instructions Drawer */}
      {isEditing && (
        <form onSubmit={handleEditSubmit} className="mt-4 p-3 rounded-xl bg-[#1d1d23] border border-cyan-500/30 flex gap-2 animate-fadeIn">
          <input
            type="text"
            value={customInstruction}
            onChange={(e) => setCustomInstruction(e.target.value)}
            placeholder="E.g., Prioritize dark theme contrast over animation speed..."
            className="flex-1 bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
            autoFocus
          />
          <button
            type="submit"
            className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition-colors"
          >
            Send
          </button>
        </form>
      )}

      {/* Current action & active agent status rows */}
      <div className="mt-4 space-y-2.5 relative z-10">
        <div className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">Active Agent Stack</div>
        
        <div className="grid grid-cols-1 gap-2">
          {/* Master Orchestrator */}
          <div className="flex items-center justify-between p-2.5 rounded-xl bg-white/[0.03] border border-white/5">
            <div className="flex items-center gap-2.5">
              <span className="text-base">🤖</span>
              <div>
                <div className="text-xs font-medium text-white">Master Orchestrator</div>
                <div className="text-[11px] text-gray-400">Delegating sub-tasks across 4 worker agents</div>
              </div>
            </div>
            <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              <CheckCircle2 className="w-3 h-3" /> Active
            </span>
          </div>

          {/* UI Design Agent */}
          <div className="flex items-center justify-between p-2.5 rounded-xl bg-cyan-500/5 border border-cyan-500/20">
            <div className="flex items-center gap-2.5">
              <span className="text-base">🎨</span>
              <div>
                <div className="text-xs font-medium text-cyan-200">UI Design Agent</div>
                <div className="text-[11px] text-cyan-300/80">Synthesizing responsive glassmorphism cards</div>
              </div>
            </div>
            <span className="flex items-center gap-1 text-[11px] font-mono text-cyan-300 bg-cyan-500/20 px-2 py-0.5 rounded-full border border-cyan-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" /> Running
            </span>
          </div>

          {/* Memory Agent */}
          <div className="flex items-center justify-between p-2.5 rounded-xl bg-white/[0.03] border border-white/5">
            <div className="flex items-center gap-2.5">
              <span className="text-base">🧠</span>
              <div>
                <div className="text-xs font-medium text-white">Memory Agent</div>
                <div className="text-[11px] text-gray-400">Indexing 19 recent file edits into Project Brain</div>
              </div>
            </div>
            <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              <CheckCircle2 className="w-3 h-3" /> Active
            </span>
          </div>

          {/* Governance Agent */}
          <div className="flex items-center justify-between p-2.5 rounded-xl bg-white/[0.03] border border-white/5">
            <div className="flex items-center gap-2.5">
              <span className="text-base">🛡️</span>
              <div>
                <div className="text-xs font-medium text-white">Governance Agent</div>
                <div className="text-[11px] text-gray-400">Auditing tool calls for Mock-Safe sandboxing</div>
              </div>
            </div>
            <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              <CheckCircle2 className="w-3 h-3" /> Active
            </span>
          </div>

          {/* Implementation Agent */}
          <div className="flex items-center justify-between p-2.5 rounded-xl bg-amber-500/5 border border-amber-500/20">
            <div className="flex items-center gap-2.5">
              <span className="text-base">⚡</span>
              <div>
                <div className="text-xs font-medium text-amber-200">Implementation Agent</div>
                <div className="text-[11px] text-amber-300/80">
                  {pendingApproval ? `Waiting approval on: ${pendingApproval.toolName}` : 'All requested tool calls approved'}
                </div>
              </div>
            </div>
            <span className="flex items-center gap-1 text-[11px] font-mono text-amber-300 bg-amber-500/20 px-2 py-0.5 rounded-full border border-amber-500/30">
              <Clock className="w-3 h-3" /> Waiting Approval
            </span>
          </div>
        </div>
      </div>

      {/* Progress timeline */}
      <div className="mt-4 pt-3 border-t border-white/10 relative z-10">
        <div className="flex items-center justify-between text-xs mb-1.5">
          <span className="text-gray-400 font-mono">Pipeline Progress</span>
          <span className="text-cyan-300 font-mono font-semibold">{mission.progress}%</span>
        </div>
        <div className="w-full h-2 rounded-full bg-black/60 overflow-hidden p-0.5 border border-white/5">
          <div 
            className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-sky-500 to-blue-500 transition-all duration-500"
            style={{ width: `${mission.progress}%` }}
          />
        </div>
      </div>

      {/* Approval controls & Safety Banner */}
      {pendingApproval ? (
        <div className="mt-4 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 relative z-10">
          <div className="flex items-start gap-2.5">
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <div className="text-xs font-semibold text-amber-200">{pendingApproval.title}</div>
              <div className="text-[11px] text-amber-300/80">
                Action: {pendingApproval.plannedAction}
              </div>
            </div>
          </div>
          <button
            onClick={() => approveRequest(pendingApproval.id)}
            className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-black font-semibold text-xs transition-all shadow-lg shrink-0 self-start sm:self-auto"
          >
            <Check className="w-4 h-4 stroke-[3]" />
            <span>Approve Implementation</span>
          </button>
        </div>
      ) : (
        <div className="mt-4 p-3 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between text-xs text-gray-400 relative z-10">
          <span className="flex items-center gap-2 font-mono">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> All high-risk tool operations have been approved.
          </span>
          <button
            onClick={() => showToast('Advancing orchestration to next checkpoint...', 'info')}
            className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium"
          >
            <span>Next Phase</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Safety text */}
      <div className="mt-3 text-[11px] text-center text-gray-500 font-mono relative z-10 flex items-center justify-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
        <span>No real tool action will run until you approve it. Planning-First Mode Active.</span>
      </div>
    </div>
  );
};
