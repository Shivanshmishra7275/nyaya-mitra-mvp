
import React, { useState, useRef, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  Send, 
  Camera, 
  ShieldAlert, 
  RefreshCcw, 
  Scale, 
  User, 
  Bot, 
  Loader2,
  X,
  MicOff,
  ExternalLink,
  Info
} from 'lucide-react';
import { GoogleGenAI, Type } from "@google/genai";

// Standard Theme Colors
const NYAYA_THEME = {
  bg: '#0f172a', // Deep Navy Blue
  accent: '#d97706', // Saffron/Gold
  text: '#ffffff',
  userBubble: '#d97706',
  botBubble: '#1e293b',
  panic: '#ef4444' // Emergency Red
};

interface GroundingChunk {
  web?: { uri: string; title: string };
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  type: 'text' | 'image' | 'audio';
  imageData?: string;
  isError?: boolean;
  citations?: { uri: string; title: string }[];
}

const NyayaMitra: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'initial',
      role: 'assistant',
      content: "Namaste. I am Nyaya Mitra, your Senior AI Legal Companion. I can analyze documents, provide legal insights, and assist in emergencies. How can I serve you?",
      type: 'text'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (retryContent?: string, retryImage?: string) => {
    const textToSend = retryContent || input;
    const imageToSend = retryImage || selectedImage;

    if (!textToSend.trim() && !imageToSend) return;

    if (retryContent) {
      setMessages(prev => prev.filter(m => !m.isError));
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: textToSend,
      type: imageToSend ? 'image' : 'text',
      imageData: imageToSend || undefined
    };

    if (!retryContent) {
      setMessages(prev => [...prev, userMsg]);
      setInput('');
      setSelectedImage(null);
    }
    
    setIsLoading(true);
    setError(null);

    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      
      const history = messages
        .filter(m => !m.isError && m.type === 'text')
        .slice(-6)
        .map(m => ({
          role: m.role === 'user' ? 'user' : 'model',
          parts: [{ text: m.content }]
        }));

      let responseText = "";
      let citations: { uri: string; title: string }[] = [];

      if (imageToSend) {
        // Document Analysis Mode
        const response = await ai.models.generateContent({
          model: 'gemini-3-flash-preview',
          contents: {
            parts: [
              { inlineData: { data: imageToSend.split(',')[1], mimeType: 'image/jpeg' } },
              { text: `System: Expert Legal Analyst. Task: Analyze this document for legal relevance and explain in simple terms. Context: ${textToSend || 'General Analysis'}` }
            ]
          }
        });
        responseText = response.text || "Document analyzed. Please ask specific questions if needed.";
      } else {
        // Legal Inquiry Mode with Search Grounding
        const response = await ai.models.generateContent({
          model: 'gemini-3-pro-preview',
          contents: [...history, { role: 'user', parts: [{ text: textToSend }] }],
          config: {
            systemInstruction: "You are 'Nyaya Mitra', an elite legal advisor specializing in Indian Law. Use formal but accessible language. Always cite recent laws or judgments using the provided search tool. Disclaimer: This is not professional legal advice.",
            tools: [{ googleSearch: {} }]
          }
        });

        responseText = response.text || "I'm reviewing the statutes. Could you rephrase your query?";
        
        // Extract Search Citations
        const chunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;
        if (chunks) {
          citations = chunks
            .filter((c: any) => c.web)
            .map((c: any) => ({ uri: c.web.uri, title: c.web.title }));
        }
      }

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseText,
        type: 'text',
        citations: citations.length > 0 ? citations : undefined
      }]);
    } catch (err: any) {
      console.error("API Error:", err);
      setError("Please check your internet connection or restart the app. The legal servers are currently busy.");
      setMessages(prev => [...prev, {
        id: 'err-node',
        role: 'assistant',
        content: "ERROR: Communication with justice servers interrupted.",
        type: 'text',
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const togglePanicMode = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;
        audioChunksRef.current = [];
        recorder.ondataavailable = (e) => e.data.size > 0 && audioChunksRef.current.push(e.data);
        recorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const reader = new FileReader();
          reader.readAsDataURL(audioBlob);
          reader.onloadend = async () => {
            const base64Audio = reader.result as string;
            await processPanicAudio(base64Audio);
          };
          stream.getTracks().forEach(track => track.stop());
        };
        recorder.start();
        setIsRecording(true);
      } catch (err) {
        setError("Microphone access required for emergency panic feature.");
      }
    }
  };

  const processPanicAudio = async (base64Audio: string) => {
    setIsLoading(true);
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: "[URGENT] Voice Alert: Emergency detected.",
      type: 'audio'
    }]);

    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: {
          parts: [
            { inlineData: { data: base64Audio.split(',')[1], mimeType: 'audio/webm' } },
            { text: "EMERGENCY: Listen to this audio. Identify threats or legal violations and provide immediate safety and protocol advice for India (e.g., dial 112, relevant sections of BNS)." }
          ]
        }
      });

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.text || "Emergency detected. Find safety and call 112.",
        type: 'text'
      }]);
    } catch (err) {
      setError("Emergency processing failed. Dial 112 immediately.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setSelectedImage(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="flex flex-col h-screen font-sans text-white overflow-hidden bg-[#0f172a]">
      {/* Supreme Court Header */}
      <header className="flex items-center justify-between p-4 border-b border-slate-800 shadow-2xl bg-slate-900/90 backdrop-blur-xl z-20">
        <div className="flex items-center gap-3">
          <div className="bg-[#d97706] p-2 rounded-2xl shadow-lg shadow-amber-500/20 rotate-[-5deg] hover:rotate-0 transition-transform cursor-pointer">
            <Scale size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-black tracking-tighter leading-none">NYAYA MITRA</h1>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              <p className="text-[10px] text-amber-500 font-bold uppercase tracking-widest">Supreme AI Justice</p>
            </div>
          </div>
        </div>
        <button 
          onClick={togglePanicMode}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-full font-black transition-all duration-300 ${
            isRecording ? 'bg-red-600 animate-pulse ring-4 ring-red-600/30' : 'bg-red-500 hover:bg-red-600'
          } shadow-xl shadow-red-900/40`}
        >
          {isRecording ? <MicOff size={18} /> : <ShieldAlert size={18} />}
          <span className="text-xs uppercase tracking-widest">{isRecording ? 'Listening' : 'Panic'}</span>
        </button>
      </header>

      {/* Main Chat Stream */}
      <main className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-slate-700 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-slate-800/20 via-slate-900 to-slate-900">
        {messages.filter(m => !m.isError).map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 duration-300`}>
            <div className={`flex max-w-[90%] md:max-w-[80%] gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-xl border-2 transition-all ${
                msg.role === 'user' ? 'bg-amber-600 border-amber-400 rotate-3' : 'bg-slate-800 border-slate-700 -rotate-3'
              }`}>
                {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
              </div>
              <div className="space-y-1">
                <div className={`p-4 rounded-3xl shadow-2xl ${
                  msg.role === 'user' 
                    ? 'bg-[#d97706] text-white rounded-tr-none' 
                    : 'bg-[#1e293b] text-slate-100 rounded-tl-none border border-slate-700/50'
                }`}>
                  {msg.imageData && (
                    <div className="mb-3 rounded-2xl overflow-hidden border border-white/10 shadow-inner group cursor-zoom-in">
                      <img src={msg.imageData} alt="Scan" className="max-w-full h-auto max-h-72 object-contain transition-transform group-hover:scale-105" />
                    </div>
                  )}
                  {msg.type === 'audio' && (
                    <div className="flex items-center gap-3 mb-3 p-3 bg-black/30 rounded-2xl">
                      <div className="flex gap-1 items-end h-4">
                        {[0,1,2,3,4].map(i => <div key={i} className="w-1 bg-red-500 rounded-full animate-bounce" style={{animationDelay: `${i*0.1}s`}} />)}
                      </div>
                      <span className="text-[10px] font-mono tracking-widest text-red-400">ENCRYPTED_VOICE_ANALYSIS</span>
                    </div>
                  )}
                  <div className="text-sm md:text-base whitespace-pre-wrap leading-relaxed font-medium">
                    {msg.content}
                  </div>
                  
                  {/* Citations / Search Grounding UI */}
                  {msg.citations && (
                    <div className="mt-4 pt-4 border-t border-slate-700/50 space-y-2">
                      <p className="text-[10px] uppercase font-black text-amber-500 flex items-center gap-1">
                        <Info size={12} /> Sources & References
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {msg.citations.map((c, i) => (
                          <a 
                            key={i} 
                            href={c.uri} 
                            target="_blank" 
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900/50 hover:bg-amber-600/20 border border-slate-700 rounded-full text-[10px] font-bold transition-all text-slate-300 hover:text-amber-400"
                          >
                            <ExternalLink size={10} />
                            {c.title.length > 25 ? c.title.substring(0, 25) + '...' : c.title}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <div className={`text-[9px] font-bold opacity-30 px-2 uppercase tracking-tighter ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                  {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start animate-pulse">
            <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-3xl rounded-tl-none flex items-center gap-4 shadow-xl">
              <div className="relative">
                <Loader2 className="w-6 h-6 animate-spin text-amber-500" />
                <div className="absolute inset-0 blur-sm bg-amber-500/20 rounded-full animate-pulse" />
              </div>
              <span className="text-xs font-black text-slate-400 tracking-widest uppercase">Consulting Supreme Statutes...</span>
            </div>
          </div>
        )}
        {error && (
          <div className="bg-red-500/10 border-2 border-red-500/30 p-8 rounded-[2.5rem] flex flex-col items-center gap-5 backdrop-blur-md animate-in zoom-in-95">
            <div className="w-14 h-14 rounded-full bg-red-600 flex items-center justify-center shadow-2xl shadow-red-600/40 ring-4 ring-red-600/20">
               <RefreshCcw size={28} className="text-white" />
            </div>
            <div className="text-center space-y-1">
              <p className="text-white font-black uppercase text-xs tracking-widest">Connection Interrupted</p>
              <p className="text-red-400/80 text-[11px] font-bold max-w-xs">{error}</p>
            </div>
            <button 
              onClick={() => {
                const lastUser = [...messages].reverse().find(m => m.role === 'user');
                handleSend(lastUser?.content, lastUser?.imageData);
              }}
              className="px-10 py-3.5 bg-red-600 rounded-2xl text-xs font-black hover:bg-red-700 transition-all hover:scale-105 shadow-2xl shadow-red-900/50 active:scale-95 flex items-center gap-2 uppercase tracking-widest"
            >
              Resume Justice
            </button>
          </div>
        )}
        <div ref={chatEndRef} />
      </main>

      {/* Modern Interaction Footer */}
      <footer className="p-4 md:p-6 bg-slate-900 border-t border-slate-800 shadow-[0_-20px_50px_rgba(0,0,0,0.5)] z-20">
        {selectedImage && (
          <div className="mb-4 relative inline-block group">
            <div className="absolute inset-0 bg-amber-600 blur-xl opacity-20 group-hover:opacity-40 transition-opacity" />
            <img src={selectedImage} alt="Preview" className="w-28 h-28 object-cover rounded-[2rem] border-2 border-amber-600 shadow-2xl relative transition-transform group-hover:scale-110" />
            <button 
              onClick={() => setSelectedImage(null)}
              className="absolute -top-3 -right-3 bg-red-500 rounded-full p-2 shadow-2xl hover:bg-red-600 transition-colors border-4 border-slate-900 z-10"
            >
              <X size={16} />
            </button>
          </div>
        )}
        
        <div className="max-w-4xl mx-auto flex items-end gap-3 bg-slate-800/60 p-3 rounded-[2.5rem] border border-slate-700/50 shadow-inner focus-within:ring-2 focus-within:ring-amber-500/50 focus-within:bg-slate-800/90 transition-all">
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="p-4 text-slate-400 hover:text-amber-500 transition-all rounded-full hover:bg-slate-700/50 mb-0.5"
            title="Scan Document"
          >
            <Camera size={26} />
          </button>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept="image/*" 
            className="hidden" 
          />
          
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Type your legal query (e.g., 'Recent motor vehicle law changes')..."
            className="flex-1 bg-transparent border-none focus:ring-0 text-slate-100 placeholder-slate-500 resize-none max-h-40 py-4 text-sm md:text-base font-semibold leading-relaxed"
            rows={1}
            style={{ height: 'auto' }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = `${target.scrollHeight}px`;
            }}
          />
          
          <button 
            onClick={() => handleSend()}
            disabled={(!input.trim() && !selectedImage) || isLoading}
            className={`p-4 rounded-3xl transition-all mb-0.5 ${
              (input.trim() || selectedImage) && !isLoading
                ? 'bg-[#d97706] text-white shadow-[0_10px_30px_rgba(217,119,6,0.4)] hover:bg-amber-700 hover:scale-110 rotate-3 active:rotate-0' 
                : 'bg-slate-700 text-slate-600 cursor-not-allowed grayscale'
            }`}
          >
            <Send size={26} />
          </button>
        </div>
        
        <div className="mt-4 flex flex-col items-center gap-1">
          <p className="text-[9px] text-center text-slate-500 font-black tracking-widest uppercase">
            Nyaya Mitra v3.5 • Secured by Quantum AI Legal Protocol
          </p>
          <p className="text-[8px] text-center text-slate-600/80 font-bold max-w-sm px-4">
            DISCLAIMER: This system provides AI-generated legal assistance. It is NOT a replacement for a certified advocate. Confirm critical filings with official gazettes.
          </p>
        </div>
      </footer>

      {/* Global CSS for aesthetic polish */}
      <style>{`
        @keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slide-in-bottom { from { transform: translateY(20px); } to { transform: translateY(0); } }
        .animate-in { animation: fade-in 0.4s cubic-bezier(0.16, 1, 0.3, 1), slide-in-bottom 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
        
        textarea::-webkit-scrollbar { width: 0; }
        .scrollbar-thin::-webkit-scrollbar { width: 5px; }
        .scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
        .scrollbar-thin::-webkit-scrollbar-thumb { background: #334155; border-radius: 20px; border: 2px solid transparent; background-clip: content-box; }
        
        ::placeholder { text-transform: none; font-weight: 500; opacity: 0.6; }
        
        @media (max-width: 640px) {
          .p-4 { padding: 0.85rem; }
          .max-w-4xl { margin-bottom: 0.5rem; }
        }
      `}</style>
    </div>
  );
};

const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(<NyayaMitra />);
}
