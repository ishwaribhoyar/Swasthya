/**
 * SourceEvidenceDrawer
 *
 * Production-grade clinical evidence provenance viewer.
 *
 * What it does:
 *  1. Fetches document provenance metadata (IDocumentProvenance)
 *  2. Fetches the actual original file bytes as a Blob URL
 *  3. Renders the file correctly based on MIME type:
 *     - PDF     → <object> / <embed> with Blob URL
 *     - Image   → <img> with zoom, rotate, reset controls
 *     - Text    → <pre> with original content from extracted_text
 *     - Unknown → download link
 *  4. Three tabs: Original | Extracted Data | Evidence Chain
 *  5. Provenance header: filename, type, date, extraction engine, confidence
 *  6. Evidence chain: timeline event count, lab result count, param history count
 *  7. "Open Original" + "Download" buttons
 *
 * Security:
 *  - File served via authenticated axios call (bearer token forwarded)
 *  - Blob URL created client-side — never exposes storage path
 *  - "Missing" state shown cleanly if file unavailable
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  X,
  FileText,
  FlaskConical,
  Pill,
  HeartPulse,
  Stethoscope,
  AlertTriangle,
  Download,
  ExternalLink,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Maximize2,
  Minimize2,
  RefreshCw,
  CheckCircle,
  Shield,
  BarChart3,
  Activity,
  FileX,
  Copy,
} from 'lucide-react';
import { ingestionApi } from '@/services/api/ingestion';
import { IDocumentProvenance, IDocument } from '@/types/ingestion';

interface SourceEvidenceDrawerProps {
  documentId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

type ViewTab = 'original' | 'extracted' | 'evidence';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
    }) + ', ' + d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  } catch { return iso; }
}

function getParseSourceLabel(source: string | null | undefined): string {
  switch (source) {
    case 'sarvam_parse': return 'Sarvam Parse (PDF Extraction)';
    case 'sarvam_vision': return 'Sarvam Vision OCR (AI Image Analysis)';
    case 'pymupdf_fallback': return 'PyMuPDF (Fallback PDF Parser)';
    case 'direct_text': return 'Direct Text Entry';
    default: return source || 'Automated AI Extraction';
  }
}

function getCategoryIcon(cat: string) {
  switch (cat) {
    case 'lab': return FlaskConical;
    case 'prescription': return Pill;
    case 'vitals': return HeartPulse;
    default: return Stethoscope;
  }
}

function isImageMime(mime: string): boolean {
  return mime.startsWith('image/');
}

function isPdfMime(mime: string): boolean {
  return mime === 'application/pdf';
}

function isTextMime(mime: string, fileType: string): boolean {
  return mime.startsWith('text/') || fileType === 'txt';
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function ProvenanceHeader({ p }: { p: IDocumentProvenance }) {
  const CatIcon = getCategoryIcon(p.doc_category);
  const confPct = Math.round(p.confidence_score * 100);

  return (
    <div className="px-6 py-5 border-b border-slate-200 bg-gradient-to-r from-slate-50 to-white">
      <div className="flex items-start gap-4">
        {/* Category icon */}
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 shrink-0">
          <CatIcon className="h-6 w-6 text-primary" />
        </div>

        {/* File identity */}
        <div className="flex-1 min-w-0">
          <h2 className="text-base font-bold text-slate-900 truncate" title={p.original_filename}>
            {p.original_filename}
          </h2>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-xs text-slate-500">
            <span className="font-bold uppercase tracking-wide text-slate-700">
              {p.file_type.toUpperCase()}
            </span>
            <span>·</span>
            <span>{formatBytes(p.file_size_bytes)}</span>
            <span>·</span>
            <span className="font-semibold text-slate-700 uppercase">{p.doc_category}</span>
            {p.document_date && (
              <>
                <span>·</span>
                <span>{formatDate(p.document_date)}</span>
              </>
            )}
          </div>
        </div>

        {/* Confidence badge */}
        <div className={`flex flex-col items-center px-3 py-2 rounded-lg border shrink-0 ${
          confPct >= 90 ? 'bg-emerald-50 border-emerald-200 text-emerald-700' :
          confPct >= 70 ? 'bg-amber-50 border-amber-200 text-amber-700' :
          'bg-red-50 border-red-200 text-red-700'
        }`}>
          <span className="text-xl font-bold">{confPct}%</span>
          <span className="text-[9px] font-bold uppercase tracking-wider">Confidence</span>
        </div>
      </div>

      {/* Provenance details row */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
        <div className="bg-white rounded-lg border border-slate-200 p-2.5">
          <p className="text-slate-400 text-[10px] uppercase tracking-wider font-semibold mb-0.5">Uploaded</p>
          <p className="font-semibold text-slate-800">{formatDate(p.uploaded_at)}</p>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-2.5">
          <p className="text-slate-400 text-[10px] uppercase tracking-wider font-semibold mb-0.5">Extraction Engine</p>
          <p className="font-semibold text-slate-800">{getParseSourceLabel(p.parse_source)}</p>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-2.5">
          <p className="text-slate-400 text-[10px] uppercase tracking-wider font-semibold mb-0.5">SHA-256</p>
          <p className="font-mono text-slate-600 truncate">{p.sha256_hash?.slice(0, 16)}…</p>
        </div>
      </div>

      {/* File availability status */}
      <div className={`mt-3 flex items-center gap-2 text-xs px-3 py-2 rounded-lg border ${
        p.file_available
          ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
          : 'bg-amber-50 border-amber-200 text-amber-700'
      }`}>
        {p.file_available
          ? <CheckCircle className="h-3.5 w-3.5 shrink-0" />
          : <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
        }
        <span className="font-semibold">
          {p.file_available
            ? 'Original source artifact available'
            : `Original artifact unavailable — ${p.file_unavailable_reason || 'file not found on disk'}`
          }
        </span>
      </div>
    </div>
  );
}

