import React from 'react';
import { Activity, Server, RefreshCw, Cpu } from 'lucide-react';

export default function StatusBadge({ status, loading, onRefresh }) {
  const isOnline = status?.is_online;

  return (
    <div className="glass-card rounded-2xl p-4 border border-slate-800 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-sky-400" />
          <span className="font-semibold text-sm text-slate-200">AI Engine Status</span>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
          title="Refresh Ollama status"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-sky-400' : ''}`} />
        </button>
      </div>

      <div className="flex items-center justify-between bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-3 w-3">
            {isOnline && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
            <span className={`relative inline-flex rounded-full h-3 w-3 ${isOnline ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
          </span>
          <span className={`text-xs font-semibold ${isOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isOnline ? status.status_msg : (status?.status_msg || 'Ollama Offline')}
          </span>
        </div>
      </div>

      <div className="space-y-1.5 text-xs text-slate-400 pt-1">
        <div className="flex items-center justify-between">
          <span className="text-slate-500 flex items-center gap-1">
            <Cpu className="w-3.5 h-3.5" /> Model:
          </span>
          <span className="font-mono text-slate-300 font-medium bg-slate-800/80 px-2 py-0.5 rounded text-[11px]">
            {status?.target_model || 'llama3.2:3b'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">Local URL:</span>
          <span className="font-mono text-slate-400 text-[11px] truncate max-w-[160px]">
            {status?.ollama_url || 'http://localhost:11434'}
          </span>
        </div>
      </div>
    </div>
  );
}
