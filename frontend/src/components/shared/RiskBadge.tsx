import React from 'react';
import { RiskLevel } from '../../types';
import { ShieldAlert, ShieldCheck, Shield } from 'lucide-react';

interface RiskBadgeProps {
  level: RiskLevel;
  size?: 'sm' | 'md';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, size = 'md' }) => {
  let bgClass = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
  let Icon = ShieldCheck;
  let label = 'Low Risk';

  if (level === 'medium') {
    bgClass = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
    Icon = Shield;
    label = 'Medium Risk';
  } else if (level === 'high') {
    bgClass = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
    Icon = ShieldAlert;
    label = 'High Risk';
  }

  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-mono font-medium border ${bgClass} ${sizeClass}`}>
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>{label}</span>
    </span>
  );
};
