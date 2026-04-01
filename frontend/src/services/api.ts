// API Service for NeuroGraph Backend

const API_BASE = 'http://localhost:8000/api/v1';

// Streaming types
export interface StreamingStepDetail {
  type: 'info' | 'connection' | 'search' | 'node' | 'error' | 'result';
  content: string;
  metadata?: Record<string, unknown>;
}

export interface StreamingStep {
  step_number: number;
  action: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  description: string;
  reasoning: string;
  result?: string;
  duration_ms?: number;
  details: StreamingStepDetail[];
}

export interface StreamingResponse {
  id: string;
  conversation_id: string;
  content: string;
  confidence: number;
  model_used: string;
  provider_used: string;
  sources: Array<{
    node_id: string;
    content: string;
    score: number;
    layer: string;
  }>;
  processing_steps: StreamingStep[];
  graph_paths: Array<{
    source: string;
    relationship: string;
    target: string;
    reason?: string;
  }>;
}

function ApiError(status: number, message: string): Error {
  const error = new Error(message) as Error & { status: number };
  error.name = 'ApiError';
  error.status = status;
  return error;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('access_token');
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw ApiError(response.status, errorData.detail || 'Request failed');
  }
  
  return response.json();
}

// Auth API
export const authApi = {
  async login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw ApiError(response.status, error.detail || 'Login failed');
    }
    
    return response.json();
  },
  
  async register(email: string, password: string, fullName: string) {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
      }),
    });
  },
  
  async getCurrentUser() {
    return request('/auth/me');
  },
  
  async refreshToken(refreshToken: string) {
    return request('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  },
};

// Memory API
export const memoryApi = {
  async store(
    content: string,
    layer: 'personal' | 'workspace' | 'global' = 'personal',
    workspaceId?: string
  ) {
    // Map workspace to tenant for backend compatibility
    const backendLayer = layer === 'workspace' ? 'tenant' : layer;
    const body: Record<string, unknown> = { content, layer: backendLayer };
    if (backendLayer === 'tenant' && workspaceId) {
      body.workspace_id = workspaceId;
      body.tenant_id = workspaceId;
      body.metadata = { workspace_id: workspaceId };
    }
    return request('/memory/remember', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
  
  async recall(query: string, limit = 10, layers?: string[], workspaceId?: string) {
    // Map workspace to tenant
    const backendLayers = layers?.map(l => l === 'workspace' ? 'tenant' : l);
    const body: Record<string, unknown> = { query, max_results: limit, layers: backendLayers };
    if (backendLayers?.includes('tenant') && workspaceId) {
      body.workspace_id = workspaceId;
    }
    return request('/memory/recall', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
  
  async search(query: string, limit = 20, layers?: string[], workspaceId?: string) {
    const params = new URLSearchParams();
    params.append('q', query);
    params.append('limit', String(limit));
    layers?.map(l => l === 'workspace' ? 'tenant' : l).forEach(layer => params.append('layers', layer));
    if (workspaceId) params.append('workspace_id', workspaceId);
    return request(`/memory/search?${params}`);
  },
  
  async list(
    layer: 'personal' | 'workspace' | 'global' = 'personal',
    limit = 50,
    offset = 0,
    workspaceId?: string
  ) {
    const backendLayer = layer === 'workspace' ? 'tenant' : layer;
    const params = new URLSearchParams();
    params.append('layer', backendLayer);
    params.append('limit', String(limit));
    params.append('offset', String(offset));
    if (backendLayer === 'tenant' && workspaceId) params.append('workspace_id', workspaceId);
    return request(`/memory/list?${params}`);
  },
  
  async getCount(workspaceId?: string) {
    return request(`/memory/count${workspaceId ? `?workspace_id=${workspaceId}` : ''}`);
  },
  
  async getStatus(workspaceId?: string) {
    return request(`/memory/status${workspaceId ? `?workspace_id=${workspaceId}` : ''}`);
  },
  
  async getById(memoryId: string) {
    return request(`/memory/${memoryId}`);
  },
  
  async delete(memoryId: string) {
    return request(`/memory/${memoryId}`, { method: 'DELETE' });
  },

  // Canvas operations
  async toggleLock(memoryId: string) {
    return request(`/memory/${memoryId}/lock`, { method: 'PATCH' });
  },

  async updatePosition(memoryId: string, x: number, y: number) {
    return request(`/memory/${memoryId}/position`, {
      method: 'PATCH',
      body: JSON.stringify({ x, y }),
    });
  },

  async duplicate(memoryId: string) {
    return request(`/memory/${memoryId}/duplicate`, { method: 'POST' });
  },

  async getDetail(memoryId: string) {
    return request(`/memory/${memoryId}/detail`);
  },

  // Canvas edges
  async createEdge(sourceId: string, targetId: string, reason?: string | null, confidence?: number) {
    return request('/memory/edges', {
      method: 'POST',
      body: JSON.stringify({ 
        source_id: sourceId, 
        target_id: targetId, 
        reason: reason || undefined,
        confidence: confidence ?? 0.8,
      }),
    });
  },

  async listEdges(layer: 'personal' | 'workspace', workspaceId?: string) {
    const backendLayer = layer === 'workspace' ? 'tenant' : layer;
    const params = new URLSearchParams();
    params.append('layer', backendLayer);
    if (workspaceId) params.append('workspace_id', workspaceId);
    return request(`/memory/edges?${params}`);
  },

  async deleteEdge(edgeId: string) {
    return request(`/memory/edges/${edgeId}`, { method: 'DELETE' });
  },
};

// Chat API
export const chatApi = {
  async sendMessage(
    content: string,
    conversationId?: string,
    layer: 'personal' | 'workspace' | 'global' = 'personal',
    includeGlobal = false,
    provider?: string,
    model?: string,
    agentsEnabled = true,
    workspaceId?: string
  ) {
    return request('/chat/message', {
      method: 'POST',
      body: JSON.stringify({
        content,
        conversation_id: conversationId,
        workspace_id: workspaceId,
        layer,
        include_global: includeGlobal,
        provider,
        model,
        agents_enabled: agentsEnabled,
      }),
    });
  },

  /**
   * Stream chat with SSE for real-time processing updates.
   * Returns an EventSource-like interface that emits events for each pipeline step.
   */
  streamMessage(
    content: string,
    conversationId?: string,
    layer: 'personal' | 'workspace' | 'global' = 'personal',
    includeGlobal = false,
    provider?: string,
    model?: string,
    agentsEnabled = true,
    workspaceId?: string,
    onStep?: (step: StreamingStep) => void,
    onResponse?: (response: StreamingResponse) => void,
    onError?: (error: string) => void,
    onInit?: (conversationId: string) => void
  ): { abort: () => void } {
    const token = localStorage.getItem('access_token');
    const abortController = new AbortController();

    const body = JSON.stringify({
      content,
      conversation_id: conversationId,
      workspace_id: workspaceId,
      layer,
      include_global: includeGlobal,
      provider,
      model,
      agents_enabled: agentsEnabled,
    });

    fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body,
      signal: abortController.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          onError?.(errorData.detail || 'Stream failed');
          return;
        }

        const reader = response.body?.getReader();
        if (!reader) {
          onError?.('No response body');
          return;
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'init') {
                  onInit?.(data.conversation_id);
                } else if (data.type === 'step') {
                  onStep?.(data.data);
                } else if (data.type === 'response') {
                  onResponse?.(data.data);
                } else if (data.type === 'error') {
                  onError?.(data.message);
                }
              } catch {
                // Ignore parse errors
              }
            }
          }
        }
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          onError?.(err.message || 'Stream failed');
        }
      });

    return { abort: () => abortController.abort() };
  },
  
  async getConversations(workspaceId?: string, limit = 50, offset = 0) {
    const params = new URLSearchParams();
    if (workspaceId) params.append('workspace_id', workspaceId);
    params.append('limit', String(limit));
    params.append('offset', String(offset));
    return request(`/chat/conversations?${params}`);
  },
  
  async getConversation(conversationId: string) {
    return request(`/chat/conversations/${conversationId}`);
  },
  
  async deleteConversation(conversationId: string) {
    return request(`/chat/conversations/${conversationId}`, { method: 'DELETE' });
  },
};

