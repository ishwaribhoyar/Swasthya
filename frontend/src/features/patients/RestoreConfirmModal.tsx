import { useState } from 'react';
import { RotateCcw, X } from 'lucide-react';

interface RestoreConfirmModalProps {
  isOpen: boolean;
  patientName: string;
  mrn: string;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export default function RestoreConfirmModal({
  isOpen,
  patientName,
  mrn,
  onClose,
  onConfirm,
}: RestoreConfirmModalProps) {
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    try {
      setLoading(true);
      await onConfirm();
      onClose();
    } catch (err) {
      console.error('Failed to restore patient:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="w-full max-w-md rounded-xl bg-white shadow-xl border border-slate-200 overflow-hidden">
        <div className="flex items-center justify-between border-b px-6 py-4 bg-slate-50">
          <div className="flex items-center gap-2 text-emerald-600">
            <RotateCcw className="h-5 w-5" />
            <h2 className="text-base font-semibold text-slate-900">Restore Patient Record</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <p className="text-sm text-slate-600">
            Restore <strong className="text-slate-900">{patientName}</strong> ({mrn}) to active status?
          </p>
          <p className="text-xs text-slate-500 bg-emerald-50 border border-emerald-200 p-3 rounded-md text-emerald-800">
            The patient will reappear in active searches, timeline, and clinical analytics.
          </p>

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-md transition-colors shadow-sm disabled:opacity-50"
            >
              <RotateCcw className="h-4 w-4" />
              {loading ? 'Restoring...' : 'Restore Patient'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
