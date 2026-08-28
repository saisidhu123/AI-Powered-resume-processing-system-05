import React, { useState } from 'react';
import axios from 'axios';
import {
  Upload,
  FileText,
  FileSpreadsheet,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Download,
  Bot,
  Activity,
  Tag,
  Clock,
  Sparkles
} from 'lucide-react';
import ExtractedTable from './ExtractedTable';
import DiagnosticsModal from './DiagnosticsModal';

export default function SingleResumeView({ systemStatus }) {
  const [resumeFile, setResumeFile] = useState(null);
  const [templateFile, setTemplateFile] = useState(null);
  const [detectedHeaders, setDetectedHeaders] = useState([]);
  
  const [processing, setProcessing] = useState(false);
  const [progressStep, setProgressStep] = useState('');
  const [progressPct, setProgressPct] = useState(0);

  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('data');
  const [showDiagnostics, setShowDiagnostics] = useState(false);

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

  const handleProcess = async () => {
    if (!resumeFile) {
      setError('Please upload a candidate resume file.');
      return;
    }
    if (!templateFile) {
      setError('Please upload an Excel column template file.');
      return;
    }
    if (!systemStatus?.is_online) {
      setError(`Groq LLM offline: ${systemStatus?.status_msg || 'Cannot connect'}`);
      return;
    }

    setProcessing(true);
    setError(null);
    setResult(null);

    setProgressPct(20);
    setProgressStep('Step 1/4: Extracting text from resume...');

    const formData = new FormData();
    formData.append('resume', resumeFile);
    formData.append('template', templateFile);

    try {
      setTimeout(() => {
        setProgressPct(50);
        setProgressStep('Step 2/4: AI Semantic Field Extraction via Groq Cloud LLM...');
      }, 800);

      setTimeout(() => {
        setProgressPct(80);
        setProgressStep('Step 3/4: Duplicate Check & Excel Sheet Population...');
      }, 2500);

      const res = await axios.post('/api/process-single', formData);

      setProgressPct(100);
      setProgressStep('Step 4/4: Complete!');
      setTimeout(() => {
        setProcessing(false);
        setResult(res.data);
      }, 400);
    } catch (err) {
      setProcessing(false);
      setError(err.response?.data?.detail || err.message || 'An error occurred during resume processing.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Resume File Upload */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col gap-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-200">
            <FileText className="w-5 h-5 text-sky-400" />
            <span>Candidate Resume Upload</span>
          </div>

          <label className="border-2 border-dashed border-slate-700 hover:border-sky-500/50 bg-slate-900/40 hover:bg-slate-900/80 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all group">
            <Upload className="w-8 h-8 text-slate-500 group-hover:text-sky-400 group-hover:scale-110 transition-all mb-2" />
            <span className="text-xs font-semibold text-slate-300">
              {resumeFile ? resumeFile.name : 'Choose or Drag & Drop Resume File'}
            </span>
            <span className="text-[11px] text-slate-500 mt-1">Supports PDF, DOCX, DOC files</span>
            <input
              type="file"
              accept=".pdf,.docx,.doc"
              className="hidden"
              onChange={(e) => {
                setResumeFile(e.target.files[0]);
                setError(null);
              }}
            />
          </label>

          {resumeFile && (
            <div className="flex items-center justify-between text-xs bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-300 font-medium truncate max-w-[240px]">📄 {resumeFile.name}</span>
              <span className="text-slate-500">{(resumeFile.size / 1024).toFixed(1)} KB</span>
            </div>
          )}
        </div>

        {/* Excel Template Upload */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col gap-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-200">
            <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
            <span>Excel Column Template Upload</span>
          </div>

          <label className="border-2 border-dashed border-slate-700 hover:border-emerald-500/50 bg-slate-900/40 hover:bg-slate-900/80 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all group">
            <Upload className="w-8 h-8 text-slate-500 group-hover:text-emerald-400 group-hover:scale-110 transition-all mb-2" />
            <span className="text-xs font-semibold text-slate-300">
              {templateFile ? templateFile.name : 'Choose Excel Template (.xlsx)'}
            </span>
            <span className="text-[11px] text-slate-500 mt-1">Contains column headers in Row 1</span>
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

      {/* Process Action & Progress */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <button
          onClick={handleProcess}
          disabled={processing || !resumeFile || !templateFile}
          className="w-full py-3.5 px-6 rounded-xl font-bold text-sm bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white shadow-lg shadow-sky-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
        >
          {processing ? (
            <>
              <Sparkles className="w-5 h-5 animate-spin" />
              <span>Processing Resume with AI...</span>
            </>
          ) : (
            <>
              <Zap className="w-5 h-5" />
              <span>Process Resume & Populate Excel</span>
            </>
          )}
        </button>

        {processing && (
          <div className="space-y-2 pt-2">
            <div className="flex justify-between text-xs text-slate-400 font-medium">
              <span>{progressStep}</span>
              <span>{progressPct}%</span>
            </div>
            <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-sky-500 to-blue-400 transition-all duration-300 rounded-full"
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

      {/* Results View */}
      {result && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6 animate-fade-in">
          {/* Header Summary */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-extrabold text-white">{result.candidate_name}</h3>
                <span className="bg-sky-500/10 text-sky-400 border border-sky-500/20 px-2.5 py-0.5 rounded-full text-xs font-semibold">
                  Extracted
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">Single resume successfully parsed and populated.</p>
            </div>

            {/* Quick Metadata Badges */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1.5 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-xl text-xs">
                <Tag className="w-3.5 h-3.5 text-sky-400" />
                <span className="text-slate-400">Tech:</span>
                <span className="font-semibold text-slate-200">
                  {(result.tech_domains || []).join(', ')}
                </span>
              </div>

              <div className="flex items-center gap-1.5 bg-amber-950/40 border border-amber-800/60 px-3 py-1.5 rounded-xl text-xs text-amber-300">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                <span className="font-bold">{result.exp_bucket}</span>
              </div>

              <button
                onClick={() => setShowDiagnostics(true)}
                className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors"
              >
                <Activity className="w-3.5 h-3.5 text-cyan-400" />
                <span>Diagnostics</span>
              </button>
            </div>
          </div>

          {/* Duplicate Alert */}
          {result.is_duplicate && (
            <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-800 text-amber-300 text-xs flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block mb-0.5">Duplicate Candidate Detected!</span>
                {result.duplicate_warning}
              </div>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 gap-2">
            <button
              onClick={() => setActiveTab('data')}
              className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${
                activeTab === 'data'
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileSpreadsheet className="w-4 h-4" /> Extracted Field Matrix
            </button>
            <button
              onClick={() => setActiveTab('screening')}
              className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${
                activeTab === 'screening'
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Bot className="w-4 h-4" /> AI Candidate Screening Q&A
            </button>
            <button
              onClick={() => setActiveTab('missing')}
              className={`pb-3 px-4 text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${
                activeTab === 'missing'
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <AlertTriangle className="w-4 h-4" /> Missing Fields Log ({result.missing_fields?.length || 0})
            </button>
          </div>

          {/* Tab Content */}
          <div className="pt-2">
            {activeTab === 'data' && (
              <ExtractedTable fields={result.extracted_fields || []} />
            )}

            {activeTab === 'screening' && (
              <div className="space-y-4 text-xs text-slate-300 bg-slate-900/60 p-5 rounded-xl border border-slate-800">
                <div>
                  <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px] block mb-1">
                    AI Screening Executive Summary
                  </span>
                  <p className="text-sm font-medium text-slate-200 leading-relaxed">
                    {result.ai_screening?.summary || 'N/A'}
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                    <span className="text-slate-400 block mb-1">Oracle Experience:</span>
                    <span className="font-bold text-sky-400 text-sm">{result.ai_screening?.oracle_exp}</span>
                  </div>
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                    <span className="text-slate-400 block mb-1">Suitable Technical Roles:</span>
                    <span className="font-bold text-emerald-400 text-sm">{result.ai_screening?.suitable_roles}</span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'missing' && (
              <div>
                {result.missing_fields && result.missing_fields.length > 0 ? (
                  <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-900 text-rose-300 text-xs space-y-2">
                    <span className="font-bold block">
                      The following {result.missing_fields.length} requested fields were missing or blank in the resume:
                    </span>
                    <div className="flex flex-wrap gap-2 pt-1">
                      {result.missing_fields.map((mf, idx) => (
                        <span key={idx} className="bg-rose-900/60 text-rose-200 border border-rose-700 px-2.5 py-1 rounded font-mono">
                          `{mf}`
                        </span>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>All requested Excel template fields were successfully extracted without missing items!</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Download Button */}
          <div className="pt-4 border-t border-slate-800">
            <a
              href={result.download_url}
              download={result.output_filename}
              className="w-full py-3 px-6 rounded-xl font-bold text-xs bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 transition-all flex items-center justify-center gap-2"
            >
              <Download className="w-4 h-4" />
              <span>Download Populated Excel ({result.output_filename})</span>
            </a>
          </div>
        </div>
      )}

      {/* Diagnostics Modal */}
      {showDiagnostics && result && (
        <DiagnosticsModal
          diagnostics={result.diagnostics}
          onClose={() => setShowDiagnostics(false)}
        />
      )}
    </div>
  );
}
