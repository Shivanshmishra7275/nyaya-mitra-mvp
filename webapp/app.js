/**
 * Nyaya Mitra Web App — app.js
 * ==============================
 * Pure vanilla JS — no framework needed.
 * All communication goes through the user's configured backend.
 *
 * BYOK Flow:
 *   1. User enters Gemini API key in modal → stored in memory (session only) or localStorage (opt-in).
 *   2. Every legal query sends the key as: Authorization: Bearer <key>
 *   3. Key is NEVER sent to any server other than the user's own Nyaya Mitra backend.
 *   4. The backend forwards it to Google Gemini API per-request and discards it immediately.
 *
 * Zero cost:
 *   - This file is static HTML/CSS/JS — host anywhere for free (GitHub Pages, Netlify, etc.)
 *   - Backend runs on Render free tier (or any host)
 *   - Gemini API cost is 100% on the user's key
 */

'use strict';

// ─── Constants ───────────────────────────────────────────────────────────────

const STORAGE_KEY_API     = 'nyaya_mitra_api_key';
const STORAGE_KEY_API_URL = 'nyaya_mitra_api_url';
const STORAGE_KEY_HISTORY = 'nyaya_mitra_chat_history';
const MAX_HISTORY         = 80;  // max messages to persist
const HEALTH_POLL_MS      = 30_000;  // 30 second server health poll

// Default API base — override in sidebar input or set before deploying
const DEFAULT_API_BASE = (() => {
  // If served via file:// or localhost, point to local backend
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  // Production: point to your deployed backend URL
  // Update this if you have a deployed backend on Render/Railway etc.
  return 'http://localhost:8000';
})();

// ─── State ───────────────────────────────────────────────────────────────────

let state = {
  apiKey:     '',
  apiBaseUrl: '',
  messages:   [],        // { id, role: 'user'|'assistant'|'error', content }
  isLoading:  false,
  lastQuery:  '',
  serverHealthy: null,   // null | true | false
  healthTimer: null,
};

// ─── Init ────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Load persisted state
  state.apiKey     = loadApiKey();
  state.apiBaseUrl = localStorage.getItem(STORAGE_KEY_API_URL) || DEFAULT_API_BASE;
  state.messages   = loadHistory();

  // Render sidebar API URL input
  renderSidebarExtras();

  // Render saved messages or welcome screen
  if (state.messages.length === 0) {
    renderWelcome();
  } else {
    state.messages.forEach(renderMessage);
    scrollToBottom();
  }

  // Update key pill
  updateKeyPill();

  // Start health polling
  checkServer();
  state.healthTimer = setInterval(checkServer, HEALTH_POLL_MS);

  // Wire input events
  const input = document.getElementById('query-input');
  input.addEventListener('input', () => {
    const len = input.value.length;
    document.getElementById('char-count').textContent = `${len} / 1000`;
    document.getElementById('send-btn').disabled = len < 3 || state.isLoading;
  });

  // Initialize Lucide icons
  lucide.createIcons();
});

// ─── Sidebar extras (API URL config) ─────────────────────────────────────────

function renderSidebarExtras() {
  const section = document.createElement('div');
  section.id = 'api-url-section';
  section.className = 'sidebar-section';
  section.innerHTML = `
    <h3 class="section-label">BACKEND URL</h3>
    <input
      type="text"
      class="api-url-input"
      id="api-url-input"
      placeholder="http://localhost:8000"
      value="${escHtml(state.apiBaseUrl)}"
      onchange="updateApiUrl(this.value)"
      spellcheck="false"
      autocomplete="off"
    />
    <p class="sidebar-hint" style="margin-top:6px">
      Change this to your Render URL or LAN IP for mobile access.
    </p>
  `;
  // Insert before sidebar-actions
  const actions = document.querySelector('.sidebar-actions');
  document.getElementById('sidebar').insertBefore(section, actions);
}

function updateApiUrl(val) {
  const trimmed = val.trim().replace(/\/$/, ''); // remove trailing slash
  state.apiBaseUrl = trimmed || DEFAULT_API_BASE;
  localStorage.setItem(STORAGE_KEY_API_URL, state.apiBaseUrl);
  checkServer(); // immediately re-check with new URL
}