// Workspace API
export const workspaceApi = {
  async create(name: string, description?: string, isPublic = false) {
    return request('/workspaces', {
      method: 'POST',
      body: JSON.stringify({ name, description, is_public: isPublic }),
    });
  },
  
  async list(includeShared = true) {
    return request(`/workspaces?include_shared=${includeShared}`);
  },
  
  async get(workspaceId: string) {
    return request(`/workspaces/${workspaceId}`);
  },
  
  async update(workspaceId: string, data: { name?: string; description?: string; is_public?: boolean }) {
    return request(`/workspaces/${workspaceId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },
  
  async delete(workspaceId: string) {
    return request(`/workspaces/${workspaceId}`, { method: 'DELETE' });
  },
  
  async join(workspaceId: string, shareToken: string) {
    return request(`/workspaces/${workspaceId}/join?share_token=${shareToken}`, {
      method: 'POST',
    });
  },
  
  async getMembers(workspaceId: string) {
    return request(`/workspaces/${workspaceId}/members`);
  },
  
  async regenerateToken(workspaceId: string) {
    return request(`/workspaces/${workspaceId}/regenerate-token`, { method: 'POST' });
  },
};

// Conversations API (direct access)
export const conversationsApi = {
  async create(workspaceId?: string, title?: string) {
    return request('/conversations', {
      method: 'POST',
      body: JSON.stringify({ workspace_id: workspaceId, title }),
    });
  },
  
  async list(workspaceId?: string, includeArchived = false, limit = 50) {
    const params = new URLSearchParams();
    if (workspaceId) params.append('workspace_id', workspaceId);
    params.append('include_archived', String(includeArchived));
    params.append('limit', String(limit));
    return request(`/conversations?${params}`);
  },
  
  async get(conversationId: string, includeMessages = true) {
    return request(`/conversations/${conversationId}?include_messages=${includeMessages}`);
  },
  
  async update(conversationId: string, data: { title?: string; is_pinned?: boolean; is_archived?: boolean }) {
    return request(`/conversations/${conversationId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },
  
  async delete(conversationId: string) {
    return request(`/conversations/${conversationId}`, { method: 'DELETE' });
  },
  
  async getSteps(conversationId: string, messageId?: string) {
    const params = messageId ? `?message_id=${messageId}` : '';
    return request(`/conversations/${conversationId}/steps${params}`);
  },
};

// Models API
export const modelsApi = {
  async getProviders() {
    return request('/models/providers');
  },
  
  async getAllModels() {
    return request('/models/all');
  },
  
  async getProviderModels(providerId: string) {
    return request(`/models/provider/${providerId}`);
  },
  
  async getRecommendations() {
    return request('/models/recommendations');
  },
  
  async testModel(providerId: string, modelId: string) {
    return request(`/models/test/${providerId}/${modelId}`, { method: 'POST' });
  },
};

export interface ProfileSettingsPayload {
  default_provider?: string;
  default_model?: string;
  default_memory_layer?: 'personal' | 'workspace' | 'global';
  theme?: 'dark' | 'light' | 'system';
  compact_mode?: boolean;
  show_confidence?: boolean;
  show_reasoning?: boolean;
  agents_enabled?: boolean;
  agent_orchestrator_enabled?: boolean;
  agent_memory_enabled?: boolean;
  agent_web_enabled?: boolean;
  agent_parallel_enabled?: boolean;
  agent_safe_mode?: boolean;
  agent_auto_retry?: boolean;
  auto_memory_update?: boolean;
  analytics_enabled?: boolean;
  sidebar_collapsed?: boolean;
  custom_keys?: Array<{ provider: 'gemini' | 'groq' | 'nvidia'; api_key: string }>;
}

export interface ProfileSettingsResponse {
  user: {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
    created_at: string;
  };
  settings: {
    default_provider: string;
    default_model: string;
    default_memory_layer: 'personal' | 'tenant' | 'global';
    agents_enabled: boolean;
    theme: 'dark' | 'light' | 'system';
    compact_mode: boolean;
    show_confidence: boolean;
    show_reasoning: boolean;
    agent_orchestrator_enabled: boolean;
    agent_memory_enabled: boolean;
    agent_web_enabled: boolean;
    agent_parallel_enabled: boolean;
    agent_safe_mode: boolean;
    agent_auto_retry: boolean;
    auto_memory_update: boolean;
    analytics_enabled: boolean;
    sidebar_collapsed: boolean;
    custom_provider_keys: Record<string, { configured: boolean; masked: string }>;
    available_providers: Array<{
      id: string;
      name: string;
      is_available: boolean;
      models: Array<{ id: string; name: string; type?: string; provider?: string }>;
    }>;
    available_models: Record<string, Array<{ id: string; name: string; type?: string; provider?: string }>>;
  };
}

export const profileApi = {
  async getSettings() {
    return request<ProfileSettingsResponse>('/profile/settings');
  },

  async updateSettings(payload: ProfileSettingsPayload) {
    return request('/profile/settings', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  async updateProfile(fullName: string) {
    return request('/profile/user', {
      method: 'PATCH',
      body: JSON.stringify({ full_name: fullName }),
    });
  },

  async updatePassword(currentPassword: string, newPassword: string, confirmPassword: string) {
    return request('/profile/password', {
      method: 'PATCH',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      }),
    });
  },

  async exportData() {
    return request('/profile/export');
  },
};

// Graph API
export const graphApi = {
  async getEntities(query?: string, types?: string[], layer?: string, limit = 50) {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (types) types.forEach(t => params.append('types', t));
    if (layer) params.append('layer', layer);
    params.append('limit', String(limit));
    
    return request(`/graph/entities?${params}`);
  },
  
  async createEntity(name: string, entityType: string, properties?: Record<string, unknown>, layer = 'personal') {
    return request('/graph/entities', {
      method: 'POST',
      body: JSON.stringify({
        name,
        entity_type: entityType,
        properties,
        layer,
      }),
    });
  },
  
  async getVisualization(centerEntity?: string, depth = 2, maxNodes = 100) {
    const params = new URLSearchParams();
    if (centerEntity) params.append('center_entity', centerEntity);
    params.append('depth', String(depth));
    params.append('max_nodes', String(maxNodes));
    
    return request(`/graph/visualize?${params}`);
  },
  
  async getRelationships(entityId: string, direction = 'both', types?: string[]) {
    const params = new URLSearchParams();
    params.append('direction', direction);
    if (types) types.forEach(t => params.append('types', t));
    
    return request(`/graph/relationships/${entityId}?${params}`);
  },
  
  async createRelationship(
    sourceId: string,
    targetId: string,
    relationshipType: string,
    reason?: string,
    confidence = 1.0
  ) {
    return request('/graph/relationships', {
      method: 'POST',
      body: JSON.stringify({
        source_id: sourceId,
        target_id: targetId,
        relationship_type: relationshipType,
        reason,
        confidence,
      }),
    });
  },
  
  async getCentrality(entityIds?: string[]) {
    const params = new URLSearchParams();
    if (entityIds) entityIds.forEach(id => params.append('entity_ids', id));
    
    return request(`/graph/centrality?${params}`);
  },
  
  async findPaths(sourceId: string, targetId: string, maxDepth = 5) {
    return request(`/graph/paths/${sourceId}/${targetId}?max_depth=${maxDepth}`);
  },
};

// Integrations API
export interface Integration {
  id: string;
  integration_type: string;
  scope: string;
  name: string | null;
  external_id: string | null;
  external_name: string | null;
  enabled: boolean;
  status: string;
  last_sync_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface IntegrationType {
  type: string;
  name: string;
  description: string;
  scopes: string[];
  supports_multiple: boolean;
  oauth_required: boolean;
}

export const integrationsApi = {
  async listConnections(scope?: string, integrationType?: string) {
    const params = new URLSearchParams();
    if (scope) params.append('scope', scope);
    if (integrationType) params.append('integration_type', integrationType);
    return request<{ connections: Integration[] }>(`/integrations/connections?${params}`);
  },

  async getConnection(id: string) {
    return request<Integration>(`/integrations/connections/${id}`);
  },

  async updateConnection(id: string, data: { name?: string; enabled?: boolean }) {
    return request<Integration>(`/integrations/connections/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async deleteConnection(id: string) {
    return request(`/integrations/connections/${id}`, { method: 'DELETE' });
  },

  async getTypes() {
    return request<{ integrations: IntegrationType[] }>('/integrations/types');
  },

  async initiateOAuth(integrationType: string, scope: string, workspaceId?: string) {
    const body: Record<string, unknown> = { integration_type: integrationType, scope };
    if (workspaceId) body.workspace_id = workspaceId;
    return request<{ authorization_url: string }>('/integrations/oauth/initiate', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
};

export { ApiError };
