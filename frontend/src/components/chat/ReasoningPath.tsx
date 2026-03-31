import { Loader2, BrainCircuit, ChevronRight } from 'lucide-react';
import { ShinyText } from '@/components/reactbits/ShinyText';

export default function ReasoningPath() {
  return (
    <div className="mx-auto mb-2 w-full max-w-4xl">
      <div className="inline-flex items-center gap-2 rounded-full border border-purple-200/20 bg-purple-400/8 px-3 py-1.5 text-xs font-medium">
        <BrainCircuit className="h-3.5 w-3.5 animate-pulse text-purple-300" />
        <span className="flex items-center gap-1.5">
          <span className="text-white/60">Graph Traversal</span>
          <ChevronRight className="h-3 w-3 text-white/35" />
          <ShinyText text="Locating Node 452" speed={3} className="font-semibold text-purple-100" />
        </span>
        <Loader2 className="ml-1 h-3 w-3 animate-spin text-white/50" />
      </div>
    </div>
  );
}
