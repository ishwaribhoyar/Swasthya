import { CheckCircle2 } from 'lucide-react';
import { IBatchUploadSummary } from '@/types/ingestion';

interface BatchUploadSummaryBannerProps {
  summary: IBatchUploadSummary | null;
  onClose: () => void;
}

export default function BatchUploadSummaryBanner({ summary, onClose }: BatchUploadSummaryBannerProps) {
  if (!summary) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Batch Processing Completed</h3>
            <p className="text-xs text-slate-500 font-mono">Job ID: {summary.job_id}</p>
          </div>
        </div>

        <button onClick={onClose} className="text-xs text-slate-400 hover:text-slate-600 font-medium">
          Dismiss
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Total Documents</span>
          <span className="text-base font-bold text-slate-800">{summary.total_files}</span>
        </div>

        <div className="bg-emerald-50/60 p-2.5 rounded-lg border border-emerald-100">
          <span className="text-[10px] font-semibold text-emerald-700 uppercase tracking-wider block">Successfully Processed</span>
          <span className="text-base font-bold text-emerald-800">{summary.completed_files}</span>
        </div>

        <div className="bg-amber-50/60 p-2.5 rounded-lg border border-amber-100">
          <span className="text-[10px] font-semibold text-amber-700 uppercase tracking-wider block">Duplicates Skipped</span>
          <span className="text-base font-bold text-amber-800">{summary.duplicate_files}</span>
        </div>

        <div className="bg-blue-50/60 p-2.5 rounded-lg border border-blue-100">
          <span className="text-[10px] font-semibold text-blue-700 uppercase tracking-wider block">Avg Confidence</span>
          <span className="text-base font-bold text-blue-800">{(summary.average_confidence * 100).toFixed(1)}%</span>
        </div>

        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Processing Time</span>
          <span className="text-base font-bold text-slate-800">{(summary.total_processing_time_ms / 1000).toFixed(2)}s</span>
        </div>
      </div>
    </div>
  );
}
