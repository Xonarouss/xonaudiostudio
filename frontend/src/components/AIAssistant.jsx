import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Sparkles, X, ChevronDown, ChevronUp, Copy, Check, MessageSquare, Wand2, Lightbulb } from 'lucide-react';

export default function AIAssistant({ onApplyPrompt, activeTab }) {
  const [isOpen, setIsOpen] = useState(true);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am your **XonAudio AI Assistant** powered by local Llama.\n\nI can brainstorm sound effects, craft cinematic prompts, or write natural voice scripts for you. How can I help?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim() || isTyping) return;

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

      if (!res.ok) throw new Error('Failed to get reply');
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'I had trouble connecting to the local Llama engine. Please verify the backend is running.'
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const copyToClipboard = (text, index) => {
    navigator.clipboard?.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const quickPrompts = [
    "Suggest a sci-fi laser sound prompt",
    "Write a short commercial voice script",
    "Describe a massive cinematic explosion",
    "How to get the cleanest voice clone?"
  ];

  return (
    <aside 
      aria-label="Llama AI Assistant"
      className="fixed bottom-[390px] right-6 z-40 w-80 bg-white rounded-2xl shadow-xl border border-slate-200/90 overflow-hidden font-sans transition-all duration-200 flex flex-col hover:shadow-2xl max-h-[460px]"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-purple-50 to-cyan-50 border-b border-slate-100 select-none">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-600 to-cyan-600 flex items-center justify-center text-white shadow-2xs">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <span className="font-extrabold text-xs text-slate-900 tracking-tight block">Llama AI Assistant</span>
            <span className="text-[10px] text-slate-500 block leading-tight">Prompt &amp; Foley Director</span>
          </div>
        </div>

        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200/50 transition-colors"
          title={isOpen ? "Minimize assistant" : "Expand assistant"}
        >
          {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {isOpen && (
        <>
          {/* Chat Messages */}
          <div className="p-3.5 space-y-3 overflow-y-auto flex-1 text-xs max-h-64 bg-slate-50/50">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`p-3 rounded-2xl max-w-[90%] leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-tr-xs shadow-xs'
                      : 'bg-white border border-slate-200 text-slate-800 rounded-tl-xs shadow-xs'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.content}</p>
                </div>

                {m.role === 'assistant' && idx > 0 && (
                  <div className="flex items-center gap-2 mt-1 ml-1 text-[10px] text-slate-400">
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

          {/* Quick Suggestions */}
          {messages.length <= 2 && (
            <div className="px-3 py-2 bg-white border-t border-slate-100 flex gap-1.5 overflow-x-auto text-[10px]">
              {quickPrompts.slice(0, 2).map((qp, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(qp)}
                  className="px-2 py-1 rounded-md bg-slate-100 hover:bg-purple-50 text-slate-600 hover:text-purple-700 border border-slate-200 flex-shrink-0 transition-colors"
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
              placeholder="Ask Llama for prompts or advice..."
              className="flex-1 px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:border-cyan-600 focus:ring-1 focus:ring-cyan-600/30 text-slate-800 placeholder-slate-400"
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
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

