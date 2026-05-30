/**
 * src/services/api.js
 * ====================
 * API service layer for Nyaya Mitra.
 * All fetch calls go through here — easy to mock for tests.
 *
 * BYOK Security notes:
 *  - The key is passed per-call, never cached at module level.
 *  - It is sent only in the Authorization header, not in the request body.
 *  - It is never logged or stored in the service layer.
 */
import { LEGAL_QUERY_URL, HEALTH_URL } from '../config/api';

/**
 * Send a legal query to the Nyaya Mitra backend.
 *
 * @param {string} query     - The user's legal question (max 1000 chars)
 * @param {string} [apiKey]  - Optional Gemini API key (BYOK). If omitted,
 *                             server will use its own key if configured.
 * @returns {Promise<{explanation, citations, suggested_next_steps, retrieval_note}>}
 */
export async function sendLegalQuery(query, apiKey) {
  const headers = { 'Content-Type': 'application/json' };

  // Attach BYOK key only if provided — never send an empty Authorization header
  if (apiKey && apiKey.trim() !== '') {
    headers['Authorization'] = `Bearer ${apiKey.trim()}`;
  }

  const response = await fetch(LEGAL_QUERY_URL, {
    method: 'POST',
    headers,
    body: JSON.stringify({ user_query: query }),
  });

  if (!response.ok) {
    let detail = `Server error: ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch (_) {}
    const err = new Error(detail);
    err.status = response.status;
    throw err;
  }

  return response.json();
}

/**
 * Check backend health / connectivity.
 * Use this for the "Test Connection" button in the BYOK modal.
 *
 * @param {string} [apiKey] - Optional key to validate connectivity
 * @returns {Promise<{status, version, retrieval_mode, chunks_loaded}>}
 */
export async function checkHealth(apiKey) {
  const headers = {};
  if (apiKey && apiKey.trim() !== '') {
    headers['Authorization'] = `Bearer ${apiKey.trim()}`;
  }

  const response = await fetch(HEALTH_URL, { method: 'GET', headers });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}
