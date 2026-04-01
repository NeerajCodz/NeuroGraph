import { ShinyText } from '@/components/reactbits/ShinyText';
import { Bot, BrainCircuit, Activity, Settings2, Loader2, ChevronDown, ChevronUp, Cpu, Brain, Zap, Send } from 'lucide-react';
import { useState, useRef, useEffect, useCallback } from 'react';
import { chatApi, modelsApi, profileApi } from '@/services/api';
import type { StreamingStep, StreamingResponse } from '@/services/api';
import { workspaceApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useLocation, useParams } from 'react-router-dom';
import { useTheme } from '@/contexts/ThemeContext';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  reasoning_path?: ReasoningStep[] | null;
  sources?: MemorySource[] | null;
  confidence?: number;
  created_at: string;
  processing_steps?: ProcessingStep[];
  graph_paths?: GraphPath[];
}

interface GraphPath {
  source: string;
  relationship: string;
  target: string;
  reason?: string;
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
  node_id?: string;
}

interface ProcessingStepDetail {
  type: 'info' | 'connection' | 'search' | 'node' | 'error' | 'result';
  content: string;
  metadata?: Record<string, unknown>;
}

interface ProcessingStep {
  step_number: number;
  action: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  result?: string;
  reasoning?: string;
  duration_ms?: number;
  details?: ProcessingStepDetail[];
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

// Processing Accordion Component for completed messages
function ProcessingAccordion({ steps }: { steps: ProcessingStep[] }) {
  const [expanded, setExpanded] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  
  const toggleStep = (stepNum: number) => {
    setExpandedSteps(prev => {
      const next = new Set(prev);
      if (next.has(stepNum)) next.delete(stepNum);
      else next.add(stepNum);
      return next;
    });
  };
  
  const getStepIcon = (action: string) => {
    if (action.toLowerCase().includes('rag') || action.toLowerCase().includes('memory')) return '🧠';
    if (action.toLowerCase().includes('graph')) return '🔗';
    if (action.toLowerCase().includes('web') || action.toLowerCase().includes('search')) return '🌐';
    if (action.toLowerCase().includes('response') || action.toLowerCase().includes('generat')) return '✨';
    return '⚡';
  };
  
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-white/5 transition-colors text-left"
      >
        <span className="text-xs text-white/60">
          {steps.length} processing steps completed
        </span>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-white/40" />
        ) : (
          <ChevronDown className="w-4 h-4 text-white/40" />
        )}
      </button>
      
      {expanded && (
        <div className="px-4 pb-3 space-y-2 border-t border-white/10 pt-3">
          {steps.map((step) => (
            <div key={step.step_number} className="space-y-1">
              <button
                onClick={() => toggleStep(step.step_number)}
                className="w-full flex items-center gap-2 text-xs text-left hover:bg-white/5 rounded-lg p-1.5 -ml-1.5 transition-colors"
              >
                <span className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-[10px] ${
                  step.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                  step.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                  'bg-white/10 text-white/40'
                }`}>
                  {getStepIcon(step.action)}
                </span>
                <span className="text-white/70 flex-1">{step.action}</span>
                {step.duration_ms && (
                  <span className="text-white/30">{step.duration_ms}ms</span>
                )}
                <ChevronDown className={`w-3 h-3 text-white/30 transition-transform ${expandedSteps.has(step.step_number) ? 'rotate-180' : ''}`} />
              </button>
              
              {expandedSteps.has(step.step_number) && (
                <div className="ml-7 space-y-1.5 bg-black/20 rounded-lg p-2.5 text-[11px]">
                  {step.description && (
                    <p className="text-white/50">{step.description}</p>
                  )}
                  {step.reasoning && (
                    <p className="text-purple-300/70"><span className="text-white/40">Reasoning:</span> {step.reasoning}</p>
                  )}
                  {step.details && step.details.map((detail, idx) => (
                    <div key={idx} className={`flex gap-2 ${
                      detail.type === 'connection' ? 'text-cyan-300/70' :
                      detail.type === 'node' ? 'text-green-300/70' :
                      detail.type === 'search' ? 'text-yellow-300/70' :
                      detail.type === 'error' ? 'text-red-400/70' :
                      detail.type === 'result' ? 'text-purple-300/70' :
                      'text-white/50'
                    }`}>
                      <span className="shrink-0">
                        {detail.type === 'connection' ? '→' :
                         detail.type === 'node' ? '◉' :
                         detail.type === 'search' ? '🔍' :
                         detail.type === 'error' ? '⚠' :
                         detail.type === 'result' ? '✓' : '•'}
                      </span>
                      <span>{detail.content}</span>
                    </div>
                  ))}
                  {step.result && (
                    <p className="text-green-300/70"><span className="text-white/40">Result:</span> {step.result}</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Chat() {
  const location = useLocation();
  const { conversationId: routeConversationId } = useParams<{ conversationId: string }>();
  const { compactMode, showConfidence, showReasoning } = useTheme();
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
  const [includeGlobal] = useState(true);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string | null>(null);
  const [workspaces, setWorkspaces] = useState<Array<{ id: string; name: string }>>([]);
  
  // Processing status
  

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

  useEffect(() => {
    const loadProfileDefaults = async () => {
      try {
        const profile = await profileApi.getSettings();
        const preferredProvider = profile.settings.default_provider;
        const preferredModel = profile.settings.default_model;
        const preferredLayer = profile.settings.default_memory_layer;
        const preferredAgentsEnabled = profile.settings.agents_enabled;

        if (preferredProvider) {
          setSelectedProvider(preferredProvider);
          localStorage.setItem('ng_default_provider', preferredProvider);
        }
        if (preferredModel) {
          setSelectedModel(preferredModel);
          localStorage.setItem('ng_default_model', preferredModel);
        }
        if (preferredLayer === 'tenant') {
          setMemoryLayer('workspace');
          localStorage.setItem('ng_default_layer', 'tenant');
        } else if (preferredLayer === 'personal' || preferredLayer === 'global') {
          setMemoryLayer(preferredLayer);
          localStorage.setItem('ng_default_layer', preferredLayer);
        }
        setAgentsEnabled(Boolean(preferredAgentsEnabled));
      } catch {
        // Keep local defaults if profile settings are unavailable.
      }
    };
    loadProfileDefaults();
  }, []);

  useEffect(() => {
    const loadWorkspaces = async () => {
      try {
        const ws = await workspaceApi.list() as Array<{ id: string; name: string }>;
        const items = Array.isArray(ws) ? ws : [];
        setWorkspaces(items);
        if (!selectedWorkspace && items.length > 0) {
          setSelectedWorkspace(items[0].id);
        }
      } catch (err) {
        console.error('Failed to load workspaces:', err);
      }
    };
    loadWorkspaces();
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

  const [processingState, setProcessingState] = useState<{
    isProcessing: boolean;
    currentAction: string;
    steps: ProcessingStep[];
    expanded: boolean;
  }>({ isProcessing: false, currentAction: '', steps: [], expanded: false });

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const workspaceId = params.get('workspace_id');
    if (workspaceId) {
      setSelectedWorkspace(workspaceId);
      setMemoryLayer('workspace');
    }
  }, [location.search]);

  useEffect(() => {
    if (routeConversationId) {
      setConversationId(routeConversationId);
    } else {
      setConversationId(null);
    }
  }, [routeConversationId]);

  useEffect(() => {
    const onNewChat = (event: Event) => {
      const detail = (event as CustomEvent<{ workspaceId?: string | null }>).detail;
      const workspaceId = detail?.workspaceId ?? null;
      setMessages([]);
      setConversationId(null);
      setCurrentReasoning(null);
      setCurrentSources(null);
      setProcessingState({ isProcessing: false, currentAction: '', steps: [], expanded: false });
      if (workspaceId) {
        setSelectedWorkspace(workspaceId);
        setMemoryLayer('workspace');
      } else {
        setSelectedWorkspace(null);
        setMemoryLayer('personal');
      }
    };
    window.addEventListener('new-chat', onNewChat as EventListener);
    return () => window.removeEventListener('new-chat', onNewChat as EventListener);
  }, []);

  // Abort controller for streaming
  const streamAbortRef = useRef<{ abort: () => void } | null>(null);

  const handleSend = useCallback(async (message: string) => {
    if (!message.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError('');
    setCurrentReasoning(null);
    setCurrentSources(null);

    // Initialize processing state with pending steps
    const initialSteps: ProcessingStep[] = [
      { 
        step_number: 1, 
        action: 'Fetching relevant info from RAG', 
        description: 'Searching vector database for semantically similar memories',
        status: 'pending', 
        reasoning: 'Converting query to embeddings and performing similarity search',
        details: []
      },
      { 
        step_number: 2, 
        action: 'Accessing graph memory', 
        description: 'Traversing knowledge graph for connected concepts',
        status: 'pending', 
        reasoning: 'Following relationships between memory nodes',
        details: []
      },
      { 
        step_number: 3, 
        action: 'Surfing web', 
        description: 'Searching for additional context online',
        status: 'pending', 
        reasoning: 'Fetching current information if memories are insufficient',
        details: []
      },
      { 
        step_number: 4, 
        action: 'Generating response', 
        description: 'Synthesizing answer from all gathered context',
        status: 'pending', 
        reasoning: 'LLM processing with retrieved context and reasoning',
        details: []
      },
    ];
    setProcessingState({ isProcessing: true, currentAction: initialSteps[0].action, steps: initialSteps, expanded: false });

    // Use streaming API for real-time updates
    const streamController = chatApi.streamMessage(
      userMessage.content,
      conversationId || undefined,
      memoryLayer,
      includeGlobal,
      selectedProvider,
      selectedModel,
      agentsEnabled,
      selectedWorkspace || undefined,
      // onStep: Real-time step updates from backend
      (step: StreamingStep) => {
        setProcessingState(prev => {
          const updatedSteps = prev.steps.map(s => {
            if (s.step_number === step.step_number) {
              return {
                ...s,
                status: step.status,
                description: step.description,
                reasoning: step.reasoning,
                result: step.result,
                duration_ms: step.duration_ms,
                details: step.details || [],
              };
            }
            return s;
          });
          return {
            ...prev,
            steps: updatedSteps,
            currentAction: step.status === 'running' ? step.action : prev.currentAction,
          };
        });
      },
      // onResponse: Final response with all data
      (response: StreamingResponse) => {
        const assistantMessage: Message = {
          id: response.id || `assistant-${Date.now()}`,
          role: 'assistant',
          content: response.content,
          sources: response.sources,
          confidence: response.confidence,
          created_at: new Date().toISOString(),
          processing_steps: response.processing_steps,
          graph_paths: response.graph_paths,
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setCurrentSources(response.sources || null);
        
        // Complete processing
        setProcessingState(prev => ({ 
          ...prev, 
          isProcessing: false, 
          currentAction: '',
          steps: response.processing_steps || prev.steps.map(s => ({ ...s, status: 'completed' as const }))
        }));
        setIsLoading(false);
      },
      // onError
      (errorMsg: string) => {
        setError(errorMsg);
        setProcessingState(prev => ({ 
          ...prev, 
          isProcessing: false,
          currentAction: 'Error',
          steps: prev.steps.map(s => s.status === 'running' 
            ? { ...s, status: 'failed' as const, result: errorMsg }
            : s
          )
        }));
        setIsLoading(false);
      },
      // onInit: New conversation created
      (newConversationId: string) => {
        if (!conversationId) {
          setConversationId(newConversationId);
        }
      }
    );

    streamAbortRef.current = streamController;
  }, [isLoading, conversationId, memoryLayer, includeGlobal, selectedProvider, selectedModel, agentsEnabled, selectedWorkspace]);

  const getAvailableModels = () => {
    const provider = providers.find(p => p.id === selectedProvider);
    return provider?.models || [];
  };

  const startNewChat = () => {
    setMessages([]);
    setConversationId(null);
    setCurrentReasoning(null);
    setCurrentSources(null);
    setProcessingState({ isProcessing: false, currentAction: '', steps: [], expanded: false });
  };

  return (
    <div className="absolute inset-0 flex flex-col">
      <section className="flex flex-1 h-full min-h-0 w-full max-w-4xl mx-auto flex-col">
        {/* Top Bar */}
        <div className={cn('flex justify-between items-center px-4 md:px-6 shrink-0 gap-3 border-b border-white/5', compactMode ? 'py-2' : 'py-3')}>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={startNewChat}
              className="border-white/10 text-white/70 hover:bg-white/10"
            >
              + New Chat
            </Button>
            <Select
              value={selectedWorkspace || 'none'}
              onValueChange={(v) => {
                if (v === 'none') {
                  setSelectedWorkspace(null);
                  return;
                }
                setSelectedWorkspace(v);
                startNewChat();
              }}
            >
              <SelectTrigger className="h-9 w-52 rounded-xl border-white/10 bg-white/5 text-white/80">
                <SelectValue placeholder="Workspace" />
              </SelectTrigger>
              <SelectContent className="bg-[#0a0520] border-white/10 z-[100]">
                <SelectItem value="none" className="text-white/70">No workspace</SelectItem>
                {workspaces.map((ws) => (
                  <SelectItem key={ws.id} value={ws.id} className="text-white">
                    {ws.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {showReasoning ? (
            <button
              onClick={() => setIsOrchestratorOpen((prev) => !prev)}
              className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/70 transition-colors hover:bg-white/10 hover:text-white"
            >
              <Settings2 className="size-3.5" />
              Orchestrator
            </button>
          ) : null}
        </div>

        {/* Messages Area - Takes full remaining height */}
        <div className={cn('flex-1 min-h-0 overflow-y-auto px-4 md:px-6', compactMode ? 'py-2.5' : 'py-4')}>
          <div className={cn('max-w-3xl mx-auto', compactMode ? 'space-y-4' : 'space-y-6')}>
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
                <div className="mb-6 p-5 rounded-full bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30">
                  <Bot className="w-10 h-10 text-purple-300" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-3">Start a Conversation</h2>
                <p className="text-white/60 max-w-md">
                  Ask anything about your knowledge graph, traverse memory, or explore relationships.
                </p>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div key={message.id} className="space-y-4">
                    {/* User Message */}
                    {message.role === 'user' && (
                      <div className="flex gap-3 items-start">
                        <div className="shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
                          <span className="text-white text-sm font-semibold">Y</span>
                        </div>
                        <div className="flex-1 min-w-0 pt-1">
                          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-white/45 mb-1">You</p>
                          <div className="text-[15px] leading-7 text-white">
                            {message.content}
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Assistant Message */}
                    {message.role === 'assistant' && (
                      <div className="flex gap-3 items-start">
                        <div className="shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-white" />
                        </div>
                        <div className="flex-1 min-w-0 pt-1 space-y-3">
                          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-white/45">NeuroGraph</p>
                           
                          {/* Processing Steps Accordion (shown on completed messages) */}
                          {showReasoning && message.processing_steps && message.processing_steps.length > 0 && (
                            <ProcessingAccordion steps={message.processing_steps} />
                          )}
                          
                          {/* Response */}
                          <div className="text-[15px] leading-7 text-white/90">
                            {message.content}
                          </div>
                          
                          {/* Metadata */}
                          {showConfidence && message.confidence && (
                            <div className="text-xs text-white/40">
                              Confidence: {(message.confidence * 100).toFixed(0)}%
                              {message.sources && message.sources.length > 0 && (
                                <span className="ml-3">{message.sources.length} sources</span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                
                {/* Live Processing State (while loading) */}
                {isLoading && (
                  <div className="flex gap-3 items-start">
                    <div className="shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                    <div className="flex-1 min-w-0 pt-1 space-y-3">
                      <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-white/45">NeuroGraph</p>
                      
                      {/* Live Processing Accordion */}
                      {showReasoning ? (
                        <div className="rounded-xl border border-purple-500/30 bg-purple-500/10 overflow-hidden">
                          <button
                            onClick={() => setProcessingState(p => ({ ...p, expanded: !p.expanded }))}
                            className="w-full flex items-center justify-between px-4 py-3 hover:bg-purple-500/5 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                              <ShinyText
                                text={processingState.currentAction || 'Processing...'}
                                speed={2}
                                className="text-sm font-medium"
                              />
                            </div>
                            {processingState.expanded ? (
                              <ChevronUp className="w-4 h-4 text-white/50" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-white/50" />
                            )}
                          </button>
                          
                          {processingState.expanded && (
                            <div className="px-4 pb-4 space-y-3 border-t border-purple-500/20 pt-3">
                              {processingState.steps.map((step) => (
                                <div key={step.step_number} className="space-y-1.5">
                                  <div className="flex items-center gap-2 text-xs">
                                    <span className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
                                      step.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                                      step.status === 'running' ? 'bg-purple-500/30 text-purple-300' :
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
                                    <span className={step.status === 'running' ? 'text-purple-200 font-medium' : step.status === 'completed' ? 'text-white/70' : 'text-white/40'}>
                                      {step.action}
                                    </span>
                                    {step.duration_ms && (
                                      <span className="text-white/30 ml-auto">{step.duration_ms}ms</span>
                                    )}
                                  </div>
                                  
                                  {/* Step description and details */}
                                  {(step.status === 'running' || step.status === 'completed') && (
                                    <div className="ml-7 space-y-1 text-[11px]">
                                      {step.description && (
                                        <p className="text-white/50">{step.description}</p>
                                      )}
                                      {step.details && step.details.map((detail, idx) => (
                                        <div key={idx} className={`flex gap-2 ${
                                          detail.type === 'connection' ? 'text-cyan-300/70' :
                                          detail.type === 'node' ? 'text-green-300/70' :
                                          detail.type === 'search' ? 'text-yellow-300/70' :
                                          detail.type === 'error' ? 'text-red-400/70' :
                                          detail.type === 'result' ? 'text-purple-300/70' :
                                          'text-white/50'
                                        }`}>
                                          <span className="shrink-0">
                                            {detail.type === 'connection' ? '→' :
                                             detail.type === 'node' ? '◉' :
                                             detail.type === 'search' ? '🔍' :
                                             detail.type === 'error' ? '⚠' :
                                             detail.type === 'result' ? '✓' : '•'}
                                          </span>
                                          <span>{detail.content}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="rounded-xl border border-purple-500/30 bg-purple-500/10 px-4 py-3 text-sm text-purple-100/85">
                          <div className="flex items-center gap-3">
                            <Loader2 className="w-4 h-4 animate-spin text-purple-300" />
                            <span>{processingState.currentAction || 'Processing...'}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mx-4 md:mx-6 mb-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-sm">
            {error}
          </div>
        )}

        {/* Input Area */}
        <div className={cn('shrink-0 px-4 md:px-6 border-t border-white/5', compactMode ? 'pb-3 pt-2' : 'pb-4 pt-3')}>
          <div className="max-w-3xl mx-auto">
            <div className="relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (input.trim() && !isLoading) {
                      handleSend(input.trim());
                      setInput('');
                    }
                  }
                }}
                placeholder="Message NeuroGraph..."
                rows={1}
                disabled={isLoading}
                className="w-full resize-none rounded-2xl border border-white/10 bg-white/5 px-4 py-3 pr-12 text-[15px] text-white placeholder:text-white/40 focus:border-purple-500/50 focus:outline-none focus:ring-1 focus:ring-purple-500/20 disabled:opacity-50 transition-all"
              />
              <button
                onClick={() => {
                  if (input.trim() && !isLoading) {
                    handleSend(input.trim());
                    setInput('');
                  }
                }}
                disabled={!input.trim() || isLoading}
                className="absolute right-2 bottom-2 p-2 rounded-xl bg-purple-500/80 text-white hover:bg-purple-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>

            {/* Chat Settings Row */}
            <div className="flex flex-wrap gap-3 mt-3 items-center">
              {/* Model Selector */}
              <div className="flex items-center gap-2">
                <Select 
                  value={selectedProvider} 
                  onValueChange={(newProvider) => { 
                    setSelectedProvider(newProvider);
                    // Find models for the new provider
                    const newProviderData = providers.find(p => p.id === newProvider);
                    if (newProviderData?.models?.length) {
                      setSelectedModel(newProviderData.models[0].id);
                    }
                  }}
                >
                  <SelectTrigger className="w-28 h-8 text-xs bg-white/5 border-white/10 text-white/70 hover:text-white rounded-lg">
                    <SelectValue placeholder="Provider" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#0a0520] border-white/10 z-[100]">        
                    {providers.filter(p => p.is_available).map(p => (
                      <SelectItem key={p.id} value={p.id} className="text-white text-xs">
                        {p.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={selectedModel} onValueChange={setSelectedModel}>   
                  <SelectTrigger className="w-40 h-8 text-xs bg-white/5 border-white/10 text-white/70 hover:text-white rounded-lg">
                    <Cpu className="w-3 h-3 mr-1" />
                    <SelectValue placeholder="Model" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#0a0520] border-white/10 max-h-60 z-[100]">
                    {getAvailableModels().map(m => (
                      <SelectItem key={m.id} value={m.id} className="text-white text-xs">
                        {m.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="h-4 w-px bg-white/10"></div>
              
              {/* Memory Layer */}
              <Select
                value={memoryLayer}
                onValueChange={(v) => {
                  const nextLayer = v as 'personal' | 'workspace' | 'global';
                  setMemoryLayer(nextLayer);
                  if (nextLayer !== 'workspace') {
                    setSelectedWorkspace(null);
                  } else if (!selectedWorkspace && workspaces.length > 0) {
                    setSelectedWorkspace(workspaces[0].id);
                  }
                }}
              >
                <SelectTrigger className="w-32 h-8 text-xs bg-white/5 border-white/10 text-white/70 hover:text-white rounded-lg">
                  <Brain className="w-3 h-3 mr-1" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#0a0520] border-white/10 z-[100]">        
                  <SelectItem value="personal" className="text-white text-xs">  
                    <span className="flex items-center gap-2">Personal</span>
                  </SelectItem>
                  <SelectItem value="workspace" className="text-white text-xs"> 
                    <span className="flex items-center gap-2">Workspace</span>
                  </SelectItem>
                  <SelectItem value="global" className="text-white text-xs">    
                    <span className="flex items-center gap-2">Global</span>
                  </SelectItem>
                </SelectContent>
              </Select>
              
              <div className="h-4 w-px bg-white/10 ml-auto"></div>

              {/* Agents Toggle */}
              <div className="flex items-center gap-2">
                <Label htmlFor="agents" className="text-xs text-white/70 cursor-pointer flex items-center gap-1.5 hover:text-white">
                  <Zap className={`w-3 h-3 ${agentsEnabled ? "text-purple-400" : "text-white/40"}`} />
                  Agents
                </Label>
                <Switch
                  id="agents"
                  checked={agentsEnabled}
                  onCheckedChange={setAgentsEnabled}
                  className="data-[state=checked]:bg-purple-500 scale-75"
                />
              </div>
            </div>
          </div>
          
          <p className="text-center text-[10px] text-white/30 mt-3 font-light">
            NeuroGraph can make mistakes. Verify important information.
          </p>
        </div>
      </section>

      {/* Orchestrator Panel */}
      {showReasoning && isOrchestratorOpen && (
        <aside className="absolute right-0 top-0 bottom-0 z-10 w-80 border-l border-white/10 bg-[#090512]/95 backdrop-blur-md shadow-2xl">
          <div className="absolute inset-0 flex flex-col">
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






