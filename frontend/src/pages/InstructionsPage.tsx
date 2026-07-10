import React, { useState } from 'react';
import { GlassCard } from '../components/shared/GlassCard';
import { PageId } from '../types';
import { useApp } from '../context/AppContext';
import {
  BookOpen,
  MessageSquare,
  Terminal,
  ShieldCheck,
  Compass,
  Users,
  Brain,
  Wrench,
  Shield,
  Settings,
  LayoutDashboard,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Lock,
  Eye,
  Zap,
  ChevronDown
} from 'lucide-react';

const sidebarGuide: { id: PageId; icon: React.ElementType; label: string; desc: string }[] = [
  { id: 'home', icon: LayoutDashboard, label: 'Home Dashboard', desc: 'Your command center — quick actions, live stats, and what needs your attention right now.' },
  { id: 'chat', icon: MessageSquare, label: 'Simple Mode Chat', desc: 'Just type what you want and the AI routes it to the right specialist agent. This is where most work happens.' },
  { id: 'dev-console', icon: Terminal, label: 'Dev Mode Console', desc: 'The "under the hood" view — see exactly which agents ran, what they decided, and why.' },
  { id: 'mission-control', icon: Compass, label: 'Mission Control', desc: 'For bigger, multi-step goals. Break a big ask into tracked phases and tasks instead of one chat message.' },
  { id: 'agents', icon: Users, label: 'Agents', desc: 'See every specialist agent, what it is trusted to do, and how it is performing.' },
  { id: 'approvals', icon: ShieldCheck, label: 'Approvals', desc: 'Anything risky (editing files, running commands) waits here for a human yes/no before it happens.' },
  { id: 'project-brain', icon: Brain, label: 'Project Brain', desc: 'The AI\'s long-term memory for this project — search past decisions, facts, and context.' },
  { id: 'tools', icon: Wrench, label: 'Tools / MCP Hub', desc: 'Connected tools and integrations the agents are allowed to use, and under what conditions.' },
  { id: 'governance', icon: Shield, label: 'Governance', desc: 'The safety rulebook — what is blocked, what needs approval, and the audit trail of every decision.' },
  { id: 'settings', icon: Settings, label: 'Settings', desc: 'Model routing, safety defaults, and appearance preferences for your workspace.' },
];

const faqs = [
  {
    q: 'Is the AI allowed to just do things on its own?',
    a: 'Low-risk, read-only actions can run automatically. Anything with real-world consequences — editing a file, running a command, calling an external tool — is held in the Approvals queue until a person says yes. Nothing risky happens silently.'
  },
  {
    q: 'What is the difference between Mock-Safe and Real Actions mode?',
    a: 'Mock-Safe simulates actions so you can see what the AI would do without anything actually happening — great for testing and demos. Real Actions mode lets safe, non-risky actions actually execute, while risky ones are still always approval-gated.'
  },
  {
    q: 'What if the AI gets something wrong?',
    a: 'Every action is logged in Governance, and anything pending is reversible from the Approvals queue by rejecting it. You are always the last checkpoint before something risky happens.'
  },
  {
    q: 'Do I need to use Dev Mode?',
    a: 'No — Simple Mode Chat is enough for everyday use. Dev Mode is there for when you want to understand exactly how a decision was made, or you are debugging something that did not go as expected.'
  }
];

