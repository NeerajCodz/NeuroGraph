// API Service for NeuroGraph Backend

const API_BASE = 'http://localhost:8000/api/v1';

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
  async store(content: string, layer: 'personal' | 'workspace' | 'global' = 'personal') {
    // Map workspace to tenant for backend compatibility
    const backendLayer = layer === 'workspace' ? 'tenant' : layer;
    return request('/memory/remember', {
      method: 'POST',
      body: JSON.stringify({ content, layer: backendLayer }),
    });
  },
  
  async recall(query: string, limit = 10, layers?: string[]) {
    // Map workspace to tenant
    const backendLayers = layers?.map(l => l === 'workspace' ? 'tenant' : l);
    return request('/memory/recall', {
      method: 'POST',
      body: JSON.stringify({ query, max_results: limit, layers: backendLayers }),
    });
  },
  
  async search(query: string, limit = 20) {
    return request(`/memory/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  },
  
  async list(layer: 'personal' | 'workspace' | 'global' = 'personal', limit = 50, offset = 0) {
    const backendLayer = layer === 'workspace' ? 'tenant' : layer;
    return request(`/memory/list?layer=${backendLayer}&limit=${limit}&offset=${offset}`);
  },
  
  async getCount() {
    return request('/memory/count');
  },
  
  async getStatus() {
    return request('/memory/status');
  },
  
  async getById(memoryId: string) {
    return request(`/memory/${memoryId}`);
  },
  
  async delete(memoryId: string) {
    return request(`/memory/${memoryId}`, { method: 'DELETE' });
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

export { ApiError };
