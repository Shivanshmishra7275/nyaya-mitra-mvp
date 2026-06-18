'use client';

import { useState, useRef, useEffect } from 'react';
import { 
  Scale, ScrollText, Landmark, BookOpen, Flag, Key, 
  Loader2, Trash2, ExternalLink, Mail, Linkedin, Github, 
  Menu, AlertTriangle, X, WifiOff, Send, ShieldCheck, Zap,
  Lock, Eye
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1'; // Update for production

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [isKeyModalOpen, setKeyModalOpen] = useState(false);
  const [serverStatus, setServerStatus] = useState('checking'); // checking, ok, offline
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [showKeyText, setShowKeyText] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const savedKey = localStorage.getItem('nyaya_mitra_api_key');
    if (savedKey) setApiKey(savedKey);
    checkServer(savedKey);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const checkServer = async (key = apiKey) => {
    setServerStatus('checking');
    try {
      const headers = {};
      if (key) headers['Authorization'] = `Bearer ${key}`;
      
      const res = await fetch('http://localhost:8000/health', { headers }); // Use base health route
      if (res.ok) {
        setServerStatus('ok');
      } else {
        setServerStatus('offline');
      }
    } catch (e) {
      setServerStatus('offline');
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;
    
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;
      
      const res = await fetch(`${API_BASE}/legal-query`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ user_query: userMsg.content })
      });
      
      if (!res.ok) {
         if (res.status === 401) throw new Error('API Key required or invalid.');
         throw new Error(`Server error: ${res.status}`);
      }
      
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'ai', content: data }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'error', content: e.message }]);
    } finally {
      setIsTyping(false);
    }
  };

  const clearChat = () => setMessages([]);
  
  const saveKeyLocal = () => {
    localStorage.setItem('nyaya_mitra_api_key', apiKey);
    setKeyModalOpen(false);
    checkServer(apiKey);
  };
  
  const clearKeyLocal = () => {
    localStorage.removeItem('nyaya_mitra_api_key');
    setApiKey('');
  };

  return (
    <div id="app">
      {/* Sidebar */}
      <aside id="sidebar" className={isSidebarOpen ? 'open' : ''}>
        <div className="sidebar-header">
          <div className="logo-icon-box">
            <Scale className="logo-icon" />
          </div>
          <div>
            <h1 className="app-title">Nyaya Mitra</h1>
            <p className="app-subtitle">AI Legal Guide · Indian Law</p>
          </div>
        </div>

        <div className="sidebar-section">
          <h3 className="section-label">Knowledge Base</h3>
          <ul className="coverage-list">
            <li><ScrollText size={18} /> Bharatiya Nyaya Sanhita (BNS)</li>
            <li><Landmark size={18} /> BNSS</li>
            <li><BookOpen size={18} /> Bharatiya Sakshya (BSA)</li>
            <li><Flag size={18} /> Constitution of India</li>
          </ul>
        </div>

        <div className="sidebar-section">
          <h3 className="section-label">API Key</h3>
          <div 
            className={`key-pill ${apiKey ? 'key-set' : 'key-missing'}`} 
            onClick={() => setKeyModalOpen(true)}
          >
            <Key size={16} /> <span>{apiKey ? 'Key Saved' : 'No key — tap to add'}</span>
          </div>
        </div>

        <div className="sidebar-section">
          <h3 className="section-label">Server Status</h3>
          <div className="server-pill">
            {serverStatus === 'checking' && <Loader2 size={16} className="spin" />}
            {serverStatus === 'ok' && <span style={{color: '#86EFAC'}}>● Online</span>}
            {serverStatus === 'offline' && <span style={{color: '#FCA5A5'}}>● Offline</span>}
          </div>
        </div>

        <div className="sidebar-actions">
          <button className="btn-ghost" onClick={clearChat}><Trash2 size={16} /> Clear Chat</button>
          <a href="https://aistudio.google.com/app/apikey" target="_blank" className="btn-ghost">
            <ExternalLink size={16} /> Get Free API Key
          </a>
        </div>
      </aside>

      {/* Main content */}
      <main id="main">
        <header id="mobile-header">
          <button id="menu-btn" onClick={() => setSidebarOpen(!isSidebarOpen)}>
            <Menu />
          </button>
          <div className="mobile-title-wrap">
            <Scale className="mobile-logo-icon" size={20} />
            <span className="app-title">Nyaya Mitra</span>
          </div>
        </header>

        {serverStatus === 'offline' && (
          <div id="offline-banner" className="offline-banner">
            <div className="banner-content">
              <WifiOff size={18} />
              <span>Cannot reach server. Ensure backend is running.</span>
            </div>
            <button onClick={() => checkServer()} className="btn-sm">Retry</button>
          </div>
        )}

        <div id="chat-messages">
          {messages.length === 0 && (
             <div className="ai-card" style={{margin: 'auto'}}>
                <div className="card-header">
                  <span className="card-badge">Namaste 🙏</span>
                </div>
                <div className="explanation">
                  I am Nyaya Mitra, your AI legal guide for Indian criminal law. Ask me about BNS, BNSS, BSA, or the Constitution.
                </div>
             </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`msg-${msg.role}`}>
              {msg.role === 'user' && <div className="user-bubble">{msg.content}</div>}
              {msg.role === 'error' && (
                <div className="error-card">
                  <div className="error-badge">ERROR</div>
                  <div className="error-text">{msg.content}</div>
                </div>
              )}
              {msg.role === 'ai' && (
                <div className="ai-card">
                  <div className="card-header">
                    <span className="card-badge">Nyaya Mitra AI</span>
                  </div>
                  <div className="explanation">{msg.content.answer || msg.content.explanation}</div>
                  
                  {msg.content.legal_mapping?.length > 0 && (
                    <>
                      <hr className="section-divider" />
                      <div className="section-title">Legal Sections Applicable</div>
                      <div className="citations-row">
                        {msg.content.legal_mapping.map((c, j) => (
                          <span key={j} className="citation-pill">{c}</span>
                        ))}
                      </div>
                    </>
                  )}
                  
                  {msg.content.next_actions?.length > 0 && (
                    <>
                      <hr className="section-divider" />
                      <div className="section-title">Suggested Next Steps</div>
                      <ul style={{fontSize: '14px', color: 'var(--text-secondary)', paddingLeft: '20px'}}>
                        {msg.content.next_actions.map((act, j) => <li key={j} style={{marginBottom: '4px'}}>{act}</li>)}
                      </ul>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
          {isTyping && (
            <div className="msg-typing">
              <div className="typing-bubble">
                <div className="spinner"></div> Nyaya Mitra is thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div id="input-area">
          <div id="input-wrapper">
            <textarea
              id="query-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a legal question... (e.g. 'Punishment for theft?')"
              rows={1}
            />
            <button id="send-btn" onClick={handleSend} disabled={!input.trim() || isTyping}>
              <Send size={20} />
            </button>
          </div>
        </div>
      </main>

      {/* API Key Modal */}
      {isKeyModalOpen && (
        <div className="modal-overlay" onClick={() => setKeyModalOpen(false)}>
          <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-icon-box"><Key size={24} /></div>
              <h2>Gemini API Key</h2>
            </div>
            
            <div className="api-explainer">
              <div className="explainer-step">
                <div className="step-icon"><ShieldCheck size={20} /></div>
                <div className="step-text">
                  <h4>Private & Secure</h4>
                  <p>Stored locally, sent directly to Gemini API.</p>
                </div>
              </div>
            </div>

            <div className="key-input-row" style={{marginBottom: '20px'}}>
              <Lock className="input-icon" size={18} />
              <input
                type={showKeyText ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="AIzaSy..."
                style={{flex: 1, background: 'transparent', border: 'none', color: 'white', padding: '10px'}}
              />
              <button onClick={() => setShowKeyText(!showKeyText)} style={{background: 'transparent', color: 'white', padding: '10px'}}>
                <Eye size={18} />
              </button>
            </div>

            <div className="modal-actions" style={{display: 'flex', gap: '10px'}}>
              <button className="btn-primary" onClick={saveKeyLocal} style={{flex: 1}}>Save & Close</button>
              <button className="btn-ghost" onClick={clearKeyLocal}>Clear</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
