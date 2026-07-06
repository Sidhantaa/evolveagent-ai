import React from 'react';
import { useApp } from '../../context/AppContext';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

export const Toast: React.FC = () => {
  const { toast } = useApp();

  if (!toast) return null;

  let bgClass = 'bg-[#1e1e24] border-emerald-500/40 text-emerald-300';
  let Icon = CheckCircle2;

  if (toast.type === 'warning') {
    bgClass = 'bg-[#261d1d] border-rose-500/40 text-rose-300';
    Icon = AlertTriangle;
  } else if (toast.type === 'info') {
    bgClass = 'bg-[#1c1d26] border-purple-500/40 text-purple-300';
    Icon = Info;
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-bounce sm:animate-none flex items-center gap-3 px-4 py-3 rounded-xl border shadow-2xl backdrop-blur-xl font-sans text-xs font-medium max-w-sm" style={{ backgroundColor: 'rgba(23, 23, 23, 0.95)' }}>
      <Icon className={`w-4 h-4 shrink-0 ${toast.type === 'success' ? 'text-emerald-400' : toast.type === 'warning' ? 'text-rose-400' : 'text-purple-400'}`} />
      <span className="text-white flex-1">{toast.message}</span>
    </div>
  );
};
