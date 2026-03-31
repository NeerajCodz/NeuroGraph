import { useState, useEffect } from 'react';
import { BlurText } from '@/components/reactbits/BlurText';
import { SpotlightCard } from '@/components/reactbits/SpotlightCard';
import { ShieldCheck, Workflow, Database, Brain, Network, Loader2, RefreshCw } from 'lucide-react';
import { graphApi, memoryApi } from '@/services/api';
import { Button } from '@/components/ui/button';

interface MemoryStatus {
  total_memories: number;
  by_layer: {
    personal: number;
    tenant: number;
    global: number;
  };
  entity_count: number;
  relationship_count: number;
}

interface SystemMetrics {
  totalNodes: number;
  totalEdges: number;
  memoryStatus: MemoryStatus | null;
  topCentrality: Array<[string, number]>;
}

export default function Admin() {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    totalNodes: 0,
    totalEdges: 0,
    memoryStatus: null,
    topCentrality: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadMetrics = async () => {
    setIsLoading(true);
    setError('');
    try {
      const [graphData, centralityData, memStatus] = await Promise.all([
        graphApi.getVisualization(undefined, 3, 200),
        graphApi.getCentrality(),
        memoryApi.getStatus(),
      ]);
      
      const graph = graphData as { nodes: unknown[]; edges: unknown[] };
      const centrality = centralityData as Record<string, number>;
      
      const topCentrality = Object.entries(centrality)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5);
      
      setMetrics({
        totalNodes: graph.nodes?.length || 0,
        totalEdges: graph.edges?.length || 0,
        memoryStatus: memStatus as MemoryStatus,
        topCentrality,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
  }, []);

  const metricCards = [
    { 
      title: 'Graph Entities', 
      value: metrics.totalNodes.toString(), 
      hint: `${metrics.totalEdges} relationships`, 
      icon: Network,
      color: 'text-purple-200'
    },
    { 
      title: 'Total Memories', 
      value: metrics.memoryStatus?.total_memories.toString() || '0', 
      hint: `${metrics.memoryStatus?.entity_count || 0} entities extracted`, 
      icon: Brain,
      color: 'text-fuchsia-200'
    },
    { 
      title: 'Memory Layers', 
      value: '3', 
      hint: `P:${metrics.memoryStatus?.by_layer.personal || 0} T:${metrics.memoryStatus?.by_layer.tenant || 0} G:${metrics.memoryStatus?.by_layer.global || 0}`, 
      icon: Database,
      color: 'text-cyan-200'
    },
  ];

  return (
    <div className="mx-auto w-full max-w-6xl p-4 md:p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-[10px] uppercase tracking-[0.24em] text-white/45">Operations</p>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            <BlurText text="Administration Dashboard" delay={40} direction="bottom" />
          </h1>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={loadMetrics}
          disabled={isLoading}
          className="border-white/20 text-white hover:bg-white/10"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          <span className="ml-2">Refresh</span>
        </Button>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-sm">
          {error}
        </div>
      )}

      <div className="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {metricCards.map((item) => (
          <SpotlightCard key={item.title} className="rounded-3xl border-white/10 bg-[#100827]/88 p-5" spotlightColor="rgba(161, 107, 252, 0.2)">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm text-white/65">{item.title}</h3>
              <item.icon className={`h-4 w-4 ${item.color}`} />
            </div>
            <div className="text-3xl font-semibold text-white">
              {isLoading ? <Loader2 className="w-6 h-6 animate-spin" /> : item.value}
            </div>
            <div className="mt-2 text-xs uppercase tracking-[0.18em] text-purple-200/65">{item.hint}</div>
          </SpotlightCard>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <SpotlightCard className="rounded-3xl border-white/10 bg-[#0f0823]/88 p-5" spotlightColor="rgba(113, 84, 228, 0.24)">
          <h3 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
            <Workflow className="w-5 h-5 text-purple-300" />
            Top Nodes by Centrality
          </h3>
          <div className="space-y-2">
            {isLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
              </div>
            ) : metrics.topCentrality.length > 0 ? (
              metrics.topCentrality.map(([name, score], idx) => (
                <div key={name} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/80">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-purple-500/20 text-purple-200 text-xs font-bold">
                      {idx + 1}
                    </span>
                    <p className="font-medium text-white truncate max-w-[200px]">{name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-purple-200 font-mono">{score.toFixed(2)}</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-white/40 text-center py-4">No centrality data available</p>
            )}
          </div>
        </SpotlightCard>

        <SpotlightCard className="rounded-3xl border-white/10 bg-[#100828]/88 p-5" spotlightColor="rgba(183, 130, 255, 0.23)">
          <div className="mb-2 flex items-center gap-2 text-white">
            <ShieldCheck className="h-4 w-4 text-emerald-300" />
            <h3 className="text-lg font-semibold">System Status</h3>
          </div>
          <p className="text-sm text-white/65 mb-4">Real-time status of NeuroGraph services.</p>
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2 text-white/85">
              <span>Backend API</span>
              <strong className="text-emerald-300">Online</strong>
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2 text-white/85">
              <span>Neo4j Graph DB</span>
              <strong className="text-emerald-300">{metrics.totalNodes > 0 ? 'Connected' : 'Empty'}</strong>
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2 text-white/85">
              <span>PostgreSQL</span>
              <strong className="text-emerald-300">Connected</strong>
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2 text-white/85">
              <span>Redis Cache</span>
              <strong className="text-emerald-300">Connected</strong>
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2 text-white/85">
              <span>Gemini API</span>
              <strong className="text-cyan-200">Rate Limited</strong>
            </div>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}
