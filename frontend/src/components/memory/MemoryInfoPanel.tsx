import { X, Brain, Clock, Lock, Unlock, Hash, Layers, Database } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MemoryDetail {
  id: string;
  content: string;
  layer: string;
  confidence: number;
  is_locked: boolean;
  canvas_x: number | null;
  canvas_y: number | null;
  embedding_preview: number[];
  embedding_dim: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

interface InfoPanelProps {
  memory: MemoryDetail | null;
  isLoading?: boolean;
  onClose: () => void;
}

export default function MemoryInfoPanel({ memory, isLoading, onClose }: InfoPanelProps) {
  if (!memory && !isLoading) return null;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div
      className={cn(
        'w-80 h-full flex flex-col',
        'bg-[#0d0620]/90 border-l border-white/10 backdrop-blur-xl'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <div className="flex items-center gap-2 text-white">
          <Database className="w-4 h-4 text-purple-400" />
          <span className="text-sm font-medium">Memory Details</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-pulse text-white/40">Loading...</div>
        </div>
      ) : memory ? (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Content preview */}
          <div>
            <p className="text-[10px] uppercase tracking-wider text-white/40 mb-2">Content</p>
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <p className="text-sm text-white/80 leading-relaxed">{memory.content}</p>
            </div>
          </div>

          {/* Metadata grid */}
          <div className="grid grid-cols-2 gap-2">
            <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-1.5 text-white/40 mb-1">
                <Layers className="w-3 h-3" />
                <span className="text-[10px] uppercase tracking-wider">Layer</span>
              </div>
              <p className="text-sm text-white/90 capitalize">{memory.layer}</p>
            </div>

            <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-1.5 text-white/40 mb-1">
                <Brain className="w-3 h-3" />
                <span className="text-[10px] uppercase tracking-wider">Confidence</span>
              </div>
              <p className={cn(
                'text-sm font-medium',
                memory.confidence >= 0.7 ? 'text-green-400' :
                memory.confidence >= 0.4 ? 'text-yellow-400' : 'text-red-400'
              )}>
                {Math.round(memory.confidence * 100)}%
              </p>
            </div>

            <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-1.5 text-white/40 mb-1">
                {memory.is_locked ? (
                  <Lock className="w-3 h-3 text-amber-400" />
                ) : (
                  <Unlock className="w-3 h-3" />
                )}
                <span className="text-[10px] uppercase tracking-wider">Status</span>
              </div>
              <p className="text-sm text-white/90">
                {memory.is_locked ? 'Locked' : 'Unlocked'}
              </p>
            </div>

            <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-1.5 text-white/40 mb-1">
                <Hash className="w-3 h-3" />
                <span className="text-[10px] uppercase tracking-wider">Embedding</span>
              </div>
              <p className="text-sm text-white/90">{memory.embedding_dim} dims</p>
            </div>
          </div>

          {/* Timestamps */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-white/50 text-xs">
              <Clock className="w-3 h-3" />
              <span>Created: {formatDate(memory.created_at)}</span>
            </div>
            <div className="flex items-center gap-2 text-white/50 text-xs">
              <Clock className="w-3 h-3" />
              <span>Updated: {formatDate(memory.updated_at)}</span>
            </div>
          </div>

          {/* Embedding preview */}
          {memory.embedding_preview.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-white/40 mb-2">
                Embedding Preview (first 10 dims)
              </p>
              <div className="p-3 rounded-xl bg-black/30 border border-white/10 font-mono text-[10px] text-white/60 overflow-x-auto">
                [{memory.embedding_preview.map(v => v.toFixed(4)).join(', ')}...]
              </div>
            </div>
          )}

          {/* ID */}
          <div>
            <p className="text-[10px] uppercase tracking-wider text-white/40 mb-1">Memory ID</p>
            <code className="text-[11px] text-white/50 font-mono break-all">{memory.id}</code>
          </div>
        </div>
      ) : null}
    </div>
  );
}