// ─── Server health ────────────────────────────────────────────────────────────

async function checkServer() {
  const dot  = document.getElementById('server-dot');
  const text = document.getElementById('server-text');
  const mob  = document.getElementById('mobile-server-dot');

  try {
    const url     = `${state.apiBaseUrl}/health`;
    const headers = {};
    if (state.apiKey) headers['Authorization'] = `Bearer ${state.apiKey}`;

    const res = await fetch(url, {
      method: 'GET',
      headers,
      signal: AbortSignal.timeout(8000),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    state.serverHealthy = true;
    dot.className = 'server-icon';
    dot.setAttribute('data-lucide', 'check-circle-2');
    dot.style.color = 'var(--success-text)';
    
    mob.innerHTML = '<i data-lucide="check-circle-2" style="color:var(--success-text)"></i>';
    text.textContent = `${data.retrieval_mode || 'Ready'} · ${data.chunks_loaded ?? 0} chunks`;
    document.getElementById('offline-banner').classList.add('hidden');
    lucide.createIcons();

  } catch (err) {
    state.serverHealthy = false;
    dot.className = 'server-icon';
    dot.setAttribute('data-lucide', 'x-circle');
    dot.style.color = 'var(--error-text)';
    
    mob.innerHTML = '<i data-lucide="x-circle" style="color:var(--error-text)"></i>';
    text.textContent = 'Unreachable';
    document.getElementById('offline-banner').classList.remove('hidden');
    lucide.createIcons();
  }
}

// ─── Chat rendering ───────────────────────────────────────────────────────────

function renderWelcome() {
  const container = document.getElementById('chat-messages');
  const card = document.createElement('div');
  card.className = 'welcome-card';
  card.innerHTML = `
    <div class="welcome-logo-box"><i data-lucide="scale"></i></div>
    <div class="welcome-title">Namaste 🙏 I am Nyaya Mitra</div>
    <div class="welcome-subtitle">
      Your AI legal guide for Indian law. I can provide insights based on:
    </div>
    <div class="welcome-grid">
      <div class="welcome-chip" onclick="document.getElementById('query-input').value='What is the punishment for theft under BNS?'; document.getElementById('query-input').focus()">
        <div class="chip-icon"><i data-lucide="scroll-text"></i></div>
        <div class="chip-title">BNS (Sanhita)</div>
        <div class="chip-desc">Bharatiya Nyaya Sanhita — the criminal code of India.</div>
      </div>
      <div class="welcome-chip" onclick="document.getElementById('query-input').value='What are the rules for an arrest under BNSS?'; document.getElementById('query-input').focus()">
        <div class="chip-icon"><i data-lucide="landmark"></i></div>
        <div class="chip-title">BNSS</div>
        <div class="chip-desc">Bharatiya Nagarik Suraksha Sanhita — criminal procedure.</div>
      </div>
      <div class="welcome-chip" onclick="document.getElementById('query-input').value='What constitutes electronic evidence under BSA?'; document.getElementById('query-input').focus()">
        <div class="chip-icon"><i data-lucide="book-open"></i></div>
        <div class="chip-title">BSA</div>
        <div class="chip-desc">Bharatiya Sakshya Adhiniyam — the rules of evidence.</div>
      </div>
      <div class="welcome-chip" onclick="document.getElementById('query-input').value='What are the fundamental rights in the Constitution?'; document.getElementById('query-input').focus()">
        <div class="chip-icon"><i data-lucide="flag"></i></div>
        <div class="chip-title">Constitution</div>
        <div class="chip-desc">The supreme law and fundamental rights of India.</div>
      </div>
    </div>
    <div class="welcome-disclaimer">
      <i data-lucide="alert-triangle"></i>
      <span>I provide legal <strong>information</strong>, not legal advice. Always consult a qualified lawyer for your specific situation.</span>
    </div>
  `;
  container.appendChild(card);
  lucide.createIcons();
}

function renderMessage(msg) {
  const container = document.getElementById('chat-messages');

  if (msg.role === 'user') {
    const wrapper = document.createElement('div');
    wrapper.className = 'msg-user';
    wrapper.id = `msg-${msg.id}`;
    wrapper.innerHTML = `<div class="user-bubble">${escHtml(msg.content)}</div>`;
    container.appendChild(wrapper);
    return;
  }

  if (msg.role === 'error') {
    const wrapper = document.createElement('div');
    wrapper.className = 'msg-ai';
    wrapper.id = `msg-${msg.id}`;
    wrapper.innerHTML = `
      <div class="error-card">
        <div class="error-badge"><i data-lucide="alert-circle" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-right:4px;"></i> ERROR</div>
        <div class="error-text">${escHtml(msg.content)}</div>
        <button class="retry-btn" onclick="retryLast()"><i data-lucide="refresh-cw" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-right:4px;"></i> Retry</button>
      </div>
    `;
    container.appendChild(wrapper);
    lucide.createIcons();
    return;
  }

  // Assistant message
  const content = msg.content;
  const wrapper = document.createElement('div');
  wrapper.className = 'msg-ai';
  wrapper.id = `msg-${msg.id}`;

  const explanation = content.explanation || '';
  const citations   = (content.citations || []).filter(c => typeof c === 'string' && c.trim());
  const steps       = (content.suggested_next_steps || []).filter(s => typeof s === 'string' && s.trim());
  const note        = content.retrieval_note || '';

  let citationsHtml = '';
  if (citations.length) {
    citationsHtml = `
      <hr class="section-divider"/>
      <div class="section-title">📜 CITED SOURCES</div>
      <div class="citations-row">
        ${citations.map(c => `<span class="citation-pill">${escHtml(c)}</span>`).join('')}
      </div>
    `;
  }

  let stepsHtml = '';
  if (steps.length) {
    stepsHtml = `
      <hr class="section-divider"/>
      <div class="section-title">✅ SUGGESTED NEXT STEPS</div>
      <div class="steps-list">
        ${steps.map((s, i) => `
          <div class="step-row">
            <div class="step-num">${i + 1}</div>
            <div class="step-text">${escHtml(s)}</div>
          </div>
        `).join('')}
      </div>
    `;
  }

  let noteHtml = note ? `<div class="retrieval-note">🔍 ${escHtml(note)}</div>` : '';

  // Unique ID for copy btn
  const copyId = `copy-${msg.id}`;

  wrapper.innerHTML = `
    <div class="ai-card">
      <div class="card-header">
        <span class="card-badge"><i data-lucide="scale" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-right:4px;"></i> NYAYA MITRA</span>
        <button class="copy-btn" id="${copyId}" onclick="copyAnswer('${msg.id}', '${copyId}')"><i data-lucide="copy" style="width:14px;height:14px;"></i> Copy</button>
      </div>
      <div class="disclaimer-pill"><i data-lucide="alert-triangle" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-right:4px;"></i> Legal information only — not legal advice. Consult a lawyer.</div>
      <div class="explanation">${escHtml(explanation)}</div>
      ${citationsHtml}
      ${stepsHtml}
      ${noteHtml}
    </div>
  `;

  // Store for copy
  wrapper.dataset.explanation = explanation;
  wrapper.dataset.citations   = JSON.stringify(citations);
  wrapper.dataset.steps       = JSON.stringify(steps);

  container.appendChild(wrapper);
  lucide.createIcons();
}

function renderTypingIndicator() {
  const container = document.getElementById('chat-messages');
  const el = document.createElement('div');
  el.id = 'typing-indicator';
  el.className = 'msg-typing';
  el.innerHTML = `<div class="typing-bubble"><div class="spinner"></div> Nyaya Mitra is thinking…</div>`;
  container.appendChild(el);
  scrollToBottom();
}

function removeTypingIndicator() {
  document.getElementById('typing-indicator')?.remove();
}

// ─── Send message ─────────────────────────────────────────────────────────────

async function sendMessage() {
  const input   = document.getElementById('query-input');
  const sendBtn = document.getElementById('send-btn');
  const query   = input.value.trim();

  if (!query || state.isLoading) return;

  if (!state.apiKey) {
    openKeyModal();
    return;
  }

  // User message
  const userMsg = { id: `u-${Date.now()}`, role: 'user', content: query };
  state.messages.push(userMsg);
  renderMessage(userMsg);
  saveHistory();

  state.lastQuery = query;
  input.value = '';
  input.style.height = 'auto';
  document.getElementById('char-count').textContent = '0 / 1000';

  // Loading state
  state.isLoading = true;
  sendBtn.disabled = true;
  renderTypingIndicator();
  scrollToBottom();

  try {
    const data = await callLegalQuery(query);
    const aiMsg = { id: `a-${Date.now()}`, role: 'assistant', content: data };
    state.messages.push(aiMsg);
    removeTypingIndicator();
    renderMessage(aiMsg);
    saveHistory();

  } catch (err) {
    removeTypingIndicator();
    const errMsg = { id: `e-${Date.now()}`, role: 'error', content: buildErrorMessage(err) };
    state.messages.push(errMsg);
    renderMessage(errMsg);
    saveHistory();

  } finally {
    state.isLoading = false;
    sendBtn.disabled = query.length < 3;
    scrollToBottom();
  }
}

function retryLast() {
  if (!state.lastQuery || state.isLoading) return;
  const input = document.getElementById('query-input');
  input.value = state.lastQuery;
  sendMessage();
}

function handleKeyDown(e) {
  // Send on Enter (but not Shift+Enter)
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ─── API call ─────────────────────────────────────────────────────────────────

async function callLegalQuery(query) {
  const url     = `${state.apiBaseUrl}/api/v1/legal-query`;
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${state.apiKey}`,
  };

  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ user_query: query }),
    signal: AbortSignal.timeout(45000),
  });

  if (!res.ok) {
    let detail = `Server error: ${res.status}`;
    try { detail = (await res.json()).detail || detail; } catch (_) {}
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

// ─── Error messages ───────────────────────────────────────────────────────────

function buildErrorMessage(err) {
  if (err.name === 'TimeoutError' || err.name === 'AbortError') {
    return '⏱ Request timed out. The server may be slow or unreachable. Please try again.';
  }
  if (err.status === 401) {
    return '🔑 API key required.\n\nPlease enter your Gemini API key using the key icon in the sidebar.\n\nGet a free key at: aistudio.google.com/app/apikey';
  }
  if (err.status === 503) {
    return '⚙️ The server is starting up or the legal database is not ready. Please wait a moment and try again.';
  }
  if (err.status === 404) {
    return '🔍 No relevant legal information found for your query. Try rephrasing your question.';
  }
  if (err.message?.includes('Failed to fetch') || err.message?.includes('NetworkError')) {
    return `📡 Cannot reach the Nyaya Mitra server.\n\nPlease check:\n• Is the backend running?\n• Is the Backend URL correct? (Check sidebar)\n• Current URL: ${state.apiBaseUrl}`;
  }
  return `⚠️ ${err.message || 'An unexpected error occurred.'}`;
}

// ─── API Key modal ────────────────────────────────────────────────────────────

function openKeyModal() {
  document.getElementById('api-key-input').value = state.apiKey;
  document.getElementById('persist-checkbox').checked = !!localStorage.getItem(STORAGE_KEY_API);
  document.getElementById('test-result').classList.add('hidden');
  document.getElementById('key-modal').classList.remove('hidden');
  setTimeout(() => document.getElementById('api-key-input').focus(), 100);
}

function closeKeyModal() {
  document.getElementById('key-modal').classList.add('hidden');
}

function closeModalOnOverlay(e) {
  if (e.target === e.currentTarget) closeKeyModal();
}

function toggleKeyVisibility() {
  const input = document.getElementById('api-key-input');
  const btn   = document.getElementById('toggle-eye');
  if (input.type === 'password') {
    input.type = 'text';
    btn.innerHTML = '<i data-lucide="eye-off"></i>';
  } else {
    input.type = 'password';
    btn.innerHTML = '<i data-lucide="eye"></i>';
  }
  lucide.createIcons();
}

async function testConnection() {
  const key    = document.getElementById('api-key-input').value.trim();
  const btn    = document.getElementById('test-btn');
  const result = document.getElementById('test-result');

  if (!key) {
    result.className = 'test-result test-err';
    result.textContent = '✗ Please enter an API key first.';
    result.classList.remove('hidden');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Testing…';
  result.classList.add('hidden');

  try {
    const url = `${state.apiBaseUrl}/health`;
    const res = await fetch(url, {
      headers: { 'Authorization': `Bearer ${key}` },
      signal: AbortSignal.timeout(10000),
    });
    const data = await res.json();
    result.className = 'test-result test-ok';
    result.textContent = `✓ Connected!\nServer: ${data.status}\nRetrieval: ${data.retrieval_mode}\nChunks: ${data.chunks_loaded}`;
  } catch (err) {
    result.className = 'test-result test-err';
    result.textContent = `✗ ${err.message}`;
  } finally {
    result.classList.remove('hidden');
    btn.disabled = false;
    btn.textContent = 'Test Connection';
  }
}

function saveKey() {
  const key     = document.getElementById('api-key-input').value.trim();
  const persist = document.getElementById('persist-checkbox').checked;

  state.apiKey = key;

  if (persist && key) {
    localStorage.setItem(STORAGE_KEY_API, key);
  } else {
    localStorage.removeItem(STORAGE_KEY_API);
  }

  updateKeyPill();
  closeKeyModal();

  // Re-check server health with new key
  checkServer();
}

function clearKey() {
  state.apiKey = '';
  document.getElementById('api-key-input').value = '';
  localStorage.removeItem(STORAGE_KEY_API);
  updateKeyPill();
  closeKeyModal();
}

function loadApiKey() {
  return localStorage.getItem(STORAGE_KEY_API) || '';
}

function updateKeyPill() {
  const pill    = document.getElementById('key-status-pill');
  const pillTxt = document.getElementById('key-status-text');
  if (state.apiKey) {
    pill.className = 'key-pill key-set';
    pillTxt.innerHTML = `<i data-lucide="check" style="width:14px;height:14px;vertical-align:middle;margin-right:4px;"></i> Key set (${state.apiKey.slice(0, 6)}…)`;
  } else {
    pill.className = 'key-pill key-missing';
    pillTxt.innerHTML = `<i data-lucide="key" style="width:14px;height:14px;vertical-align:middle;margin-right:4px;"></i> No key — tap to add`;
  }
  lucide.createIcons();
}

// ─── Chat management ──────────────────────────────────────────────────────────

function clearChat() {
  if (!confirm('Clear all chat messages? This cannot be undone.')) return;
  state.messages = [];
  state.lastQuery = '';
  document.getElementById('chat-messages').innerHTML = '';
  saveHistory();
  renderWelcome();
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// ─── Copy answer ──────────────────────────────────────────────────────────────

async function copyAnswer(msgId, btnId) {
  const wrapper = document.getElementById(`msg-${msgId}`);
  if (!wrapper) return;

  const explanation = wrapper.dataset.explanation || '';
  const citations   = JSON.parse(wrapper.dataset.citations || '[]');
  const steps       = JSON.parse(wrapper.dataset.steps || '[]');

  const text = [
    explanation,
    citations.length ? '\nSources:\n' + citations.join('\n') : '',
    steps.length ? '\nNext Steps:\n' + steps.map((s, i) => `${i+1}. ${s}`).join('\n') : '',
  ].filter(Boolean).join('\n');

  try {
    await navigator.clipboard.writeText(text);
    const btn = document.getElementById(btnId);
    if (btn) {
      btn.textContent = '✓ Copied';
      setTimeout(() => { btn.textContent = '⎘ Copy'; }, 2000);
    }
  } catch (_) {
    alert('Could not copy to clipboard. Please select and copy manually.');
  }
}

// ─── Persistence ──────────────────────────────────────────────────────────────

function saveHistory() {
  try {
    const toStore = state.messages.slice(-MAX_HISTORY);
    localStorage.setItem(STORAGE_KEY_HISTORY, JSON.stringify(toStore));
  } catch (_) {}
}

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_HISTORY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (_) {
    return [];
  }
}

// ─── Utils ───────────────────────────────────────────────────────────────────

function escHtml(str) {
  if (typeof str !== 'string') return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/\n/g, '<br/>');
}

function scrollToBottom() {
  const el = document.getElementById('chat-messages');
  requestAnimationFrame(() => {
    el.scrollTop = el.scrollHeight;
  });
}
