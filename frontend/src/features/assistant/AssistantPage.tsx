import { useState, useEffect, useRef } from 'react';
import { Bot, Send, ShieldCheck, FileText, Sparkles, AlertCircle, CheckCircle2 } from 'lucide-react';
import PageLayout from '@/components/common/PageLayout';
import EmptyState from '@/components/common/EmptyState';
import { patientsApi } from '@/services/api/patients';
import { assistantApi, IAIQueryResponse } from '@/services/api/assistant';
import { IPatientListItem } from '@/types/patients';

export default function AssistantPage() {
  const [patients, setPatients] = useState<IPatientListItem[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [queryInput, setQueryInput] = useState('');
  const [chatHistory, setChatHistory] = useState<IAIQueryResponse[]>([]);
  const [loadingPatients, setLoadingPatients] = useState(true);
  const [sendingQuery, setSendingQuery] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadPatients = async () => {
      try {
        setLoadingPatients(true);
        const res = await patientsApi.list({ page: 1, page_size: 50 });
        if (res.data?.items) {
          setPatients(res.data.items);
          if (res.data.items.length > 0) {
            setSelectedPatientId(res.data.items[0].id);
          }
        }
      } catch (err: any) {
        setError(err?.message || 'Failed to load patient records.');
      } finally {
        setLoadingPatients(false);
      }
    };
    loadPatients();
  }, []);

  useEffect(() => {
    if (!selectedPatientId) return;
    const fetchHistory = async () => {
      try {
        const res = await assistantApi.getHistory(selectedPatientId);
        if (res.data) {
          setChatHistory(res.data.reverse());
        }
      } catch (err) {
        setChatHistory([]);
      }
    };
    fetchHistory();
  }, [selectedPatientId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, sendingQuery]);

  const handleSend = async () => {
    if (!queryInput.trim() || !selectedPatientId || sendingQuery) return;
    const queryText = queryInput.trim();
    setQueryInput('');
    setSendingQuery(true);
    setError(null);

    try {
      const res = await assistantApi.query(selectedPatientId, queryText);
      if (res.data) {
        setChatHistory((prev) => [...prev, res.data]);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to execute clinical RAG reasoning.');
    } finally {
      setSendingQuery(false);
    }
  };

  const selectedPatient = patients.find((p) => p.id === selectedPatientId);

  const suggestedQueries = [
    'What are the latest lab results and glucose readings?',
    'Summarize vitals and active clinical alerts for this patient.',
    'Are there any drug-drug interactions or allergy warnings?',
    'Provide a full clinical history and timeline summary.',
  ];

  return (
    <PageLayout
      title="GPT-5 Nano Clinical RAG Assistant"
      description="Production 12-Stage Hybrid RAG Reasoning Engine grounded strictly on patient records."
    >
      <div className="flex flex-col h-[calc(100vh-12rem)] bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Header Bar — Patient Selector */}
        <div className="p-4 border-b border-slate-200 bg-slate-50/80 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Active Patient Context</p>
              {loadingPatients ? (
                <p className="text-sm font-medium text-slate-400">Loading patients...</p>
              ) : (
                <select
                  value={selectedPatientId}
                  onChange={(e) => setSelectedPatientId(e.target.value)}
                  className="bg-white border border-slate-200 text-slate-900 text-sm font-semibold rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/40"
                >
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.first_name} {p.last_name} ({p.mrn}) • {p.gender.toUpperCase()}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>

          {selectedPatient && (
            <div className="flex items-center gap-3 text-xs text-slate-600 bg-white px-3 py-1.5 rounded-md border border-slate-200">
              <span><strong>Age:</strong> {selectedPatient.age}</span>
              <span>•</span>
              <span><strong>Blood:</strong> {selectedPatient.blood_group || 'O+'}</span>
              <span>•</span>
              <span className="text-emerald-700 font-medium flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Hybrid RAG Grounded
              </span>
            </div>
          )}
        </div>

        {/* Message Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          {chatHistory.length === 0 && !sendingQuery ? (
            <div className="h-full flex flex-col items-center justify-center space-y-6">
              <EmptyState
                icon={Bot}
                title="Clinical Decision Support Ready"
                description={`Ask specific medical questions regarding ${
                  selectedPatient ? `${selectedPatient.first_name} ${selectedPatient.last_name}` : 'the selected patient'
                }.`}
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full px-4">
                {suggestedQueries.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setQueryInput(q);
                    }}
                    className="p-3 bg-slate-50 hover:bg-slate-100/80 border border-slate-200 rounded-lg text-left text-xs font-medium text-slate-700 transition-colors flex items-center justify-between"
                  >
                    <span>{q}</span>
                    <Sparkles className="w-3.5 h-3.5 text-primary opacity-70 shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            chatHistory.map((item) => (
              <div key={item.id} className="space-y-4">
                {/* User Message */}
                <div className="flex justify-end">
                  <div className="bg-primary text-white text-sm px-4 py-3 rounded-2xl rounded-tr-none max-w-xl shadow-sm">
                    {item.query}
                  </div>
                </div>

                {/* Assistant Response */}
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1 bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-none p-5 text-slate-900 space-y-4 shadow-sm">
                    {/* Grounding & Confidence header */}
                    <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        {(item.confidence_score * 100).toFixed(1)}% Grounded Confidence
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">
                        Audit Hash: {item.audit_hash.slice(0, 16)}...
                      </span>
                    </div>

                    {/* Answer text */}
                    <div className="text-sm leading-relaxed whitespace-pre-line font-normal text-slate-800">
                      {item.answer}
                    </div>

                    {/* Source Citations */}
                    {item.sources && item.sources.length > 0 && (
                      <div className="pt-3 border-t border-slate-200/80">
                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1">
                          <FileText className="w-3.5 h-3.5" /> Sources Cited ({item.sources.length})
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {item.sources.map((src, sIdx) => (
                            <div
                              key={sIdx}
                              className="p-2.5 bg-white border border-slate-200 rounded-lg text-xs space-y-1 shadow-2xs"
                            >
                              <div className="flex items-center justify-between font-semibold text-slate-900">
                                <span>{src.filename}</span>
                                <span className="uppercase text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                                  {src.category}
                                </span>
                              </div>
                              <p className="text-slate-500 italic truncate text-[11px]">"{src.snippet}"</p>
                              <p className="text-[10px] text-emerald-700 font-mono text-right">
                                Relevance: {(src.relevance_score * 100).toFixed(1)}%
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}

          {sendingQuery && (
            <div className="flex gap-3 items-center py-4">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center animate-pulse">
                <Bot className="w-4 h-4 text-primary" />
              </div>
              <div className="text-sm text-slate-500 font-medium">
                Running 12-Stage Hybrid RAG Reasoning (Dense + BM25 + RRF + MMR)...
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50">
          <div className="relative max-w-4xl mx-auto flex items-center gap-2">
            <input
              type="text"
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder={
                selectedPatient
                  ? `Ask GPT-5 Nano about ${selectedPatient.first_name} ${selectedPatient.last_name}'s medical records...`
                  : 'Select a patient to begin RAG query...'
              }
              disabled={!selectedPatientId || sendingQuery}
              className="flex-1 pl-4 pr-12 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary shadow-sm text-sm bg-white disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!queryInput.trim() || !selectedPatientId || sendingQuery}
              className="p-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-center text-[11px] text-slate-400 mt-2">
            ClinIQ Assistant is grounded strictly on patient records & medical literature. Verifiable via cryptographic SHA256 audit hash.
          </p>
        </div>
      </div>
    </PageLayout>
  );
}
