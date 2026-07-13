import React from 'react';
import { GlassCard } from './GlassCard';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  trend?: string;
  isPositive?: boolean;
  subtitle?: string;
  icon?: React.ReactNode;
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  trend,
  isPositive = true,
  subtitle,
  icon,
  onClick
}) => {
  return (
    <GlassCard hover={!!onClick} onClick={onClick} padding="sm" className="flex flex-col justify-between">
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-medium text-gray-400">{label}</span>
        {icon && (
          <div className="p-1.5 rounded-lg bg-white/[0.04] text-cyan-400 border border-white/5">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-2 flex items-baseline justify-between gap-2">
        <span className="text-2xl sm:text-3xl font-bold font-mono tracking-tight text-white">{value}</span>
        {trend && (
          <span
            className={`inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-full border ${
              isPositive
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            }`}
          >
            {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {trend}
          </span>
        )}
      </div>

      {subtitle && <div className="mt-1.5 text-[11px] text-gray-500 truncate">{subtitle}</div>}
    </GlassCard>
  );
};
