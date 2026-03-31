import { useState, useEffect } from 'react';
import { useLocation, useNavigate, Outlet } from 'react-router-dom';
import { 
  User, 
  Bot, 
  Cpu, 
  Sliders, 
  Link2, 
  Shield, 
  Settings,
  ChevronRight,
  Save,
  Loader2,
  Check
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
} from "@/components/ui/select";
import { useAuth } from '@/contexts/AuthContext';
import { modelsApi } from '@/services/api';

interface ProfileNavItem {
  id: string;
  title: string;
  icon: React.ElementType;
  description: string;
}

const navItems: ProfileNavItem[] = [
  { id: 'profile', title: 'Profile', icon: User, description: 'Personal information' },
  { id: 'agents', title: 'Agents', icon: Bot, description: 'AI agent configuration' },
  { id: 'models', title: 'AI Models', icon: Cpu, description: 'Model preferences' },
  { id: 'preferences', title: 'Preferences', icon: Sliders, description: 'App preferences' },
  { id: 'integrations', title: 'Integrations', icon: Link2, description: 'Connected services' },
  { id: 'security', title: 'Security', icon: Shield, description: 'Security settings' },
  { id: 'settings', title: 'Settings', icon: Settings, description: 'Advanced settings' },
];

interface ProviderInfo {
  id: string;
  name: string;
  is_available: boolean;
  models: { id: string; name: string; provider: string }[];
}

