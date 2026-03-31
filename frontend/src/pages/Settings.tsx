import { BlurText } from '@/components/reactbits/BlurText';
import { SpotlightCard } from '@/components/reactbits/SpotlightCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Database, KeyRound, BellRing, Brain } from 'lucide-react';

export default function Settings() {
  return (
    <div className="mx-auto w-full max-w-6xl p-4 md:p-6">
      <div className="mb-6">
        <p className="text-[10px] uppercase tracking-[0.24em] text-white/45">Configuration</p>
        <h2 className="text-3xl font-semibold tracking-tight text-white">
          <BlurText text="System Settings" delay={34} direction="top" />
        </h2>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <SpotlightCard className="rounded-3xl border-white/10 bg-[#100828]/88 p-5" spotlightColor="rgba(161, 105, 252, 0.22)">
          <div className="mb-4 flex items-center gap-2 text-white/85">
            <Brain className="h-4 w-4 text-purple-300" />
            <h3 className="text-lg font-semibold">Model Orchestration</h3>
          </div>
          <p className="text-sm text-white/60">Choose defaults for routing and fallback behavior across orchestrator requests.</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button className="gradient-primary text-primary-foreground">Groq Llama 3.3</Button>
            <Button variant="outline" className="border-white/15 bg-white/5 text-white/80 hover:bg-white/10">Gemini 2.0</Button>
            <Button variant="outline" className="border-white/15 bg-white/5 text-white/80 hover:bg-white/10">Parallel mode</Button>
          </div>
        </SpotlightCard>

        <SpotlightCard className="rounded-3xl border-white/10 bg-[#0f0824]/88 p-5" spotlightColor="rgba(116, 80, 228, 0.25)">
          <div className="mb-4 flex items-center gap-2 text-white/85">
            <Database className="h-4 w-4 text-indigo-300" />
            <h3 className="text-lg font-semibold">Memory Layers</h3>
          </div>
          <p className="text-sm text-white/60">Control default memory scope for chat sessions and retrieval depth.</p>
          <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
            <Button variant="outline" className="border-white/15 bg-white/5 text-white">Personal</Button>
            <Button className="gradient-secondary text-white">Shared</Button>
            <Button variant="outline" className="border-white/15 bg-white/5 text-white">Org</Button>
          </div>
        </SpotlightCard>

        <SpotlightCard className="rounded-3xl border-white/10 bg-[#100828]/88 p-5" spotlightColor="rgba(181, 126, 255, 0.24)">
          <div className="mb-4 flex items-center gap-2 text-white/85">
            <KeyRound className="h-4 w-4 text-fuchsia-300" />
            <h3 className="text-lg font-semibold">API & Webhooks</h3>
          </div>
          <div className="space-y-3">
            <Input placeholder="GROQ_API_KEY" className="border-white/12 bg-black/25 text-white placeholder:text-white/35" />
            <Input placeholder="GEMINI_API_KEY" className="border-white/12 bg-black/25 text-white placeholder:text-white/35" />
            <Input placeholder="WEBHOOK_SIGNING_SECRET" className="border-white/12 bg-black/25 text-white placeholder:text-white/35" />
          </div>
        </SpotlightCard>

        <SpotlightCard className="rounded-3xl border-white/10 bg-[#0f0824]/88 p-5" spotlightColor="rgba(98, 80, 228, 0.25)">
          <div className="mb-4 flex items-center gap-2 text-white/85">
            <BellRing className="h-4 w-4 text-cyan-300" />
            <h3 className="text-lg font-semibold">Notification Policy</h3>
          </div>
          <p className="text-sm text-white/60">Alert channels for conflict spikes, webhook failures, and orchestration fallbacks.</p>
          <div className="mt-4 space-y-2 text-sm text-white/80">
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2"><span>Conflict threshold alerts</span><span className="text-purple-200">Enabled</span></div>
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2"><span>Webhook retry warnings</span><span className="text-purple-200">Enabled</span></div>
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2"><span>Daily digest</span><span className="text-white/50">Paused</span></div>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}
