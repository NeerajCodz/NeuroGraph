import { memo, useCallback } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Lock, Unlock, Brain, Users, MessageSquare, Mail, FileText, GitBranch } from 'lucide-react';
import { cn } from '@/lib/utils';

// Integration source icons and colors
const INTEGRATION_BADGES: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  slack: { icon: <MessageSquare className="w-2.5 h-2.5" />, color: 'bg-[#4A154B]/60 text-[#E01E5A]', label: 'Slack' },
  gmail: { icon: <Mail className="w-2.5 h-2.5" />, color: 'bg-[#EA4335]/20 text-[#EA4335]', label: 'Gmail' },
  notion: { icon: <FileText className="w-2.5 h-2.5" />, color: 'bg-white/10 text-white/80', label: 'Notion' },
  github: { icon: <GitBranch className="w-2.5 h-2.5" />, color: 'bg-[#24292e]/60 text-white/80', label: 'GitHub' },
};

export interface MemoryNodeData extends Record<string, unknown> {
  id: string;
  content: string;
  layer: 'personal' | 'workspace';
  confidence: number;
  isLocked: boolean;
  metadata?: {
    source?: string;
    event_type?: string;
    [key: string]: unknown;
  };
  onContextMenu?: (id: string, event: React.MouseEvent) => void;
  onSelect?: (id: string) => void;
}

function MemoryNode({ data, selected }: NodeProps) {
  const nodeData = data as unknown as MemoryNodeData;
  
  const handleContextMenu = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      nodeData.onContextMenu?.(nodeData.id, e);
    },
    [nodeData]
  );

  const handleClick = useCallback(() => {
    nodeData.onSelect?.(nodeData.id);
  }, [nodeData]);

  const layerColor = nodeData.layer === 'personal' 
    ? 'from-purple-500/20 to-fuchsia-500/20 border-purple-500/40'
    : 'from-blue-500/20 to-cyan-500/20 border-blue-500/40';

  const layerIcon = nodeData.layer === 'personal' ? (
    <Brain className="w-3 h-3" />
  ) : (
    <Users className="w-3 h-3" />
  );

  const confidenceColor = nodeData.confidence >= 0.7 
    ? 'text-green-400' 
    : nodeData.confidence >= 0.4 
      ? 'text-yellow-400' 
      : 'text-red-400';

  // Get integration source from metadata
  const integrationSource = nodeData.metadata?.source;
  const integrationBadge = integrationSource ? INTEGRATION_BADGES[integrationSource] : null;

  return (
    <div
      onContextMenu={handleContextMenu}
      onClick={handleClick}
      className={cn(
        'relative min-w-[180px] max-w-[280px] rounded-2xl border backdrop-blur-xl transition-all duration-200 cursor-pointer',
        'bg-gradient-to-br shadow-lg',
        layerColor,
        selected
          ? 'ring-2 ring-purple-400/60 shadow-purple-500/30 shadow-xl scale-[1.02]'
          : 'hover:scale-[1.01] hover:shadow-xl',
        nodeData.isLocked && 'opacity-80'
      )}
    >
      {/* Liquid glass effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/10 to-transparent pointer-events-none" />
      
      {/* Content */}
      <div className="relative p-3">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-white/50">
            {layerIcon}
            <span>{nodeData.layer}</span>
          </div>
          <div className="flex items-center gap-2">
            {/* Integration source badge */}
            {integrationBadge && (
              <span 
                className={cn(
                  'flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-medium',
                  integrationBadge.color
                )}
                title={`From ${integrationBadge.label}`}
              >
                {integrationBadge.icon}
              </span>
            )}
            <span className={cn('text-[10px] font-medium', confidenceColor)}>
              {Math.round(nodeData.confidence * 100)}%
            </span>
            {nodeData.isLocked ? (
              <Lock className="w-3 h-3 text-amber-400" />
            ) : (
              <Unlock className="w-3 h-3 text-white/30" />
            )}
          </div>
        </div>

        {/* Content text */}
        <p className="text-sm text-white/90 leading-relaxed line-clamp-4">
          {nodeData.content}
        </p>
      </div>

      {/* Connection handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-purple-400/80 !border-2 !border-purple-200/50 !rounded-full"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-fuchsia-400/80 !border-2 !border-fuchsia-200/50 !rounded-full"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        className="!w-3 !h-3 !bg-purple-400/80 !border-2 !border-purple-200/50 !rounded-full"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        className="!w-3 !h-3 !bg-fuchsia-400/80 !border-2 !border-fuchsia-200/50 !rounded-full"
      />
    </div>
  );
}

export default memo(MemoryNode);
