import { ShinyText } from '@/components/reactbits/ShinyText';
import { Bot, BrainCircuit, Activity, Settings2, Send, Loader2, ChevronDown, ChevronUp, Cpu, Brain, Users, Globe, Zap } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { chatApi, modelsApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  reasoning_path?: ReasoningStep[] | null;
  sources?: MemorySource[] | null;
  confidence?: number;
  created_at: string;
  processing_steps?: ProcessingStep[];
}

interface ReasoningStep {
  step: number;
  action: string;
  result: string;
}

interface MemorySource {
  content: string;
  layer: string;
  score: number;
}

interface ProcessingStep {
  step_number: number;
  action: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: string;
  reasoning?: string;
  duration_ms?: number;
}

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
}

interface ProviderInfo {
  id: string;
  name: string;
  is_available: boolean;
  models: ModelInfo[];
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

  // Model selection
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [selectedProvider, setSelectedProvider] = useState('gemini');
  const [selectedModel, setSelectedModel] = useState('gemini-2.0-flash');
  
  // Chat settings
  const [agentsEnabled, setAgentsEnabled] = useState(true);
  const [memoryLayer, setMemoryLayer] = useState<'personal' | 'workspace' | 'global'>('personal');
  const [includeGlobal, setIncludeGlobal] = useState(true);

  // Processing status
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([]);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [isProcessingExpanded, setIsProcessingExpanded] = useState(false);

  // Workspace for chat
  const [selectedWorkspace, setSelectedWorkspace] = useState<string | null>(null);

  // Load models on mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        const result = await modelsApi.getProviders() as { providers: ProviderInfo[] };
        setProviders(result.providers || []);
        