function EvidenceChain({ p }: { p: IDocumentProvenance }) {
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-2 mb-3">
        <Shield className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-bold text-slate-900">Evidence Chain</h3>
      </div>

      <p className="text-xs text-slate-500 leading-relaxed">
        This document generated the following structured clinical data. Every observation displayed
        in the timeline and analytics can be traced back to this source artifact.
      </p>

      {/* Evidence counts */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Timeline Events', value: p.timeline_event_count, icon: Activity, color: 'blue' },
          { label: 'Lab Results', value: p.lab_result_count, icon: FlaskConical, color: 'emerald' },
          { label: 'Parameters', value: p.parameter_history_count, icon: BarChart3, color: 'purple' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className={`bg-${color}-50 border border-${color}-200 rounded-lg p-3 text-center`}>
            <Icon className={`h-4 w-4 text-${color}-500 mx-auto mb-1`} />
            <p className={`text-xl font-bold text-${color}-700`}>{value}</p>
            <p className={`text-[10px] font-bold uppercase tracking-wide text-${color}-500`}>{label}</p>
          </div>
        ))}
      </div>

      {/* Provenance chain diagram */}
      <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-2">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Traceability Chain</p>
        {[
          { label: 'Original Artifact', detail: p.original_filename },
          { label: 'Document Record', detail: `ID: ${p.document_id.slice(0, 8)}…` },
          { label: 'Ingestion & Extraction', detail: getParseSourceLabel(p.parse_source) },
          { label: 'Structured Clinical Data', detail: `${p.lab_result_count} labs · ${p.parameter_history_count} params` },
          { label: 'Clinical Events', detail: `${p.timeline_event_count} timeline events` },
        ].map((step, i, arr) => (
          <div key={i}>
            <div className="flex items-center gap-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 border border-primary/20 text-[10px] font-bold text-primary shrink-0">
                {i + 1}
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-800">{step.label}</p>
                <p className="text-[11px] text-slate-500">{step.detail}</p>
              </div>
            </div>
            {i < arr.length - 1 && (
              <div className="ml-[11px] w-px h-4 bg-slate-300 my-1" />
            )}
          </div>
        ))}
      </div>

      {/* SHA-256 integrity */}
      <div className="bg-slate-800 rounded-xl p-4 text-xs font-mono">
        <p className="text-slate-400 text-[10px] uppercase tracking-wider mb-2 font-sans font-semibold">SHA-256 Integrity Hash</p>
        <p className="text-emerald-400 break-all leading-relaxed">{p.sha256_hash}</p>
        <p className="text-slate-500 text-[10px] mt-2 font-sans">
          This hash uniquely identifies this exact original file. It will not match if the file was modified.
        </p>
      </div>
    </div>
  );
}

// ─── Image Viewer ─────────────────────────────────────────────────────────────

