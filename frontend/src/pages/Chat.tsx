import { ShinyText } from '@/components/reactbits/ShinyText';
import { Bot, BrainCircuit, Activity, Settings2, Send, Loader2 } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { chatApi } from '@/services/api';
import type { ChatResponse, ReasoningStep, MemorySource } from '@/types/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  reasoning_path?: ReasoningStep[] | null;
  sources?: MemorySource[] | null;
  confidence?: number;
  created_at: string;
}

export default function Chat() {
  const [isOrchestratorOpen, setIsOrchestratorOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [currentReasoning, setCurrentReasoning] = useState<ReasoningStep[] | null>(null);
  const [currentSources, setCurrentSources] = useState<MemorySource[] | null>(null);
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Get selected model from localStorage (set in Settings)
  const getSelectedModel = () => {
    return {
      provider: localStorage.getItem('ng_default_provider') || 'nvidia',
      model: localStorage.getItem('ng_default_model') || 'devstral-2-123b',
    };
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError('');
    setCurrentReasoning(null);
    setCurrentSources(null);

    const { provider, model } = getSelectedModel();

    try {
      const response = await chatApi.sendMessage(
        userMessage.content,
        conversationId || undefined,
        'personal',
        true,
        provider,
        model
      ) as ChatResponse;

      if (response.conversation_id && !conversationId) {
        setConversationId(response.conversation_id);
      }

      const assistantMessage: Message = {
        id: response.id || `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.content,
        reasoning_path: response.reasoning_path,
        sources: response.sources,
        confidence: response.confidence,
        created_at: response.created_at,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setCurrentReasoning(response.reasoning_path);
      setCurrentSources(response.sources);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      // Remove the user message if we failed
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="absolute inset-0 flex flex-col w-full bg-linear-to-b from-[#050110] via-[#0a0520] to-[#050110]">
      <section className="flex flex-col flex-1 min-h-0 min-w-0 mx-auto max-w-3xl w-full">
        <div className="flex justify-end px-4 md:px-6 pt-4 mb-2 shrink-0">
          <button
            onClick={() => setIsOrchestratorOpen((prev) => !prev)}
            className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/70 transition-colors hover:bg-white/10 hover:text-white"
          >
            <Settings2 className="size-3.5" />
            Orchestrator
          </button>
        </div>

        {/* Messages */}
        <div className="scrollbar-thin flex-1 min-h-0 overflow-y-auto px-4 md:px-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="mb-6 p-4 rounded-full bg-linear-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30">
                <BrainCircuit className="w-12 h-12 text-purple-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-3">Welcome to NeuroGraph</h2>
              <p className="text-white/60 max-w-md text-sm leading-relaxed">
                Ask me anything. I'll use your knowledge graph and memory to provide context-aware answers with explainable reasoning.
              </p>
            </div>
          ) : (
            <div className="space-y-6 pb-4 pt-2">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className="group"
                >
                  {message.role === 'assistant' && (
                    <div className="flex gap-4 items-start">
                      <div className="shrink-0 w-7 h-7 rounded-lg bg-linear-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-[15px] leading-7 text-white/90">
                          {message.content}
                        </div>
                        {message.confidence && (
                          <div className="flex items-center gap-2 mt-2 text-xs text-white/40">
                            <span>{formatTime(message.created_at)}</span>
                            <span>•</span>
                            <span className="text-purple-400">
                              {(message.confidence * 100).toFixed(0)}% confidence
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {message.role === 'user' && (
                    <div className="flex gap-4 items-start">
                      <div className="shrink-0 w-7 h-7 rounded-lg bg-linear-to-br from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg">
                        <span className="text-white text-xs font-semibold">Y</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-[15px] leading-7 text-white">
                          {message.content}
                        </div>
                        <div className="text-xs text-white/40 mt-2">
                          {formatTime(message.created_at)}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-4 items-start">
                  <div className="shrink-0 w-7 h-7 rounded-lg bg-linear-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 text-white/50 text-sm">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mx-4 md:mx-6 mb-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-sm">
            {error}
          </div>
        )}

        {/* Input */}
        <div className="shrink-0 px-4 md:px-6 pb-6 pt-4">
          <div className="relative max-w-full">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
              }}
              onKeyDown={handleKeyDown}
              placeholder="Message NeuroGraph..."
              rows={1}
              className="w-full resize-none rounded-3xl border border-white/10 bg-white/5 px-5 py-4 pr-14 text-[15px] text-white placeholder:text-white/40 focus:border-white/20 focus:outline-none focus:bg-white/[0.07] disabled:opacity-50 transition-all max-h-50 shadow-lg shadow-black/20"
              disabled={isLoading}
              style={{ minHeight: '52px' }}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="absolute right-3 bottom-3 p-2.5 rounded-xl bg-white/10 text-white hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-center text-xs text-white/30 mt-3">
            NeuroGraph can make mistakes. Verify important information.
          </p>
        </div>
      </section>

      {/* Orchestrator Panel */}
      {isOrchestratorOpen && (
        <aside className="absolute right-0 top-0 bottom-0 z-10 w-80 border-l border-white/10 bg-[#090512]/95 backdrop-blur-md shadow-2xl">
          <div className="flex h-full w-full flex-col">
            <div className="flex items-center justify-between border-b border-white/10 p-4">
              <div>
                <h3 className="text-sm font-semibold text-white">Live Session Panel</h3>
                <p className="text-[10px] uppercase tracking-[0.2em] text-purple-200/60">Orchestrator</p>
              </div>
              <button
                onClick={() => setIsOrchestratorOpen(false)}
                className="rounded-lg p-2 text-white/50 hover:bg-white/10 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="scrollbar-thin flex-1 space-y-6 overflow-y-auto p-4 md:p-5">
              {/* Session Stats */}
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/45">Session Pulse</p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm text-white/80">
                    <span className="flex items-center gap-2"><BrainCircuit className="size-4 text-purple-400" />Messages</span>
                    <strong className="text-purple-200">{messages.length}</strong>
                  </div>
                  <div className="flex items-center justify-between text-sm text-white/80">
                    <span className="flex items-center gap-2"><Bot className="size-4 text-indigo-400" />Sources Used</span>
                    <strong className="text-indigo-200">{currentSources?.length || 0}</strong>
                  </div>
                  <div className="flex items-center justify-between text-sm text-white/80">
                    <span className="flex items-center gap-2"><Activity className="size-4 text-fuchsia-400" />Reasoning Steps</span>
                    <strong className="text-fuchsia-200">{currentReasoning?.length || 0}</strong>
                  </div>
                </div>
              </div>

              {/* Sources */}
              {currentSources && currentSources.length > 0 && (
                <div className="rounded-2xl border border-blue-500/20 bg-blue-500/5 p-4">
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-blue-200/50">Memory Sources</p>
                  <div className="space-y-2">
                    {currentSources.map((source, i) => (
                      <div key={i} className="text-xs text-white/70 bg-black/20 rounded-lg p-2">
                        <p className="line-clamp-2">{source.content}</p>
                        <div className="flex justify-between mt-1 text-white/40">
                          <span>{source.layer}</span>
                          <span>{(source.score * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Reasoning */}
              {currentReasoning && currentReasoning.length > 0 && (
                <div className="rounded-2xl border border-purple-500/20 bg-purple-500/5 p-4">
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-purple-200/50">Reasoning Stream</p>
                  <div className="space-y-2">
                    {currentReasoning.map((step, i) => (
                      <div key={i} className="text-xs">
                        <div className="flex items-center gap-2 text-purple-200">
                          <span className="font-mono text-purple-400">{step.step}.</span>
                          <span className="font-medium">{step.action}</span>
                        </div>
                        <p className="text-white/50 mt-1 pl-5">{step.result}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Empty State */}
              {!currentSources && !currentReasoning && (
                <div className="rounded-2xl border border-purple-500/20 bg-purple-500/5 p-4">
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-purple-200/50">Reasoning Stream</p>
                  <ShinyText
                    text="Waiting for query..."
                    speed={4}
                    className="mb-2 text-sm font-medium text-purple-100"
                  />
                  <p className="text-xs leading-relaxed text-white/60">
                    Send a message to see the reasoning process and memory sources used.
                  </p>
                </div>
              )}
            </div>
          </div>
        </aside>
      )}
    </div>
  );
}

