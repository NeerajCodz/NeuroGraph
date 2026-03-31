import { useState, useEffect } from 'react';
import { BlurText } from '@/components/reactbits/BlurText';
import { SpotlightCard } from '@/components/reactbits/SpotlightCard';
import { Button } from '@/components/ui/button';
import { Database, KeyRound, BellRing, Brain, User, Mail, Shield, Check, Loader2, LogOut, Cpu, Zap, Code2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { modelsApi } from '@/services/api';

interface ModelInfo {
  id: string;
  name: string;
  type: string;
  provider?: string;
}

interface ProviderInfo {
  id: string;
  name: string;
  models: ModelInfo[];
}

export default function Settings() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeProvider, setActiveProvider] = useState('nvidia');
  const [activeModel, setActiveModel] = useState('devstral-2-123b');
  const [activeLayer, setActiveLayer] = useState('personal');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(true);

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    setIsLoadingModels(true);
    try {
      const data = await modelsApi.getProviders() as any;
      setProviders(data.providers || []);
      if (data.default_provider) {
        setActiveProvider(data.default_provider);
      }
      if (data.default_model) {
        setActiveModel(data.default_model);
      }
    } catch (err) {
      console.error('Failed to load providers:', err);
      // Fallback to hardcoded defaults
      setProviders([
        {
          id: 'nvidia',
          name: 'NVIDIA AI',
          models: [
            { id: 'step-3.5-flash', name: 'Step 3.5 Flash (Reasoning)', type: 'reasoning' },
            { id: 'glm4.7', name: 'GLM 4.7 (Reasoning)', type: 'reasoning' },
            { id: 'deepseek-v3.2', name: 'DeepSeek V3.2 (Reasoning)', type: 'reasoning' },
            { id: 'devstral-2-123b', name: 'Devstral 2 123B (Code)', type: 'code' },
          ],
        },
        {
          id: 'gemini',
          name: 'Google Gemini',
          models: [
            { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', type: 'fast' },
            { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro', type: 'premium' },
          ],
        },
        {
          id: 'groq',
          name: 'Groq',
          models: [
            { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B', type: 'fast' },
          ],
        },
      ]);
    } finally {
      setIsLoadingModels(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    // Save to localStorage for now (could be API call later)
    localStorage.setItem('ng_default_provider', activeProvider);
    localStorage.setItem('ng_default_model', activeModel);
    localStorage.setItem('ng_default_layer', activeLayer);
    await new Promise(resolve => setTimeout(resolve, 500));
    setIsSaving(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleProviderChange = (providerId: string) => {
    setActiveProvider(providerId);
    // Set first model of the provider as default
    const provider = providers.find(p => p.id === providerId);
    if (provider && provider.models.length > 0) {
      setActiveModel(provider.models[0].id);
    }
  };

  const currentProviderModels = providers.find(p => p.id === activeProvider)?.models || [];

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'reasoning': return <Brain className="w-4 h-4 text-purple-400" />;
      case 'code': return <Code2 className="w-4 h-4 text-cyan-400" />;
      case 'fast': return <Zap className="w-4 h-4 text-yellow-400" />;
      case 'premium': return <Cpu className="w-4 h-4 text-pink-400" />;
      default: return <Brain className="w-4 h-4 text-white/40" />;
    }
  };

  const layers = [
    { id: 'personal', name: 'Personal', description: 'Your private memories' },
    { id: 'tenant', name: 'Tenant', description: 'Shared with team' },
    { id: 'global', name: 'Global', description: 'Organization-wide' },
  ];

  return (
    <div className="mx-auto w-full max-w-6xl p-4 md:p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-[10px] uppercase tracking-[0.24em] text-white/45">Configuration</p>
          <h2 className="text-3xl font-semibold tracking-tight text-white">
            <BlurText text="System Settings" delay={34} direction="top" />
          </h2>
        </div>
        <Button
          onClick={handleSave}
          disabled={isSaving}
          className="bg-gradient-to-r from-purple-500 to-pink-500 text-white"
        >
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : saveSuccess ? (
            <Check className="w-4 h-4 mr-2" />
          ) : null}
          {saveSuccess ? 'Saved!' : 'Save Changes'}
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {/* User Profile Card */}
        <SpotlightCard className="rounded-3xl border-white/10 bg-[#100828]/88 p-5" spotlightColor="rgba(161, 105, 252, 0.22)">
          <div className="mb-4 flex items-center gap-2 text-white/85">
            <User className="h-4 w-4 text-purple-300" />
            <h3 className="text-lg font-semibold">User Profile</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-3 rounded-2xl bg-white/5 border border-white/10">
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-xl font-bold">
                {user?.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2) || 'U'}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-white">{user?.full_name || 'User'}</p>
                <p className="text-sm text-white/60 flex items-center gap-1">
                  <Mail className="w-3 h-3" />
                  {user?.email || 'No email'}
                </p>
              </div>
              <div className="text-right">
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  <Shield className="w-3 h-3" />
                  Active
                </span>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={handleLogout}
              className="w-full border-red-500/30 text-red-300 hover:bg-red-500/10 hover:text-red-200"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </SpotlightCard>

        {/* Provider Selection */}
        <SpotlightCard className="rounded-3xl border-white/10 bg-[#100828]/88 p-5" spotlightColor="rgba(161, 105, 252, 0.22)">
          <div className="mb-4 flex items-center gap-2 text-white/85">
            <Cpu className="h-4 w-4 text-cyan-300" />
            <h3 className="text-lg font-semibold">LLM Provider</h3>
          </div>
          <p className="text-sm text-white/60 mb-4">Choose the AI provider for chat and reasoning.</p>
          {isLoadingModels ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-2">
              {providers.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => handleProviderChange(provider.id)}
                  className={`flex flex-col items-center rounded-2xl px-3 py-4 transition-all ${
                    activeProvider === provider.id
                      ? 'bg-gradient-to-br from-cyan-500/30 to-purple-500/30 border border-cyan-400/40 text-white'
                      : 'bg-white/5 border border-white/10 text-white/70 hover:bg-white/10'
                  }`}
                >
                  <p className="font-medium text-sm">{provider.name}</p>
                  <p className="text-[10px] text-white/50 mt-1">{provider.models.length} models</p>
                </button>
              ))}
            </div>
          )}
        </SpotlightCard>

        {/* Model Selection */}
        <SpotlightCard className="xl:col-span-2 rounded-3xl border-white/10 bg-[#100828]/88 p-5" spotlightColor="rgba(161, 105, 252, 0.22)">
          <div className="mb-4 flex items-center gap-2 text-white/85">
            <Brain className="h-4 w-4 text-purple-300" />
            <h3 className="text-lg font-semibold">Model Selection</h3>
            <span className="ml-auto text-xs text-white/40">Provider: {providers.find(p => p.id === activeProvider)?.name}</span>
          </div>
          <p className="text-sm text-white/60 mb-4">Choose the specific model for chat. Embedding model is fixed (text-embedding-004).</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {currentProviderModels.map((model) => (
              <button
                key={model.id}
                onClick={() => setActiveModel(model.id)}
                className={`w-full flex items-center justify-between rounded-2xl px-4 py-3 transition-all ${
                  activeModel === model.id
                    ? 'bg-purple-500/20 border border-purple-500/40 text-white'
                    : 'bg-white/5 border border-white/10 text-white/70 hover:bg-white/10'
                }`}
              >
                <div className="flex items-center gap-3">
                  {getTypeIcon(model.type)}
                  <div className="text-left">
                    <p className="font-medium text-sm">{model.name}</p>
                    <p className="text-xs text-white/50">{model.type}</p>
                  </div>
                </div>
                {activeModel === model.id && (
                  <Check className="w-5 h-5 text-purple-300" />
                )}
              </button>
            ))}
          </div>
        </SpotlightCard>

        {/* Memory Layer Default */}
        <SpotlightCard className="rounded-3xl border-white/10 bg-[#0f0824]/88 p-5" spotlightColor="rgba(116, 80, 228, 0.25)">
          <div className="mb-4 flex items-center gap-2 text-white/85">
            <Database className="h-4 w-4 text-indigo-300" />
            <h3 className="text-lg font-semibold">Default Memory Layer</h3>
          </div>
          <p className="text-sm text-white/60 mb-4">Set the default memory scope for storing new memories.</p>
          <div className="grid grid-cols-3 gap-2">
            {layers.map((layer) => (
              <button
                key={layer.id}
                onClick={() => setActiveLayer(layer.id)}
                className={`flex flex-col items-center rounded-2xl px-3 py-4 transition-all ${
                  activeLayer === layer.id
                    ? 'bg-gradient-to-br from-purple-500/30 to-pink-500/30 border border-purple-400/40 text-white'
                    : 'bg-white/5 border border-white/10 text-white/70 hover:bg-white/10'
                }`}
              >
                <p className="font-medium text-sm">{layer.name}</p>
                <p className="text-[10px] text-white/50 mt-1 text-center">{layer.description}</p>
              </button>
            ))}
          </div>
        </SpotlightCard>

        {/* API Keys (Display Only) */}
        <SpotlightCard className="rounded-3xl border-white/10 bg-[#100828]/88 p-5" spotlightColor="rgba(181, 126, 255, 0.24)">
          <div className="mb-4 flex items-center gap-2 text-white/85">
            <KeyRound className="h-4 w-4 text-fuchsia-300" />
            <h3 className="text-lg font-semibold">API Configuration</h3>
          </div>
          <p className="text-sm text-white/60 mb-4">API keys are configured on the server. Contact admin to update.</p>
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-2xl bg-black/25 border border-white/10 px-4 py-3">
              <span className="text-white/70">GEMINI_API_KEY</span>
              <span className="text-emerald-300 text-sm">Configured ✓</span>
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-black/25 border border-white/10 px-4 py-3">
              <span className="text-white/70">NVIDIA_API_KEY</span>
              <span className="text-emerald-300 text-sm">Configured ✓</span>
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-black/25 border border-white/10 px-4 py-3">
              <span className="text-white/70">GROQ_API_KEY</span>
              <span className="text-emerald-300 text-sm">Configured ✓</span>
            </div>
          </div>
        </SpotlightCard>

        {/* Notification Settings */}
        <SpotlightCard className="xl:col-span-2 rounded-3xl border-white/10 bg-[#0f0824]/88 p-5" spotlightColor="rgba(98, 80, 228, 0.25)">
          <div className="mb-4 flex items-center gap-2 text-white/85">
            <BellRing className="h-4 w-4 text-cyan-300" />
            <h3 className="text-lg font-semibold">Features & Capabilities</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              <span className="text-white/80">Graph Memory</span>
              <span className="text-emerald-300 text-sm font-medium">Enabled</span>
            </div>
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              <span className="text-white/80">Vector Search</span>
              <span className="text-emerald-300 text-sm font-medium">Enabled</span>
            </div>
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              <span className="text-white/80">NVIDIA Reasoning</span>
              <span className="text-emerald-300 text-sm font-medium">Enabled</span>
            </div>
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              <span className="text-white/80">Reasoning Paths</span>
              <span className="text-emerald-300 text-sm font-medium">Enabled</span>
            </div>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}
