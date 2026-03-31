import MessageList from '@/components/chat/MessageList';
import MessageInput from '@/components/chat/MessageInput';
import { SpotlightCard } from '@/components/reactbits/SpotlightCard';
import { BlurText } from '@/components/reactbits/BlurText';
import { ShinyText } from '@/components/reactbits/ShinyText';
import { Bot, BrainCircuit, Activity, ChevronLeft, ChevronRight } from 'lucide-react';
import { useState } from 'react';

export default function Chat() {
  const [isOrchestratorOpen, setIsOrchestratorOpen] = useState(true);

  return (
    <div className="flex h-full min-h-0 w-full">
      <section className="flex h-full min-h-0 min-w-0 flex-1 flex-col">
        <div className="scrollbar-thin flex-1 min-h-0 overflow-y-auto px-2 md:px-4">
          <MessageList />
        </div>

        <div className="mt-auto shrink-0 border-t border-white/10 bg-black/20 px-2 py-2 md:px-4 md:py-3">
          <MessageInput />
        </div>
      </section>

      <aside
        className={
          'relative h-full shrink-0 border-l border-white/10 bg-[#0d0722]/88 transition-[width] duration-300 ease-out ' +
          (isOrchestratorOpen ? 'w-[320px]' : 'w-12')
        }
      >
        <div className="flex h-full w-full flex-col">
          <div className="flex h-12 items-center border-b border-white/10 px-2">
            <button
              type="button"
              onClick={() => setIsOrchestratorOpen((prev) => !prev)}
              className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-white/75 transition hover:bg-white/10 hover:text-white"
              aria-label={isOrchestratorOpen ? 'Collapse orchestrator sidebar' : 'Expand orchestrator sidebar'}
            >
              {isOrchestratorOpen ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            </button>

            {isOrchestratorOpen && (
              <div className="ml-3 min-w-0">
                <p className="text-[10px] uppercase tracking-[0.24em] text-purple-200/60">Orchestrator</p>
                <p className="truncate text-sm font-semibold text-white">Live Session Panel</p>
              </div>
            )}
          </div>

          {isOrchestratorOpen && (
            <div className="scrollbar-thin flex-1 space-y-4 overflow-y-auto p-4 md:p-5">
              <SpotlightCard className="purple-stroke rounded-3xl border-white/10 bg-[#10082a]/90 p-5" spotlightColor="rgba(186, 121, 255, 0.2)">
                <p className="mb-2 text-[10px] uppercase tracking-[0.24em] text-purple-200/65">Session Pulse</p>
                <BlurText
                  text="Orchestrator live"
                  animateBy="letters"
                  delay={40}
                  className="text-lg font-semibold text-white"
                />
                <div className="mt-4 space-y-3">
                  <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-white/85">
                    <span className="flex items-center gap-2"><BrainCircuit className="size-4 text-purple-300" />Active Agents</span>
                    <strong className="text-purple-200">04</strong>
                  </div>
                  <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-white/85">
                    <span className="flex items-center gap-2"><Bot className="size-4 text-indigo-300" />Tool Calls</span>
                    <strong className="text-indigo-200">17</strong>
                  </div>
                  <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-white/85">
                    <span className="flex items-center gap-2"><Activity className="size-4 text-fuchsia-300" />Context Depth</span>
                    <strong className="text-fuchsia-200">3 hops</strong>
                  </div>
                </div>
              </SpotlightCard>

              <SpotlightCard className="rounded-3xl border-white/10 bg-[#0d0722]/90 p-5" spotlightColor="rgba(124, 87, 245, 0.26)">
                <p className="mb-2 text-[10px] uppercase tracking-[0.24em] text-white/45">Reasoning Stream</p>
                <ShinyText
                  text="Hybrid retrieval confidence: 0.92"
                  speed={4}
                  className="text-sm font-medium text-purple-100"
                />
                <p className="mt-3 text-xs leading-relaxed text-white/60">
                  Graph traversal and semantic retrieval are aligned. Ask follow-up questions to zoom into entity relationships, timeline conflicts, or ownership drift.
                </p>
              </SpotlightCard>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

