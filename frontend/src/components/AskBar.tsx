'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Send, X, FileText, BarChart3, Loader2, ExternalLink } from 'lucide-react';
import { AskResponse } from '@/types';
import { formatCurrency } from '@/lib/format';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// Component to format answer text with better typography
function FormattedAnswer({ text }: { text: string }) {
  // Split into paragraphs first
  const paragraphs = text.split(/\n\n+/).filter(p => p.trim());
  
  return (
    <div className="text-gray-900 leading-relaxed space-y-4">
      {paragraphs.map((paragraph, pIdx) => {
        // Check if it's a numbered list item
        const listMatch = paragraph.match(/^(\d+)\.\s+(.+)$/);
        if (listMatch) {
          return (
            <div key={pIdx} className="flex gap-3">
              <span className="font-bold text-turquoise text-lg flex-shrink-0 w-6">{listMatch[1]}.</span>
              <div className="flex-1">
                <FormattedText text={listMatch[2]} />
              </div>
            </div>
          );
        }
        
        // Regular paragraph
        return (
          <p key={pIdx} className="text-base">
            <FormattedText text={paragraph} />
          </p>
        );
      })}
    </div>
  );
}

// Helper to format inline text (bold, etc.)
function FormattedText({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={i} className="font-bold text-gray-900">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

interface AskBarProps {
  onAsk: (question: string) => Promise<AskResponse>;
}

export default function AskBar({ onAsk }: AskBarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    setIsLoading(true);
    setResponse(null); // Clear previous response
    
    try {
      const result = await onAsk(question);
      setResponse(result);
    } catch (error) {
      console.error('Failed to get answer:', error);
      // Set error response so user sees the error
      setResponse({
        answer: error instanceof Error ? error.message : 'Failed to get answer. Please try again.',
        numbers: null,
        chart_data: null,
        citations: [],
        confidence: 0.0,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setQuestion('');
    setResponse(null);
  };

  const exampleQuestions = [
    "How much was allocated for education this year?",
    "What is the national debt?",
    "What is the Bahamas National Health Strategy?",
    "What are the health strategy goals for 2026-2030?",
    "Compare health vs education spending",
    "What health targets are mentioned in the strategy?",
  ];

  return (
    <>
      {/* Floating Ask Button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-turquoise text-white p-4 rounded-full shadow-lg z-40 flex items-center gap-2"
      >
        <Search className="w-5 h-5" />
        <span className="font-medium hidden sm:inline">Ask questions</span>
      </motion.button>

      {/* Ask Modal */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={handleClose}
              className="fixed inset-0 bg-black/50 z-50"
            />

            {/* Panel */}
            <motion.div
              initial={{ opacity: 0, y: '100%' }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed bottom-0 left-0 right-0 bg-white rounded-t-2xl z-50 max-h-[80vh] overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Ask about the budget & health strategy</h2>
                <button
                  onClick={handleClose}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-4">
                {!response ? (
                  <div className="space-y-4">
                    <p className="text-gray-600">
                      Ask me anything about the Bahamas budget, spending, revenue, debt, or national health strategy.
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {exampleQuestions.map((q, i) => (
                        <button
                          key={i}
                          onClick={() => setQuestion(q)}
                          className="text-left p-3 rounded-lg bg-gray-50 hover:bg-turquoise/10 text-sm text-gray-700 hover:text-turquoise transition-colors"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Question */}
                    <div className="bg-turquoise/10 rounded-lg p-3">
                      <p className="text-sm font-medium text-turquoise">Your question</p>
                      <p className="text-gray-900">{question}</p>
                    </div>

                    {/* Answer */}
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h3 className="text-lg font-bold text-gray-900 mb-4">Answer</h3>
                      <div className="prose prose-sm max-w-none">
                        <FormattedAnswer text={response.answer} />
                      </div>
                    </div>

                    {/* Numbers */}
                    {response.numbers && Object.keys(response.numbers).length > 0 && (
                      <div className="bg-turquoise/5 border border-turquoise/20 rounded-lg p-4">
                        <h3 className="text-sm font-bold text-gray-900 mb-3">Key Figures</h3>
                        <div className="grid grid-cols-2 gap-3">
                          {Object.entries(response.numbers).map(([key, value]) => (
                            <div key={key} className="bg-white border border-gray-200 rounded-lg p-3">
                              <p className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">
                                {key.replace(/_/g, ' ')}
                              </p>
                              <p className="text-xl font-bold text-turquoise tabular-nums">
                                {typeof value === 'number' && value > 1000
                                  ? formatCurrency(value, true)
                                  : typeof value === 'number' && value < 1
                                  ? `${(value * 100).toFixed(1)}%`
                                  : value}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Chart */}
                    {response.chart_data && response.chart_data.length > 0 && (
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-3">
                          <BarChart3 className="w-4 h-4 text-turquoise" />
                          <p className="text-sm font-medium text-gray-700">Trend</p>
                        </div>
                        <div className="h-40">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={response.chart_data}>
                              <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                              <YAxis 
                                tick={{ fontSize: 11 }} 
                                tickFormatter={(v) => formatCurrency(v, true)}
                              />
                              <Tooltip 
                                formatter={(value: number) => formatCurrency(value, true)}
                              />
                              <Bar dataKey="amount" fill="#00CED1" radius={[4, 4, 0, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    )}

                    {/* Citations */}
                    {response.citations.length > 0 && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <h3 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                          <FileText className="w-4 h-4 text-turquoise" />
                          Source Documents
                        </h3>
                        <div className="space-y-2">
                          {response.citations.map((citation, i) => {
                            // Build PDF URL - browsers support #page=N for PDF navigation
                            const pdfFilename = encodeURIComponent(citation.document);
                            const pdfPath = `/api/v1/documents/${pdfFilename}#page=${citation.page}`;
                            return (
                              <a
                                key={i}
                                href={pdfPath}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-200 hover:border-turquoise hover:shadow-sm transition-all group"
                              >
                                <FileText className="w-5 h-5 text-turquoise flex-shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <p className="font-semibold text-gray-900 text-sm">
                                      {citation.document.replace(/_/g, ' ')}
                                    </p>
                                    <ExternalLink className="w-3 h-3 text-gray-400" />
                                  </div>
                                  <p className="text-xs font-medium text-turquoise mb-2">
                                    Page {citation.page}
                                  </p>
                                  {citation.snippet && (
                                    <p className="text-xs text-gray-500 italic line-clamp-2 border-l-2 border-turquoise/30 pl-2 py-1">
                                      "{citation.snippet.substring(0, 150)}{citation.snippet.length > 150 ? '...' : ''}"
                                    </p>
                                  )}
                                </div>
                              </a>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Confidence */}
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <div className={`w-2 h-2 rounded-full ${
                        response.confidence > 0.8 ? 'bg-green-500' :
                        response.confidence > 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                      }`} />
                      <span>Confidence: {(response.confidence * 100).toFixed(0)}%</span>
                    </div>

                    {/* Ask another */}
                    <button
                      onClick={() => {
                        setQuestion('');
                        setResponse(null);
                      }}
                      className="text-turquoise text-sm font-medium hover:underline"
                    >
                      Ask another question
                    </button>
                  </div>
                )}
              </div>

              {/* Input */}
              {!response && (
                <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
                  <div className="flex items-center gap-2">
                    <input
                      ref={inputRef}
                      type="text"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="Ask about spending, revenue, debt, or health strategy..."
                      className="flex-1 px-4 py-3 rounded-full bg-gray-100 border-0 focus:ring-2 focus:ring-turquoise focus:bg-white transition-all"
                    />
                    <button
                      type="submit"
                      disabled={!question.trim() || isLoading}
                      className="p-3 bg-turquoise text-white rounded-full disabled:opacity-50 disabled:cursor-not-allowed hover:bg-turquoise-dark transition-colors"
                    >
                      {isLoading ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <Send className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </form>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