export const InstructionsPage: React.FC = () => {
  const { setActivePage } = useApp();
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  return (
    <div className="space-y-8 animate-fadeIn pb-16">
      {/* Header Banner */}
      <div className="rounded-3xl border border-purple-500/40 bg-gradient-to-br from-[#1c1a29] via-[#14141c] to-[#121217] p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-purple-600/20 rounded-full blur-3xl" />
        <div className="relative">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/15 border border-purple-500/30 text-purple-300 text-xs font-mono mb-4">
            <BookOpen className="w-3.5 h-3.5" />
            Start Here
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight text-white mb-2">
            Welcome to EvolveAgent AI
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed max-w-2xl">
            This is a local-first AI operating system: instead of one chatbot, a team of specialist
            agents work together on your requests. The whole system is built so nothing risky happens
            without your sign-off — you are always in control.
          </p>
        </div>
      </div>

      {/* Quick Start Steps */}
      <div>
        <h2 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-purple-400" /> Quick Start
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { step: '1', title: 'Say what you need', desc: 'Go to Simple Mode Chat and type your request in plain language, like you would text a friend.', page: 'chat' as PageId },
            { step: '2', title: 'Review anything risky', desc: 'If the AI wants to do something with real consequences, it will wait in Approvals for your go-ahead.', page: 'approvals' as PageId },
            { step: '3', title: 'Go deeper if curious', desc: 'Want to see exactly how a decision was made? Dev Mode Console shows the full step-by-step trace.', page: 'dev-console' as PageId },
          ].map((s) => (
            <GlassCard key={s.step} hover onClick={() => setActivePage(s.page)} className="group">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-600 to-blue-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
                  {s.step}
                </div>
                <h3 className="text-sm font-semibold text-white">{s.title}</h3>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed mb-3">{s.desc}</p>
              <span className="inline-flex items-center gap-1 text-[11px] font-mono text-purple-400 group-hover:gap-2 transition-all">
                Go there <ArrowRight className="w-3 h-3" />
              </span>
            </GlassCard>
          ))}
        </div>
      </div>

      {/* Simple Mode vs Dev Mode */}
      <div>
        <h2 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-400" /> Two Ways to Work
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <GlassCard glow="purple">
            <div className="flex items-center gap-2 mb-2">
              <MessageSquare className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-semibold text-white">Simple Mode</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                Everyday use
              </span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              A clean chat interface. You type a request, the AI figures out which specialist agents
              to use, and you get one clear answer back. No clutter, no internals — just the result.
            </p>
          </GlassCard>
          <GlassCard>
            <div className="flex items-center gap-2 mb-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-white">Dev Mode</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Power users
              </span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              The same requests, but with the curtain pulled back: which agents ran, what each one
              decided, timing, and raw output. Useful for debugging or just understanding the "why."
            </p>
          </GlassCard>
        </div>
      </div>

      {/* Trust & Safety */}
      <div>
        <h2 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <Lock className="w-4 h-4 text-purple-400" /> How Safety Works Here
        </h2>
        <GlassCard>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <div className="flex gap-3">
              <Eye className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-white mb-1">Everything is visible</h4>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  Every action agents take is written to Governance. Nothing happens off the record.
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <ShieldCheck className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-white mb-1">Risky things wait for you</h4>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  File edits, commands, and tool calls with real consequences sit in Approvals until
                  you say yes.
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-white mb-1">You can always say no</h4>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  Rejecting an approval blocks the action and logs why — nothing is forced through.
                </p>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Sidebar Guide */}
      <div>
        <h2 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <Compass className="w-4 h-4 text-purple-400" /> What's in the Sidebar
        </h2>
        <GlassCard padding="none">
          <div className="divide-y divide-white/[0.06]">
            {sidebarGuide.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActivePage(item.id)}
                  className="w-full flex items-start gap-3 p-4 text-left hover:bg-white/[0.03] transition-colors group"
                >
                  <div className="w-8 h-8 rounded-lg bg-white/[0.05] border border-white/10 flex items-center justify-center shrink-0 group-hover:border-purple-500/30">
                    <Icon className="w-4 h-4 text-gray-400 group-hover:text-purple-400" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h4 className="text-xs font-semibold text-white mb-0.5">{item.label}</h4>
                    <p className="text-[11px] text-gray-400 leading-relaxed">{item.desc}</p>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-gray-600 group-hover:text-purple-400 shrink-0 mt-1 transition-colors" />
                </button>
              );
            })}
          </div>
        </GlassCard>
      </div>

      {/* FAQ */}
      <div>
        <h2 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-purple-400" /> Common Questions
        </h2>
        <div className="space-y-2">
          {faqs.map((f, i) => (
            <GlassCard key={i} padding="none" className="overflow-hidden">
              <button
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                className="w-full flex items-center justify-between gap-3 p-4 text-left"
              >
                <span className="text-xs font-semibold text-white">{f.q}</span>
                <ChevronDown className={`w-4 h-4 text-gray-500 shrink-0 transition-transform ${openFaq === i ? 'rotate-180' : ''}`} />
              </button>
              {openFaq === i && (
                <div className="px-4 pb-4 -mt-1">
                  <p className="text-[11px] text-gray-400 leading-relaxed">{f.a}</p>
                </div>
              )}
            </GlassCard>
          ))}
        </div>
      </div>
    </div>
  );
};
