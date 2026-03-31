import GraphVisualization from '../components/graph/GraphVisualization';
import { SpotlightCard } from '@/components/reactbits/SpotlightCard';
import { BlurText } from '@/components/reactbits/BlurText';
import { Activity, GitBranch, ShieldAlert } from 'lucide-react';

export default function Graph() {
  return (
    <div className="grid h-full min-h-0 gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
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
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/45">Conflict Watch</p>
          <div className="mt-3 space-y-2 text-sm text-white/80">
            <div className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2">
              <span className="flex items-center gap-2"><ShieldAlert className="size-4 text-rose-300" />High risk</span>
              <strong className="text-rose-200">2 nodes</strong>
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2">
              <span className="flex items-center gap-2"><GitBranch className="size-4 text-purple-300" />Conflict edges</span>
              <strong className="text-purple-200">5 links</strong>
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-white/5 px-3 py-2">
              <span className="flex items-center gap-2"><Activity className="size-4 text-cyan-300" />Signal quality</span>
              <strong className="text-cyan-200">0.92</strong>
            </div>
          </div>
        </SpotlightCard>

        <SpotlightCard className="rounded-3xl border-white/10 bg-[#0c0620]/92 p-5" spotlightColor="rgba(114, 77, 232, 0.26)">
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/45">Legend</p>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#b084ff]" />Core intelligence</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#dd8cff]" />Projects / nodes</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#7fb5ff]" />Teams / owners</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-[#ff8d9d]" />Risk vectors</li>
          </ul>
        </SpotlightCard>
      </aside>
    </div>
  );
}
