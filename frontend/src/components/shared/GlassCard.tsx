import React from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  glow?: 'purple' | 'blue' | 'none';
  onClick?: () => void;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  hover = false,
  glow = 'none',
  onClick,
  padding = 'md'
}) => {
  const baseClass = hover ? 'glass-card-hover cursor-pointer' : 'glass-card';
  const glowClass = glow === 'purple' ? 'glow-purple' : glow === 'blue' ? 'glow-blue' : '';
  
  const padClass = 
    padding === 'none' ? 'p-0' :
    padding === 'sm' ? 'p-3 sm:p-4' :
    padding === 'lg' ? 'p-6 sm:p-8' :
    'p-4 sm:p-6'; // md default

  return (
    <div
      onClick={onClick}
      className={`rounded-2xl border border-white/[0.07] bg-[#171717]/80 backdrop-blur-xl shadow-xl transition-all duration-200 ${baseClass} ${glowClass} ${padClass} ${className}`}
    >
      {children}
    </div>
  );
};
