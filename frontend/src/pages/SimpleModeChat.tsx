import React, { useState, useRef, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { GlassCard } from '../components/shared/GlassCard';
import { LiveWorkingCard } from '../components/shared/LiveWorkingCard';
import { 
  Send, 
  Paperclip, 
  Mic, 
  Database, 
  Sparkles, 
  Bot, 
  User, 
  ShieldCheck, 
  Brain, 
  CheckSquare, 
  ArrowRight, 
  Layers, 
  FileCode, 
  Wrench,
  Clock,
  ChevronRight
} from 'lucide-react';

export const SimpleModeChat: React.FC = () => {
  const { chatMessages, sendMessage, mission, agents, connectors, memories, setActivePage, showToast } = useApp();
  const [inputText, setInputText] = useState('');
  const [selectedDb, setSelectedDb] = useState('Workspace Memory + Postgres');
  const [attachments, setAttachments] = useState<{ name: string; size: string; type: string }[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeAgents = agents.filter(a => a.status === 'active' || a.status === 'running');

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() && attachments.length === 0) return;
    
    sendMessage(inputText, attachments.length > 0 ? attachments : undefined);
    setInputText('');
    setAttachments([]);
  };

  const handleAttachMock = () => {
    const mockFiles = [
      { name: 'App.tsx', size: '12 KB', type: 'TypeScript Component' },
      { name: 'tailwind.config.ts', size: '4 KB', type: 'Config' },
      { name: 'ADR-12-design-tokens.md', size: '18 KB', type: 'Markdown Memory' }
    ];
    const nextFile = mockFiles[attachments.length % mockFiles.length];
    setAttachments(prev => [...prev, nextFile]);
    showToast(`Attached ${nextFile.name} (${nextFile.size}) to chat context`, 'info');
  };

  const toggleMic = () => {
    if (!isRecording) {
      setIsRecording(true);
      showToast('Listening to voice command...', 'info');
      setTimeout(() => {
        setIsRecording(false);
        setInputText(prev => prev + (prev ? ' ' : '') + 'Redesign the agents grid cards with higher contrast and clearer status icons.');
        showToast('Voice transcribed successfully!', 'success');
      }, 2500);
    } else {
      setIsRecording(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-8.5rem)] animate-fadeIn pb-6">
      {/* Left 3 Cols: Chat Messages & Input Bar */}
      <div className="lg:col-span-3 flex flex-col h-full bg-[#111116] rounded-3xl border border-white/10 shadow-2xl overflow-hidden">
        {/* Chat Header */}
        <div className="p-4 border-b border-white/10 bg-[#16161c]/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-purple-500/20">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-white">Master Orchestrator & Specialized Agents</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Mock-Safe Mode
                </span>
              </div>
              <p className="text-[11px] text-gray-400 font-mono">Routing across {activeAgents.length} active agents • Planning-First Active</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActivePage('dev-console')}
              className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-gray-300 hover:text-white transition-colors font-mono hidden sm:block"
            >
              Trace Inspector
            </button>
          </div>
        </div>

        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {chatMessages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div key={msg.id} className={`flex items-start gap-3 sm:gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
                {/* Avatar */}
                <div
                  className={`w-8 h-8 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center text-base sm:text-lg shrink-0 ${
                    isUser
                      ? 'bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-lg'
                      : 'bg-[#1e1e26] border border-white/10 text-white shadow-md'
                  }`}
                >
                  {isUser ? <User className="w-5 h-5" /> : msg.avatar || '🤖'}
                </div>

                {/* Message Bubble */}
                <div className={`max-w-2xl space-y-2 ${isUser ? 'items-end text-right' : 'items-start'}`}>
                  <div className="flex items-center gap-2 px-1">
                    <span className="text-xs font-semibold text-gray-300">{isUser ? 'You' : msg.agentName || 'AI Assistant'}</span>
                    <span className="text-[10px] font-mono text-gray-500">{msg.timestamp}</span>
                  </div>

                  <div
                    className={`p-4 rounded-2xl text-sm leading-relaxed ${
                      isUser
                        ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-tr-none shadow-lg'
                        : 'bg-[#1a1a22] border border-white/10 text-gray-200 rounded-tl-none shadow-md'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.text}</p>

                    {/* Attachments inside message if any */}
                    {msg.attachments && msg.attachments.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-white/15 flex flex-wrap gap-2">
                        {msg.attachments.map((file, idx) => (
                          <div key={idx} className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-black/30 border border-white/10 text-xs text-gray-300 font-mono">
                            <FileCode className="w-3.5 h-3.5 text-purple-400" />
                            <span>{file.name}</span>
                            <span className="text-gray-500">({file.size})</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* If this message contains the Live Orchestration Card */}
                  {msg.isWorkingCard && <LiveWorkingCard />}
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Footer Area */}
        <div className="p-4 bg-[#14141a] border-t border-white/10 space-y-3">
          {/* Attached Files Preview */}
          {attachments.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 px-2">
              <span className="text-[11px] font-mono text-gray-400">Attached:</span>
              {attachments.map((file, i) => (
                <div key={i} className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-purple-500/15 border border-purple-500/30 text-purple-300 text-xs font-mono animate-fadeIn">
                  <FileCode className="w-3.5 h-3.5" />
                  <span>{file.name}</span>
                  <button
                    onClick={() => setAttachments(prev => prev.filter((_, idx) => idx !== i))}
                    className="hover:text-white ml-1"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Main Input Form */}
          <form onSubmit={handleSend} className="relative flex items-center gap-2">
            <div className="relative flex-1 flex items-center bg-black/60 rounded-2xl border border-white/15 focus-within:border-purple-500 transition-all shadow-inner px-3 py-2">
              {/* Attachment Button */}
              <button
                type="button"
                onClick={handleAttachMock}
                title="Attach workspace file or code snippet"
                className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
              >
                <Paperclip className="w-4 h-4" />
              </button>

              {/* Database selector dropdown */}
              <div className="relative hidden sm:block border-r border-white/10 pr-2 mr-2">
                <select
                  value={selectedDb}
                  onChange={(e) => setSelectedDb(e.target.value)}
                  className="bg-transparent text-xs text-purple-300 font-mono focus:outline-none cursor-pointer pr-1"
                >
                  <option className="bg-[#171717]">Workspace Memory + Postgres</option>
                  <option className="bg-[#171717]">Project Brain (Vector Index)</option>
                  <option className="bg-[#171717]">Local Filesystem (/src)</option>
                  <option className="bg-[#171717]">GitHub Repo Metadata</option>
                </select>
              </div>

              {/* Input field */}
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Instruct agents, ask questions, or describe what to build next..."
                className="flex-1 bg-transparent text-sm text-white placeholder-gray-500 focus:outline-none px-2 py-1.5"
              />

              {/* Mic Button */}
              <button
                type="button"
                onClick={toggleMic}
                title="Voice input transcription"
                className={`p-2 rounded-xl transition-colors ${
                  isRecording
                    ? 'bg-rose-500/20 text-rose-400 animate-pulse border border-rose-500/30'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Mic className="w-4 h-4" />
              </button>
            </div>

            {/* Send Button */}
            <button
              type="submit"
              disabled={!inputText.trim() && attachments.length === 0}
              className="p-3.5 rounded-2xl bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20 transition-all flex items-center justify-center shrink-0"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>

          {/* Quick prompt suggestions */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <span className="text-gray-500 font-mono shrink-0">Try asking:</span>
            {[
              'Run a safety check on all connected MCP tools',
              'Summarize ADR #12 from Project Brain',
              'Deploy our container build to Cloud Run sandbox',
            ].map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => setInputText(prompt)}
                className="shrink-0 px-2.5 py-1 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-white/5 text-gray-300 text-[11px] transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Right 1 Col: Workspace Context Panel */}
      <div className="space-y-4 flex flex-col h-full overflow-y-auto">
        {/* Active Mission Overview */}
        <GlassCard>
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-purple-400" />
              <h4 className="text-xs font-semibold text-white">Active Mission</h4>
            </div>
            <button onClick={() => setActivePage('mission-control')} className="text-[11px] text-purple-400 hover:underline">
              View
            </button>
          </div>
          <div className="mt-3 space-y-2">
            <div className="text-xs font-semibold text-white">{mission.title}</div>
            <div className="flex items-center justify-between text-[11px] font-mono text-gray-400">
              <span>Progress</span>
              <span className="text-purple-300 font-semibold">{mission.progress}%</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-black/60 overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-purple-500 to-blue-500" style={{ width: `${mission.progress}%` }} />
            </div>
            <div className="flex items-center justify-between text-[10px] text-gray-500 font-mono pt-1">
              <span>5 phases</span>
              <span>4 agents assigned</span>
            </div>
          </div>
        </GlassCard>

        {/* Project Brain Memory Context */}
        <GlassCard>
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-indigo-400" />
              <h4 className="text-xs font-semibold text-white">Brain Context</h4>
            </div>
            <button onClick={() => setActivePage('project-brain')} className="text-[11px] text-purple-400 hover:underline">
              {memories.length} matches
            </button>
          </div>
          <div className="mt-3 space-y-2.5">
            {memories.slice(0, 3).map((mem) => (
              <div key={mem.id} className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-gray-200 truncate max-w-[150px]">{mem.title}</span>
                  <span className="text-[10px] font-mono text-purple-400">{mem.relevance}%</span>
                </div>
                <p className="text-[10px] text-gray-400 line-clamp-2">{mem.snippet}</p>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Active Tools in Session */}
        <GlassCard className="flex-1">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <Wrench className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-semibold text-white">Active Tools</h4>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
              Safe
            </span>
          </div>
          <div className="mt-3 space-y-2">
            {connectors.filter(c => c.status === 'connected' || c.status === 'approval-gated').slice(0, 4).map(tool => (
              <div key={tool.id} className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02] text-xs">
                <span className="text-gray-300 truncate">{tool.name}</span>
                <span className="text-[10px] font-mono text-gray-500">{tool.callsToday}x</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
