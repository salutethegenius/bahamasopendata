'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Send, X, FileText, BarChart3, Loader2 } from 'lucide-react';
import { AskResponse } from '@/types';
import { formatCurrency } from '@/lib/format';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

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
    try {
      const result = await onAsk(question);
      setResponse(result);
    } catch (error) {
      console.error('Failed to get answer:', error);
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
    "Compare health vs education spending",
    "How much VAT was collected?",
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
        <span className="font-medium hidden sm:inline">Ask about the budget</span>
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
                <h2 className="text-lg font-semibold text-gray-900">Ask about the budget</h2>
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
                      Ask me anything about the Bahamas budget, spending, revenue, or debt.
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
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-gray-900 leading-relaxed">{response.answer}</p>
                    </div>

                    {/* Numbers */}
                    {response.numbers && Object.keys(response.numbers).length > 0 && (
                      <div className="grid grid-cols-2 gap-3">
                        {Object.entries(response.numbers).map(([key, value]) => (
                          <div key={key} className="bg-white border border-gray-200 rounded-lg p-3">
                            <p className="text-xs text-gray-500 capitalize">
                              {key.replace(/_/g, ' ')}
                            </p>
                            <p className="text-lg font-bold text-turquoise tabular-nums">
                              {typeof value === 'number' && value > 1000
                                ? formatCurrency(value, true)
                                : value}
                            </p>
                          </div>
                        ))}
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
                      <div className="border-t border-gray-200 pt-4">
                        <p className="text-xs font-medium text-gray-500 mb-2">Sources</p>
                        {response.citations.map((citation, i) => (
                          <a
                            key={i}
                            href={citation.url || '#'}
                            className="flex items-center gap-2 text-sm text-gray-600 hover:text-turquoise py-1"
                          >
                            <FileText className="w-4 h-4" />
                            <span>{citation.document}, page {citation.page}</span>
                          </a>
                        ))}
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
                      placeholder="Ask about spending, revenue, or debt..."
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

