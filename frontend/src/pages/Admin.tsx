import { BlurText } from '@/components/reactbits/BlurText';
import { SpotlightCard } from '@/components/reactbits/SpotlightCard';
import { ShieldCheck, Clock3, Workflow, AlertTriangle } from 'lucide-react';

const metrics = [
  { title: 'Active Nodes', value: '1,284', hint: '+3.2% today', icon: Workflow },
  { title: 'Resolved Conflicts', value: '342', hint: '28 in last 24h', icon: ShieldCheck },
  { title: 'Avg. Orchestration Latency', value: '212ms', hint: 'p95: 418ms', icon: Clock3 },
];

const incidents = [
  { id: 'INC-1192', scope: 'Webhook', status: 'monitoring', severity: 'medium' },
  { id: 'INC-1199', scope: 'Node 452', status: 'open', severity: 'high' },
  { id: 'INC-1204', scope: 'Redis queue', status: 'resolved', severity: 'low' },
];

export default function Admin() {
  return (
    <div className="mx-auto w-full max-w-6xl p-4 md:p-6">
      <p className="text-[10px] uppercase tracking-[0.24em] text-white/45">Operations</p>
      <h1 className="mb-6 text-3xl font-bold tracking-tight text-white">
        <BlurText text="Administration Dashboard" delay={40} direction="bottom" />
      </h1>

      <div className="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {metrics.map((item) => (
          <SpotlightCard key={item.title} className="rounded-3xl border-white/10 bg-[#100827]/88 p-5" spotlightColor="rgba(161, 107, 252, 0.2)">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm text-white/65">{item.title}</h3>
              <item.icon className="h-4 w-4 text-purple-200" />
            </div>
            <div className="text-3xl font-semibold text-white">{item.value}</div>
            <div className="mt-2 text-xs uppercase tracking-[0.18em] text-purple-200/65">{item.hint}</div>
          </SpotlightCard>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <SpotlightCard className="rounded-3xl border-white/10 bg-[#0f0823]/88 p-5" spotlightColor="rgba(113, 84, 228, 0.24)">
          <h3 className="mb-4 text-lg font-semibold text-white">Open Incident Feed</h3>
          <div className="space-y-2">
            {incidents.map((incident) => (
              <div key={incident.id} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/80">
                <div>
                  <p className="font-medium text-white">{incident.id}</p>
                  <p className="text-xs text-white/55">{incident.scope}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/50">{incident.status}</p>
                  <p className="text-xs text-purple-200">{incident.severity}</p>
                </div>
              </div>
            ))}
          </div>
        </SpotlightCard>

        <SpotlightCard className="rounded-3xl border-white/10 bg-[#100828]/88 p-5" spotlightColor="rgba(183, 130, 255, 0.23)">
          <div className="mb-2 flex items-center gap-2 text-white">
            <AlertTriangle className="h-4 w-4 text-amber-300" />
            <h3 className="text-lg font-semibold">System Health</h3>
          </div>
          <p className="text-sm text-white/65">Core services are healthy. One queue depth warning is currently being observed.</p>
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2 text-white/85"><span>API uptime</span><strong className="text-emerald-300">99.98%</strong></div>
            <div className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2 text-white/85"><span>Redis queue depth</span><strong className="text-amber-200">146 jobs</strong></div>
            <div className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2 text-white/85"><span>Neo4j response p95</span><strong className="text-cyan-200">184ms</strong></div>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}
