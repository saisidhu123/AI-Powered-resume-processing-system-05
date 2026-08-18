import React, { useState } from 'react';
import { Search, CheckCircle2, AlertTriangle, FileSpreadsheet } from 'lucide-react';

export default function ExtractedTable({ fields }) {
  const [search, setSearch] = useState('');

  const filtered = fields.filter(
    (f) =>
      f.column.toLowerCase().includes(search.toLowerCase()) ||
      f.value.toLowerCase().includes(search.toLowerCase())
  );

  const extractedCount = fields.filter((f) => f.status === 'Extracted').length;
  const missingCount = fields.filter((f) => f.status !== 'Extracted').length;

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search column or extracted value..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
          />
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-emerald-400 font-medium bg-emerald-950/40 px-2.5 py-1 rounded-md border border-emerald-900/50">
            <CheckCircle2 className="w-3.5 h-3.5" /> Extracted: {extractedCount}
          </span>
          <span className="flex items-center gap-1.5 text-amber-400 font-medium bg-amber-950/40 px-2.5 py-1 rounded-md border border-amber-900/50">
            <AlertTriangle className="w-3.5 h-3.5" /> Missing: {missingCount}
          </span>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800 max-h-[400px]">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0 border-b border-slate-800 uppercase tracking-wider">
            <tr>
              <th className="py-3 px-4 w-1/3">Template Column Header</th>
              <th className="py-3 px-4">AI Extracted Value</th>
              <th className="py-3 px-4 w-28 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 bg-slate-950/60">
            {filtered.length > 0 ? (
              filtered.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-3 px-4 font-medium text-slate-200 flex items-center gap-2">
                    <FileSpreadsheet className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                    {item.column}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-300">
                    {item.value === '(Blank)' ? (
                      <span className="text-slate-600 italic">(Blank)</span>
                    ) : (
                      item.value
                    )}
                  </td>
                  <td className="py-3 px-4 text-center">
                    {item.status === 'Extracted' ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                        ✅ Extracted
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-950 text-rose-400 border border-rose-800">
                        ⚠️ Missing
                      </span>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={3} className="py-8 text-center text-slate-500">
                  No matching field values found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
