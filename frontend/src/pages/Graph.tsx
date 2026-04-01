import { useState, useEffect } from 'react';
import GraphVisualization from '@/components/graph/GraphVisualization';
import { SpotlightCard } from '@/components/reactbits/SpotlightCard';
import { BlurText } from '@/components/reactbits/BlurText';
import { Activity, Loader2 } from 'lucide-react';
import { graphApi } from '@/services/api';

interface CentralityData {
  [key: string]: number;
}

export default function Graph() {
  const [centrality, setCentrality] = useState<CentralityData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadCentrality = async () => {
      setIsLoading(true);
      try {
        const data = await graphApi.getCentrality() as CentralityData;
        setCentrality(data);
      } catch (err) {
        console.error('Failed to load centrality:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadCentrality();
  }, []);

  const topNodes = centrality
    ? Object.entries(centrality)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
    : [];

  return (
    <div className="h-full grid p-4 gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
      <section className="flex min-h-0 flex-col gap-3 rounded-3xl border border-white/10 bg-[#0d0620]/65 p-4 backdrop-blur-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-[0.25em] text-purple-200/55">Topology Explorer</p>
            <h2 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">
              <BlurText text="Knowledge Graph Engine" delay={34} direction="top" />
            </h2>
          </div>
          <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-purple-100">
            Live force simulation
          </div>
        </div>

        <SpotlightCard className="min-h-0 flex-1 overflow-hidden rounded-3xl border-white/10 bg-transparent p-0" spotlightColor="rgba(146, 95, 255, 0.2)">
          <GraphVisualization />
        </SpotlightCard>
      </section>

      <aside className="hidden min-h-0 flex-col gap-4 xl:flex">
        <SpotlightCard className="rounded-3xl border-white/10 bg-[#110829]/90 p-5" spotlightColor="rgba(182, 126, 255, 0.22)">
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/45">Centrality Scores</p>
          <div className="mt-3 space-y-2 text-sm text-white/80">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
              </div>
            ) : topNodes.length > 0 ? (
              topNodes.map(([name, score]) => (
                <div key={name} className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2">
                  <span className="flex items-center gap-2 truncate">
                    <Activity className="size-4 text-purple-300 flex-shrink-0" />
                    <span className="truncate">{name}</span>
                  </span>
                  <strong className="text-purple-200 ml-2">{score.toFixed(2)}</strong>
                </div>
              ))
            ) : (
              <p className="text-white/40 text-center py-4">No centrality data</p>
            )}
          </div>
        </SpotlightCard>

        <SpotlightCard className="rounded-3xl border-white/10 bg-[#0c0620]/92 p-5" spotlightColor="rgba(114, 77, 232, 0.26)">
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/45">Entity Types</p>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#7fb5ff]" />Person</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#b084ff]" />Organization</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#dd8cff]" />Project</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#7bffa3]" />Technology</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#ff8d9d]" />Concept</li>
          </ul>
        </SpotlightCard>

        <SpotlightCard className="rounded-3xl border-white/10 bg-[#0c0620]/92 p-5" spotlightColor="rgba(114, 77, 232, 0.26)">
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/45">Memory Layers</p>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#b084ff]" />Personal</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#7fb5ff]" />Tenant</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#7bffa3]" />Global</li>
          </ul>
        </SpotlightCard>
      </aside>
    </div>
  );
}
