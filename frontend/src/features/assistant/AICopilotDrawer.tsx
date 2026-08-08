import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Bot, X, Send, ShieldCheck, 
  FileText, ChevronRight, Info, RefreshCw, ExternalLink
} from 'lucide-react';
import { copilotApi, IAICopilotChatResponse, ISourceAttribution, IAmbiguousCandidate } from '@/services/api/copilot';
import SourceEvidenceDrawer from '@/features/ingestion/SourceEvidenceDrawer';

interface AICopilotDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activePatientId?: string | null;
  activePatientName?: string | null;
}

interface IChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  confidence?: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';
  sources?: ISourceAttribution[];
  isGeneralInfo?: boolean;
  ambiguousCandidates?: IAmbiguousCandidate[];
}

export const AICopilotDrawer: React.FC<AICopilotDrawerProps> = ({
  isOpen,
  onClose,
  activePatientId,
  activePatientName,
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sourceDocId, setSourceDocId] = useState<string | null>(null);
  const [messages, setMessages] = useState<IChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: activePatientName
        ? `Hello, Dr.! I am ClinIQ AI Copilot. Ask me any clinical question regarding **${activePatientName}** (e.g., "Has kidney function worsened?", "How many times was metformin prescribed?").`
        : `Hello, Dr.! I am ClinIQ AI Copilot. Mention a patient name or ask any grounded clinical question across your patient roster.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || inputMessage;
    if (!textToSend.trim() || isLoading) return;

    const userMsgId = `user_${Date.now()}`;
    const userMsg: IChatMessage = {
      id: userMsgId,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customText) setInputMessage('');
    setIsLoading(true);

    try {
      const res: IAICopilotChatResponse = await copilotApi.chat({
        message: textToSend,
        patient_id: activePatientId || null,
      });

      const aiMsg: IChatMessage = {
        id: `ai_${Date.now()}`,
        sender: 'assistant',
        text: res.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        confidence: res.confidence,
        sources: res.sources,
        isGeneralInfo: res.is_general_info,
        ambiguousCandidates: res.ambiguous_candidates,
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: IChatMessage = {
        id: `err_${Date.now()}`,
        sender: 'assistant',
        text: err?.message || 'AI Copilot request failed. Please check your network connection.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        confidence: 'INSUFFICIENT',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {

      setIsLoading(false);
    }
  };

  const handleSelectCandidate = (cand: IAmbiguousCandidate) => {
    handleSendMessage(`Tell me about patient ${cand.name} (MRN: ${cand.mrn})`);
  };

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.4 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-slate-900 z-40"
          />

          {/* Slide-over Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-white z-50 shadow-2xl flex flex-col"
          >
            {/* Drawer Header */}
            <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-900 text-white">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm flex items-center gap-1.5">
                    ClinIQ AI Copilot
                    <span className="text-[10px] bg-blue-500/30 text-blue-200 px-2 py-0.5 rounded-full font-medium">
                      GPT-5 Nano
                    </span>
                  </h3>
                  <p className="text-xs text-slate-300">
                    {activePatientName ? `Context: ${activePatientName}` : 'Global Patient RAG'}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Chat Messages Body */}
            <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-xl p-3.5 text-sm shadow-sm ${
                      msg.sender === 'user'
                        ? 'bg-blue-600 text-white rounded-br-none'
                        : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none'
                    }`}
                  >
                    {/* Message Content */}
                    <div className="whitespace-pre-wrap leading-relaxed">{msg.text}</div>

                    {/* Ambiguous Candidates Selection */}
                    {msg.ambiguousCandidates && msg.ambiguousCandidates.length > 0 && (
                      <div className="mt-3 space-y-2 border-t border-slate-100 pt-2">
                        <p className="text-xs font-semibold text-slate-600">Select Patient:</p>
                        {msg.ambiguousCandidates.map((cand) => (
                          <button
                            key={cand.id}
                            onClick={() => handleSelectCandidate(cand)}
                            className="w-full text-left p-2 rounded-lg bg-blue-50 hover:bg-blue-100 border border-blue-200 transition-colors flex items-center justify-between text-xs text-blue-900"
                          >
                            <div>
                              <span className="font-semibold">{cand.name}</span> ({cand.mrn})
                              <div className="text-[10px] text-blue-700">DOB: {cand.date_of_birth} · {cand.gender}</div>
                            </div>
                            <ChevronRight className="w-4 h-4 text-blue-600" />
                          </button>
                        ))}
                      </div>
                    )}

                    {/* General Knowledge Indicator */}
                    {msg.isGeneralInfo && (
                      <div className="mt-2.5 flex items-center gap-1 text-[11px] text-indigo-600 bg-indigo-50 px-2 py-1 rounded border border-indigo-100 font-medium">
                        <Info className="w-3.5 h-3.5" />
                        General Medical Information (Not from Patient Record)
                      </div>
                    )}

                    {/* Sources Attribution Chips */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-2 border-t border-slate-100 text-xs">
                        <div className="text-[11px] font-semibold text-slate-500 mb-1.5 flex items-center justify-between">
                          <span>Evidence Sources ({msg.sources.length}):</span>
                          {msg.confidence && (
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                msg.confidence === 'HIGH'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : msg.confidence === 'MEDIUM'
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-rose-100 text-rose-800'
                              }`}
                            >
                              Confidence: {msg.confidence}
                            </span>
                          )}
                        </div>
                        <div className="space-y-1">
                          {msg.sources.map((s, idx) => (
                            <button
                              key={idx}
                              onClick={() => s.record_id ? setSourceDocId(s.record_id) : undefined}
                              disabled={!s.record_id}
                              className={`w-full flex items-center gap-1.5 text-[11px] px-2 py-1.5 rounded border font-medium transition-colors ${
                                s.record_id
                                  ? 'bg-blue-50 border-blue-200 text-blue-800 hover:bg-blue-100 cursor-pointer'
                                  : 'bg-slate-100 border-slate-200 text-slate-600 cursor-default'
                              }`}
                              title={s.record_id ? 'Click to view original source document' : 'Source document not available'}
                            >
                              <FileText className="w-3.5 h-3.5 shrink-0" />
                              <span className="truncate flex-1 text-left">{s.title}</span>
                              <span className="text-[10px] opacity-70 font-mono shrink-0">{s.event_date}</span>
                              {s.record_id && <ExternalLink className="w-3 h-3 shrink-0 opacity-60" />}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    <div
                      className={`text-[10px] mt-1.5 text-right ${
                        msg.sender === 'user' ? 'text-blue-200' : 'text-slate-400'
                      }`}
                    >
                      {msg.timestamp}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-slate-200 rounded-xl p-3 flex items-center space-x-2 text-xs text-slate-500 shadow-sm">
                    <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
                    <span>Analyzing SQLite & Executing RAG Pipeline...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Input Bar */}
            <div className="p-3 bg-white border-t border-slate-200">
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder={
                    activePatientName
                      ? `Ask about ${activePatientName}...`
                      : 'Ask about any patient or type a name...'
                  }
                  disabled={isLoading}
                  className="flex-1 px-3.5 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => handleSendMessage()}
                  disabled={isLoading || !inputMessage.trim()}
                  className="p-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition-colors shadow-sm"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              <p className="text-[10px] text-slate-400 text-center mt-2 flex items-center justify-center gap-1">
                <ShieldCheck className="w-3 h-3 text-emerald-600" />
                ClinIQ Grounded RAG · Record-based evidence · Not a diagnostic tool
              </p>
            </div>
          </motion.div>
        </>
        )}
      </AnimatePresence>

      <SourceEvidenceDrawer
        documentId={sourceDocId}
        isOpen={!!sourceDocId}
        onClose={() => setSourceDocId(null)}
      />
    </>
  );
};
