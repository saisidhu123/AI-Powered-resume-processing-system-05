import React, { useState } from 'react';
import axios from 'axios';
import {
  Upload,
  Files,
  FileSpreadsheet,
  Zap,
  Users,
  Copy,
  AlertTriangle,
  Download,
  BarChart3,
  Search,
  Sparkles,
  CheckCircle2,
  Package
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import MetricCard from './MetricCard';

export default function BatchProcessingView({ systemStatus }) {
  const [resumeFiles, setResumeFiles] = useState([]);
  const [templateFile, setTemplateFile] = useState(null);
  const [detectedHeaders, setDetectedHeaders] = useState([]);

  const [processing, setProcessing] = useState(false);
  const [progressPct, setProgressPct] = useState(0);
  const [progressText, setProgressText] = useState('');

  const [batchResult, setBatchResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('master');
  const [tableSearch, setTableSearch] = useState('');

  const handleTemplateChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setTemplateFile(file);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('/api/upload-template', formData);
      setDetectedHeaders(res.data.headers || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to parse template headers.');
    }
  };

  const handleResumeFiles = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      setResumeFiles(files);
      setError(null);
    }
  };

  const handleBatchProcess = async () => {
    if (resumeFiles.length === 0) {
      setError('Please select candidate resume files for batch processing.');
      return;
    }
    if (!templateFile) {
      setError('Please upload an Excel column template file.');
      return;
    }

    setProcessing(true);
    setError(null);
    setBatchResult(null);

    setProgressPct(20);
    setProgressText(`Preparing ${resumeFiles.length} resumes for multi-worker parallel execution...`);

    const formData = new FormData();
    formData.append('template', templateFile);
    resumeFiles.forEach((file) => {
      formData.append('resumes', file);
    });

    try {
      const progressTimer = setInterval(() => {
        setProgressPct((prev) => (prev < 90 ? prev + 15 : prev));
      }, 1200);

      const res = await axios.post('/api/process-batch', formData);

      clearInterval(progressTimer);
      setProgressPct(100);
      setProgressText('Batch processing completed!');

      setTimeout(() => {
        setProcessing(false);
        setBatchResult(res.data);
      }, 500);
    } catch (err) {
      setProcessing(false);
      setError(err.response?.data?.detail || err.message || 'An error occurred during batch processing.');
    }
  };

  // Prepare chart data
  const techChartData = batchResult?.tech_stats
    ? Object.entries(batchResult.tech_stats).map(([domain, count]) => ({ domain, count }))
    : [];

  const expChartData = batchResult?.exp_stats
    ? Object.entries(batchResult.exp_stats).map(([exp, count]) => ({ exp, count }))
    : [];

  const CHART_COLORS = ['#38bdf8', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#f472b6'];

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Bulk Resume Upload */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col gap-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-200">
            <Files className="w-5 h-5 text-sky-400" />
            <span>Bulk Resume Upload (30+ Multi-Files)</span>
          </div>

          <label className="border-2 border-dashed border-slate-700 hover:border-sky-500/50 bg-slate-900/40 hover:bg-slate-900/80 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all group">
            <Upload className="w-8 h-8 text-slate-500 group-hover:text-sky-400 group-hover:scale-110 transition-all mb-2" />
            <span className="text-xs font-semibold text-slate-300">
              {resumeFiles.length > 0
                ? `${resumeFiles.length} Resume Files Selected`
                : 'Choose or Drag & Drop Multiple Resume Files'}
            </span>
            <span className="text-[11px] text-slate-500 mt-1">Select multiple PDF, DOCX, or DOC files</span>
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.doc"
              className="hidden"
              onChange={handleResumeFiles}
            />
          </label>

          {resumeFiles.length > 0 && (
            <div className="flex items-center justify-between text-xs bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-300 font-medium">📁 {resumeFiles.length} candidate files ready</span>
              <span className="text-slate-500">
                {(resumeFiles.reduce((acc, f) => acc + f.size, 0) / 1024 / 1024).toFixed(2)} MB total
              </span>
            </div>
          )}
        </div>

        {/* Excel Template Upload */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col gap-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-200">
            <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
            <span>Excel Master Column Template</span>
          </div>

          <label className="border-2 border-dashed border-slate-700 hover:border-emerald-500/50 bg-slate-900/40 hover:bg-slate-900/80 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all group">
            <Upload className="w-8 h-8 text-slate-500 group-hover:text-emerald-400 group-hover:scale-110 transition-all mb-2" />
            <span className="text-xs font-semibold text-slate-300">
              {templateFile ? templateFile.name : 'Upload Excel Master Template (.xlsx)'}
            </span>
            <span className="text-[11px] text-slate-500 mt-1">Contains column mapping headers</span>
            <input
              type="file"
              accept=".xlsx"
              className="hidden"
              onChange={handleTemplateChange}
            />
          </label>

          {detectedHeaders.length > 0 && (
            <div className="space-y-2">
              <div className="text-[11px] text-slate-400 font-medium">
                Detected <strong className="text-emerald-400">{detectedHeaders.length}</strong> template columns:
              </div>
              <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-1">
                {detectedHeaders.map((h, idx) => (
                  <span
                    key={idx}
                    className="text-[10px] font-semibold bg-slate-900 text-slate-300 border border-slate-700/80 px-2 py-0.5 rounded-full"
                  >
                    📌 {h}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Button & Progress */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <button
          onClick={handleBatchProcess}
          disabled={processing || resumeFiles.length === 0 || !templateFile}
          className="w-full py-3.5 px-6 rounded-xl font-bold text-sm bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white shadow-lg shadow-sky-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
        >
          {processing ? (
            <>
              <Sparkles className="w-5 h-5 animate-spin" />
              <span>Processing Batch Resumes in Parallel...</span>
            </>
          ) : (
            <>
              <Zap className="w-5 h-5" />
              <span>Run Parallel Batch Engine ({resumeFiles.length} Resumes)</span>
            </>
          )}
        </button>

        {processing && (
          <div className="space-y-2 pt-2">
            <div className="flex justify-between text-xs text-slate-400 font-medium">
              <span>{progressText}</span>
              <span>{progressPct}%</span>
            </div>
            <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-sky-500 via-indigo-500 to-emerald-400 transition-all duration-300 rounded-full"
                style={{ width: `${progressPct}%` }}
              ></div>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Batch Results View */}
      {batchResult && (
        <div className="space-y-6 animate-fade-in">
          {/* Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Total Resumes"
              value={batchResult.total_processed}
              icon={Files}
              color="sky"
              subtext={`Processed in ${batchResult.elapsed_seconds}s`}
            />
            <MetricCard
              title="Unique Candidates"
              value={batchResult.unique_count}
              icon={Users}
              color="emerald"
              subtext="Added to master dataset"
            />
            <MetricCard
              title="Duplicates Flagged"
              value={batchResult.duplicate_count}
              icon={Copy}
              color="amber"
              subtext="Isolated in duplicate report"
            />
            <MetricCard
              title="Failed / Errors"
              value={batchResult.failed_count}
              icon={AlertTriangle}
              color="rose"
              subtext="Logged in error log"
            />
          </div>

          {/* Results Center & Tabs */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
            <div className="flex border-b border-slate-800 gap-2 overflow-x-auto">
              <button
                onClick={() => setActiveTab('master')}
                className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 flex items-center gap-2 shrink-0 ${
                  activeTab === 'master'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Users className="w-4 h-4" /> Master Candidate Dataset ({batchResult.unique_count})
              </button>
              <button
                onClick={() => setActiveTab('duplicates')}
                className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 flex items-center gap-2 shrink-0 ${
                  activeTab === 'duplicates'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Copy className="w-4 h-4" /> Flagged Duplicates ({batchResult.duplicate_count})
              </button>
              <button
                onClick={() => setActiveTab('analytics')}
                className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 flex items-center gap-2 shrink-0 ${
                  activeTab === 'analytics'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <BarChart3 className="w-4 h-4" /> Classification Analytics
              </button>
              <button
                onClick={() => setActiveTab('errors')}
                className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 flex items-center gap-2 shrink-0 ${
                  activeTab === 'errors'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <AlertTriangle className="w-4 h-4" /> Error Log ({batchResult.failed_count})
              </button>
            </div>

            {/* TAB 1: MASTER DATASET */}
            {activeTab === 'master' && (
              <div className="space-y-4">
                <div className="relative w-full sm:w-72">
                  <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search candidate name or skill..."
                    value={tableSearch}
                    onChange={(e) => setTableSearch(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div className="overflow-x-auto rounded-xl border border-slate-800 max-h-[420px]">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0 border-b border-slate-800 uppercase tracking-wider">
                      <tr>
                        {batchResult.headers?.slice(0, 7).map((h, i) => (
                          <th key={i} className="py-3 px-4">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/60">
                      {batchResult.unique_candidates?.length > 0 ? (
                        batchResult.unique_candidates
                          .filter((c) =>
                            JSON.stringify(c).toLowerCase().includes(tableSearch.toLowerCase())
                          )
                          .map((cand, idx) => (
                            <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                              {batchResult.headers?.slice(0, 7).map((h, i) => (
                                <td key={i} className="py-2.5 px-4 font-mono text-[11px] text-slate-300">
                                  {cand[h] || '-'}
                                </td>
                              ))}
                            </tr>
                          ))
                      ) : (
                        <tr>
                          <td colSpan={7} className="py-8 text-center text-slate-500">
                            No unique candidates extracted in this batch.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 2: DUPLICATES REPORT */}
            {activeTab === 'duplicates' && (
              <div className="space-y-4">
                <div className="overflow-x-auto rounded-xl border border-slate-800 max-h-[420px]">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0 border-b border-slate-800 uppercase tracking-wider">
                      <tr>
                        <th className="py-3 px-4">Candidate Name</th>
                        <th className="py-3 px-4">Email</th>
                        <th className="py-3 px-4">Phone</th>
                        <th className="py-3 px-4">Duplicate Detection Details</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/60">
                      {batchResult.duplicate_candidates?.length > 0 ? (
                        batchResult.duplicate_candidates.map((dup, idx) => (
                          <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                            <td className="py-2.5 px-4 font-bold text-amber-300">{dup['Candidate Name'] || '-'}</td>
                            <td className="py-2.5 px-4 font-mono">{dup['Email'] || '-'}</td>
                            <td className="py-2.5 px-4 font-mono">{dup['Phone'] || '-'}</td>
                            <td className="py-2.5 px-4 text-slate-400 italic">{dup['Duplicate Match Info'] || 'Matched existing candidate entry'}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={4} className="py-8 text-center text-emerald-400 font-medium">
                            <CheckCircle2 className="w-5 h-5 mx-auto mb-1 text-emerald-400" />
                            No duplicate candidates detected in this batch!
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 3: CLASSIFICATION ANALYTICS */}
            {activeTab === 'analytics' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
                {/* Tech domain chart */}
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Candidates by Tech Domain
                  </h4>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={techChartData}>
                        <XAxis dataKey="domain" stroke="#64748b" fontSize={11} />
                        <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                        <Tooltip
                          contentStyle={{ background: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                        />
                        <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                          {techChartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Experience chart */}
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Candidates by Experience Category
                  </h4>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={expChartData}>
                        <XAxis dataKey="exp" stroke="#64748b" fontSize={11} />
                        <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                        <Tooltip
                          contentStyle={{ background: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                        />
                        <Bar dataKey="count" fill="#38bdf8" radius={[6, 6, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: ERROR LOG */}
            {activeTab === 'errors' && (
              <div className="space-y-4">
                {batchResult.failed_resumes?.length > 0 ? (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-rose-400">Failed Resumes ({batchResult.failed_resumes.length})</h4>
                    <div className="overflow-x-auto rounded-xl border border-slate-800">
                      <table className="w-full text-left text-xs text-slate-300">
                        <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
                          <tr>
                            <th className="py-2.5 px-4">Filename</th>
                            <th className="py-2.5 px-4">Error Details</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 bg-slate-950">
                          {batchResult.failed_resumes.map((f, i) => (
                            <tr key={i}>
                              <td className="py-2 px-4 font-mono text-rose-300">{f.filename || f.file}</td>
                              <td className="py-2 px-4 text-slate-400">{f.error}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>All resumes processed cleanly without fatal parsing errors!</span>
                  </div>
                )}
              </div>
            )}

            {/* Reports & Download Center */}
            <div className="pt-6 border-t border-slate-800 space-y-3">
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Download className="w-4 h-4 text-sky-400" /> Generated Reports & Export Center
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                <a
                  href={batchResult.downloads.master_excel}
                  download
                  className="p-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-200 transition-colors flex items-center gap-2 justify-center"
                >
                  <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                  <span>Master Candidates</span>
                </a>

                <a
                  href={batchResult.downloads.duplicate_report}
                  download
                  className="p-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-200 transition-colors flex items-center gap-2 justify-center"
                >
                  <Copy className="w-4 h-4 text-amber-400" />
                  <span>Duplicate Report</span>
                </a>

                <a
                  href={batchResult.downloads.error_log}
                  download
                  className="p-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-200 transition-colors flex items-center gap-2 justify-center"
                >
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  <span>Error Log</span>
                </a>

                <a
                  href={batchResult.downloads.classification_analytics}
                  download
                  className="p-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-200 transition-colors flex items-center gap-2 justify-center"
                >
                  <BarChart3 className="w-4 h-4 text-sky-400" />
                  <span>Analytics Excel</span>
                </a>

                <a
                  href={batchResult.downloads.zip_package}
                  download
                  className="p-3 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-bold transition-all shadow-lg shadow-sky-500/20 flex items-center gap-2 justify-center col-span-1 sm:col-span-2 md:col-span-1"
                >
                  <Package className="w-4 h-4" />
                  <span>Complete ZIP Bundle</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
