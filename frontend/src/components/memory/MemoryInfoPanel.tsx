import { X, Brain, Clock, Lock, Unlock, Hash, Layers, Database, MessageSquare, Mail, FileText, Link2 } from 'lucide-react';
import { cn } from '@/lib/utils';

// Integration source display info
const INTEGRATION_INFO: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
  slack: { icon: <MessageSquare className="w-3 h-3" />, label: 'Slack', color: 'text-[#E01E5A]' },
  gmail: { icon: <Mail className="w-3 h-3" />, label: 'Gmail', color: 'text-[#EA4335]' },
  notion: { icon: <FileText className="w-3 h-3" />, label: 'Notion', color: 'text-white/80' },
  github: { icon: <Link2 className="w-3 h-3" />, label: 'GitHub', color: 'text-white/80' },
};

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

  // Get integration source from metadata
  const integrationSource = memory?.metadata?.source as string | undefined;
  const integrationInfo = integrationSource ? INTEGRATION_INFO[integrationSource] : null;
  const eventType = memory?.metadata?.event_type as string | undefined;

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
          {/* Integration source badge */}
          {integrationInfo && (
            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-white/5 border border-white/10">
              <div className={cn('flex items-center gap-1.5', integrationInfo.color)}>
                {integrationInfo.icon}
                <span className="text-sm font-medium">{integrationInfo.label}</span>
              </div>
              {eventType && (
                <span className="text-xs text-white/40 ml-auto">
                  {eventType.replace(/_/g, ' ')}
                </span>
              )}
            </div>
          )}

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

          {/* Source info (if from integration) */}
          {integrationSource && (
            <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-1.5 text-white/40 mb-1">
                <Link2 className="w-3 h-3" />
                <span className="text-[10px] uppercase tracking-wider">Source</span>
              </div>
              <p className="text-sm text-white/90 capitalize">{integrationSource}</p>
              {memory.metadata?.event_id ? (
                <p className="text-[10px] text-white/40 mt-1 font-mono truncate">
                  Event: {String(memory.metadata.event_id)}
                </p>
              ) : null}
            </div>
          )}

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

          {/* Additional metadata */}
          {Object.keys(memory.metadata).filter(k => !['source', 'event_type', 'event_id'].includes(k)).length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-white/40 mb-2">
                Additional Metadata
              </p>
              <div className="p-3 rounded-xl bg-black/30 border border-white/10 font-mono text-[10px] text-white/60 overflow-x-auto">
                <pre className="whitespace-pre-wrap">
                  {JSON.stringify(
                    Object.fromEntries(
                      Object.entries(memory.metadata).filter(([k]) => !['source', 'event_type', 'event_id'].includes(k))
                    ),
                    null,
                    2
                  )}
                </pre>
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
