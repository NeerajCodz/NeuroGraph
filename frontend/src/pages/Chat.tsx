import MessageList from '@/components/chat/MessageList';
import MessageInput from '@/components/chat/MessageInput';
import { ShinyText } from '@/components/reactbits/ShinyText';
import { Bot, BrainCircuit, Activity, Settings2 } from 'lucide-react';
import { useState } from 'react';

export default function Chat() {
  const [isOrchestratorOpen, setIsOrchestratorOpen] = useState(false);

  return (
    <div className="flex h-full min-h-0 w-full relative">
      <section className="flex h-full min-h-0 min-w-0 flex-1 flex-col mx-auto max-w-4xl pt-4">
        <div className="flex justify-end px-4 md:px-0 mb-2">
          <button
            onClick={() => setIsOrchestratorOpen((prev) => !prev)}
            className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/70 transition-colors hover:bg-white/10 hover:text-white"
          >
            <Settings2 className="size-3.5" />
            Orchestrator
          </button>
        </div>

        <div className="scrollbar-thin flex-1 min-h-0 overflow-y-auto px-2 md:px-4">
          <MessageList />
        </div>

        <div className="mt-auto shrink-0 px-2 py-4 md:px-4 md:py-6">
          <MessageInput />
        </div>
      </section>

      {isOrchestratorOpen && (
        <aside className="absolute right-0 top-0 bottom-0 z-10 w-80 border-l border-white/10 bg-[#090512]/95 backdrop-blur-md shadow-2xl">
          <div className="flex h-full w-full flex-col">
            <div className="flex items-center justify-between border-b border-white/10 p-4">
              <div>
                <h3 className="text-sm font-semibold text-white">Live Session Panel</h3>
                <p className="text-[10px] uppercase tracking-[0.2em] text-purple-200/60">Orchestrator</p>
              </div>
              <button
                onClick={() => setIsOrchestratorOpen(false)}
                className="rounded-lg p-2 text-white/50 hover:bg-white/10 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="scrollbar-thin flex-1 space-y-6 overflow-y-auto p-4 md:p-5">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/45">Session Pulse</p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm text-white/80">
                    <span className="flex items-center gap-2"><BrainCircuit className="size-4 text-purple-400" />Active Agents</span>
                    <strong className="text-purple-200">04</strong>
                  </div>
                  <div className="flex items-center justify-between text-sm text-white/80">
                    <span className="flex items-center gap-2"><Bot className="size-4 text-indigo-400" />Tool Calls</span>
                    <strong className="text-indigo-200">17</strong>
                  </div>
                  <div className="flex items-center justify-between text-sm text-white/80">
                    <span className="flex items-center gap-2"><Activity className="size-4 text-fuchsia-400" />Context Depth</span>
                    <strong className="text-fuchsia-200">3 hops</strong>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-purple-500/20 bg-purple-500/5 p-4">
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-purple-200/50">Reasoning Stream</p>
                <ShinyText
                  text="Hybrid retrieval confidence: 0.92"
                  speed={4}
                  className="mb-2 text-sm font-medium text-purple-100"
                />
                <p className="text-xs leading-relaxed text-white/60">
                  Graph traversal and semantic retrieval are aligned. Ask follow-up questions to zoom into entity relationships, timeline conflicts, or ownership drift.
                </p>
              </div>
            </div>
          </div>
        </aside>
      )}
    </div>
  );
}

