import { useState, useEffect } from 'react';
import { X, CheckCircle2, Clock, Activity, AlertCircle } from 'lucide-react';
import { ingestionApi } from '@/services/api/ingestion';
import { IProcessingLog } from '@/types/ingestion';

interface PipelineTimelineModalProps {
  documentId: string | null;
  filename: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function PipelineTimelineModal({
  documentId,
  filename,
  isOpen,
  onClose,
}: PipelineTimelineModalProps) {
  const [logs, setLogs] = useState<IProcessingLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (documentId && isOpen) {
      setLoading(true);
      ingestionApi
        .getTimeline(documentId)
        .then((res) => {
          if (res.data) setLogs(res.data);
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [documentId, isOpen]);

  if (!isOpen || !documentId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg rounded-xl bg-white shadow-xl border border-slate-200 overflow-hidden">
        <div className="flex items-center justify-between border-b px-6 py-4 bg-slate-50">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            <div>
              <h2 className="text-base font-semibold text-slate-900">Processing Timeline</h2>
              <p className="text-xs text-slate-500 font-mono">{filename}</p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 max-h-[70vh] overflow-y-auto">
          {loading ? (
            <div className="py-8 text-center text-xs text-slate-400">Loading pipeline steps...</div>
          ) : logs.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">No step logs recorded.</div>
          ) : (
            <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {logs.map((log) => (
                <div key={log.id} className="relative flex items-start gap-3 text-xs">
                  <div
                    className={`absolute -left-6 top-0.5 flex h-5 w-5 items-center justify-center rounded-full border bg-white ${
                      log.status === 'completed'
                        ? 'border-emerald-500 text-emerald-600'
                        : log.status === 'failed'
                        ? 'border-red-500 text-red-600'
                        : 'border-blue-500 text-blue-600'
                    }`}
                  >
                    {log.status === 'completed' ? (
                      <CheckCircle2 className="h-3.5 w-3.5" />
                    ) : log.status === 'failed' ? (
                      <AlertCircle className="h-3.5 w-3.5" />
                    ) : (
                      <Clock className="h-3.5 w-3.5" />
                    )}
                  </div>

                  <div className="flex-1 bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <div className="flex items-center justify-between font-medium text-slate-900 mb-1 capitalize">
                      <span>{log.step_name.replace('_', ' ')}</span>
                      {log.duration_ms > 0 && <span className="text-[10px] text-slate-400">{log.duration_ms}ms</span>}
                    </div>
                    <p className="text-slate-600 text-[11px] leading-relaxed">{log.log_message}</p>
                    <span className="text-[9px] text-slate-400 block mt-1">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
