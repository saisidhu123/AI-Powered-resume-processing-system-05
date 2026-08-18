import React from 'react';
import { Layers, Zap, FileText } from 'lucide-react';

export default function Header({ mode, setMode }) {
  return (
    <header className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 shadow-lg shadow-sky-500/20">
              <Layers className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-black text-white tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                AI Resume Processing System
              </h1>
              <p className="text-xs text-slate-400 font-medium mt-0.5">
                Automated Candidate Screening, Parallel Bulk Engine & Dynamic Excel Export (100% Offline)
              </p>
            </div>
          </div>
        </div>

        {/* Mode Switcher */}
        <div className="flex bg-slate-900/90 p-1.5 rounded-xl border border-slate-800 self-start md:self-auto">
          <button
            onClick={() => setMode('batch')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              mode === 'batch'
                ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Zap className="w-4 h-4" />
            <span>⚡ Bulk Batch Processing (30+)</span>
          </button>
          <button
            onClick={() => setMode('single')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              mode === 'single'
                ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>🚀 Single Resume Mode</span>
          </button>
        </div>
      </div>
    </header>
  );
}
