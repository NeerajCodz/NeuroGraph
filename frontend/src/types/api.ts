// API Types for NeuroGraph

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Memory {
  id: string;
  content: string;
  layer: 'personal' | 'tenant' | 'global';
  confidence: number;
  created_at: string;
  score?: number;
  entities?: string[];
}

export interface MemoryRecallResult {
  node_id: string;
  content: string;
  layer: string;
  confidence: number;
  score: number;
  final_score: number;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  reasoning_path?: ReasoningStep[];
  sources?: MemorySource[];
  confidence?: number;
  created_at: string;
}

export interface ReasoningStep {
  step: number;
  action: string;
  result: string;
  details?: Record<string, unknown>;
}

export interface MemorySource {
  node_id: string;
  content: string;
  score: number;
  layer: string;
}

export interface ChatResponse {
  id: string;
  conversation_id: string;
  content: string;
  reasoning_path: ReasoningStep[] | null;
  sources: MemorySource[] | null;
  confidence: number;
  created_at: string;
}

export interface GraphEntity {
  id: string;
  name: string;
  type: string;
  layer: string;
  properties: Record<string, unknown>;
}

export interface GraphRelationship {
  id: string;
  source_id: string;
  target_id: string;
  type: string;
  reason: string | null;
  confidence: number;
}

export interface GraphVisualization {
  nodes: GraphNode[];
  edges: GraphEdge[];
  reasoning_paths: unknown[] | null;
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  layer: string;
  confidence?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  reason: string | null;
  confidence: number;
}

export interface Centrality {
  [entityId: string]: number;
}
