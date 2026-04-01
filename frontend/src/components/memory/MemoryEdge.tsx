import { memo } from 'react';
import { BaseEdge, type EdgeProps, getBezierPath, EdgeLabelRenderer } from '@xyflow/react';
import { cn } from '@/lib/utils';

export interface MemoryEdgeData extends Record<string, unknown> {
  reason?: string | null;
  confidence: number;
  weight: number;
  connectionCount: number;
}

function MemoryEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}: EdgeProps) {
  const edgeData = data as MemoryEdgeData | undefined;
  
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const strokeWidth = Math.min(4, 1 + (edgeData?.weight || 1) * 1.5);

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: selected ? 'rgba(168, 85, 247, 0.9)' : 'rgba(192, 132, 252, 0.6)',
          strokeWidth,
          filter: selected ? 'drop-shadow(0 0 6px rgba(168, 85, 247, 0.6))' : undefined,
        }}
        className={cn('transition-all duration-200', selected && 'animate-pulse')}
      />
      
      {/* Edge label with reasoning */}
      {edgeData?.reason && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className={cn(
              'px-2 py-1 rounded-lg text-[10px] max-w-[140px] truncate',
              'bg-black/60 border border-purple-500/30 text-purple-200/90 backdrop-blur-sm',
              'shadow-lg cursor-pointer hover:bg-purple-900/40 transition-colors'
            )}
          >
            {edgeData.reason}
          </div>
        </EdgeLabelRenderer>
      )}

      {/* Connection count badge */}
      {(edgeData?.connectionCount || 1) > 1 && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -100%) translate(${labelX}px,${labelY - 16}px)`,
              pointerEvents: 'none',
            }}
            className="px-1.5 py-0.5 rounded-full text-[9px] font-medium bg-fuchsia-500/80 text-white"
          >
            ×{edgeData?.connectionCount}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export default memo(MemoryEdge);
