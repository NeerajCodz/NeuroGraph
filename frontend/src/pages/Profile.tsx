import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Activity,
  Bot,
  Brain,
  Check,
  Cpu,
  Download,
  Eye,
  Loader2,
  Save,
  Settings2,
  Shield,
  SlidersHorizontal,
  SunMoon,
  Zap,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { modelsApi, profileApi, type ProfileSettingsResponse } from '@/services/api';

type ProfileSection = 'profile' | 'agents' | 'models' | 'preferences' | 'integrations' | 'security' | 'settings';

interface SaveState {
  isSaving: boolean;
  isSaved: boolean;
  error: string;
}

interface AgentFlags {
  agentsEnabled: boolean;
  orchestratorEnabled: boolean;
  memoryEnabled: boolean;
  webEnabled: boolean;
  parallelEnabled: boolean;
  safeModeEnabled: boolean;
  autoRetryEnabled: boolean;
  autoMemoryUpdate: boolean;
}

interface ModelState {
  provider: string;
  model: string;
  layer: 'personal' | 'workspace' | 'global';
  customKeys: {
    gemini: string;
    groq: string;
    nvidia: string;
  };
  testingProvider: string | null;
  testStatus: Record<string, { ok: boolean; message: string }>;
}

interface AppearanceState {
  theme: 'dark' | 'light' | 'system';
  compactMode: boolean;
  showConfidence: boolean;
  showReasoning: boolean;
}

const cardClass =
  'rounded-3xl border border-white/20 bg-white/10 backdrop-blur-2xl shadow-[inset_0_1px_0_rgba(255,255,255,0.24),0_20px_48px_-24px_rgba(0,0,0,0.65)]';

const inputClass = 'mt-1.5 bg-white/8 border-white/20 text-white placeholder:text-white/45';

