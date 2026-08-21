'use client';

import { useState } from 'react';
import styles from '@/app/home.module.css';
import { askQuestion } from '@/lib/api';
import { CURRENT_FISCAL_YEAR } from '@/lib/fiscal-year';
import type { AskResponse } from '@/types';

type ChatMessage = {
  role: 'assistant' | 'user';
  content: string;
};

const INTRO_MESSAGE =
  'Good day. I can answer questions about the Bahamas national budget — spending by ministry, revenue sources, debt, the historic surplus, and more. Every answer cites the official document it came from. What would you like to understand?';

const EXAMPLE_QUESTIONS = [
  'Where does the education budget actually go?',
  'Why is the national debt about $11.1 billion?',
  'Which ministry allocation grew the most this year?',
  "What does the surplus mean for this year's spending?",
];

const PRO_QUESTIONS = [
  'What is the debt-to-GDP trajectory over the past 5 years?',
  'Revenue composition breakdown by source',
  'Contingency fund allocation and usage',
  'Capital vs recurrent expenditure split',
];

const QUICK_PROMPTS = [
  'Where does the money go?',
  'Explain the surplus',
  'National debt breakdown',
  'Education spending',
];

export default function V2AskBudgetPanel() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: INTRO_MESSAGE },
  ]);
  const [loading, setLoading] = useState(false);

  const handleExampleClick = (text: string) => {
    setQuestion(text);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    const userMessage: ChatMessage = { role: 'user', content: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res: AskResponse = await askQuestion(trimmed, CURRENT_FISCAL_YEAR);
      const answer = res.answer ?? 'No answer returned.';
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: answer },
      ]);
    } catch (err) {
      const fallback =
        err instanceof Error ? err.message : 'Failed to retrieve an answer.';
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `I'm having trouble connecting to the budget assistant right now. You can still explore the dashboard or source documents directly.\n\nDetails: ${fallback}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderMessage = (msg: ChatMessage, index: number) => {
    const isAssistant = msg.role === 'assistant';
    return (
      <div
        key={index}
        className={`${styles.msg} ${
          isAssistant ? styles['msg-ai'] : styles['msg-user']
        }`}
      >
        <div
          className={`${styles['msg-av']} ${
            isAssistant ? styles['msg-av-ai'] : styles['msg-av-user']
          }`}
        >
          {isAssistant ? 'B' : '👤'}
        </div>
        <div
          className={`${styles['msg-bub']} ${
            isAssistant ? styles['msg-bub-ai'] : styles['msg-bub-user']
          }`}
        >
          {msg.content}
        </div>
      </div>
    );
  };

  return (
    <section className={styles['ask-section']} id="ask">
      <div className={styles['ask-left']}>
        <div className={styles['section-eyebrow']}>Ask the Budget</div>
        <h2 className={styles['section-title']}>
          Every number has
          <br />
          a <em>source document.</em>
        </h2>
        <p className={styles['ask-desc']}>
          Ask anything about the Bahamian national budget. The AI retrieves from
          official Parliament documents — Budget Communication, Estimates of
          Expenditure, Debt Reports — before generating any answer. Sources
          shown with every response.
        </p>
        <ul className={styles['ask-examples']}>
          {EXAMPLE_QUESTIONS.map((q) => (
            <li
              key={q}
              className={styles['ask-example']}
              onClick={() => handleExampleClick(q)}
            >
              {q}
            </li>
          ))}
        </ul>
        <div className={styles['ask-for-pros']}>
          <div className={styles['afp-label']}>For analysts &amp; journalists</div>
          <div className={styles['afp-links']}>
            {PRO_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                className={styles['afp-link']}
                onClick={() => handleExampleClick(q)}
              >
                {q.split('?')[0]}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className={styles['ask-chat']}>
        <div className={styles['chat-header']}>
          <div className={styles['chat-h-left']}>
            <span className={styles['chat-h-eyebrow']}>
              Budget AI · FY{CURRENT_FISCAL_YEAR}
            </span>
            <span className={styles['chat-h-name']}>
              Ask the national budget
            </span>
          </div>
          <div className={styles['chat-status']}>
            <div className={styles['status-dot']} />
            RAG connected
          </div>
        </div>

        <div className={styles['chat-messages']}>
          {messages.map(renderMessage)}
          {loading && (
            <div className={`${styles.msg} ${styles['msg-ai']}`}>
              <div
                className={`${styles['msg-av']} ${styles['msg-av-ai']}`}
              >
                B
              </div>
              <div
                className={`${styles['msg-bub']} ${styles['msg-bub-ai']}`}
              >
                Thinking…
              </div>
            </div>
          )}
        </div>

        <div className={styles['quick-prompts']}>
          {QUICK_PROMPTS.map((q) => (
            <button
              key={q}
              type="button"
              className={styles.qp}
              onClick={() => handleExampleClick(q)}
            >
              {q}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className={styles['chat-input-row']}>
          <textarea
            className={styles['chat-input']}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about the national budget…"
            rows={1}
          />
          <button
            type="submit"
            className={styles['chat-send']}
            disabled={loading || !question.trim()}
          >
            ➤
          </button>
        </form>
        <div className={styles['chat-disclaimer']}>
          All figures sourced from official Bahamas Budget {CURRENT_FISCAL_YEAR}{' '}
          documents presented to Parliament.
        </div>
      </div>
    </section>
  );
}

