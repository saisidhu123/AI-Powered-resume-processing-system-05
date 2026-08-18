import React from 'react';

export default function MetricCard({ title, value, icon: Icon, color = 'sky', subtext }) {
  const colorMap = {
    sky: 'from-sky-500/20 to-blue-600/10 text-sky-400 border-sky-500/30',
    emerald: 'from-emerald-500/20 to-teal-600/10 text-emerald-400 border-emerald-500/30',
    amber: 'from-amber-500/20 to-orange-600/10 text-amber-400 border-amber-500/30',
    rose: 'from-rose-500/20 to-red-600/10 text-rose-400 border-rose-500/30',
    indigo: 'from-indigo-500/20 to-purple-600/10 text-indigo-400 border-indigo-500/30',
  };

  const iconBgMap = {
    sky: 'bg-sky-500/10 text-sky-400',
    emerald: 'bg-emerald-500/10 text-emerald-400',
    amber: 'bg-amber-500/10 text-amber-400',
    rose: 'bg-rose-500/10 text-rose-400',
    indigo: 'bg-indigo-500/10 text-indigo-400',
  };

  return (
    <div className={`relative overflow-hidden rounded-2xl p-5 border bg-gradient-to-br glass-card ${colorMap[color]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</span>
        {Icon && (
          <div className={`p-2.5 rounded-xl ${iconBgMap[color]}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-3xl font-extrabold text-white tracking-tight">{value}</span>
      </div>
      {subtext && <p className="mt-1 text-xs text-slate-400">{subtext}</p>}
    </div>
  );
}
