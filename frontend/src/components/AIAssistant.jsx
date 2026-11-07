import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Sparkles, X, ChevronDown, ChevronUp, Copy, Check, Wand2, AlertCircle, DownloadCloud } from 'lucide-react';

export default function AIAssistant({ onApplyPrompt, activeTab, modelsStatus, onOpenModelManager }) {
  const [isOpen, setIsOpen] = useState(true);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const messagesEndRef = useRef(null);

  const isLlamaInstalled = modelsStatus?.llama?.installed === true;

  // Initialize welcome message based on install status
  useEffect(() => {
    if (isLlamaInstalled) {
      if (messages.length === 0) {
        setMessages([
          {
            role: 'assistant',
            content: 'Hello! I am your **XonAudio AI Assistant** powered by local Llama 3.\n\nI can brainstorm sound effects, craft cinematic prompts, or write natural voice scripts for you. How can I help?'
          }
        ]);
      }
    } else {
      setMessages([
        {
          role: 'assistant',
          content: '⚠️ **Llama 3 Model Not Installed**\n\nThe AI Assistant requires the local Llama 3 neural weights (2.8 GB). Please download the model to enable interactive studio chat and Magic Wand prompt refinement.'
        }
      ]);
    }
  }, [isLlamaInstalled]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleDownloadLlama = async () => {
    if (isDownloading) return;
    setIsDownloading(true);
    try {
      const res = await fetch('/api/models/download/llama', { method: 'POST' });
      if (!res.ok) throw new Error('Download failed');
      if (onOpenModelManager) onOpenModelManager();
    } catch (e) {
      console.error(e);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleSend = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim() || isTyping) return;

    if (!isLlamaInstalled) {
      setMessages(prev => [
        ...prev,
        { role: 'user', content: text },
        {
          role: 'assistant',
          content: '⚠️ **Cannot generate response:** Llama 3 model weights are missing. Please download Llama 3 in the Model Manager tab or run Start_AudioStudio.bat to install all models.'
        }
      ]);
      setInput('');
      return;
    }

    const newMessages = [...messages, { role: 'user', content: text }];
    setMessages(newMessages);
    setInput('');
    setIsTyping(true);

    try {
      const res = await fetch('/api/llama/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: newMessages.slice(-6)
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to get reply' }));
        throw new Error(err.detail || 'Llama engine error');
      }

      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ **Error:** ${err.message || 'Could not communicate with local Llama engine. Please verify the model is installed.'}`
        }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const copyToClipboard = (text, index) => {
    navigator.clipboard?.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const quickPrompts = activeTab === 'voicelab' ? [
    "Refine this voice script with emotional pacing",
    "Write a 15-second tech product introduction",
    "How to make F5-TTS sound more conversational?"
  ] : [
    "Cinematic thunder and heavy rain on glass",
    "Deep futuristic laser cannon explosion",
    "Footsteps crunching on wet autumn leaves"
  ];

  return (
    <aside className="w-80 sm:w-[340px] bg-white rounded-2xl shadow-xl border border-slate-200/90 overflow-hidden font-sans transition-all duration-200 hover:shadow-2xl flex flex-col">
      {/* Header matching Hardware Widget perfectly */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-slate-50 via-purple-50/30 to-indigo-50/40 border-b border-slate-100 select-none">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-cyan-600 to-purple-600 text-white flex items-center justify-center shadow-xs">
            <Bot className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-extrabold text-xs text-slate-900 tracking-tight block">Llama AI Assistant</span>
            <span className="text-[10px] text-slate-500 font-medium block">Prompt &amp; Foley Director</span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
            title={isOpen ? "Collapse assistant" : "Expand assistant"}
          >
            {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Collapsible Content */}
      {isOpen && (
        <>
          {/* Missing Model Banner if not installed */}
          {!isLlamaInstalled && (
            <div className="p-3 bg-amber-50 border-b border-amber-200/80">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-[11px] text-amber-800 leading-tight">
                  <span className="font-bold block">Model Not Installed</span>
                  <span>Llama 3 is required for AI chat &amp; Magic Wand.</span>
                </div>
              </div>
              <button
                onClick={onOpenModelManager || handleDownloadLlama}
                className="mt-2 w-full py-1.5 px-3 bg-amber-600 hover:bg-amber-700 text-white text-[11px] font-bold rounded-lg transition-all flex items-center justify-center gap-1.5 shadow-xs"
              >
                <DownloadCloud className="w-3.5 h-3.5" />
                <span>Download Llama 3 (2.8 GB)</span>
              </button>
            </div>
          )}

          {/* Messages Container */}
          <div className="h-60 sm:h-64 overflow-y-auto p-3 space-y-3 bg-slate-50/50 text-xs">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`p-3 rounded-2xl max-w-[92%] leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-br-xs shadow-xs'
                      : 'bg-white border border-slate-200/90 text-slate-800 rounded-bl-xs shadow-xs'
                  }`}
                >
                  <p className="whitespace-pre-wrap select-text text-[11px] sm:text-xs">{m.content}</p>
                </div>

                {m.role === 'assistant' && (
                  <div className="flex items-center gap-3 mt-1.5 px-1 text-[10px] text-slate-400">
                    <button
                      onClick={() => copyToClipboard(m.content, idx)}
                      className="flex items-center gap-1 hover:text-slate-700 transition-colors"
                    >
                      {copiedIndex === idx ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedIndex === idx ? 'Copied' : 'Copy'}</span>
                    </button>
                    {onApplyPrompt && (
                      <button
                        onClick={() => onApplyPrompt(m.content)}
                        className="flex items-center gap-1 hover:text-purple-600 text-purple-600 font-semibold transition-colors"
                      >
                        <Wand2 className="w-3 h-3" />
                        <span>Send to Studio</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex items-center gap-1.5 p-3 rounded-2xl bg-white border border-slate-200 w-24 text-slate-400 text-xs shadow-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-600 animate-bounce"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                <span className="w-1.5 h-1.5 rounded-full bg-purple-600 animate-bounce" style={{ animationDelay: '0.4s' }}></span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Suggestions (if installed) */}
          {isLlamaInstalled && messages.length <= 2 && (
            <div className="px-3 py-2 bg-white border-t border-slate-100 flex gap-1.5 overflow-x-auto text-[10px]">
              {quickPrompts.slice(0, 2).map((qp, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(qp)}
                  className="px-2 py-1 rounded-md bg-slate-100 hover:bg-purple-50 text-slate-600 hover:text-purple-700 border border-slate-200 flex-shrink-0 transition-colors truncate max-w-[150px]"
                >
                  {qp}
                </button>
              ))}
            </div>
          )}

          {/* Chat Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="p-2.5 bg-white border-t border-slate-100 flex items-center gap-1.5"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={!isLlamaInstalled}
              placeholder={!isLlamaInstalled ? "Download Llama 3 in Settings to chat..." : "Ask Llama for prompts or advice..."}
              className="flex-1 px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:border-cyan-600 focus:ring-1 focus:ring-cyan-600/30 text-slate-800 placeholder-slate-400 disabled:bg-slate-100 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={!isLlamaInstalled || !input.trim() || isTyping}
              className="p-2 rounded-xl bg-gradient-to-r from-cyan-600 to-purple-600 text-white disabled:opacity-40 hover:brightness-105 active:scale-95 transition-all shadow-xs"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </>
      )}
    </aside>
  );
}
