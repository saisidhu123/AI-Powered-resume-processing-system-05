import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import StatusBadge from './components/StatusBadge';
import SingleResumeView from './components/SingleResumeView';
import BatchProcessingView from './components/BatchProcessingView';
import { Cpu, ShieldCheck, Database, FileSpreadsheet } from 'lucide-react';

export default function App() {
  const [mode, setMode] = useState('batch'); // 'batch' or 'single'
  const [systemStatus, setSystemStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(false);

  const fetchStatus = async () => {
    setLoadingStatus(true);
    try {
      const res = await axios.get('/api/status');
      setSystemStatus(res.data);
    } catch (err) {
      setSystemStatus({
        is_online: false,
        status_msg: 'Groq Cloud LLM API unreachable',
        target_model: 'groq/compound-mini',
        llm_provider: 'Groq Cloud API'
      });
    } finally {
      setLoadingStatus(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen text-slate-100 flex flex-col">
      {/* Top Navbar & Header */}
      <div className="max-w-7xl w-full mx-auto p-4 md:p-6 space-y-6">
        <Header mode={mode} setMode={setMode} />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
          {/* Sidebar Info & Controls */}
          <div className="space-y-6 lg:col-span-1">
            <StatusBadge
              status={systemStatus}
              loading={loadingStatus}
              onRefresh={fetchStatus}
            />

            {/* System Features Card */}
            <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-4">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-400" /> Key Features
              </h3>
              <ul className="space-y-3 text-xs text-slate-300">
                <li className="flex items-start gap-2">
                  <Database className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                  <span><strong>Parallel Processing:</strong> Batch extract 30+ resumes simultaneously.</span>
                </li>
                <li className="flex items-start gap-2">
                  <Cpu className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>AI Field Mapping:</strong> Dynamic schema extraction via Groq Cloud LLM.</span>
                </li>
                <li className="flex items-start gap-2">
                  <FileSpreadsheet className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <span><strong>Excel Template Sync:</strong> Automatically map fields to custom column headers.</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Main Operating View */}
          <div className="lg:col-span-3">
            {mode === 'single' ? (
              <SingleResumeView systemStatus={systemStatus} />
            ) : (
              <BatchProcessingView systemStatus={systemStatus} />
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-auto py-6 border-t border-slate-900 bg-slate-950/80 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AI-Powered Resume Processing System • React + FastAPI + Groq Cloud LLM</span>
          <span className="font-mono text-[11px] text-slate-600">Cloud-Native Streamlit Deployment</span>
        </div>
      </footer>
    </div>
  );
}
