import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, X, AlertCircle } from 'lucide-react';
import { formatFileSize } from '@/utils/formatters';

interface DocumentUploadDropzoneProps {
  onUpload: (files: File[]) => Promise<void>;
  loading: boolean;
}

export default function DocumentUploadDropzone({ onUpload, loading }: DocumentUploadDropzoneProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (incomingFiles: FileList | File[]) => {
    setError(null);
    const newFiles = Array.from(incomingFiles);

    if (selectedFiles.length + newFiles.length > 10) {
      setError('Maximum 10 documents can be uploaded simultaneously per batch.');
      return;
    }

    const validFiles = newFiles.filter((file) => {
      const isPdf = file.type === 'application/pdf' || file.name.endsWith('.pdf');
      const isImage = file.type.startsWith('image/');
      return isPdf || isImage;
    });

    if (validFiles.length < newFiles.length) {
      setError('Some files were skipped. Only PDF documents and Medical Images (PNG, JPG, WEBP) are supported.');
    }

    setSelectedFiles((prev) => [...prev, ...validFiles]);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (selectedFiles.length === 0) return;
    try {
      await onUpload(selectedFiles);
      setSelectedFiles([]);
    } catch (err: any) {
      setError(err?.message || 'Failed to upload documents.');
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900">Upload Medical Documents</h3>
          <p className="text-xs text-slate-500">
            Select up to 10 medical reports, lab results, prescriptions, or clinical PDFs for automatic ingestion.
          </p>
        </div>
        <span className="px-2.5 py-1 text-xs font-semibold bg-primary/10 text-primary rounded-full border border-primary/20">
          Max 10 files
        </span>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-xs text-red-700 border border-red-200">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Drag Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          dragActive
            ? 'border-primary bg-primary/5'
            : 'border-slate-300 hover:border-primary hover:bg-slate-50/50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,image/*"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          className="hidden"
        />
        <div className="flex flex-col items-center gap-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
            <UploadCloud className="h-6 w-6" />
          </div>
          <p className="text-sm font-medium text-slate-800">
            Drag & drop medical documents here, or <span className="text-primary underline">browse files</span>
          </p>
          <p className="text-xs text-slate-400">Supported: Digital PDF, Scanned PDF, JPEG, PNG, WEBP (Up to 25MB each)</p>
        </div>
      </div>

      {/* Selected Files Preview List */}
      {selectedFiles.length > 0 && (
        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Selected Files ({selectedFiles.length}/10)
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1">
            {selectedFiles.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 bg-slate-50 text-xs"
              >
                <div className="flex items-center gap-2 truncate">
                  <FileText className="h-4 w-4 text-primary shrink-0" />
                  <span className="font-medium text-slate-800 truncate">{file.name}</span>
                  <span className="text-slate-400 shrink-0">({formatFileSize(file.size)})</span>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(idx);
                  }}
                  className="text-slate-400 hover:text-red-600 p-1 rounded"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-5 py-2 rounded-lg font-medium text-sm transition-colors shadow-sm disabled:opacity-50"
            >
              <UploadCloud className="h-4 w-4" />
              <span>{loading ? 'Ingesting Pipeline...' : `Upload & Process ${selectedFiles.length} Documents`}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
