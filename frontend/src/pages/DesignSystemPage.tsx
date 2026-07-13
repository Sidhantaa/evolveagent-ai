import React from 'react';
import { useApp } from '../context/AppContext';
import { GlassCard } from '../components/shared/GlassCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { RiskBadge } from '../components/shared/RiskBadge';
import { LiveWorkingCard } from '../components/shared/LiveWorkingCard';
import { 
  Palette, 
  Layers, 
  Sparkles, 
  Code2, 
  CheckCircle2, 
  ShieldCheck, 
  Cpu, 
  Bot, 
  Search, 
  Terminal, 
  LayoutDashboard, 
  MessageSquare, 
  Compass, 
  Users, 
  Brain, 
  Wrench, 
  Shield, 
  Settings, 
  ArrowRight,
  FolderGit2,
  FileCode
} from 'lucide-react';
import { PageId } from '../types';

export const DesignSystemPage: React.FC = () => {
  const { setActivePage, showToast } = useApp();

  const colorTokens = [
    { name: 'Professional Slate (Background)', hex: '#0a0a0b', tailwind: 'bg-[#0a0a0b]', border: 'border-white/10' },
    { name: 'Graphite Surface (Sidebar/Cards)', hex: '#0d0d0f / #141416', tailwind: 'bg-[#141416]/90 backdrop-blur-xl', border: 'border-white/[0.08]' },
    { name: 'Elevated Glass (Hover State)', hex: '#1a1a1d (90% opacity)', tailwind: 'bg-[#1a1a1d]/90 backdrop-blur-lg', border: 'border-white/15' },
    { name: 'Sky Cyan Polish (Primary)', hex: '#0284c7 / #0891b2', tailwind: 'bg-gradient-to-r from-sky-600 to-cyan-600', border: 'border-sky-500/50' },
    { name: 'Professional Accent (Active State)', hex: '#4f46e5 / #3b82f6', tailwind: 'bg-gradient-to-r from-sky-500 to-blue-600', border: 'border-blue-500/50' },
    { name: 'Indigo Soft Chip (Text/Badges)', hex: '#818cf8 / #c4b5fd', tailwind: 'bg-sky-500/15 text-sky-300', border: 'border-sky-500/30' },
  ];

  const typographyTokens = [
    { name: 'Display Headings', font: 'Inter Display', style: 'text-xl sm:text-2xl font-extrabold tracking-tight text-white', sample: 'What mission shall we delegate today?' },
    { name: 'UI Base Text', font: 'Inter UI Base', style: 'text-xs sm:text-sm text-slate-300 leading-relaxed', sample: 'EvolveAgent AI routes high-level intents across specialized agents with deep knowledge.' },
    { name: 'Technical / Monospace', font: 'Geist Mono', style: 'text-xs font-mono text-sky-300', sample: 'component_generator --target=AgentsGrid --tokens=ADR12' },
  ];

  const radiusTokens = [
    { name: 'Small Tag / Badge (8px)', style: 'rounded-lg bg-white/10 p-3 text-center text-xs' },
    { name: 'Standard Card / Input (12px)', style: 'rounded-xl bg-white/10 p-4 text-center text-xs' },
    { name: 'Glass Panel Container (16px)', style: 'rounded-2xl bg-white/10 p-5 text-center text-xs' },
    { name: 'Hero Spotlight Card (24px)', style: 'rounded-3xl bg-white/10 p-6 text-center text-xs font-bold' },
  ];

  const layoutThumbnails: { id: PageId; label: string; icon: React.ElementType; desc: string }[] = [
    { id: 'home', label: 'Home Dashboard', icon: LayoutDashboard, desc: 'Hero AI command bar + 5 metrics + timeline & approval queue split' },
    { id: 'chat', label: 'Simple Mode Chat', icon: MessageSquare, desc: 'ChatGPT-style messaging + working cards + right context drawer' },
    { id: 'dev-console', label: 'Dev Mode Console', icon: Terminal, desc: 'Step-by-step trace inspector + raw JSON + tool call table' },
    { id: 'mission-control', label: 'Mission Control', icon: Compass, desc: 'Radial mission progress + next best action + 4-column task graph' },
    { id: 'agents', label: 'Agents Overview', icon: Users, desc: 'Featured agent spotlight + 3-column squad grid + permission profiles' },
    { id: 'approvals', label: 'Approvals Queue', icon: ShieldCheck, desc: 'Batch approval banner + priority sign-off + check/close table' },
    { id: 'project-brain', label: 'Project Brain', icon: Brain, desc: 'Vector search hero + relevance percentage bars + graph visualizer' },
    { id: 'tools', label: 'Tools / MCP Hub', icon: Wrench, desc: 'Installed connector grid + category filter + safety modes' },
    { id: 'governance', label: 'Governance & Safety', icon: Shield, desc: 'Global policy matrix table + sandbox toggle switches' },
    { id: 'settings', label: 'Workspace Settings', icon: Settings, desc: 'Model routing controls + auto-save ADRs + theme selector' },
  ];

  const interactionRules = [
    { title: '1. Persistence Principle', desc: 'All user chat commands and architectural decisions must be embedded into Project Brain vectors for long-term recall across sessions.' },
    { title: '2. Draft-First Communication', desc: 'External MCP connectors (Slack, Linear, GitHub issues) must formulate draft payloads by default instead of immediately publishing to third-party APIs.' },
    { title: '3. Context Attribution', desc: 'Every component update or synthesized code block must cite its source ADR or memory rule in the UI to maintain transparency.' },
    { title: '4. Safe-Mode Sandboxing Default', desc: 'Destructive shell commands (rm -rf, drop table) are blocked at the AST level. High-risk filesystem writes always enter the Approvals queue.' },
  ];

  return (
    <div className="space-y-8 animate-fadeIn pb-16">
      {/* Header Banner */}
      <div className="rounded-3xl border border-cyan-500/40 bg-gradient-to-br from-[#1c1a29] via-[#14141c] to-[#121217] p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute -top-20 -right-20 w-80 h-80 bg-cyan-600/15 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-xs font-mono mb-3">
            <Palette className="w-3.5 h-3.5" />
            <span>ADR #12 Design System Manifest</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            EvolveAgent AI Brand & UI Tokens
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-gray-300 leading-relaxed">
            Standardized color swatches, typography scales, glassmorphism containers, live orchestration patterns, and 10 wireframe layout blueprints.
          </p>
        </div>
      </div>

      {/* 1. Brand Tokens: Color Palette Swatches */}
      <GlassCard>
        <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <Palette className="w-4 h-4 text-cyan-400" />
          <span>1. Brand Color Palette Swatches</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 font-mono text-xs">
          {colorTokens.map((col, idx) => (
            <div key={idx} className="p-4 rounded-2xl bg-black/40 border border-white/10 space-y-3">
              <div className={`h-16 w-full rounded-xl border ${col.border} ${col.tailwind} flex items-center justify-center shadow-lg`}>
                <span className="font-bold text-white drop-shadow">{col.name.split('(')[0]}</span>
              </div>
              <div>
                <div className="font-bold text-white">{col.name}</div>
                <div className="text-gray-400 text-[11px] mt-0.5">Hex / Rule: <span className="text-cyan-300">{col.hex}</span></div>
                <div className="text-gray-500 text-[10px] mt-0.5 truncate">Class: <code>{col.tailwind}</code></div>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* 2. Typography & Corner Radius Scales */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard>
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <Code2 className="w-4 h-4 text-cyan-400" />
            <span>2. Typography Scale & Fonts</span>
          </h3>
          <div className="space-y-4">
            {typographyTokens.map((typ, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
                <div className="flex items-center justify-between text-xs font-mono text-gray-400">
                  <span className="font-bold text-white">{typ.name}</span>
                  <span className="text-cyan-300">{typ.font}</span>
                </div>
                <div className={`${typ.style} pt-1`}>{typ.sample}</div>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard>
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-400" />
            <span>3. Corner Radius & Depth Elevation</span>
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {radiusTokens.map((rad, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col items-center justify-center space-y-2">
                <span className="text-xs font-mono font-bold text-gray-300">{rad.name.split('(')[0]}</span>
                <div className={`w-full border border-white/20 ${rad.style} text-gray-300`}>
                  {rad.name.split('(')[1]?.replace(')', '')} radius
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* 3. Core Component Library Previews */}
      <GlassCard>
        <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span>4. Core Component Library Previews</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Component 1: Status & Risk Badges */}
          <div className="p-4 rounded-2xl bg-black/40 border border-white/10 space-y-3">
            <span className="text-xs font-mono uppercase text-gray-400 block border-b border-white/10 pb-2">Status & Risk Tags</span>
            <div className="flex flex-wrap gap-2">
              <StatusBadge status="active" />
              <StatusBadge status="running" />
              <StatusBadge status="waiting_approval" />
              <StatusBadge status="completed" />
              <StatusBadge status="blocked" />
            </div>
            <div className="flex flex-wrap gap-2 pt-2 border-t border-white/5">
              <RiskBadge level="low" />
              <RiskBadge level="medium" />
              <RiskBadge level="high" />
            </div>
          </div>

          {/* Component 2: Nav Items & Command Input */}
          <div className="p-4 rounded-2xl bg-black/40 border border-white/10 space-y-3">
            <span className="text-xs font-mono uppercase text-gray-400 block border-b border-white/10 pb-2">Command & Nav Elements</span>
            <div className="p-2 rounded-xl bg-gradient-to-r from-cyan-600/20 to-blue-600/10 border border-cyan-500/30 flex items-center justify-between text-xs text-white font-semibold">
              <span className="flex items-center gap-2"><LayoutDashboard className="w-4 h-4 text-cyan-400" /> Active Nav Item</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300">Live</span>
            </div>
            <div className="p-2 rounded-xl bg-white/[0.03] border border-white/10 flex items-center justify-between text-xs text-gray-400">
              <span className="flex items-center gap-2"><Search className="w-4 h-4 text-gray-500" /> Search input trigger</span>
              <kbd className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/10">⌘K</kbd>
            </div>
          </div>

          {/* Component 3: Mini Agent Card */}
          <div className="p-4 rounded-2xl bg-[#1e1e28]/90 border border-cyan-500/40 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-cyan-300">Agent Spotlight Preview</span>
              <StatusBadge status="running" size="sm" />
            </div>
            <div className="flex items-center gap-2 pt-1">
              <span className="text-2xl">🎨</span>
              <div>
                <div className="text-xs font-bold text-white">UI Design Agent</div>
                <div className="text-[10px] font-mono text-cyan-300">Frontend Architect</div>
              </div>
            </div>
            <div className="text-[11px] text-gray-300 font-mono bg-black/30 p-2 rounded-lg border border-white/5">
              Task: Generating responsive grid for Agents Overview
            </div>
          </div>
        </div>
      </GlassCard>

      {/* 4. Live Orchestration Pattern Preview */}
      <GlassCard glow="purple">
        <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
          <Bot className="w-4 h-4 text-cyan-400" />
          <span>5. Live Orchestration Card Pattern ("EvolveAgent is working...")</span>
        </h3>
        <p className="text-xs text-gray-400 mb-4">
          This card embeds directly into Simple Mode Chat whenever an agent initiates a multi-step task delegation. Notice the real-time agent status rows, progress bar, and safety sign-off banner.
        </p>
        <LiveWorkingCard />
      </GlassCard>

      {/* 5. Page Layout Patterns (10 Wireframe Thumbnails) */}
      <GlassCard>
        <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <LayoutDashboard className="w-4 h-4 text-cyan-400" />
          <span>6. Page Layout Patterns & Navigation Blueprints (Click to Jump)</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {layoutThumbnails.map((thm) => {
            const Icon = thm.icon;
            return (
              <div
                key={thm.id}
                onClick={() => { setActivePage(thm.id); showToast(`Jumped to ${thm.label}`, 'info'); }}
                className="cursor-pointer p-4 rounded-2xl bg-white/[0.02] hover:bg-white/[0.08] border border-white/5 hover:border-cyan-500/40 transition-all group flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between pb-2 border-b border-white/10 mb-2">
                    <Icon className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                    <span className="text-[10px] font-mono text-gray-500 group-hover:text-cyan-300 uppercase">Screen</span>
                  </div>
                  <h4 className="text-xs font-bold text-white group-hover:text-cyan-200 transition-colors">{thm.label}</h4>
                  <p className="text-[11px] text-gray-400 mt-1 leading-relaxed">{thm.desc}</p>
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono text-cyan-400 pt-2 border-t border-white/5 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>Open Screen</span>
                  <ArrowRight className="w-3 h-3" />
                </div>
              </div>
            );
          })}
        </div>
      </GlassCard>

      {/* 6. Interaction Rules & Governance Safety Manifesto */}
      <GlassCard glow="blue">
        <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-blue-400" />
          <span>7. Core Interaction Rules & Governance Manifesto</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {interactionRules.map((rule, idx) => (
            <div key={idx} className="p-4 rounded-2xl bg-black/40 border border-blue-500/20 space-y-2">
              <div className="text-xs font-bold font-mono text-blue-300">{rule.title}</div>
              <p className="text-xs text-gray-300 leading-relaxed">{rule.desc}</p>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
};
