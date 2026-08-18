import React, { useState } from 'react';
import { X, Activity, FileText, Code2, Copy, Check } from 'lucide-react';

export default function DiagnosticsModal({ diagnostics, onClose }) {
  const [copiedClean, setCopiedClean] = useState(false);
  const [copiedRaw, setCopiedRaw] = useState(false);

  if (!diagnostics) return null;

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    if (type === 'clean') {
      setCopiedClean(true);
      setTimeout(() => setCopiedClean(false), 2000);
    } else {
      setCopiedRaw(true);
      setTimeout(() => setCopiedRaw(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="glass-panel w-full max-w-4xl max-h-[85vh] rounded-2xl border border-slate-700 flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/80">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-sky-400" />
            <h3 className="text-base font-bold text-white">Pipeline Extraction Debug & Diagnostics</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-slate-300">
          {/* Confidence Scores */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-slate-400 font-medium mb-1">Experience Confidence Rating</div>
              <div className="text-2xl font-bold text-sky-400">{diagnostics.exp_confidence}%</div>
              <div className="mt-2 text-slate-400 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                <span className="font-semibold text-slate-300">Calculation Log:</span> {diagnostics.exp_notes}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-slate-400 font-medium mb-1">Skills Extraction Confidence</div>
              <div className="text-2xl font-bold text-emerald-400">{diagnostics.skills_confidence}%</div>
              <div className="mt-2 text-slate-400 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                High accuracy regex matching + LLM semantic verification applied.
              </div>
            </div>
          </div>

          {/* Cleaned Text */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                <Code2 className="w-4 h-4 text-cyan-400" /> Reconstructed & Cleaned Resume Text
              </span>
              <button
                onClick={() => copyToClipboard(diagnostics.cleaned_text, 'clean')}
                className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-sky-400 bg-slate-900 px-2 py-1 rounded border border-slate-800"
              >
                {copiedClean ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedClean ? 'Copied' : 'Copy Text'}
              </button>
            </div>
            <textarea
              readOnly
              value={diagnostics.cleaned_text || ''}
              className="w-full h-40 bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-[11px] text-slate-300 focus:outline-none"
            />
          </div>

          {/* Raw Text */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-amber-400" /> Raw Extracted Resume Text (Unprocessed)
              </span>
              <button
                onClick={() => copyToClipboard(diagnostics.raw_text, 'raw')}
                className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-sky-400 bg-slate-900 px-2 py-1 rounded border border-slate-800"
              >
                {copiedRaw ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedRaw ? 'Copied' : 'Copy Text'}
              </button>
            </div>
            <textarea
              readOnly
              value={diagnostics.raw_text || ''}
              className="w-full h-40 bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-[11px] text-slate-400 focus:outline-none"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/60 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs transition-colors"
          >
            Close Diagnostics
          </button>
        </div>
      </div>
    </div>
  );
}
