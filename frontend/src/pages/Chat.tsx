import { ShinyText } from '@/components/reactbits/ShinyText';
import { Bot, BrainCircuit, Activity, Settings2, Send, Loader2 } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { chatApi } from '@/services/api';
import type { ChatResponse, ReasoningStep, MemorySource } from '@/types/api';
import { cn } from '@/lib/utils';

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

    try {
      const response = await chatApi.sendMessage(
        userMessage.content,
        conversationId || undefined,
        'personal',
        true
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
    <div className="flex h-full min-h-0 w-full relative">
      <section className="flex h-full min-h-0 min-w-0 flex-1 flex-col mx-auto max-w-4xl pt-4">
        <div className="flex justify-end px-4 md:px-0 mb-2">
          <button
            onClick={() => setIsOrchestratorOpen((prev) => !prev)}
            className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/70 transition-colors hover:bg-white/10 hover:text-white"
          >
            <Settings2 className="size-3.5" />
            Orchestrator
          </button>
        </div>

        {/* Messages */}
        <div className="scrollbar-thin flex-1 min-h-0 overflow-y-auto px-2 md:px-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <BrainCircuit className="w-16 h-16 text-purple-500/30 mb-4" />
              <h2 className="text-xl font-semibold text-white/80 mb-2">Welcome to NeuroGraph</h2>
              <p className="text-white/50 max-w-md">
                Ask me anything. I'll use your knowledge graph and memory to provide context-aware answers.
              </p>
            </div>
          ) : (
            <div className="space-y-4 pb-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    'flex gap-3',
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div
                    className={cn(
                      'max-w-[80%] rounded-2xl px-4 py-3',
                      message.role === 'user'
                        ? 'bg-purple-500/20 text-white border border-purple-500/30'
                        : 'bg-white/5 text-white/90 border border-white/10'
                    )}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-white/40">
                      <span>{formatTime(message.created_at)}</span>
                      {message.confidence && (
                        <span className="text-purple-300">
                          {(message.confidence * 100).toFixed(0)}% confident
                        </span>
                      )}
                    </div>
                  </div>
                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                      <span className="text-white text-sm font-medium">U</span>
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-3 justify-start">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-white/5 border border-white/10 rounded-2xl px-4 py-3">
                    <div className="flex items-center gap-2 text-white/60">
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
          <div className="mx-4 mb-2 px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-sm">
            {error}
          </div>
        )}

        {/* Input */}
        <div className="mt-auto shrink-0 px-2 py-4 md:px-4 md:py-6">
          <div className="relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask something..."
              rows={1}
              className="w-full resize-none rounded-2xl border border-white/10 bg-white/5 px-4 py-3 pr-12 text-white placeholder:text-white/40 focus:border-purple-500/50 focus:outline-none focus:ring-2 focus:ring-purple-500/20 disabled:opacity-50"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
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

