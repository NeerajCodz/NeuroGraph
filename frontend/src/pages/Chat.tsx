import { ShinyText } from '@/components/reactbits/ShinyText';
import { 
  Bot, Loader2, ChevronDown, ChevronUp, Cpu, Brain, Zap, Send, Database, Globe,
  Search, Link2, Sparkles, AlertTriangle, CheckCircle, Circle, ArrowRight, Network
} from 'lucide-react';
import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { chatApi, modelsApi, profileApi } from '@/services/api';
import type { StreamingStep, StreamingResponse } from '@/services/api';
import { workspaceApi } from '@/services/api';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Markdown } from '@/components/ui/markdown';
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
  reasoning_output?: string;  // Full reasoning trace from reasoning model
}

const parseProcessingSteps = (value: unknown): ProcessingStep[] => {
  if (!value) return [];
  if (Array.isArray(value)) {
    return (value as ProcessingStep[]).map((step) => {
      if (step.reasoning_output) return step;
      const detailWithReasoning = step.details?.find(
        (d) => typeof d.content === 'string' && d.content.startsWith('Reasoning output: ')
      );
      if (!detailWithReasoning) return step;
      return {
        ...step,
        reasoning_output: detailWithReasoning.content.replace('Reasoning output: ', ''),
      };
    });
  }
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value);
      if (!Array.isArray(parsed)) return [];
      return (parsed as ProcessingStep[]).map((step) => {
        if (step.reasoning_output) return step;
        const detailWithReasoning = step.details?.find(
          (d) => typeof d.content === 'string' && d.content.startsWith('Reasoning output: ')
        );
        if (!detailWithReasoning) return step;
        return {
          ...step,
          reasoning_output: detailWithReasoning.content.replace('Reasoning output: ', ''),
        };
      });
    } catch {
      return [];
    }
  }
  return [];
};

