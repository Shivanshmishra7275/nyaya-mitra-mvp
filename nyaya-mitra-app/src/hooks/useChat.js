/**
 * src/hooks/useChat.js
 * =====================
 * Custom hook encapsulating chat state, history persistence, and API calls.
 * Keeps ChatScreen clean and focused on rendering only.
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { sendLegalQuery } from '../services/api';

const HISTORY_STORAGE_KEY = '@nyaya_mitra_chat_history';
const MAX_STORED_MESSAGES = 100; // Prevent unbounded storage growth

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  content: {
    explanation:
      'Namaste 🙏  I am Nyaya Mitra, your AI legal guide for Indian law.\n\n' +
      'I can answer questions about:\n' +
      '• Bharatiya Nyaya Sanhita (BNS)\n' +
      '• Bharatiya Nagarik Suraksha Sanhita (BNSS)\n' +
      '• Bharatiya Sakshya Adhiniyam (BSA)\n' +
      '• Constitution of India\n\n' +
      '⚠️ DISCLAIMER: I provide legal information, not legal advice. ' +
      'Always consult a qualified lawyer for your specific situation.',
    citations: [],
    suggested_next_steps: ['Type your legal question below and tap Send.'],
    retrieval_note: null,
  },
};

export function useChat(apiKey) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastQuery, setLastQuery] = useState('');
  const flatListRef = useRef(null);
  const historyLoaded = useRef(false);
  // Keep a ref to lastQuery so retryLast never goes stale
  const lastQueryRef = useRef('');

  // ── Load persisted history on mount ──────────────────────────────────────
  useEffect(() => {
    if (historyLoaded.current) return;
    historyLoaded.current = true;

    AsyncStorage.getItem(HISTORY_STORAGE_KEY)
      .then((stored) => {
        if (stored) {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed) && parsed.length > 0) {
            // Prepend welcome message if not already present
            const hasWelcome = parsed[0]?.id === 'welcome';
            setMessages(hasWelcome ? parsed : [WELCOME_MESSAGE, ...parsed]);
          }
        }
      })
      .catch((e) => console.warn('Failed to load chat history:', e));
  }, []);

  // ── Persist history on change ─────────────────────────────────────────────
  const persistMessages = useCallback((msgs) => {
    const toStore = msgs.slice(-MAX_STORED_MESSAGES);
    AsyncStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(toStore)).catch((e) =>
      console.warn('Failed to save chat history:', e)
    );
  }, []);

  // ── Send a query ─────────────────────────────────────────────────────────
  const sendMessage = useCallback(
    async (query) => {
      const trimmed = query.trim();
      if (!trimmed || isLoading) return;

      setLastQuery(trimmed);
      lastQueryRef.current = trimmed;

      const userMsg = {
        id: `u-${Date.now()}`,
        role: 'user',
        content: trimmed,
      };

      setMessages((prev) => {
        const next = [...prev, userMsg];
        persistMessages(next);
        return next;
      });
      setIsLoading(true);

      try {
        const data = await sendLegalQuery(trimmed, apiKey);
        const aiMsg = {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: data,
        };
        setMessages((prev) => {
          const next = [...prev, aiMsg];
          persistMessages(next);
          return next;
        });
      } catch (error) {
        const errMsg = {
          id: `e-${Date.now()}`,
          role: 'error',
          content: buildErrorMessage(error),
        };
        setMessages((prev) => {
          const next = [...prev, errMsg];
          persistMessages(next);
          return next;
        });
      } finally {
        setIsLoading(false);
        // Scroll to bottom
        setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
      }
    },
    [isLoading, apiKey, persistMessages]
  );

  // ── Retry last query — uses ref to avoid stale closure ───────────────────
  const retryLast = useCallback(() => {
    if (lastQueryRef.current) sendMessage(lastQueryRef.current);
  }, [sendMessage]);

  // ── Clear chat ────────────────────────────────────────────────────────────
  const clearChat = useCallback(() => {
    const fresh = [WELCOME_MESSAGE];
    setMessages(fresh);
    setLastQuery('');
    lastQueryRef.current = '';
    AsyncStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(fresh)).catch(() => {});
  }, []);

  return {
    messages,
    isLoading,
    lastQuery,
    flatListRef,
    sendMessage,
    retryLast,
    clearChat,
  };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildErrorMessage(error) {
  if (error.status === 401) {
    return (
      '🔑 API key required.\n\n' +
      'Please enter your Gemini API key using the key icon (🔑) at the top of the screen.\n\n' +
      'Get a free key at: https://aistudio.google.com/app/apikey'
    );
  }
  if (error.status === 503) {
    return '⚙️ The server is starting up or the legal database is not ready. Please wait a moment and try again.';
  }
  if (error.status === 404) {
    return '🔍 No relevant legal information found for your query. Try rephrasing your question.';
  }
  if (error.message?.includes('Network request failed') || error.message?.includes('Failed to fetch')) {
    return (
      '📡 Cannot reach the Nyaya Mitra server.\n\n' +
      'Please check:\n' +
      '• Is the backend running? (uvicorn app.main:app --reload)\n' +
      '• Is the API URL correct? (Check EXPO_PUBLIC_API_BASE_URL)'
    );
  }
  return `⚠️ Error: ${error.message || 'An unexpected error occurred.'}`;
}
