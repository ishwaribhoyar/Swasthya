import { useState, useEffect, useRef } from 'react';
import { Bot, Send, ShieldCheck, FileText, Sparkles, AlertCircle, CheckCircle2, ChevronRight, Info } from 'lucide-react';
import PageLayout from '@/components/common/PageLayout';
import EmptyState from '@/components/common/EmptyState';
import { patientsApi } from '@/services/api/patients';
import { copilotApi, IAICopilotChatResponse, ISourceAttribution, IAmbiguousCandidate } from '@/services/api/copilot';
import { IPatientListItem } from '@/types/patients';

interface IChatMessageItem {
  id: string;
  query: string;
  answer: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';
  sources: ISourceAttribution[];
  intent: string;
  isGeneralInfo?: boolean;
  ambiguousCandidates?: IAmbiguousCandidate[];
}

export default function AssistantPage() {
  const [patients, setPatients] = useState<IPatientListItem[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [queryInput, setQueryInput] = useState('');
  const [chatHistory, setChatHistory] = useState<IChatMessageItem[]>([]);
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
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, sendingQuery]);

  const handleSend = async (customQuery?: string) => {
    const queryText = (customQuery || queryInput).trim();
    if (!queryText || sendingQuery) return;
    
    if (!customQuery) setQueryInput('');
    setSendingQuery(true);
    setError(null);

    try {
      const res: IAICopilotChatResponse = await copilotApi.chat({
        message: queryText,
        patient_id: selectedPatientId || null,
      });

      const newItem: IChatMessageItem = {
        id: `msg_${Date.now()}`,
        query: queryText,
        answer: res.answer,
        confidence: res.confidence,
        sources: res.sources,
        intent: res.intent,
        isGeneralInfo: res.is_general_info,
        ambiguousCandidates: res.ambiguous_candidates,
      };

      setChatHistory((prev) => [...prev, newItem]);
    } catch (err: any) {
      setError(err?.message || 'AI Copilot request failed because the OpenAI API key is missing or unconfigured.');
    } finally {
      setSendingQuery(false);
    }
  };

  const selectedPatient = patients.find((p) => p.id === selectedPatientId);

  const suggestedQueries = [
    'Has kidney function worsened?',
    'How many times was metformin prescribed?',
    'What was the latest blood pressure?',
    'Summarize vitals and active clinical alerts for this patient.',
  ];

  return (
    <PageLayout
      title="GPT-5 Nano Clinical AI Copilot"
      description="Production 12-Stage Grounded RAG Assistant using SQLite + Phase 4 Clinical Intelligence."
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
                  <option value="">-- All Patients (Global RAG Search) --</option>
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
                <ShieldCheck className="w-3.5 h-3.5" /> 12-Stage Grounded RAG
              </span>
            </div>
          )}
        </div>

        {/* Message Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
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
                title="Grounded Clinical Intelligence Ready"
                description={`Ask specific medical questions regarding ${
                  selectedPatient ? `${selectedPatient.first_name} ${selectedPatient.last_name}` : 'your patient roster'
                }.`}
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full px-4">
                {suggestedQueries.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(q)}
                    className="p-3 bg-white hover:bg-slate-100/80 border border-slate-200 rounded-lg text-left text-xs font-medium text-slate-700 transition-colors flex items-center justify-between shadow-2xs"
                  >
                    <span>{q}</span>
                    <Sparkles className="w-3.5 h-3.5 text-primary opacity-70 shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            chatHistory.map((item) => (
              <div key={item.id} className="space-y-4 max-w-4xl mx-auto">
                {/* User Message */}
                <div className="flex justify-end">
                  <div className="bg-primary text-white text-sm px-4 py-3 rounded-2xl rounded-tr-none max-w-xl shadow-sm font-medium">
                    {item.query}
                  </div>
                </div>

                {/* Assistant Response */}
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1 bg-white border border-slate-200 rounded-2xl rounded-tl-none p-5 text-slate-900 space-y-4 shadow-sm">
                    {/* Header: Confidence & Intent */}
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${
                            item.confidence === 'HIGH'
                              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                              : item.confidence === 'MEDIUM'
                              ? 'bg-amber-50 text-amber-800 border border-amber-200'
                              : 'bg-rose-50 text-rose-800 border border-rose-200'
                          }`}
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          {item.confidence} Evidence Confidence
                        </span>
                        {item.isGeneralInfo && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                            <Info className="w-3.5 h-3.5" /> General Medical Info
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                        Intent: {item.intent}
                      </span>
                    </div>

                    {/* Answer text */}
                    <div className="text-sm leading-relaxed whitespace-pre-line text-slate-800 font-normal">
                      {item.answer}
                    </div>

                    {/* Ambiguous Candidates List */}
                    {item.ambiguousCandidates && item.ambiguousCandidates.length > 0 && (
                      <div className="mt-3 space-y-2 border-t border-slate-100 pt-3">
                        <p className="text-xs font-semibold text-slate-700">Matching Patients Found:</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {item.ambiguousCandidates.map((cand) => (
                            <button
                              key={cand.id}
                              onClick={() => {
                                setSelectedPatientId(cand.id);
                                handleSend(`Tell me about patient ${cand.name} (MRN: ${cand.mrn})`);
                              }}
                              className="p-3 rounded-lg bg-blue-50/50 hover:bg-blue-100/60 border border-blue-200 text-left transition-colors flex items-center justify-between text-xs"
                            >
                              <div>
                                <span className="font-bold text-blue-900">{cand.name}</span>
                                <div className="text-[11px] text-blue-700">MRN: {cand.mrn} · DOB: {cand.date_of_birth} ({cand.gender})</div>
                              </div>
                              <ChevronRight className="w-4 h-4 text-blue-600" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Sources Citations */}
                    {item.sources && item.sources.length > 0 && (
                      <div className="pt-3 border-t border-slate-100">
                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1">
                          <FileText className="w-3.5 h-3.5" /> Evidence Sources ({item.sources.length})
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {item.sources.map((src, sIdx) => (
                            <div
                              key={sIdx}
                              className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs flex items-center justify-between"
                            >
                              <div className="flex items-center gap-2 truncate">
                                <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                                <span className="font-medium text-slate-800 truncate">{src.title}</span>
                              </div>
                              <span className="text-[10px] text-slate-500 font-mono shrink-0 ml-2">{src.event_date}</span>
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
            <div className="flex gap-3 items-center py-4 max-w-4xl mx-auto">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center animate-pulse">
                <Bot className="w-4 h-4 text-primary" />
              </div>
              <div className="text-sm text-slate-500 font-medium">
                Executing 12-Stage Grounded RAG Pipeline (Structured SQLite + Hybrid Vector + RRF)...
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
                  ? `Ask GPT-5 Nano about ${selectedPatient.first_name} ${selectedPatient.last_name}'s clinical records...`
                  : 'Type a question or patient name...'
              }
              disabled={sendingQuery}
              className="flex-1 pl-4 pr-12 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary shadow-sm text-sm bg-white disabled:opacity-50"
            />
            <button
              onClick={() => handleSend()}
              disabled={!queryInput.trim() || sendingQuery}
              className="p-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-center text-[11px] text-slate-400 mt-2">
            ClinIQ AI Copilot provides grounded clinical record information and does not replace clinician judgment.
          </p>
        </div>
      </div>
    </PageLayout>
  );
}
