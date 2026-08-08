import { useState, useEffect } from 'react';
import { X, FileText, Copy } from 'lucide-react';
import { ingestionApi } from '@/services/api/ingestion';
import { IDocument } from '@/types/ingestion';

interface DocumentViewerModalProps {
  documentId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function DocumentViewerModal({ documentId, isOpen, onClose }: DocumentViewerModalProps) {
  const [doc, setDoc] = useState<IDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'text' | 'markdown'>('text');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (documentId && isOpen) {
      setLoading(true);
      ingestionApi
        .getDocument(documentId)
        .then((res) => {
          if (res.data) setDoc(res.data);
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [documentId, isOpen]);

  if (!isOpen || !documentId) return null;

  // Clean raw zip artifacts and HTML/CSS boilerplate
  const sanitizeContent = (str?: string) => {
    if (!str) return 'No content extracted.';
    let clean = str;

    // 1. Strip ZIP headers if any
    if (clean.startsWith('PK') || clean.includes('manifest.json')) {
      clean = clean.replace(/PK[\s\S]*?(?=Extracted|Report|Lab|Hemoglobin|Regd|Sample|$)/gi, '');
    }

    // 2. Strip HTML/CSS boilerplate (<style>...</style>, <head>...</head>, tags)
    clean = clean.replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, '');
    clean = clean.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '');
    clean = clean.replace(/<head\b[^>]*>[\s\S]*?<\/head>/gi, '');
    clean = clean.replace(/<br\s*\/?>/gi, '\n');
    clean = clean.replace(/<\/(p|div|tr|h1|h2|h3|h4|li)>/gi, '\n');
    clean = clean.replace(/<[^>]+>/g, '');
    clean = clean.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').replace(/&quot;/g, '"');

    // 3. Clean up excessive empty lines
    const lines = clean.split('\n').map((l) => l.trim());
    const result: string[] = [];
    let blank = false;
    for (const line of lines) {
      if (line) {
        result.push(line);
        blank = false;
      } else if (!blank) {
        result.push('');
        blank = true;
      }
    }
    return result.join('\n').trim();
  };

  const currentContent = viewMode === 'text' ? sanitizeContent(doc?.extracted_text) : sanitizeContent(doc?.extracted_markdown || doc?.extracted_text);


  const copyToClipboard = () => {
    if (currentContent) {
      navigator.clipboard.writeText(currentContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="w-full max-w-3xl rounded-xl bg-white shadow-xl border border-slate-200 overflow-hidden my-8 flex flex-col max-h-[85vh]">
        <div className="flex items-center justify-between border-b px-6 py-4 bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-900">{doc?.original_filename || 'Document'}</h2>
              <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                <span>Category: {doc?.doc_category.toUpperCase()}</span>
                <span>•</span>
                <span>Source: {doc?.parse_source || 'Sarvam AI'}</span>
                <span>•</span>
                <span>Confidence: {doc ? (doc.confidence_score * 100).toFixed(1) : 0}%</span>
              </div>
            </div>
          </div>

          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400">Loading extracted document content...</div>
        ) : !doc ? (
          <div className="p-12 text-center text-xs text-red-500">Failed to load document details.</div>
        ) : (
          <div className="flex-1 flex flex-col min-h-0">
            {/* View Mode Bar */}
            <div className="flex items-center justify-between px-6 py-2 border-b bg-slate-50/50 text-xs">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setViewMode('text')}
                  className={`px-3 py-1 rounded-md font-medium transition-colors ${
                    viewMode === 'text' ? 'bg-primary text-white' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  Extracted Clinical Text
                </button>
                <button
                  onClick={() => setViewMode('markdown')}
                  className={`px-3 py-1 rounded-md font-medium transition-colors ${
                    viewMode === 'markdown' ? 'bg-primary text-white' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  Markdown View
                </button>
              </div>

              <button
                onClick={copyToClipboard}
                className="flex items-center gap-1 text-slate-600 hover:text-slate-900 px-2 py-1 rounded hover:bg-slate-100 font-medium"
              >
                <Copy className="h-3.5 w-3.5" />
                <span>{copied ? 'Copied!' : 'Copy'}</span>
              </button>
            </div>

            {/* Extracted Content View */}
            <div className="flex-1 p-6 overflow-y-auto font-mono text-xs text-slate-800 leading-relaxed bg-slate-900/5">
              <pre className="whitespace-pre-wrap font-mono">{currentContent}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
