import { useState, useEffect } from 'react';
import { Plus, Trash2, RefreshCw, Check, X, AlertCircle, Loader2 } from 'lucide-react';
import { SpotlightCard } from '@/components/reactbits/SpotlightCard';
import { BlurText } from '@/components/reactbits/BlurText';
import { integrationsApi, workspaceApi } from '@/services/api';
import type { Integration, IntegrationType } from '@/services/api';
import { cn } from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

// Integration icons
const INTEGRATION_ICONS: Record<string, { icon: string; color: string }> = {
  slack: { icon: '💬', color: 'from-[#4A154B] to-[#E01E5A]' },
  gmail: { icon: '📧', color: 'from-[#EA4335] to-[#FBBC05]' },
  notion: { icon: '📝', color: 'from-[#000000] to-[#FFFFFF]/20' },
  github: { icon: '🐙', color: 'from-[#24292e] to-[#6e5494]' },
};

interface Workspace {
  id: string;
  name: string;
}

const IntegrationCard: React.FC<{
  integration: Integration;
  onToggle: (id: string, enabled: boolean) => void;
  onDelete: (id: string) => void;
  onRename: (id: string, name: string) => void;
}> = ({ integration, onToggle, onDelete, onRename }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(integration.name || '');

  const iconInfo = INTEGRATION_ICONS[integration.integration_type] || { icon: '🔗', color: 'from-purple-500 to-blue-500' };

  const getStatusBadge = () => {
    if (integration.status === 'active') {
      return (
        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-xs">
          <Check className="w-3 h-3" /> Active
        </span>
      );
    } else if (integration.status === 'error') {
      return (
        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 text-xs">
          <X className="w-3 h-3" /> Error
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 text-xs">
        <AlertCircle className="w-3 h-3" /> Pending
      </span>
    );
  };

  const handleSave = async () => {
    await onRename(integration.id, editName);
    setIsEditing(false);
  };

  return (
    <SpotlightCard
      className="relative rounded-2xl border border-white/10 bg-[#0d0620]/80 p-5 backdrop-blur-md"
      spotlightColor="rgba(146, 95, 255, 0.15)"
    >
      {/* Status badge */}
      <div className="absolute top-4 right-4">
        {getStatusBadge()}
      </div>

      {/* Header with icon */}
      <div className="flex items-start gap-4 mb-4">
        <div className={cn(
          "flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br text-3xl",
          iconInfo.color
        )}>
          {iconInfo.icon}
        </div>
        <div className="flex-1 min-w-0">
          {isEditing ? (
            <div className="flex gap-2">
              <Input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="flex-1 h-8 bg-white/5 border-white/10"
                placeholder="Integration name"
                autoFocus
              />
              <Button
                size="sm"
                onClick={handleSave}
                className="h-8 bg-purple-500/20 text-purple-300 hover:bg-purple-500/30"
              >
                Save
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setEditName(integration.name || '');
                  setIsEditing(false);
                }}
                className="h-8"
              >
                Cancel
              </Button>
            </div>
          ) : (
            <h3
              className="text-lg font-semibold text-white truncate cursor-pointer hover:text-purple-300 transition-colors"
              onClick={() => setIsEditing(true)}
            >
              {integration.name || integration.external_name || `${integration.integration_type} connection`}
            </h3>
          )}
          <div className="flex items-center gap-2 mt-1 text-sm text-white/50">
            <span className={cn(
              "px-2 py-0.5 rounded-full text-xs",
              integration.scope === 'personal' 
                ? "bg-blue-500/20 text-blue-300" 
                : "bg-orange-500/20 text-orange-300"
            )}>
              {integration.scope === 'personal' ? '👤 Personal' : '👥 Workspace'}
            </span>
            {integration.external_id && (
              <span className="truncate max-w-[120px]" title={integration.external_id}>
                {integration.external_id}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Last sync info */}
      {integration.last_sync_at && (
        <p className="text-xs text-white/40 mb-3">
          Last synced: {new Date(integration.last_sync_at).toLocaleString()}
        </p>
      )}

      {/* Error message */}
      {integration.last_error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <p className="text-xs text-red-400 line-clamp-2">{integration.last_error}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 mt-auto">
        <Button
          onClick={() => onToggle(integration.id, !integration.enabled)}
          variant="ghost"
          className={cn(
            "flex-1 h-9 rounded-lg font-medium transition-all",
            integration.enabled
              ? "bg-green-500/20 text-green-400 hover:bg-green-500/30"
              : "bg-white/5 text-white/40 hover:bg-white/10"
          )}
        >
          {integration.enabled ? 'Enabled' : 'Disabled'}
        </Button>
        <Button
          onClick={() => {
            if (confirm('Are you sure you want to delete this integration?')) {
              onDelete(integration.id);
            }
          }}
          variant="ghost"
          size="icon"
          className="h-9 w-9 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-lg"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    </SpotlightCard>
  );
};

const AvailableIntegrationCard: React.FC<{
  type: IntegrationType;
  workspaces: Workspace[];
  onAdd: (type: string, scope: string, workspaceId?: string) => void;
}> = ({ type, workspaces, onAdd }) => {
  const [selectedScope, setSelectedScope] = useState<string>(type.scopes[0]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>('');
  const iconInfo = INTEGRATION_ICONS[type.type] || { icon: '🔗', color: 'from-purple-500 to-blue-500' };

  const handleAdd = () => {
    if (selectedScope === 'workspace' && !selectedWorkspace) {
      alert('Please select a workspace');
      return;
    }
    onAdd(type.type, selectedScope, selectedScope === 'workspace' ? selectedWorkspace : undefined);
  };

  return (
    <SpotlightCard
      className="rounded-2xl border border-white/10 bg-[#0d0620]/60 p-5 backdrop-blur-md"
      spotlightColor="rgba(114, 77, 232, 0.12)"
    >
      <div className="flex items-start gap-4 mb-4">
        <div className={cn(
          "flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br text-2xl",
          iconInfo.color
        )}>
          {iconInfo.icon}
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white">{type.name}</h3>
          <p className="text-sm text-white/50 mt-1 line-clamp-2">{type.description}</p>
        </div>
      </div>

      {/* Scope selection */}
      <div className="space-y-3 mb-4">
        {type.scopes.length > 1 && (
          <Select value={selectedScope} onValueChange={setSelectedScope}>
            <SelectTrigger className="h-9 bg-white/5 border-white/10 text-white">
              <SelectValue placeholder="Select scope" />
            </SelectTrigger>
            <SelectContent>
              {type.scopes.map((scope) => (
                <SelectItem key={scope} value={scope}>
                  {scope === 'personal' ? '👤 Personal' : '👥 Workspace'}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {selectedScope === 'workspace' && (
          <Select value={selectedWorkspace} onValueChange={setSelectedWorkspace}>
            <SelectTrigger className="h-9 bg-white/5 border-white/10 text-white">
              <SelectValue placeholder="Select workspace" />
            </SelectTrigger>
            <SelectContent>
              {workspaces.map((ws) => (
                <SelectItem key={ws.id} value={ws.id}>
                  {ws.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Add button */}
      <Button
        onClick={handleAdd}
        className="w-full h-9 bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 rounded-lg"
      >
        <Plus className="w-4 h-4 mr-2" />
        Connect {type.name}
      </Button>

      {type.supports_multiple && (
        <p className="text-xs text-white/30 mt-2 text-center">
          ✓ Supports multiple connections
        </p>
      )}
    </SpotlightCard>
  );
};

export default function Integrations() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [integrationTypes, setIntegrationTypes] = useState<IntegrationType[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedScope, setSelectedScope] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadIntegrations();
  }, [selectedScope, selectedType]);

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadIntegrations(),
        loadIntegrationTypes(),
        loadWorkspaces(),
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadIntegrations = async () => {
    try {
      const scope = selectedScope === 'all' ? undefined : selectedScope;
      const type = selectedType === 'all' ? undefined : selectedType;
      const data = await integrationsApi.listConnections(scope, type);
      setIntegrations(data.connections);
    } catch (error) {
      console.error('Failed to load integrations:', error);
    }
  };

  const loadIntegrationTypes = async () => {
    try {
      const data = await integrationsApi.getTypes();
      setIntegrationTypes(data.integrations);
    } catch (error) {
      console.error('Failed to load integration types:', error);
    }
  };

  const loadWorkspaces = async () => {
    try {
      const result = await workspaceApi.list() as Array<{ id: string; name: string }>;
      const workspacesList = Array.isArray(result) ? result : [];
      const dedupedWorkspaces = Array.from(new Map(workspacesList.map((workspace) => [workspace.id, workspace])).values());
      setWorkspaces(dedupedWorkspaces);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
    }
  };

  const handleToggle = async (id: string, enabled: boolean) => {
    try {
      await integrationsApi.updateConnection(id, { enabled });
      loadIntegrations();
    } catch (error) {
      console.error('Failed to toggle integration:', error);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await integrationsApi.deleteConnection(id);
      loadIntegrations();
    } catch (error) {
      console.error('Failed to delete integration:', error);
    }
  };

  const handleRename = async (id: string, name: string) => {
    try {
      await integrationsApi.updateConnection(id, { name });
      loadIntegrations();
    } catch (error) {
      console.error('Failed to rename integration:', error);
    }
  };

  const handleAddIntegration = async (type: string, scope: string, workspaceId?: string) => {
    try {
      // Try to initiate OAuth
      const result = await integrationsApi.initiateOAuth(type, scope, workspaceId);
      // Redirect to authorization URL
      window.location.href = result.authorization_url;
    } catch (error: unknown) {
      // OAuth not implemented yet - show message
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      if (errorMessage.includes('501')) {
        alert(`OAuth for ${type} is not yet implemented. This feature is coming soon!`);
      } else {
        console.error('Failed to initiate OAuth:', error);
        alert('Failed to connect integration. Please try again.');
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
      </div>
    );
  }

  const personalIntegrations = integrations.filter(i => i.scope === 'personal');
  const workspaceIntegrations = integrations.filter(i => i.scope === 'workspace');

  return (
    <div className="flex flex-1 min-h-0 gap-4 p-4">
      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-0 overflow-auto">
        {/* Header */}
        <div className="mb-6">
          <p className="text-[10px] uppercase tracking-[0.25em] text-purple-200/55">External Connections</p>
          <h1 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">
            <BlurText text="Integrations" delay={34} direction="top" />
          </h1>
          <p className="text-white/50 mt-1">
            Connect your tools to automatically capture and organize information
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-6">
          <Select value={selectedScope} onValueChange={setSelectedScope}>
            <SelectTrigger className="w-[150px] h-9 bg-white/5 border-white/10 text-white">
              <SelectValue placeholder="All Scopes" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Scopes</SelectItem>
              <SelectItem value="personal">👤 Personal</SelectItem>
              <SelectItem value="workspace">👥 Workspace</SelectItem>
            </SelectContent>
          </Select>

          <Select value={selectedType} onValueChange={setSelectedType}>
            <SelectTrigger className="w-[150px] h-9 bg-white/5 border-white/10 text-white">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {integrationTypes.map((type) => (
                <SelectItem key={type.type} value={type.type}>
                  {INTEGRATION_ICONS[type.type]?.icon || '🔗'} {type.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button
            onClick={loadData}
            variant="ghost"
            className="h-9 bg-white/5 text-white/70 hover:bg-white/10"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Connected Integrations */}
        {integrations.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Check className="w-5 h-5 text-green-400" />
              Connected ({integrations.length})
            </h2>

            {/* Personal integrations */}
            {(selectedScope === 'all' || selectedScope === 'personal') && personalIntegrations.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-white/60 mb-3">Personal</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {personalIntegrations.map((integration) => (
                    <IntegrationCard
                      key={integration.id}
                      integration={integration}
                      onToggle={handleToggle}
                      onDelete={handleDelete}
                      onRename={handleRename}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Workspace integrations */}
            {(selectedScope === 'all' || selectedScope === 'workspace') && workspaceIntegrations.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-white/60 mb-3">Workspace</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {workspaceIntegrations.map((integration) => (
                    <IntegrationCard
                      key={integration.id}
                      integration={integration}
                      onToggle={handleToggle}
                      onDelete={handleDelete}
                      onRename={handleRename}
                    />
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {/* Available Integrations */}
        <section>
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Plus className="w-5 h-5 text-purple-400" />
            Available Integrations
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {integrationTypes.map((type) => (
              <AvailableIntegrationCard
                key={type.type}
                type={type}
                workspaces={workspaces}
                onAdd={handleAddIntegration}
              />
            ))}
          </div>
        </section>
      </div>

      {/* Right sidebar - Info panel */}
      <aside className="hidden xl:flex w-80 flex-col gap-4">
        <SpotlightCard
          className="rounded-2xl border border-white/10 bg-[#110829]/90 p-5"
          spotlightColor="rgba(182, 126, 255, 0.22)"
        >
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/45 mb-3">How It Works</p>
          <div className="space-y-3 text-sm text-white/70">
            <p>
              <strong className="text-white">1. Connect</strong> your external tools using OAuth
            </p>
            <p>
              <strong className="text-white">2. Sync</strong> data automatically via webhooks
            </p>
            <p>
              <strong className="text-white">3. View</strong> in Memory Canvas & Knowledge Graph
            </p>
          </div>
        </SpotlightCard>

        <SpotlightCard
          className="rounded-2xl border border-white/10 bg-[#0c0620]/92 p-5"
          spotlightColor="rgba(114, 77, 232, 0.26)"
        >
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/45 mb-3">Data Sources</p>
          <ul className="space-y-2 text-sm text-white/70">
            <li className="flex items-center gap-2">
              <span className="text-lg">💬</span> Slack messages & reactions
            </li>
            <li className="flex items-center gap-2">
              <span className="text-lg">📧</span> Gmail emails & threads
            </li>
            <li className="flex items-center gap-2">
              <span className="text-lg">📝</span> Notion pages & databases
            </li>
            <li className="flex items-center gap-2">
              <span className="text-lg">🐙</span> GitHub issues & PRs
            </li>
          </ul>
        </SpotlightCard>

        <SpotlightCard
          className="rounded-2xl border border-white/10 bg-[#0c0620]/92 p-5"
          spotlightColor="rgba(114, 77, 232, 0.26)"
        >
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/45 mb-3">Stats</p>
          <div className="space-y-2 text-sm text-white/70">
            <div className="flex justify-between">
              <span>Active connections</span>
              <span className="text-white font-medium">
                {integrations.filter(i => i.enabled && i.status === 'active').length}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Personal</span>
              <span className="text-white font-medium">{personalIntegrations.length}</span>
            </div>
            <div className="flex justify-between">
              <span>Workspace</span>
              <span className="text-white font-medium">{workspaceIntegrations.length}</span>
            </div>
          </div>
        </SpotlightCard>
      </aside>
    </div>
  );
}
