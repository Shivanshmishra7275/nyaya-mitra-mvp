/**
 * src/hooks/useServerHealth.js
 * =============================
 * Polls the backend /health endpoint periodically to track server connectivity.
 * Used to surface a connection banner in the UI before the user even tries to send.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { checkHealth } from '../services/api';

const POLL_INTERVAL_MS = 30_000; // Re-check every 30 seconds
const INITIAL_CHECK_DELAY_MS = 1_500; // Brief delay after mount

/**
 * @returns {{ isConnected: boolean|null, serverInfo: object|null, checkNow: function }}
 *   isConnected: null = unknown/checking, true = online, false = unreachable
 *   serverInfo: { status, version, retrieval_mode, chunks_loaded } or null
 *   checkNow: manually trigger an immediate re-check
 */
export function useServerHealth(apiKey) {
  const [isConnected, setIsConnected] = useState(null); // null = initial/unknown
  const [serverInfo, setServerInfo] = useState(null);
  const timerRef = useRef(null);

  const performCheck = useCallback(async () => {
    try {
      const health = await checkHealth(apiKey);
      setIsConnected(true);
      setServerInfo(health);
    } catch (_) {
      setIsConnected(false);
      setServerInfo(null);
    }
  }, [apiKey]);

  useEffect(() => {
    // Initial check after a short delay to avoid blocking render
    const initial = setTimeout(performCheck, INITIAL_CHECK_DELAY_MS);

    // Periodic poll
    timerRef.current = setInterval(performCheck, POLL_INTERVAL_MS);

    return () => {
      clearTimeout(initial);
      clearInterval(timerRef.current);
    };
  }, [performCheck]);

  return { isConnected, serverInfo, checkNow: performCheck };
}
