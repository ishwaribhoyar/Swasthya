import { useState } from 'react';
import { Archive, AlertTriangle, X } from 'lucide-react';

interface ArchiveConfirmModalProps {
  isOpen: boolean;
  patientName: string;
  mrn: string;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export default function ArchiveConfirmModal({
  isOpen,
  patientName,
  mrn,
  onClose,
  onConfirm,
}: ArchiveConfirmModalProps) {
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    try {
      setLoading(true);
      await onConfirm();
      onClose();
    } catch (err) {
      console.error('Failed to archive patient:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="w-full max-w-md rounded-xl bg-white shadow-xl border border-slate-200 overflow-hidden">
        <div className="flex items-center justify-between border-b px-6 py-4 bg-slate-50">
          <div className="flex items-center gap-2 text-amber-600">
            <AlertTriangle className="h-5 w-5" />
            <h2 className="text-base font-semibold text-slate-900">Archive Patient Record</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <p className="text-sm text-slate-600">
            Are you sure you want to archive <strong className="text-slate-900">{patientName}</strong> ({mrn})?
          </p>
          <p className="text-xs text-slate-500 bg-amber-50 border border-amber-200 p-3 rounded-md text-amber-800">
            This performs a <strong>soft delete</strong>. Patient records, clinical notes, and medical timeline will be preserved and can be restored at any time.
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
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-md transition-colors shadow-sm disabled:opacity-50"
            >
              <Archive className="h-4 w-4" />
              {loading ? 'Archiving...' : 'Archive Patient'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
