import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Bot, Send, Trash2 } from 'lucide-react';
import { AssistantQueryRequest, AssistantQueryResponse, AnalysisResponse } from '../types/api';
import { assistantApi } from '../services/assistantApi';
import { ChatEntry, ChatMessage } from '../components/assistant/ChatMessage';
import { PromptSuggestions } from '../components/assistant/PromptSuggestions';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

interface Props {
  currentAnalysis: AnalysisResponse | null;
}

export const Assistant: React.FC<Props> = ({ currentAnalysis }) => {
  const [searchParams] = useSearchParams();
  const initialAnalysisId = searchParams.get('analysisId') || currentAnalysis?.analysis_id || '';
  const initialEmployeeId = searchParams.get('employeeId') || '';

  const [analysisId, setAnalysisId] = useState(initialAnalysisId);
  const [employeeId, setEmployeeId] = useState(initialEmployeeId);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const aid = searchParams.get('analysisId') || currentAnalysis?.analysis_id || '';
    if (aid) {
      setAnalysisId(aid);
    }
  }, [searchParams, currentAnalysis]);

  const initialGreeting: ChatEntry = {
    id: 'msg_welcome',
    sender: 'assistant',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    response: {
      question: 'Welcome',
      answer:
        'Hello! I am the Payroll Guardian Grounded AI Assistant. I can help explain flagged anomaly patterns, cite authoritative statutory acts (EPFO, ESIC, State PT), and recommend audit verification procedures. What would you like to investigate today?',
      grounded_facts: ['Connected to Phase 5 Statutory RAG & Phase 6 Grounded Explainer'],
      evidence_sources: ['Authoritative Compliance Corpus'],
      citations: [],
      category_distinction: {},
      suggested_next_steps: [
        'Ask about statutory deduction rules',
        'Inquire why a specific employee was flagged',
      ],
      disclaimer: 'AI-assisted payroll auditor assistant. Must be verified with statutory guidelines.',
    },
  };

  const [messages, setMessages] = useState<ChatEntry[]>([initialGreeting]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputText;
    if (!query.trim() || loading) return;

    const userEntry: ChatEntry = {
      id: `user_${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userEntry]);
    setInputText('');
    setLoading(true);

    try {
      const payload: AssistantQueryRequest = {
        question: query,
        analysis_id: analysisId || undefined,
        employee_id: employeeId || undefined,
      };

      const res: AssistantQueryResponse = await assistantApi.query(payload);

      const assistantEntry: ChatEntry = {
        id: `asst_${Date.now()}`,
        sender: 'assistant',
        response: res,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantEntry]);
    } catch (err: any) {
      const errorEntry: ChatEntry = {
        id: `err_${Date.now()}`,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        response: {
          question: query,
          answer: `Unable to process query: ${err.message || 'API connection failed'}. Please ensure the backend service is running.`,
          grounded_facts: [],
          evidence_sources: [],
          citations: [],
          category_distinction: {},
          suggested_next_steps: ['Check backend connection', 'Retry your question'],
          uncertainty_or_refusal: 'Backend connection error',
          disclaimer: 'Error response',
        },
      };
      setMessages((prev) => [...prev, errorEntry]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([initialGreeting]);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 flex flex-col h-[calc(100vh-8.5rem)]">
      {/* Top Header & Context Controls */}
      <div className="card-glass rounded-2xl p-4 border-slate-800 flex flex-wrap items-center justify-between gap-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-white text-base">Grounded Payroll AI Assistant</h2>
            <p className="text-[11px] text-slate-400">
              Grounded strictly in structured anomaly evidence and retrieved compliance knowledge
            </p>
          </div>
        </div>

        {/* Context Selectors */}
        <div className="flex items-center gap-2 text-xs">
          {currentAnalysis && (
            <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl font-mono text-[11px] text-slate-300">
              <span className="text-slate-500">Analysis:</span>
              <span className="text-brand-300">{currentAnalysis.analysis_id.substring(0, 12)}...</span>
            </div>
          )}

          <input
            type="text"
            value={employeeId}
            onChange={(e) => setEmployeeId(e.target.value)}
            placeholder="Focus Employee (e.g. EMP_2041)"
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-[11px] text-slate-200 focus:outline-none focus:border-brand-500 font-mono w-48"
          />

          <button
            onClick={clearChat}
            className="p-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition"
            title="Reset Chat Session"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-2">
        {messages.map((m) => (
          <ChatMessage key={m.id} entry={m} />
        ))}

        {loading && (
          <div className="flex items-start gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-brand-600/20 border border-brand-500/30 flex items-center justify-center text-brand-400 shrink-0 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="card-glass rounded-2xl rounded-tl-sm p-4 text-xs text-slate-400 border-slate-800 flex items-center gap-3">
              <LoadingSpinner size="sm" />
              <span>Retrieving compliance chunks & synthesizing grounded answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions and Input Box */}
      <div className="shrink-0 space-y-3 pt-2">
        {messages.length <= 2 && (
          <PromptSuggestions onSelectPrompt={(p) => handleSendMessage(p)} />
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="relative"
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={loading}
            placeholder={
              employeeId
                ? `Ask about ${employeeId}'s anomaly evidence, rule violations, or recommended next steps...`
                : 'Ask a grounded payroll statutory or audit question...'
            }
            className="w-full pl-5 pr-24 py-3.5 rounded-2xl bg-slate-900 border border-slate-800 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition shadow-inner"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || loading}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-xs shadow-md transition flex items-center gap-1.5"
          >
            <span>Send</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
};