function ImageViewer({ blobUrl }: { blobUrl: string }) {
  const [zoom, setZoom] = useState(100);
  const [rotation, setRotation] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);

  return (
    <div className={`flex flex-col h-full ${fullscreen ? 'fixed inset-0 z-50 bg-slate-900' : ''}`}>
      {/* Controls */}
      <div className={`flex items-center gap-2 p-3 border-b ${fullscreen ? 'border-slate-700 bg-slate-800' : 'border-slate-200 bg-slate-50'}`}>
        <button
          onClick={() => setZoom((z) => Math.max(25, z - 25))}
          className="p-1.5 rounded hover:bg-slate-200 text-slate-600 transition-colors"
          title="Zoom out"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <span className={`text-xs font-bold w-12 text-center ${fullscreen ? 'text-slate-300' : 'text-slate-600'}`}>
          {zoom}%
        </span>
        <button
          onClick={() => setZoom((z) => Math.min(400, z + 25))}
          className="p-1.5 rounded hover:bg-slate-200 text-slate-600 transition-colors"
          title="Zoom in"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <div className="w-px h-5 bg-slate-300 mx-1" />
        <button
          onClick={() => setRotation((r) => (r + 90) % 360)}
          className="p-1.5 rounded hover:bg-slate-200 text-slate-600 transition-colors"
          title="Rotate 90°"
        >
          <RotateCw className="h-4 w-4" />
        </button>
        <button
          onClick={() => { setZoom(100); setRotation(0); }}
          className="p-1.5 rounded hover:bg-slate-200 text-slate-600 transition-colors"
          title="Reset"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
        <div className="flex-1" />
        <button
          onClick={() => setFullscreen((f) => !f)}
          className="p-1.5 rounded hover:bg-slate-200 text-slate-600 transition-colors"
          title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}
        >
          {fullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
        </button>
      </div>

      {/* Image area */}
      <div className={`flex-1 overflow-auto flex items-center justify-center p-4 ${fullscreen ? 'bg-slate-900' : 'bg-slate-900/5'}`}>
        <img
          src={blobUrl}
          alt="Original clinical document"
          style={{
            transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
            transformOrigin: 'center',
            transition: 'transform 0.2s ease',
            maxWidth: '100%',
          }}
          className="block shadow-xl rounded-sm"
        />
      </div>
    </div>
  );
}

// ─── PDF Viewer ───────────────────────────────────────────────────────────────

function PdfViewer({ blobUrl }: { blobUrl: string }) {
  return (
    <div className="flex flex-col h-full">
      {/* Toolbar hint */}
      <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 border-b border-slate-200 text-xs text-slate-500">
        <FileText className="h-3.5 w-3.5" />
        <span>Original PDF — use the toolbar inside the viewer for zoom, search, and navigation.</span>
      </div>
      <div className="flex-1">
        <object
          data={`${blobUrl}#toolbar=1&navpanes=1&scrollbar=1`}
          type="application/pdf"
          className="w-full h-full min-h-[500px]"
          title="Original clinical document"
        >
          <div className="p-8 text-center">
            <FileText className="h-12 w-12 text-slate-400 mx-auto mb-4" />
            <p className="text-sm font-semibold text-slate-700 mb-2">PDF preview not supported in your browser</p>
            <p className="text-xs text-slate-500 mb-4">
              Click "Open Original" below to open the PDF in a new tab or download it.
            </p>
          </div>
        </object>
      </div>
    </div>
  );
}

// ─── Text Viewer ──────────────────────────────────────────────────────────────

function TextViewer({ doc }: { doc: IDocument | null }) {
  const [copied, setCopied] = useState(false);
  const text = doc?.extracted_text || 'No text content extracted from this document.';

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 bg-slate-50 border-b border-slate-200 text-xs">
        <div className="flex items-center gap-2 text-slate-500">
          <FileText className="h-3.5 w-3.5" />
          <span className="font-semibold">Original Text Content</span>
        </div>
        <button
          onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
          className="flex items-center gap-1 text-slate-500 hover:text-slate-800 px-2 py-1 rounded hover:bg-slate-200 transition-colors"
        >
          <Copy className="h-3.5 w-3.5" />
          <span>{copied ? 'Copied!' : 'Copy'}</span>
        </button>
      </div>
      <div className="flex-1 overflow-auto p-4 bg-slate-900/5">
        <pre className="font-mono text-xs text-slate-800 leading-relaxed whitespace-pre-wrap">{text}</pre>
      </div>
    </div>
  );
}

// ─── Extracted Data Tab ───────────────────────────────────────────────────────