export default function Profile() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Determine active section from URL
  const pathParts = location.pathname.split('/');
  const activeSection = pathParts[2] || 'profile';

  const handleNavClick = (id: string) => {
    navigate(`/profile/${id === 'profile' ? '' : id}`);
  };

  return (
    <div className="flex min-h-screen bg-linear-to-b from-[#050110] via-[#0a0520] to-[#050110]">
      {/* Profile Sidebar */}
      <aside className="w-64 border-r border-white/10 bg-black/20 p-4 shrink-0">
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-white">Settings</h2>
          <p className="text-xs text-white/50">Manage your account</p>
        </div>
        
        <nav className="space-y-1">
          {navItems.map((item) => {
            const isActive = activeSection === item.id || 
              (item.id === 'profile' && activeSection === 'profile');
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all ${
                  isActive 
                    ? 'bg-purple-500/20 text-purple-200 border border-purple-500/30' 
                    : 'text-white/60 hover:bg-white/5 hover:text-white'
                }`}
              >
                <item.icon className="w-4 h-4" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="text-[10px] text-white/40 truncate">{item.description}</p>
                </div>
                {isActive && <ChevronRight className="w-4 h-4 text-purple-400" />}
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-y-auto">
        <ProfileContent section={activeSection} />
      </main>
    </div>
  );
}

function ProfileContent({ section }: { section: string }) {
  const { user } = useAuth();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);

  // Load providers for models section
  useEffect(() => {
    if (section === 'models') {
      modelsApi.getProviders().then((result: unknown) => {
        const data = result as { providers: ProviderInfo[] };
        setProviders(data.providers || []);
      }).catch(console.error);
    }
  }, [section]);

  const handleSave = async () => {
    setSaving(true);
    // Simulate save
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const renderSection = () => {
    switch (section) {
      case 'profile':
        return <ProfileSection user={user} onSave={handleSave} saving={saving} saved={saved} />;
      case 'agents':
        return <AgentsSection onSave={handleSave} saving={saving} saved={saved} />;
      case 'models':
        return <ModelsSection providers={providers} onSave={handleSave} saving={saving} saved={saved} />;
      case 'preferences':
        return <PreferencesSection onSave={handleSave} saving={saving} saved={saved} />;
      case 'integrations':
        return <IntegrationsSection />;
      case 'security':
        return <SecuritySection onSave={handleSave} saving={saving} saved={saved} />;
      case 'settings':
        return <SettingsSection onSave={handleSave} saving={saving} saved={saved} />;
      default:
        return <ProfileSection user={user} onSave={handleSave} saving={saving} saved={saved} />;
    }
  };

  return renderSection();
}

interface SectionProps {
  onSave: () => void;
  saving: boolean;
  saved: boolean;
}

function ProfileSection({ user, onSave, saving, saved }: SectionProps & { user: any }) {
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-2">Profile</h1>
      <p className="text-white/50 mb-8">Manage your personal information</p>

      <div className="space-y-6">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Personal Information</h3>
          
          <div className="space-y-4">
            <div>
              <Label className="text-white/70">Full Name</Label>
              <Input 
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="mt-1.5 bg-white/5 border-white/10 text-white"
              />
            </div>
            <div>
              <Label className="text-white/70">Email</Label>
              <Input 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                className="mt-1.5 bg-white/5 border-white/10 text-white"
              />
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Account Details</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-white/40">User ID</p>
              <p className="text-white/80 font-mono text-xs mt-1">{user?.id || 'N/A'}</p>
            </div>
            <div>
              <p className="text-white/40">Account Created</p>
              <p className="text-white/80 mt-1">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</p>
            </div>
          </div>
        </div>

        <SaveButton onSave={onSave} saving={saving} saved={saved} />
      </div>
    </div>
  );
}

function AgentsSection({ onSave, saving, saved }: SectionProps) {
  const [orchestratorEnabled, setOrchestratorEnabled] = useState(true);
  const [memoryAgentEnabled, setMemoryAgentEnabled] = useState(true);
  const [webSurferEnabled, setWebSurferEnabled] = useState(true);
  const [autoMemoryUpdate, setAutoMemoryUpdate] = useState(true);

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-2">Agents</h1>
      <p className="text-white/50 mb-8">Configure AI agent behavior</p>

      <div className="space-y-6">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Agent Controls</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Orchestrator Agent</p>
                <p className="text-xs text-white/40">Routes queries to appropriate handlers</p>
              </div>
              <Switch checked={orchestratorEnabled} onCheckedChange={setOrchestratorEnabled} />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Memory Manager Agent</p>
                <p className="text-xs text-white/40">Manages knowledge graph operations</p>
              </div>
              <Switch checked={memoryAgentEnabled} onCheckedChange={setMemoryAgentEnabled} />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Web Surfer Agent</p>
                <p className="text-xs text-white/40">Searches external knowledge</p>
              </div>
              <Switch checked={webSurferEnabled} onCheckedChange={setWebSurferEnabled} />
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Behavior Settings</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Auto Memory Update</p>
                <p className="text-xs text-white/40">Automatically store insights from conversations</p>
              </div>
              <Switch checked={autoMemoryUpdate} onCheckedChange={setAutoMemoryUpdate} />
            </div>
          </div>
        </div>

        <SaveButton onSave={onSave} saving={saving} saved={saved} />
      </div>
    </div>
  );
}

function ModelsSection({ providers, onSave, saving, saved }: SectionProps & { providers: ProviderInfo[] }) {
  const [defaultProvider, setDefaultProvider] = useState(localStorage.getItem('ng_default_provider') || 'gemini');
  const [defaultModel, setDefaultModel] = useState(localStorage.getItem('ng_default_model') || 'gemini-2.0-flash');
  const [orchestratorModel, setOrchestratorModel] = useState(localStorage.getItem('ng_orchestrator_model') || 'groq-llama-3.3-70b');

  const availableModels = providers.find(p => p.id === defaultProvider)?.models || [];

  const handleSaveModels = () => {
    localStorage.setItem('ng_default_provider', defaultProvider);
    localStorage.setItem('ng_default_model', defaultModel);
    localStorage.setItem('ng_orchestrator_model', orchestratorModel);
    onSave();
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-2">AI Models</h1>
      <p className="text-white/50 mb-8">Configure default models for different tasks</p>

      <div className="space-y-6">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Main Chat Model</h3>
          
          <div className="space-y-4">
            <div>
              <Label className="text-white/70">Provider</Label>
              <Select value={defaultProvider} onValueChange={(v) => { setDefaultProvider(v); setDefaultModel(''); }}>
                <SelectTrigger className="mt-1.5 bg-white/5 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#0a0520] border-white/10">
                  {providers.filter(p => p.is_available).map(p => (
                    <SelectItem key={p.id} value={p.id} className="text-white">{p.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-white/70">Model</Label>
              <Select value={defaultModel} onValueChange={setDefaultModel}>
                <SelectTrigger className="mt-1.5 bg-white/5 border-white/10 text-white">
                  <SelectValue placeholder="Select a model" />
                </SelectTrigger>
                <SelectContent className="bg-[#0a0520] border-white/10 max-h-60">
                  {availableModels.map(m => (
                    <SelectItem key={m.id} value={m.id} className="text-white">{m.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Available Providers</h3>
          
          <div className="space-y-3">
            {providers.map(provider => (
              <div key={provider.id} className="flex items-center justify-between p-3 rounded-xl bg-black/20">
                <div className="flex items-center gap-3">
                  <Cpu className="w-4 h-4 text-purple-400" />
                  <div>
                    <p className="text-white text-sm font-medium">{provider.name}</p>
                    <p className="text-xs text-white/40">{provider.models.length} models</p>
                  </div>
                </div>
                <Badge variant={provider.is_available ? 'default' : 'secondary'} className={provider.is_available ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}>
                  {provider.is_available ? 'Available' : 'Unavailable'}
                </Badge>
              </div>
            ))}
          </div>
        </div>

        <SaveButton onSave={handleSaveModels} saving={saving} saved={saved} />
      </div>
    </div>
  );
}

function PreferencesSection({ onSave, saving, saved }: SectionProps) {
  const [darkMode, setDarkMode] = useState(true);
  const [compactMode, setCompactMode] = useState(false);
  const [showConfidence, setShowConfidence] = useState(true);
  const [showReasoning, setShowReasoning] = useState(true);

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-2">Preferences</h1>
      <p className="text-white/50 mb-8">Customize your experience</p>

      <div className="space-y-6">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Appearance</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Dark Mode</p>
                <p className="text-xs text-white/40">Use dark theme</p>
              </div>
              <Switch checked={darkMode} onCheckedChange={setDarkMode} />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Compact Mode</p>
                <p className="text-xs text-white/40">Reduce spacing in UI</p>
              </div>
              <Switch checked={compactMode} onCheckedChange={setCompactMode} />
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Chat Display</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Show Confidence Scores</p>
                <p className="text-xs text-white/40">Display confidence on responses</p>
              </div>
              <Switch checked={showConfidence} onCheckedChange={setShowConfidence} />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Show Reasoning Path</p>
                <p className="text-xs text-white/40">Display reasoning in orchestrator panel</p>
              </div>
              <Switch checked={showReasoning} onCheckedChange={setShowReasoning} />
            </div>
          </div>
        </div>

        <SaveButton onSave={onSave} saving={saving} saved={saved} />
      </div>
    </div>
  );
}

function IntegrationsSection() {
  const integrations = [
    { id: 'slack', name: 'Slack', description: 'Send notifications to Slack', connected: false },
    { id: 'github', name: 'GitHub', description: 'Import from repositories', connected: false },
    { id: 'notion', name: 'Notion', description: 'Sync with Notion pages', connected: false },
    { id: 'google', name: 'Google Drive', description: 'Access Google Drive files', connected: false },
  ];

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-2">Integrations</h1>
      <p className="text-white/50 mb-8">Connect external services</p>

      <div className="space-y-4">
        {integrations.map(integration => (
          <div key={integration.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
                  <Link2 className="w-5 h-5 text-white/60" />
                </div>
                <div>
                  <p className="text-white font-medium">{integration.name}</p>
                  <p className="text-xs text-white/40">{integration.description}</p>
                </div>
              </div>
              <Button 
                variant={integration.connected ? 'secondary' : 'outline'}
                size="sm"
                className={integration.connected ? 'bg-green-500/20 text-green-300' : 'border-white/20 text-white hover:bg-white/10'}
              >
                {integration.connected ? 'Connected' : 'Connect'}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SecuritySection({ onSave, saving, saved }: SectionProps) {
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-2">Security</h1>
      <p className="text-white/50 mb-8">Manage security settings</p>

      <div className="space-y-6">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Password</h3>
          
          <div className="space-y-4">
            <div>
              <Label className="text-white/70">Current Password</Label>
              <Input type="password" className="mt-1.5 bg-white/5 border-white/10 text-white" />
            </div>
            <div>
              <Label className="text-white/70">New Password</Label>
              <Input type="password" className="mt-1.5 bg-white/5 border-white/10 text-white" />
            </div>
            <div>
              <Label className="text-white/70">Confirm New Password</Label>
              <Input type="password" className="mt-1.5 bg-white/5 border-white/10 text-white" />
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Two-Factor Authentication</h3>
          
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Enable 2FA</p>
              <p className="text-xs text-white/40">Add extra security to your account</p>
            </div>
            <Switch checked={twoFactorEnabled} onCheckedChange={setTwoFactorEnabled} />
          </div>
        </div>

        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6">
          <h3 className="text-sm font-semibold text-red-300 mb-4">Danger Zone</h3>
          <p className="text-sm text-white/60 mb-4">Once you delete your account, there is no going back.</p>
          <Button variant="destructive" size="sm">Delete Account</Button>
        </div>

        <SaveButton onSave={onSave} saving={saving} saved={saved} />
      </div>
    </div>
  );
}

function SettingsSection({ onSave, saving, saved }: SectionProps) {
  const [dataExport, setDataExport] = useState(false);
  const [analyticsEnabled, setAnalyticsEnabled] = useState(true);

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-2">Settings</h1>
      <p className="text-white/50 mb-8">Advanced application settings</p>

      <div className="space-y-6">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Data</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Export Data</p>
                <p className="text-xs text-white/40">Download all your data</p>
              </div>
              <Button variant="outline" size="sm" className="border-white/20 text-white hover:bg-white/10">
                Export
              </Button>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Analytics</p>
                <p className="text-xs text-white/40">Help improve NeuroGraph</p>
              </div>
              <Switch checked={analyticsEnabled} onCheckedChange={setAnalyticsEnabled} />
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">API</h3>
          
          <div className="space-y-4">
            <div>
              <Label className="text-white/70">API Key</Label>
              <div className="flex gap-2 mt-1.5">
                <Input 
                  value="ng_sk_••••••••••••••••" 
                  readOnly
                  className="bg-white/5 border-white/10 text-white font-mono text-sm"
                />
                <Button variant="outline" size="sm" className="border-white/20 text-white hover:bg-white/10">
                  Regenerate
                </Button>
              </div>
            </div>
          </div>
        </div>

        <SaveButton onSave={onSave} saving={saving} saved={saved} />
      </div>
    </div>
  );
}

function SaveButton({ onSave, saving, saved }: SectionProps) {
  return (
    <div className="flex justify-end">
      <Button 
        onClick={onSave} 
        disabled={saving}
        className="bg-purple-500 hover:bg-purple-600 text-white"
      >
        {saving ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Saving...
          </>
        ) : saved ? (
          <>
            <Check className="w-4 h-4 mr-2" />
            Saved!
          </>
        ) : (
          <>
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </>
        )}
      </Button>
    </div>
  );
}
