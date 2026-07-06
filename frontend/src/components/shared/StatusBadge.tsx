import React from 'react';
import { Activity, PlayCircle, Clock, AlertTriangle, CheckCircle2, ShieldAlert } from 'lucide-react';

export type BadgeStatus = 
  | 'active' 
  | 'idle' 
  | 'running' 
  | 'waiting' 
  | 'waiting_approval' 
  | 'blocked' 
  | 'completed' 
  | 'in_progress'
  | 'pending'
  | 'connected'
  | 'disconnected'
  | 'approval-gated'
  | 'error'
  | 'allowed'
  | 'mock_executed';

interface StatusBadgeProps {
  status: BadgeStatus | string;
  size?: 'sm' | 'md';
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true
}) => {
  const normalized = status.toLowerCase().replace('_', ' ');
  
  let bgClass = 'bg-gray-500/15 text-gray-300 border-gray-500/20';
  let dotClass = 'bg-gray-400';
  let Icon = Clock;

  if (['active', 'completed', 'connected', 'allowed', 'mock executed'].includes(normalized)) {
    bgClass = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
    dotClass = 'bg-emerald-400 animate-pulse';
    Icon = CheckCircle2;
  } else if (['running', 'in progress'].includes(normalized)) {
    bgClass = 'bg-purple-500/15 text-purple-300 border-purple-500/30';
    dotClass = 'bg-purple-400 animate-pulse';
    Icon = PlayCircle;
  } else if (['waiting approval', 'waiting', 'pending', 'approval-gated', 'pending review'].includes(normalized)) {
    bgClass = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
    dotClass = 'bg-amber-400';
    Icon = Clock;
  } else if (['blocked', 'error', 'disconnected', 'rejected'].includes(normalized)) {
    bgClass = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
    dotClass = 'bg-rose-400';
    Icon = ShieldAlert;
  } else if (['idle'].includes(normalized)) {
    bgClass = 'bg-blue-500/15 text-blue-300 border-blue-500/30';
    dotClass = 'bg-blue-400';
    Icon = Activity;
  }

  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-mono font-medium border ${bgClass} ${sizeClass}`}>
      {showIcon ? (
        <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      ) : (
        <span className={`w-1.5 h-1.5 rounded-full ${dotClass}`} />
      )}
      <span className="capitalize">{normalized}</span>
    </span>
  );
};