function ExtractedDataTab({ doc }: { doc: IDocument | null }) {
  if (!doc) return <div className="p-8 text-center text-sm text-slate-400">Loading extracted data…</div>;

  const fields = [
    { label: 'Original Filename', value: doc.original_filename },
    { label: 'Category', value: doc.doc_category.toUpperCase() },
    { label: 'File Type', value: doc.file_type.toUpperCase() },
    { label: 'MIME Type', value: doc.mime_type },
    { label: 'File Size', value: formatBytes(doc.file_size_bytes) },
    { label: 'Extraction Engine', value: getParseSourceLabel(doc.parse_source) },
    { label: 'Confidence Score', value: `${Math.round(doc.confidence_score * 100)}%` },
    { label: 'Processing Status', value: doc.status.toUpperCase() },
    { label: 'Processing Time', value: `${doc.processing_time_ms}ms` },
    { label: 'SHA-256', value: doc.sha256_hash, mono: true, truncate: true },
  ];

  return (
    <div className="p-6 space-y-3">
      <div className="flex items-center gap-2 mb-4">
        <CheckCircle className="h-4 w-4 text-emerald-500" />
        <h3 className="text-sm font-bold text-slate-900">Extracted Document Data</h3>
      </div>
      <div className="space-y-1">
        {fields.map(({ label, value, mono, truncate }) => (
          <div key={label} className="flex items-start gap-4 py-2.5 border-b border-slate-100">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide w-40 shrink-0 pt-0.5">
              {label}
            </span>
            <span className={`text-xs text-slate-900 flex-1 ${mono ? 'font-mono' : 'font-medium'} ${truncate ? 'truncate' : ''}`}>
              {value}
            </span>
          </div>
        ))}
      </div>

      {/* Extracted text preview */}
      {doc.extracted_text && (
        <div className="mt-4">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
            AI-Extracted Clinical Text
          </p>
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 max-h-40 overflow-y-auto">
            <pre className="font-mono text-[11px] text-slate-700 whitespace-pre-wrap leading-relaxed">
              {doc.extracted_text.slice(0, 1000)}{doc.extracted_text.length > 1000 ? '\n…[truncated]' : ''}
            </pre>
          </div>
          <p className="text-[10px] text-slate-400 mt-1">
            Note: This is AI-extracted text, not the original document. Use the "Original" tab to view the authentic source.
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Main drawer ──────────────────────────────────────────────────────────────

export default function SourceEvidenceDrawer({
  documentId,
  isOpen,
  onClose,
}: SourceEvidenceDrawerProps) {
  const [provenance, setProvenance] = useState<IDocumentProvenance | null>(null);
  const [doc, setDoc] = useState<IDocument | null>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [loadingFile, setLoadingFile] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ViewTab>('original');
  const prevBlobUrl = useRef<string | null>(null);

  // Clean up blob URLs to avoid memory leaks
  const releaseBlobUrl = useCallback(() => {
    if (prevBlobUrl.current) {
      URL.revokeObjectURL(prevBlobUrl.current);
      prevBlobUrl.current = null;
    }
  }, []);

  useEffect(() => {
    if (!isOpen || !documentId) return;

    setLoadingMeta(true);
    setLoadingFile(false);
    setFileError(null);
    setBlobUrl(null);
    setDoc(null);
    setProvenance(null);
    setActiveTab('original');

    // Fetch metadata in parallel
    Promise.all([
      ingestionApi.getDocumentProvenance(documentId),
      ingestionApi.getDocument(documentId),
    ]).then(([provRes, docRes]) => {
      const p = provRes.data;
      const d = docRes.data;
      if (p) setProvenance(p);
      if (d) setDoc(d);

      // Fetch actual file bytes if available
      if (p?.file_available) {
        setLoadingFile(true);
        ingestionApi
          .fetchContentBlob(documentId)
          .then((url) => {
            releaseBlobUrl();
            prevBlobUrl.current = url;
            setBlobUrl(url);
          })
          .catch((err) => {
            setFileError(err?.response?.data?.detail || 'Failed to load original file artifact.');
          })
          .finally(() => setLoadingFile(false));
      }
    }).catch((err) => {
      console.error('Failed to load document provenance:', err);
      setFileError(err?.response?.data?.detail || 'Document record unavailable or replaced during database re-indexing.');
    }).finally(() => setLoadingMeta(false));

    return releaseBlobUrl;
  }, [documentId, isOpen, releaseBlobUrl]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    if (isOpen) window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  if (!isOpen || !documentId) return null;

  const mime = provenance?.mime_type || doc?.mime_type || '';
  const fileType = provenance?.file_type || doc?.file_type || '';
  const isImage = isImageMime(mime);
  const isPdf = isPdfMime(mime);
  const isText = isTextMime(mime, fileType);
  const filename = provenance?.original_filename || doc?.original_filename || 'document';

  const tabs: { id: ViewTab; label: string }[] = [
    { id: 'original', label: 'Original Source' },
    { id: 'extracted', label: 'Extracted Data' },
    { id: 'evidence', label: 'Evidence Chain' },
  ];

  const handleDownload = () => {
    if (blobUrl) {
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename;
      a.click();
    }
  };

  const handleOpenOriginal = () => {
    if (blobUrl) {
      window.open(blobUrl, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer panel */}
      <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-2xl flex-col bg-white shadow-2xl border-l border-slate-200 overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-900 text-white shrink-0">
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-emerald-400" />
            <div>
              <h2 className="text-sm font-bold">Source Evidence</h2>
              <p className="text-[11px] text-slate-400">Original artifact · Full provenance chain</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-700 transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Loading metadata */}
        {loadingMeta ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 text-primary animate-spin mx-auto mb-3" />
              <p className="text-sm text-slate-600 font-medium">Loading evidence provenance…</p>
            </div>
          </div>
        ) : (
          <>
            {/* Provenance header */}
            {provenance && <ProvenanceHeader p={provenance} />}

            {/* Tabs */}
            <div className="flex border-b border-slate-200 bg-white shrink-0">
              {tabs.map(({ id, label }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`flex-1 py-3 px-4 text-xs font-semibold transition-colors border-b-2 ${
                    activeTab === id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-auto min-h-0">
              {activeTab === 'original' && (
                <>
                  {loadingFile && (
                    <div className="flex flex-col items-center justify-center h-full py-16">
                      <RefreshCw className="h-8 w-8 text-primary animate-spin mb-3" />
                      <p className="text-sm text-slate-600 font-medium">Loading original document…</p>
                      <p className="text-xs text-slate-400 mt-1">Streaming authenticated file bytes</p>
                    </div>
                  )}

                  {!loadingFile && fileError && (
                    <div className="p-8 text-center">
                      <FileX className="h-12 w-12 text-amber-400 mx-auto mb-4" />
                      <p className="text-sm font-bold text-slate-800 mb-2">Original source unavailable</p>
                      <p className="text-xs text-slate-500">{fileError}</p>
                      <p className="text-xs text-slate-400 mt-3">
                        The clinical event remains in the patient record, but the original source artifact is no longer available.
                      </p>
                    </div>
                  )}

                  {!loadingFile && !fileError && blobUrl && (
                    <div className="h-full">
                      {isPdf && <PdfViewer blobUrl={blobUrl} />}
                      {isImage && <ImageViewer blobUrl={blobUrl} />}
                      {isText && <TextViewer doc={doc} />}
                      {!isPdf && !isImage && !isText && (
                        <div className="p-8 text-center">
                          <FileText className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                          <p className="text-sm font-semibold text-slate-700 mb-2">File preview not available</p>
                          <p className="text-xs text-slate-500">Use the buttons below to open or download the original file.</p>
                        </div>
                      )}
                    </div>
                  )}

                  {!loadingFile && !fileError && !blobUrl && provenance && !provenance.file_available && (
                    <div className="p-8 text-center">
                      <AlertTriangle className="h-12 w-12 text-amber-400 mx-auto mb-4" />
                      <p className="text-sm font-bold text-slate-800 mb-2">Original source unavailable</p>
                      <p className="text-xs text-slate-500 mb-2">
                        {provenance.file_unavailable_reason || 'The original file artifact could not be located.'}
                      </p>
                      <p className="text-xs text-slate-400">
                        The clinical event remains in the patient record, but the original source artifact is no longer available on disk.
                      </p>
                    </div>
                  )}
                </>
              )}

              {activeTab === 'extracted' && <ExtractedDataTab doc={doc} />}
              {activeTab === 'evidence' && provenance && <EvidenceChain p={provenance} />}
            </div>

            {/* Footer action bar */}
            <div className="flex items-center justify-between gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50 shrink-0">
              <div className="text-[11px] text-slate-400">
                {provenance && (
                  <span className="font-mono">ID: {provenance.document_id.slice(0, 12)}…</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {blobUrl && (
                  <>
                    <button
                      onClick={handleOpenOriginal}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-primary bg-primary/5 hover:bg-primary/10 border border-primary/20 rounded-lg transition-colors"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      Open Original
                    </button>
                    <button
                      onClick={handleDownload}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                    >
                      <Download className="h-3.5 w-3.5" />
                      Download
                    </button>
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}