function SaveButton({ state, onClick, label = 'Save Changes' }: { state: SaveState; onClick: () => void; label?: string }) {
  return (
    <div className="flex items-center justify-end gap-3">
      {state.error ? <p className="text-xs text-red-300">{state.error}</p> : null}
      <Button
        onClick={onClick}
        disabled={state.isSaving}
        className="bg-gradient-to-r from-purple-500/90 via-fuchsia-500/85 to-violet-500/90 text-white shadow-lg"
      >
        {state.isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
        {!state.isSaving && state.isSaved ? <Check className="mr-2 h-4 w-4" /> : null}
        {state.isSaving ? 'Saving...' : state.isSaved ? 'Saved' : label}
      </Button>
    </div>
  );
}

export default function Profile() {
  const location = useLocation();
  const { user, refreshUser } = useAuth();
  const {
    theme,
    setTheme,
    compactMode,
    setCompactMode,
    showConfidence,
    setShowConfidence,
    showReasoning,
    setShowReasoning,
    sidebarCollapsed,
    setSidebarCollapsed,
  } = useTheme();

  const section = (location.pathname.split('/')[2] || 'profile') as ProfileSection;
  const [isLoading, setIsLoading] = useState(true);
  const [globalError, setGlobalError] = useState('');
  const [settingsSnapshot, setSettingsSnapshot] = useState<ProfileSettingsResponse | null>(null);

  const [fullName, setFullName] = useState('');
  const [profileSave, setProfileSave] = useState<SaveState>({ isSaving: false, isSaved: false, error: '' });

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [securitySave, setSecuritySave] = useState<SaveState>({ isSaving: false, isSaved: false, error: '' });

  const [agents, setAgents] = useState<AgentFlags>({
    agentsEnabled: true,
    orchestratorEnabled: true,
    memoryEnabled: true,
    webEnabled: true,
    parallelEnabled: true,
    safeModeEnabled: true,
    autoRetryEnabled: true,
    autoMemoryUpdate: true,
  });
  const [agentsSave, setAgentsSave] = useState<SaveState>({ isSaving: false, isSaved: false, error: '' });

  const [models, setModels] = useState<ModelState>({
    provider: 'gemini',
    model: 'gemini-2.0-flash',
    layer: 'personal',
    customKeys: { gemini: '', groq: '', nvidia: '' },
    testingProvider: null,
    testStatus: {},
  });
  const [modelSave, setModelSave] = useState<SaveState>({ isSaving: false, isSaved: false, error: '' });

  const [appearance, setAppearance] = useState<AppearanceState>({
    theme: theme,
    compactMode,
    showConfidence,
    showReasoning,
  });
  const [appearanceSave, setAppearanceSave] = useState<SaveState>({ isSaving: false, isSaved: false, error: '' });

  const [analyticsEnabled, setAnalyticsEnabled] = useState(true);
  const [settingsSave, setSettingsSave] = useState<SaveState>({ isSaving: false, isSaved: false, error: '' });
  const [exporting, setExporting] = useState(false);

  const providers = settingsSnapshot?.settings.available_providers || [];
  const providerModels = useMemo(
    () => settingsSnapshot?.settings.available_models?.[models.provider] || [],
    [settingsSnapshot, models.provider],
  );

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setIsLoading(true);
      setGlobalError('');
      try {
        const data = await profileApi.getSettings();
        if (cancelled) return;

        setSettingsSnapshot(data);
        setFullName(data.user.full_name || user?.full_name || '');
        setAgents({
          agentsEnabled: data.settings.agents_enabled,
          orchestratorEnabled: data.settings.agent_orchestrator_enabled,
          memoryEnabled: data.settings.agent_memory_enabled,
          webEnabled: data.settings.agent_web_enabled,
          parallelEnabled: data.settings.agent_parallel_enabled,
          safeModeEnabled: data.settings.agent_safe_mode,
          autoRetryEnabled: data.settings.agent_auto_retry,
          autoMemoryUpdate: data.settings.auto_memory_update,
        });
        setModels({
          provider: data.settings.default_provider,
          model: data.settings.default_model,
          layer: data.settings.default_memory_layer === 'tenant' ? 'workspace' : data.settings.default_memory_layer,
          customKeys: { gemini: '', groq: '', nvidia: '' },
          testingProvider: null,
          testStatus: {},
        });
        setAppearance({
          theme: data.settings.theme,
          compactMode: data.settings.compact_mode,
          showConfidence: data.settings.show_confidence,
          showReasoning: data.settings.show_reasoning,
        });
        setAnalyticsEnabled(data.settings.analytics_enabled);
      } catch (err) {
        setGlobalError(err instanceof Error ? err.message : 'Failed to load profile settings');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [user?.full_name]);

  useEffect(() => {
    if (!providerModels.some((m) => m.id === models.model) && providerModels.length > 0) {
      setModels((prev) => ({ ...prev, model: providerModels[0].id }));
    }
  }, [providerModels, models.model]);

  const pulseSaved = (setter: (state: SaveState) => void) => {
    setter({ isSaving: false, isSaved: true, error: '' });
    setTimeout(() => setter({ isSaving: false, isSaved: false, error: '' }), 1800);
  };

  const saveProfile = async () => {
    setProfileSave({ isSaving: true, isSaved: false, error: '' });
    try {
      await profileApi.updateProfile(fullName.trim());
      await refreshUser();
      pulseSaved(setProfileSave);
    } catch (err) {
      setProfileSave({ isSaving: false, isSaved: false, error: err instanceof Error ? err.message : 'Failed to save profile' });
    }
  };

  const saveSecurity = async () => {
    setSecuritySave({ isSaving: true, isSaved: false, error: '' });
    try {
      await profileApi.updatePassword(currentPassword, newPassword, confirmPassword);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      pulseSaved(setSecuritySave);
    } catch (err) {
      setSecuritySave({ isSaving: false, isSaved: false, error: err instanceof Error ? err.message : 'Failed to update password' });
    }
  };

  const saveAgents = async () => {
    setAgentsSave({ isSaving: true, isSaved: false, error: '' });
    try {
      await profileApi.updateSettings({
        agents_enabled: agents.agentsEnabled,
        agent_orchestrator_enabled: agents.orchestratorEnabled,
        agent_memory_enabled: agents.memoryEnabled,
        agent_web_enabled: agents.webEnabled,
        agent_parallel_enabled: agents.parallelEnabled,
        agent_safe_mode: agents.safeModeEnabled,
        agent_auto_retry: agents.autoRetryEnabled,
        auto_memory_update: agents.autoMemoryUpdate,
      });
      pulseSaved(setAgentsSave);
    } catch (err) {
      setAgentsSave({ isSaving: false, isSaved: false, error: err instanceof Error ? err.message : 'Failed to save agent settings' });
    }
  };

  const saveModels = async () => {
    setModelSave({ isSaving: true, isSaved: false, error: '' });
    try {
      const customKeys = (['gemini', 'groq', 'nvidia'] as const)
        .filter((provider) => models.customKeys[provider].trim().length > 0)
        .map((provider) => ({ provider, api_key: models.customKeys[provider].trim() }));

      await profileApi.updateSettings({
        default_provider: models.provider,
        default_model: models.model,
        default_memory_layer: models.layer,
        custom_keys: customKeys.length > 0 ? customKeys : undefined,
      });
      localStorage.setItem('ng_default_provider', models.provider);
      localStorage.setItem('ng_default_model', models.model);
      localStorage.setItem('ng_default_layer', models.layer === 'workspace' ? 'tenant' : models.layer);
      const refreshed = await profileApi.getSettings();
      setSettingsSnapshot(refreshed);
      setModels((prev) => ({ ...prev, customKeys: { gemini: '', groq: '', nvidia: '' } }));
      pulseSaved(setModelSave);
    } catch (err) {
      setModelSave({ isSaving: false, isSaved: false, error: err instanceof Error ? err.message : 'Failed to save model settings' });
    }
  };

  const testProvider = async (provider: 'gemini' | 'groq' | 'nvidia') => {
    const providerInfo = providers.find((p) => p.id === provider);
    const testModel = providerInfo?.models?.[0]?.id;
    if (!testModel) return;

    setModels((prev) => ({ ...prev, testingProvider: provider }));
    try {
      const result = await modelsApi.testModel(provider, testModel) as {
        success: boolean;
        error?: string;
        used_custom_key?: boolean;
      };
      setModels((prev) => ({
        ...prev,
        testingProvider: null,
        testStatus: {
          ...prev.testStatus,
          [provider]: {
            ok: Boolean(result.success),
            message: result.success
              ? result.used_custom_key
                ? 'Connection verified (using your custom key)'
                : 'Connection verified'
              : result.error || 'Test failed',
          },
        },
      }));
    } catch (err) {
      setModels((prev) => ({
        ...prev,
        testingProvider: null,
        testStatus: {
          ...prev.testStatus,
          [provider]: { ok: false, message: err instanceof Error ? err.message : 'Test failed' },
        },
      }));
    }
  };

  const saveAppearance = async () => {
    setAppearanceSave({ isSaving: true, isSaved: false, error: '' });
    try {
      setTheme(appearance.theme);
      setCompactMode(appearance.compactMode);
      setShowConfidence(appearance.showConfidence);
      setShowReasoning(appearance.showReasoning);

      await profileApi.updateSettings({
        theme: appearance.theme,
        compact_mode: appearance.compactMode,
        show_confidence: appearance.showConfidence,
        show_reasoning: appearance.showReasoning,
        sidebar_collapsed: sidebarCollapsed,
      });
      const refreshed = await profileApi.getSettings();
      setSettingsSnapshot(refreshed);
      pulseSaved(setAppearanceSave);
    } catch (err) {
      setAppearanceSave({ isSaving: false, isSaved: false, error: err instanceof Error ? err.message : 'Failed to save appearance settings' });
    }
  };

  const saveGeneralSettings = async () => {
    setSettingsSave({ isSaving: true, isSaved: false, error: '' });
    try {
      await profileApi.updateSettings({ analytics_enabled: analyticsEnabled, sidebar_collapsed: sidebarCollapsed });
      const refreshed = await profileApi.getSettings();
      setSettingsSnapshot(refreshed);
      pulseSaved(setSettingsSave);
    } catch (err) {
      setSettingsSave({ isSaving: false, isSaved: false, error: err instanceof Error ? err.message : 'Failed to save settings' });
    }
  };

  const exportData = async () => {
    setExporting(true);
    setSettingsSave((prev) => ({ ...prev, error: '' }));
    try {
      const payload = await profileApi.exportData();
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `neurograph-export-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setSettingsSave((prev) => ({ ...prev, error: err instanceof Error ? err.message : 'Export failed' }));
    } finally {
      setExporting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-purple-300" />
      </div>
    );
  }

  const renderProfile = () => (
    <div className="space-y-6">
      <section className={`${cardClass} p-6`}>
        <h2 className="mb-1 text-xl font-semibold text-white">Profile</h2>
        <p className="mb-5 text-sm text-white/65">Update your account details and identity.</p>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label className="text-white/75">Full Name</Label>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} className={inputClass} />
          </div>
          <div>
            <Label className="text-white/75">Email</Label>
            <Input value={user?.email || settingsSnapshot?.user.email || ''} readOnly className={`${inputClass} opacity-80`} />
          </div>
        </div>

        <div className="mt-5 grid gap-3 rounded-2xl border border-white/15 bg-black/20 p-4 text-xs text-white/65 md:grid-cols-2">
          <p>
            User ID: <span className="font-mono text-white/85">{user?.id || settingsSnapshot?.user.id}</span>
          </p>
          <p>
            Created: <span className="text-white/85">{new Date(user?.created_at || settingsSnapshot?.user.created_at || '').toLocaleString()}</span>
          </p>
        </div>
      </section>

      <SaveButton state={profileSave} onClick={saveProfile} />
    </div>
  );

  const renderAgents = () => (
    <div className="space-y-6">
      <section className={`${cardClass} p-6`}>
        <h2 className="mb-1 text-xl font-semibold text-white">Agents</h2>
        <p className="mb-5 text-sm text-white/65">Fine tune orchestration, memory and safety controls.</p>

        <div className="space-y-4">
          {[
            {
              key: 'agentsEnabled',
              title: 'Enable Agents',
              desc: 'Master switch for agent-based reasoning and context assembly.',
              icon: Bot,
            },
            {
              key: 'orchestratorEnabled',
              title: 'Orchestrator Agent',
              desc: 'Routes each prompt to the best processing strategy.',
              icon: Activity,
            },
            {
              key: 'memoryEnabled',
              title: 'Memory Agent',
              desc: 'Retrieves relevant graph memories automatically.',
              icon: Brain,
            },
            {
              key: 'webEnabled',
              title: 'Web Agent',
              desc: 'Allows web-assisted enrichment when memory is insufficient.',
              icon: Zap,
            },
            {
              key: 'parallelEnabled',
              title: 'Parallel Planning',
              desc: 'Run independent agent tasks concurrently for faster results.',
              icon: Cpu,
            },
            {
              key: 'safeModeEnabled',
              title: 'Safe Mode',
              desc: 'Adds conservative checks before tool execution.',
              icon: Shield,
            },
            {
              key: 'autoRetryEnabled',
              title: 'Auto Retry',
              desc: 'Retry failed model/tool calls automatically when safe.',
              icon: Settings2,
            },
            {
              key: 'autoMemoryUpdate',
              title: 'Auto Memory Update',
              desc: 'Persist useful conversation insights to memory.',
              icon: Save,
            },
          ].map((item) => {
            const Icon = item.icon;
            const key = item.key as keyof AgentFlags;
            return (
              <div key={item.key} className="flex items-center justify-between rounded-2xl border border-white/15 bg-black/20 px-4 py-3">
                <div>
                  <p className="flex items-center gap-2 text-sm font-medium text-white">
                    <Icon className="h-4 w-4 text-purple-300" />
                    {item.title}
                  </p>
                  <p className="mt-0.5 text-xs text-white/55">{item.desc}</p>
                </div>
                <Switch
                  checked={agents[key]}
                  onCheckedChange={(value) => setAgents((prev) => ({ ...prev, [key]: value }))}
                />
              </div>
            );
          })}
        </div>
      </section>

      <SaveButton state={agentsSave} onClick={saveAgents} />
    </div>
  );

  const renderModels = () => (
    <div className="space-y-6">
      <section className={`${cardClass} p-6`}>
        <h2 className="mb-1 text-xl font-semibold text-white">AI Models</h2>
        <p className="mb-5 text-sm text-white/65">Choose providers/models and optionally use your own API keys.</p>

        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <Label className="text-white/75">Provider</Label>
            <Select value={models.provider} onValueChange={(value) => setModels((prev) => ({ ...prev, provider: value }))}>
              <SelectTrigger className={inputClass}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="border-white/20 bg-[#100828] text-white">
                {providers.map((provider) => (
                  <SelectItem key={provider.id} value={provider.id}>
                    {provider.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-white/75">Model</Label>
            <Select value={models.model} onValueChange={(value) => setModels((prev) => ({ ...prev, model: value }))}>
              <SelectTrigger className={inputClass}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="max-h-72 border-white/20 bg-[#100828] text-white">
                {providerModels.map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    {model.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-white/75">Default Memory Layer</Label>
            <Select
              value={models.layer}
              onValueChange={(value) => setModels((prev) => ({ ...prev, layer: value as 'personal' | 'workspace' | 'global' }))}
            >
              <SelectTrigger className={inputClass}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="border-white/20 bg-[#100828] text-white">
                <SelectItem value="personal">Personal</SelectItem>
                <SelectItem value="workspace">Workspace</SelectItem>
                <SelectItem value="global">Global</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </section>

      <section className={`${cardClass} p-6`}>
        <h3 className="mb-4 text-lg font-semibold text-white">Bring Your Own API Keys</h3>
        <div className="grid gap-4 md:grid-cols-3">
          {(['gemini', 'groq', 'nvidia'] as const).map((provider) => (
            <div key={provider} className="rounded-2xl border border-white/15 bg-black/20 p-4">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm font-medium capitalize text-white">{provider}</p>
                <Badge
                  className={
                    settingsSnapshot?.settings.custom_provider_keys?.[provider]?.configured
                      ? 'border-emerald-400/30 bg-emerald-500/20 text-emerald-200'
                      : 'border-white/20 bg-white/10 text-white/70'
                  }
                >
                  {settingsSnapshot?.settings.custom_provider_keys?.[provider]?.configured ? 'Configured' : 'Not Set'}
                </Badge>
              </div>
              <Input
                placeholder={`Paste ${provider.toUpperCase()} key`}
                type="password"
                value={models.customKeys[provider]}
                onChange={(e) =>
                  setModels((prev) => ({
                    ...prev,
                    customKeys: { ...prev.customKeys, [provider]: e.target.value },
                  }))
                }
                className={inputClass}
              />
              {settingsSnapshot?.settings.custom_provider_keys?.[provider]?.masked ? (
                <p className="mt-2 text-[11px] text-white/50">
                  Current: {settingsSnapshot.settings.custom_provider_keys[provider].masked}
                </p>
              ) : null}
              <Button
                variant="outline"
                size="sm"
                className="mt-3 w-full border-white/25 bg-white/10 text-white hover:bg-white/15"
                onClick={() => testProvider(provider)}
                disabled={models.testingProvider === provider}
              >
                {models.testingProvider === provider ? <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" /> : <Eye className="mr-2 h-3.5 w-3.5" />}
                Test Provider
              </Button>
              {models.testStatus[provider] ? (
                <p className={`mt-2 text-xs ${models.testStatus[provider].ok ? 'text-emerald-300' : 'text-red-300'}`}>
                  {models.testStatus[provider].message}
                </p>
              ) : null}
            </div>
          ))}
        </div>
      </section>

      <section className={`${cardClass} p-6`}>
        <h3 className="mb-4 text-lg font-semibold text-white">Available Providers</h3>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {providers.map((provider) => (
            <div key={provider.id} className="rounded-2xl border border-white/15 bg-black/20 p-4">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-medium text-white">{provider.name}</p>
                <Badge className={provider.is_available ? 'border-emerald-400/30 bg-emerald-500/20 text-emerald-200' : 'border-red-400/30 bg-red-500/20 text-red-200'}>
                  {provider.is_available ? 'Live' : 'Server Key Missing'}
                </Badge>
              </div>
              <p className="text-xs text-white/55">{provider.models.length} models available</p>
            </div>
          ))}
        </div>
      </section>

      <SaveButton state={modelSave} onClick={saveModels} />
    </div>
  );

  const renderPreferences = () => (
    <div className="space-y-6">
      <section className={`${cardClass} p-6`}>
        <h2 className="mb-1 text-xl font-semibold text-white">Preferences</h2>
        <p className="mb-5 text-sm text-white/65">Theme, density and chat display preferences.</p>

        <div className="space-y-4">
          <div className="flex items-center justify-between rounded-2xl border border-white/15 bg-black/20 px-4 py-3">
            <div>
              <p className="flex items-center gap-2 text-sm font-medium text-white">
                <SunMoon className="h-4 w-4 text-purple-300" />
                Theme
              </p>
              <p className="text-xs text-white/55">Switch between dark, light, and system mode.</p>
            </div>
            <Select
              value={appearance.theme}
              onValueChange={(value) => setAppearance((prev) => ({ ...prev, theme: value as 'dark' | 'light' | 'system' }))}
            >
              <SelectTrigger className="h-8 w-32 bg-white/8 border-white/20 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="border-white/20 bg-[#100828] text-white">
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between rounded-2xl border border-white/15 bg-black/20 px-4 py-3">
            <div>
              <p className="flex items-center gap-2 text-sm font-medium text-white">
                <SlidersHorizontal className="h-4 w-4 text-purple-300" />
                Compact Mode
              </p>
              <p className="text-xs text-white/55">Reduce paddings and spacing for dense workspace usage.</p>
            </div>
            <Switch checked={appearance.compactMode} onCheckedChange={(value) => setAppearance((prev) => ({ ...prev, compactMode: value }))} />
          </div>

          <div className="flex items-center justify-between rounded-2xl border border-white/15 bg-black/20 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-white">Show Confidence Scores</p>
              <p className="text-xs text-white/55">Display model confidence on assistant responses.</p>
            </div>
            <Switch checked={appearance.showConfidence} onCheckedChange={(value) => setAppearance((prev) => ({ ...prev, showConfidence: value }))} />
          </div>

          <div className="flex items-center justify-between rounded-2xl border border-white/15 bg-black/20 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-white">Show Reasoning Stream</p>
              <p className="text-xs text-white/55">Show orchestrator steps and reasoning panel in chat.</p>
            </div>
            <Switch checked={appearance.showReasoning} onCheckedChange={(value) => setAppearance((prev) => ({ ...prev, showReasoning: value }))} />
          </div>
        </div>
      </section>

      <SaveButton state={appearanceSave} onClick={saveAppearance} />
    </div>
  );

  const renderIntegrations = () => (
    <section className={`${cardClass} p-6`}>
      <h2 className="mb-1 text-xl font-semibold text-white">Integrations</h2>
      <p className="text-sm text-white/65">As requested, this section is intentionally left non-functional for now.</p>
      <div className="mt-4 rounded-2xl border border-white/15 bg-black/20 p-4 text-sm text-white/65">
        Integrations are excluded from this rollout.
      </div>
    </section>
  );

  const renderSecurity = () => (
    <div className="space-y-6">
      <section className={`${cardClass} p-6`}>
        <h2 className="mb-1 text-xl font-semibold text-white">Security</h2>
        <p className="mb-5 text-sm text-white/65">Update account password.</p>

        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <Label className="text-white/75">Current Password</Label>
            <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className={inputClass} />
          </div>
          <div>
            <Label className="text-white/75">New Password</Label>
            <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className={inputClass} />
          </div>
          <div>
            <Label className="text-white/75">Confirm Password</Label>
            <Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className={inputClass} />
          </div>
        </div>
      </section>

      <SaveButton state={securitySave} onClick={saveSecurity} label="Update Password" />
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6">
      <section className={`${cardClass} p-6`}>
        <h2 className="mb-1 text-xl font-semibold text-white">Advanced Settings</h2>
        <p className="mb-5 text-sm text-white/65">Workspace-wide controls, export and sidebar behavior.</p>

        <div className="space-y-4">
          <div className="flex items-center justify-between rounded-2xl border border-white/15 bg-black/20 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-white">Analytics</p>
              <p className="text-xs text-white/55">Share anonymous performance diagnostics.</p>
            </div>
            <Switch checked={analyticsEnabled} onCheckedChange={setAnalyticsEnabled} />
          </div>

          <div className="flex items-center justify-between rounded-2xl border border-white/15 bg-black/20 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-white">Collapse Sidebar by Default</p>
              <p className="text-xs text-white/55">Applies to all authenticated pages including profile/settings.</p>
            </div>
            <Switch checked={sidebarCollapsed} onCheckedChange={setSidebarCollapsed} />
          </div>

          <div className="flex items-center justify-between rounded-2xl border border-white/15 bg-black/20 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-white">Export Data</p>
              <p className="text-xs text-white/55">Download profile, settings, conversations, messages, and memories.</p>
            </div>
            <Button
              variant="outline"
              className="border-white/25 bg-white/10 text-white hover:bg-white/15"
              onClick={exportData}
              disabled={exporting}
            >
              {exporting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
              {exporting ? 'Exporting...' : 'Export JSON'}
            </Button>
          </div>
        </div>
      </section>

      <SaveButton state={settingsSave} onClick={saveGeneralSettings} />
    </div>
  );

  const content = (() => {
    if (section === 'profile') return renderProfile();
    if (section === 'agents') return renderAgents();
    if (section === 'models') return renderModels();
    if (section === 'preferences') return renderPreferences();
    if (section === 'integrations') return renderIntegrations();
    if (section === 'security') return renderSecurity();
    return renderSettings();
  })();

  return (
    <div className="mx-auto w-full max-w-7xl p-4 md:p-6">
      <div className="mb-5">
        <p className="text-xs uppercase tracking-[0.22em] text-white/45">Profile Workspace</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-white">Profile & Settings</h1>
        <p className="mt-2 text-sm text-white/60">
          Unified controls for account, models, agents, appearance, and advanced workspace behavior.
        </p>
      </div>

      {globalError ? <div className="mb-4 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">{globalError}</div> : null}
      {content}
    </div>
  );
}