const renderDetailIcon = (type: string) => {
  switch (type) {
    case 'connection': return <ArrowRight className="w-3 h-3 shrink-0" />;
    case 'node': return <Circle className="w-3 h-3 shrink-0 fill-current" />;
    case 'search': return <Search className="w-3 h-3 shrink-0" />;
    case 'error': return <AlertTriangle className="w-3 h-3 shrink-0" />;
    case 'result': return <CheckCircle className="w-3 h-3 shrink-0" />;
    default: return <Circle className="w-2 h-2 shrink-0" />;
  }
};

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
  
  // Guard against non-array steps
  if (!steps || !Array.isArray(steps) || steps.length === 0) {
    return null;
  }
  
  const toggleStep = (stepNum: number) => {
    setExpandedSteps(prev => {
      const next = new Set(prev);
      if (next.has(stepNum)) next.delete(stepNum);
      else next.add(stepNum);
      return next;
    });
  };
  
  const getStepIcon = (action: string) => {
    const actionLower = action.toLowerCase();
    if (actionLower.includes('rag') || actionLower.includes('fetching')) 
      return <Database className="w-3 h-3" />;
    if (actionLower.includes('connected')) 
      return <Link2 className="w-3 h-3" />;
    if (actionLower.includes('graph')) 
      return <Network className="w-3 h-3" />;
    if (actionLower.includes('web') || actionLower.includes('surfing')) 
      return <Globe className="w-3 h-3" />;
    if (actionLower.includes('reasoning')) 
      return <Brain className="w-3 h-3" />;
    if (actionLower.includes('response') || actionLower.includes('generat')) 
      return <Sparkles className="w-3 h-3" />;
    return <Zap className="w-3 h-3" />;
  };
  
  return (
    <div className="rounded-xl border border-white/10 overflow-hidden">
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
                <span className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
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
                    <div key={idx} className={`flex items-center gap-2 ${
                      detail.type === 'connection' ? 'text-cyan-300/70' :
                      detail.type === 'node' ? 'text-green-300/70' :
                      detail.type === 'search' ? 'text-yellow-300/70' :
                      detail.type === 'error' ? 'text-red-400/70' :
                      detail.type === 'result' ? 'text-purple-300/70' :
                      'text-white/50'
                    }`}>
                      {renderDetailIcon(detail.type)}
                      <span>{detail.content}</span>
                    </div>
                  ))}
                  {step.result && (
                    <p className="text-green-300/70"><span className="text-white/40">Result:</span> {step.result}</p>
                  )}
                  {/* Reasoning Output from Reasoning Model */}
                  {step.reasoning_output && (
                    <div className="mt-2 pt-2 border-t border-white/10">
                      <p className="text-white/40 text-[10px] uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                        <Brain className="w-3 h-3" />
                        Reasoning Model Output
                      </p>
                      <div className="bg-black/30 rounded-lg p-2.5 text-[11px] text-cyan-200/80 whitespace-pre-wrap font-mono max-h-40 overflow-y-auto">
                        {step.reasoning_output}
                      </div>
                    </div>
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
  const { compactMode, showReasoning } = useTheme();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const messagesScrollRef = useRef<HTMLDivElement>(null);
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
  
  // Reasoning model selection
  const [selectedReasoningModel, setSelectedReasoningModel] = useState('qwen3-32b');
  const reasoningEnabled = selectedReasoningModel !== 'none';
  const [reasoningModels, setReasoningModels] = useState<Array<{ key: string; id: string; supports_thinking: boolean }>>([]);
  const sessionSources = useMemo(() => {
    const seen = new Set<string>();
    const out: MemorySource[] = [];
    for (const msg of messages) {
      if (msg.role !== 'assistant' || !msg.sources?.length) continue;
      for (const source of msg.sources) {
        const key = `${source.node_id ?? ''}|${source.layer}|${source.content}`;
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(source);
      }
    }
    return out;
  }, [messages]);
  
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
    
    const loadReasoningModels = async () => {
      try {
        const result = await modelsApi.getReasoningModels() as { 
          reasoning_models: Array<{ key: string; id: string; supports_thinking: boolean }>;
          default: string;
        };
        setReasoningModels(result.reasoning_models || []);
        
        // Load saved reasoning model preference
        const savedReasoningModel = localStorage.getItem('ng_reasoning_model');
        if (savedReasoningModel) {
          setSelectedReasoningModel(savedReasoningModel);
        } else if (result.default) {
          setSelectedReasoningModel(result.default);
        }
      } catch (err) {
        console.error('Failed to load reasoning models:', err);
      }
    };
    
    loadModels();
    loadReasoningModels();
  }, []);

  useEffect(() => {
    const loadProfileDefaults = async () => {
      try {
        const profile = await profileApi.getSettings();
        const preferredProvider = profile.settings.default_provider;
        const preferredModel = profile.settings.default_model;
        const preferredLayer = profile.settings.default_memory_layer;
        const preferredAgentsEnabled = profile.settings.agents_enabled;
        const preferredReasoningModel = profile.settings.reasoning_model;

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
        if (preferredReasoningModel) {
          setSelectedReasoningModel(preferredReasoningModel);
          localStorage.setItem('ng_reasoning_model', preferredReasoningModel);
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

  const scrollToBottom = useCallback(() => {
    const container = messagesScrollRef.current;
    if (!container) return;
    requestAnimationFrame(() => {
      container.scrollTop = container.scrollHeight;
    });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Save model preferences
  useEffect(() => {
    localStorage.setItem('ng_default_provider', selectedProvider);
    localStorage.setItem('ng_default_model', selectedModel);
  }, [selectedProvider, selectedModel]);
  
  // Save reasoning model preference
  useEffect(() => {
    localStorage.setItem('ng_reasoning_model', selectedReasoningModel);
  }, [selectedReasoningModel]);
  
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
      // Load conversation messages
      const loadConversation = async () => {
        try {
          setIsLoading(true);
          const conversation = await chatApi.getConversation(routeConversationId) as {
            id: string;
            messages: Array<{
              id: string;
              role: 'user' | 'assistant';
              content: string;
              reasoning_path?: ReasoningStep[] | ProcessingStep[] | string | null;
              sources?: MemorySource[] | null;
              processing_steps?: ProcessingStep[] | string | null;
              confidence?: number;
              created_at: string;
            }>;
          };
          
          // Convert to Message format with processing_steps from DB
          const loadedMessages: Message[] = conversation.messages.map(msg => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            reasoning_path: (() => {
              const parsed = parseProcessingSteps(msg.reasoning_path);
              if (parsed.length > 0) {
                return parsed.map((s) => ({
                  step: s.step_number,
                  action: s.action,
                  result: s.result || '',
                })) as ReasoningStep[];
              }
              return Array.isArray(msg.reasoning_path) ? (msg.reasoning_path as ReasoningStep[]) : undefined;
            })(),
            sources: msg.sources,
            confidence: msg.confidence,
            created_at: msg.created_at,
            // Processing steps are stored in processing_steps (or reasoning_path as fallback)
            processing_steps: (() => {
              const fromProcessingSteps = parseProcessingSteps(msg.processing_steps);
              if (fromProcessingSteps.length > 0) return fromProcessingSteps;
              return parseProcessingSteps(msg.reasoning_path);
            })(),
            graph_paths: [],
          }));
          
          setMessages(loadedMessages);
        } catch (err) {
          console.error('Failed to load conversation:', err);
          setError('Failed to load conversation');
        } finally {
          setIsLoading(false);
        }
      };
      loadConversation();
    } else {
      setConversationId(null);
      setMessages([]);
    }
  }, [routeConversationId]);

  useEffect(() => {
    // Keep window scroll pinned so the chat viewport doesn't drift and reveal page background.
    const resetWindowScroll = () => {
      window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
    };
    resetWindowScroll();
    const rafId = requestAnimationFrame(resetWindowScroll);
    const timeoutId = window.setTimeout(resetWindowScroll, 120);
    return () => {
      cancelAnimationFrame(rafId);
      window.clearTimeout(timeoutId);
    };
  }, [routeConversationId]);

  useEffect(() => {
    const onNewChat = (event: Event) => {
      const detail = (event as CustomEvent<{ workspaceId?: string | null }>).detail;
      const workspaceId = detail?.workspaceId ?? null;
      setMessages([]);
      setConversationId(null);
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
        action: 'Checking connected memories', 
        description: 'Evaluating user-defined memory connections with confidence scoring',
        status: 'pending', 
        reasoning: 'Combining embedding similarity, reason, and edge metadata',
        details: []
      },
      { 
        step_number: 3, 
        action: 'Accessing graph memory', 
        description: 'Traversing knowledge graph for connected concepts',
        status: 'pending', 
        reasoning: 'Following relationships between memory nodes',
        details: []
      },
      { 
        step_number: 4, 
        action: 'Surfing web', 
        description: 'Searching for additional context online',
        status: 'pending', 
        reasoning: 'Fetching current information if memories are insufficient',
        details: []
      },
      { 
        step_number: 5, 
        action: 'Reasoning over context', 
        description: 'Running reasoning model over memory and graph context',
        status: 'pending', 
        reasoning: 'Generate synthesized context and reasoning trace for final LLM',
        details: []
      },
      { 
        step_number: 6, 
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
      reasoningEnabled ? selectedReasoningModel : undefined,
      reasoningEnabled,
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
                  reasoning_output: step.reasoning_output,
              };
            }
            return s;
          });
          if (!updatedSteps.some(s => s.step_number === step.step_number)) {
            updatedSteps.push({
              step_number: step.step_number,
              action: step.action,
              status: step.status,
              description: step.description || '',
              reasoning: step.reasoning || '',
              result: step.result,
              duration_ms: step.duration_ms,
              details: step.details || [],
              reasoning_output: step.reasoning_output,
            });
            updatedSteps.sort((a, b) => a.step_number - b.step_number);
          }
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
  }, [isLoading, conversationId, memoryLayer, includeGlobal, selectedProvider, selectedModel, agentsEnabled, selectedWorkspace, reasoningEnabled, selectedReasoningModel]);

  const getAvailableModels = () => {
    const provider = providers.find(p => p.id === selectedProvider);
    return provider?.models || [];
  };

  return (
    <div className="flex h-full min-h-0 w-full overflow-hidden">
      <section className="relative flex h-full min-h-0 flex-1 flex-col overflow-hidden">
        {/* Messages Area */}
        <div ref={messagesScrollRef} className={cn('flex-1 min-h-0 overflow-y-auto overscroll-contain px-4 md:px-6', compactMode ? 'py-2.5 pb-28' : 'py-4 pb-32')}>
          <div className={cn('mx-auto w-full max-w-5xl', compactMode ? 'space-y-4' : 'space-y-6')}>
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
                          {message.processing_steps && message.processing_steps.length > 0 && (
                            <ProcessingAccordion steps={message.processing_steps} />
                          )}
                          
                          {/* Response */}
                          <div className="text-[15px] leading-7">
                            <Markdown content={message.content} />
                          </div>
                          
                          {/* Metadata */}
                          {message.confidence && (
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
                                        <CheckCircle className="w-3 h-3" />
                                      ) : step.status === 'failed' ? (
                                        <AlertTriangle className="w-3 h-3" />
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
                                        <div key={idx} className={`flex items-center gap-2 ${
                                          detail.type === 'connection' ? 'text-cyan-300/70' :
                                          detail.type === 'node' ? 'text-green-300/70' :
                                          detail.type === 'search' ? 'text-yellow-300/70' :
                                          detail.type === 'error' ? 'text-red-400/70' :
                                          detail.type === 'result' ? 'text-purple-300/70' :
                                          'text-white/50'
                                        }`}>
                                          {renderDetailIcon(detail.type)}
                                          <span>{detail.content}</span>
                                        </div>
                                      ))}
                                      {step.reasoning_output && (
                                        <div className="mt-2 pt-2 border-t border-white/10">
                                          <p className="text-white/40 text-[10px] uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                                            <Brain className="w-3 h-3" />
                                            Reasoning Model Output
                                          </p>
                                          <div className="bg-black/30 rounded-lg p-2.5 text-[11px] text-cyan-200/80 whitespace-pre-wrap font-mono max-h-32 overflow-y-auto">
                                            {step.reasoning_output}
                                          </div>
                                        </div>
                                      )}
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
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mx-4 md:mx-6 mb-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-sm">
            {error}
          </div>
        )}

        {/* Input Area */}
        <div className={cn('absolute inset-x-0 bottom-0 z-10 px-4 md:px-6 border-t border-white/10 bg-[#090512]/95 backdrop-blur-md', compactMode ? 'pb-3 pt-2' : 'pb-4 pt-3')}>
          <div className="mx-auto w-full max-w-5xl">
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

              {/* Reasoning Model */}
              {reasoningModels.length > 0 && (
                <Select value={selectedReasoningModel} onValueChange={setSelectedReasoningModel}>
                  <SelectTrigger className="h-7 w-32 text-xs bg-fuchsia-500/10 border-fuchsia-500/30 text-fuchsia-200 hover:text-white rounded-lg">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#0a0520] border-fuchsia-500/20 z-[100]">
                    <SelectItem value="none" className="text-white/70 text-xs">
                      None
                    </SelectItem>
                    {reasoningModels.map((m) => (
                      <SelectItem key={m.key} value={m.key} className="text-white text-xs">
                        <span className="flex items-center gap-1.5">
                          {m.key}
                          {m.supports_thinking && (
                            <span className="text-[8px] text-fuchsia-400 bg-fuchsia-500/20 px-1 rounded">think</span>
                          )}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
          </div>
          
          <p className="text-center text-[10px] text-white/30 mt-3 font-light">
            NeuroGraph can make mistakes. Verify important information.
          </p>
        </div>
      </section>

      <aside className="hidden h-full w-80 shrink-0 border-l border-white/10 bg-[#090512]/92 backdrop-blur-md lg:flex lg:flex-col">
        <div className="border-b border-white/10 p-4">
          <h3 className="text-sm font-semibold text-white">Session Memories</h3>
          <p className="mt-1 text-[10px] uppercase tracking-[0.2em] text-purple-200/60">Accessed in current chat</p>
        </div>

        <div className="border-b border-white/10 p-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/45">Memory Layer</p>
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
            <SelectTrigger className="h-8 w-full rounded-lg border-white/10 bg-white/5 text-xs text-white/80">
              <Brain className="mr-1 h-3 w-3" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="z-[100] border-white/10 bg-[#0a0520]">
              <SelectItem value="personal" className="text-xs text-white">Personal</SelectItem>
              <SelectItem value="workspace" className="text-xs text-white">Workspace</SelectItem>
              <SelectItem value="global" className="text-xs text-white">Global</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="scrollbar-thin flex-1 space-y-2 overflow-y-auto p-4">
          {sessionSources.length > 0 ? (
            sessionSources.map((source, idx) => (
              <div key={`${source.node_id ?? idx}-${idx}`} className="rounded-xl border border-white/10 bg-white/5 p-3">
                <p className="line-clamp-3 text-xs leading-relaxed text-white/80">{source.content}</p>
                <div className="mt-2 flex items-center justify-between text-[10px] text-white/45">
                  <span className="inline-flex items-center gap-1">
                    <Database className="h-3 w-3" />
                    {source.layer}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Globe className="h-3 w-3" />
                    {(source.score * 100).toFixed(0)}%
                  </span>
                </div>
                {source.node_id ? (
                  <p className="mt-1 truncate text-[10px] text-white/35">{source.node_id}</p>
                ) : null}
              </div>
            ))
          ) : (
            <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-xs text-white/50">
              No memories accessed yet in this session.
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}