        // Load from localStorage or use defaults
        const savedProvider = localStorage.getItem('ng_default_provider');
        const savedModel = localStorage.getItem('ng_default_model');
        if (savedProvider) setSelectedProvider(savedProvider);
        if (savedModel) setSelectedModel(savedModel);
      } catch (err) {
        console.error('Failed to load models:', err);
      }
    };
    loadModels();
  }, []);

  // Load workspaces
  useEffect(() => {
    const loadWorkspaces = async () => {
      try {
        const result = await workspaceApi.list() as Workspace[];
        setWorkspaces(Array.isArray(result) ? result : []);
      } catch (err) {
        console.error('Failed to load workspaces:', err);
      }
    };
    loadWorkspaces();
  }, []);

  // Load conversations when workspace changes
  useEffect(() => {
    const loadConversations = async () => {
      try {
        const result = await conversationsApi.list(selectedWorkspace || undefined) as Conversation[];
        setConversations(Array.isArray(result) ? result : []);
      } catch (err) {
        console.error('Failed to load conversations:', err);
      }
    };
    loadConversations();
  }, [selectedWorkspace]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Save model preferences
  useEffect(() => {
    localStorage.setItem('ng_default_provider', selectedProvider);
    localStorage.setItem('ng_default_model', selectedModel);
  }, [selectedProvider, selectedModel]);

  const simulateProcessingSteps = () => {
    const steps: ProcessingStep[] = [
      { step_number: 1, action: 'Analyzing query', status: 'pending' },
      { step_number: 2, action: 'Searching memory', status: 'pending' },
      { step_number: 3, action: 'RAG retrieval', status: 'pending' },
      { step_number: 4, action: 'Building context', status: 'pending' },
      { step_number: 5, action: 'Generating response', status: 'pending' },
    ];
    setProcessingSteps(steps);
    
    // Simulate progress
    let currentIdx = 0;
    const interval = setInterval(() => {
      if (currentIdx < steps.length) {
        setProcessingSteps(prev => prev.map((s, i) => ({
          ...s,
          status: i < currentIdx ? 'completed' : i === currentIdx ? 'running' : 'pending'
        })));
        setCurrentStep(steps[currentIdx].action);
        currentIdx++;
      } else {
        clearInterval(interval);
      }
    }, 600);
    
    return () => clearInterval(interval);
  };

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

    // Start processing simulation
    simulateProcessingSteps();

    try {
      const response = await chatApi.sendMessage(
        userMessage.content,
        conversationId || undefined,
        memoryLayer,
        includeGlobal,
        selectedProvider,
        selectedModel,
        agentsEnabled,
        selectedWorkspace || undefined
      ) as {
        id: string;
        content: string;
        conversation_id: string;
        reasoning_path?: ReasoningStep[];
        sources?: MemorySource[];
        confidence?: number;
        created_at: string;
        processing_steps?: ProcessingStep[];
      };

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
        processing_steps: response.processing_steps,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setCurrentReasoning(response.reasoning_path || null);
      setCurrentSources(response.sources || null);
      
      // Complete all processing steps
      setProcessingSteps(prev => prev.map(s => ({ ...s, status: 'completed' as const })));
      setCurrentStep('Complete');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
      setProcessingSteps(prev => prev.map(s => ({ ...s, status: 'failed' as const })));
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

  const getAvailableModels = () => {
    const provider = providers.find(p => p.id === selectedProvider);
    return provider?.models || [];
  };

  const getMemoryIcon = (layer: string) => {
    switch (layer) {
      case 'personal': return <Brain className="w-3 h-3" />;
      case 'workspace': return <Users className="w-3 h-3" />;
      case 'global': return <Globe className="w-3 h-3" />;
      default: return <Brain className="w-3 h-3" />;
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setConversationId(null);
    setCurrentReasoning(null);
    setCurrentSources(null);
    setProcessingSteps([]);
    setCurrentStep('');
  };

  return (
    <div className="absolute inset-0 flex flex-col w-full bg-linear-to-b from-[#050110] via-[#0a0520] to-[#050110]">
      <section className="flex flex-col flex-1 min-h-0 min-w-0 mx-auto max-w-4xl w-full">
        {/* Top Bar */}
        <div className="flex justify-between items-center px-4 md:px-6 pt-4 mb-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={startNewChat}
            className="border-white/10 text-white/70 hover:bg-white/10"
          >
            + New Chat
          </Button>
          <button
            onClick={() => setIsOrchestratorOpen((prev) => !prev)}
            className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/70 transition-colors hover:bg-white/10 hover:text-white"
          >
            <Settings2 className="size-3.5" />
            Orchestrator
          </button>
        </div>

        {/* Processing Status Bar */}
        {isLoading && (
          <div className="mx-4 md:mx-6 mb-2">
            <div 
              className="rounded-xl border border-purple-500/20 bg-purple-500/5 px-4 py-2 cursor-pointer"
              onClick={() => setIsProcessingExpanded(!isProcessingExpanded)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                  <ShinyText
                    text={currentStep || 'Processing...'}
                    speed={2}
                    className="text-sm font-medium text-purple-200"
                  />
                </div>
                {isProcessingExpanded ? (
                  <ChevronUp className="w-4 h-4 text-white/40" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-white/40" />
                )}
              </div>
              
              {isProcessingExpanded && (
                <div className="mt-3 space-y-2 border-t border-purple-500/10 pt-3">
                  {processingSteps.map((step) => (
                    <div key={step.step_number} className="flex items-center gap-2 text-xs">
                      <span className={`w-5 h-5 rounded-full flex items-center justify-center ${
                        step.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                        step.status === 'running' ? 'bg-purple-500/20 text-purple-400' :
                        step.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                        'bg-white/5 text-white/30'
                      }`}>
                        {step.status === 'running' ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : step.status === 'completed' ? (
                          '✓'
                        ) : step.status === 'failed' ? (
                          '✗'
                        ) : (
                          step.step_number
                        )}
                      </span>
                      <span className={step.status === 'running' ? 'text-purple-200' : 'text-white/50'}>
                        {step.action}
                      </span>
                      {step.duration_ms && (
                        <span className="text-white/30 ml-auto">{step.duration_ms}ms</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

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
              <div className="flex gap-2 mt-4 text-xs text-white/40">
                <Badge variant="outline" className="border-purple-500/30">
                  <Cpu className="w-3 h-3 mr-1" />
                  {selectedProvider} / {selectedModel}
                </Badge>
                <Badge variant="outline" className="border-blue-500/30">
                  {getMemoryIcon(memoryLayer)}
                  <span className="ml-1">{memoryLayer} memory</span>
                </Badge>
                {agentsEnabled && (
                  <Badge variant="outline" className="border-green-500/30">
                    <Zap className="w-3 h-3 mr-1" />
                    Agents
                  </Badge>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-6 pb-4 pt-2">
              {messages.map((message) => (
                <div key={message.id} className="group">
                  {message.role === 'assistant' && (
                    <div className="flex gap-4 items-start">
                      <div className="shrink-0 w-7 h-7 rounded-lg bg-linear-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-[15px] leading-7 text-white/90 whitespace-pre-wrap">
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
                        <div className="text-[15px] leading-7 text-white whitespace-pre-wrap">
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
                      <ShinyText text="Thinking..." speed={2} className="text-purple-200" />
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

        {/* Input Area */}
        <div className="shrink-0 px-4 md:px-6 pb-4 pt-2">
          {/* Chat Settings Row */}
          <div className="flex flex-wrap gap-3 mb-3 items-center">
            {/* Model Selector */}
            <div className="flex items-center gap-2">
              <Label className="text-xs text-white/50">Model:</Label>
              <Select value={selectedProvider} onValueChange={(v) => { setSelectedProvider(v); setSelectedModel(getAvailableModels()[0]?.id || ''); }}>
                <SelectTrigger className="w-24 h-8 text-xs bg-white/5 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#0a0520] border-white/10">
                  {providers.filter(p => p.is_available).map(p => (
                    <SelectItem key={p.id} value={p.id} className="text-white text-xs">
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger className="w-40 h-8 text-xs bg-white/5 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#0a0520] border-white/10 max-h-60">
                  {getAvailableModels().map(m => (
                    <SelectItem key={m.id} value={m.id} className="text-white text-xs">
                      {m.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Memory Layer */}
            <div className="flex items-center gap-2">
              <Label className="text-xs text-white/50">Memory:</Label>
              <Select value={memoryLayer} onValueChange={(v) => setMemoryLayer(v as 'personal' | 'workspace' | 'global')}>
                <SelectTrigger className="w-28 h-8 text-xs bg-white/5 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#0a0520] border-white/10">
                  <SelectItem value="personal" className="text-white text-xs">
                    <span className="flex items-center gap-1"><Brain className="w-3 h-3" /> Personal</span>
                  </SelectItem>
                  <SelectItem value="workspace" className="text-white text-xs">
                    <span className="flex items-center gap-1"><Users className="w-3 h-3" /> Workspace</span>
                  </SelectItem>
                  <SelectItem value="global" className="text-white text-xs">
                    <span className="flex items-center gap-1"><Globe className="w-3 h-3" /> Global</span>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Agents Toggle */}
            <div className="flex items-center gap-2">
              <Switch
                id="agents"
                checked={agentsEnabled}
                onCheckedChange={setAgentsEnabled}
                className="data-[state=checked]:bg-purple-500"
              />
              <Label htmlFor="agents" className="text-xs text-white/50 cursor-pointer flex items-center gap-1">
                <Zap className="w-3 h-3" />
                Agents
              </Label>
            </div>

            {/* Include Global */}
            <div className="flex items-center gap-2">
              <Switch
                id="includeGlobal"
                checked={includeGlobal}
                onCheckedChange={setIncludeGlobal}
                className="data-[state=checked]:bg-green-500"
              />
              <Label htmlFor="includeGlobal" className="text-xs text-white/50 cursor-pointer">
                +Global
              </Label>
            </div>
          </div>

          {/* Text Input */}
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

              {/* Current Model */}
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/45">Current Model</p>
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm text-white">{selectedProvider}</span>
                  <span className="text-white/30">/</span>
                  <span className="text-sm text-cyan-200">{selectedModel}</span>
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

