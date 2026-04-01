import { useState, useEffect, useCallback, useRef } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
  Panel,
} from '@xyflow/react';
import type { Node, Edge, Connection, NodeChange, OnNodesChange, OnEdgesChange } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { memoryApi, workspaceApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import MemoryNode from '@/components/memory/MemoryNode';
import MemoryEdge from '@/components/memory/MemoryEdge';
import MemoryContextMenu from '@/components/memory/MemoryContextMenu';
import EdgeReasonDialog from '@/components/memory/EdgeReasonDialog';
import MemoryInfoPanel from '@/components/memory/MemoryInfoPanel';
import { cn } from '@/lib/utils';
import {
  Brain,
  Users,
  Plus,
  Search,
  Loader2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

// Types for API responses
interface MemoryItem {
  id: string;
  content: string;
  layer: string;
  confidence: number;
  score: number;
  created_at: string;
  is_locked?: boolean;
  canvas_x?: number | null;
  canvas_y?: number | null;
}

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

interface CanvasEdgeItem {
  id: string;
  source_id: string;
  target_id: string;
  reason: string | null;
  confidence: number;
  weight: number;
  connection_count: number;
}

interface WorkspaceItem {
  id: string;
  name: string;
}

interface ContextMenuState {
  x: number;
  y: number;
  nodeId: string;
  isLocked: boolean;
}

interface PendingConnection {
  sourceId: string;
  targetId: string;
  sourceContent: string;
  targetContent: string;
}

interface ConnectSourceState {
  id: string;
  content: string;
}

// Node data interface - with index signature for React Flow compatibility
interface NodeData {
  [key: string]: unknown;
  id: string;
  content: string;
  layer: 'personal' | 'workspace';
  confidence: number;
  isLocked: boolean;
  onContextMenu?: (id: string, event: React.MouseEvent) => void;
  onSelect?: (id: string) => void;
}

// Edge data interface - with index signature for React Flow compatibility
interface EdgeData {
  [key: string]: unknown;
  reason?: string | null;
  confidence: number;
  weight: number;
  connectionCount: number;
}

// Type aliases for React Flow
type FlowNode = Node<NodeData>;
type FlowEdge = Edge<EdgeData>;

const nodeTypes = { memory: MemoryNode };
const edgeTypes = { memory: MemoryEdge };

const initialNodes: FlowNode[] = [];
const initialEdges: FlowEdge[] = [];

export default function MemoryCanvas() {
  // Layer state
  const [activeLayer, setActiveLayer] = useState<'personal' | 'workspace'>('personal');
  const [workspaces, setWorkspaces] = useState<WorkspaceItem[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string>('');

  // Flow state - pass typed initial arrays
  const [nodes, setNodes, onNodesChangeBase] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChangeBase] = useEdgesState(initialEdges);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Context menu
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);
  const [connectSource, setConnectSource] = useState<ConnectSourceState | null>(null);

  // Edge creation dialog
  const [pendingConnection, setPendingConnection] = useState<PendingConnection | null>(null);
  const [isCreatingEdge, setIsCreatingEdge] = useState(false);

  // Info panel
  const [selectedMemoryId, setSelectedMemoryId] = useState<string | null>(null);
  const [selectedMemoryDetail, setSelectedMemoryDetail] = useState<MemoryDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  // Add memory dialog
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newMemory, setNewMemory] = useState('');
  const [isStoring, setIsStoring] = useState(false);
  const [storeSuccess, setStoreSuccess] = useState(false);

  // Search
  const [searchQuery, setSearchQuery] = useState('');

  const reactFlowRef = useRef<HTMLDivElement>(null);

  // Counts for stats
  const counts = {
    nodes: nodes.length,
    edges: edges.length,
  };

  // Load workspaces
  useEffect(() => {
    const loadWorkspaces = async () => {
      try {
        const result = await workspaceApi.list() as WorkspaceItem[];
        setWorkspaces(Array.isArray(result) ? result : []);
      } catch {
        console.error('Failed to load workspaces');
      }
    };
    loadWorkspaces();
  }, []);

  // Handle context menu - defined early so it can be used in loadData
  const handleContextMenu = useCallback((nodeId: string, event: React.MouseEvent) => {
    setNodes(currentNodes => {
      const node = currentNodes.find((n) => n.id === nodeId);
      if (node) {
        const nodeData = node.data as NodeData;
        setContextMenu({
          x: event.clientX,
          y: event.clientY,
          nodeId,
          isLocked: nodeData.isLocked,
        });
      }
      return currentNodes;
    });
  }, [setNodes]);

  // Handle node selection
  const handleNodeSelect = useCallback(async (nodeId: string) => {
    setSelectedMemoryId(nodeId);
    setIsLoadingDetail(true);
    try {
      const detail = await memoryApi.getDetail(nodeId) as MemoryDetail;
      setSelectedMemoryDetail(detail);
    } catch {
      setSelectedMemoryDetail(null);
    } finally {
      setIsLoadingDetail(false);
    }
  }, []);

  const handleNodeSelectWithConnect = useCallback(async (nodeId: string) => {
    if (connectSource && connectSource.id !== nodeId) {
      setNodes((currentNodes) => {
        const target = currentNodes.find((n) => n.id === nodeId);
        if (target) {
          const targetData = target.data as NodeData;
          setPendingConnection({
            sourceId: connectSource.id,
            targetId: nodeId,
            sourceContent: connectSource.content,
            targetContent: targetData.content,
          });
        }
        return currentNodes;
      });
      setConnectSource(null);
    }
    await handleNodeSelect(nodeId);
  }, [connectSource, handleNodeSelect, setNodes]);

  // Load memories and edges
  const loadData = useCallback(async () => {
    if (activeLayer === 'workspace' && !selectedWorkspaceId) {
      setNodes([]);
      setEdges([]);
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Fetch memories
      let memories: MemoryItem[];
      if (searchQuery.trim()) {
        memories = await memoryApi.search(
          searchQuery,
          100,
          [activeLayer],
          selectedWorkspaceId || undefined
        ) as MemoryItem[];
      } else {
        memories = await memoryApi.list(
          activeLayer,
          200,
          0,
          selectedWorkspaceId || undefined
        ) as MemoryItem[];
      }

      // Fetch edges
      const canvasEdges = await memoryApi.listEdges(
        activeLayer,
        selectedWorkspaceId || undefined
      ) as CanvasEdgeItem[];

      // Convert to React Flow nodes
      const flowNodes: FlowNode[] = memories.map((mem, i) => ({
        id: mem.id,
        type: 'memory',
        position: {
          x: mem.canvas_x ?? (150 + (i % 5) * 300),
          y: mem.canvas_y ?? (100 + Math.floor(i / 5) * 200),
        },
          data: {
            id: mem.id,
            content: mem.content,
            layer: activeLayer,
            confidence: mem.confidence,
            isLocked: mem.is_locked ?? false,
            onContextMenu: handleContextMenu,
            onSelect: handleNodeSelectWithConnect,
          },
        }));

      // Convert to React Flow edges
      const flowEdges: FlowEdge[] = canvasEdges.map((e) => ({
        id: e.id,
        type: 'memory',
        source: e.source_id,
        target: e.target_id,
        markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(192, 132, 252, 0.8)' },
        data: {
          reason: e.reason,
          confidence: e.confidence,
          weight: e.weight,
          connectionCount: e.connection_count,
        },
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (err) {
      // Handle error - ensure it's a string
      let errorMessage = 'Failed to load data';
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === 'object' && err !== null) {
        // Handle API error objects like {detail: [...]}
        const errObj = err as { detail?: unknown; message?: string };
        if (errObj.detail) {
          errorMessage = typeof errObj.detail === 'string' 
            ? errObj.detail 
            : JSON.stringify(errObj.detail);
        } else if (errObj.message) {
          errorMessage = errObj.message;
        }
      }
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [activeLayer, selectedWorkspaceId, searchQuery, setNodes, setEdges, handleContextMenu, handleNodeSelectWithConnect]);

  // Load on layer/workspace change
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle node changes (position updates)
  const onNodesChange: OnNodesChange<FlowNode> = useCallback(
    (changes: NodeChange<FlowNode>[]) => {
      onNodesChangeBase(changes);

      // Persist position changes (fire and forget)
      for (const change of changes) {
        if (change.type === 'position' && change.position && !change.dragging) {
          memoryApi.updatePosition(change.id, change.position.x, change.position.y).catch(() => {
            console.error('Failed to save position');
          });
        }
      }
    },
    [onNodesChangeBase]
  );

  // Handle edge changes
  const onEdgesChange: OnEdgesChange<FlowEdge> = useCallback(
    (changes) => {
      onEdgesChangeBase(changes);
    },
    [onEdgesChangeBase]
  );

  // Handle new connections
  const onConnect = useCallback(
    (params: Connection) => {
      if (!params.source || !params.target) return;

      const sourceNode = nodes.find((n) => n.id === params.source);
      const targetNode = nodes.find((n) => n.id === params.target);

      if (sourceNode && targetNode) {
        const sourceData = sourceNode.data as NodeData;
        const targetData = targetNode.data as NodeData;
        setPendingConnection({
          sourceId: params.source,
          targetId: params.target,
          sourceContent: sourceData.content,
          targetContent: targetData.content,
        });
      }
    },
    [nodes]
  );

  // Confirm edge creation with reason
  const handleEdgeConfirm = useCallback(
    async (reason: string) => {
      if (!pendingConnection) return;

      setIsCreatingEdge(true);
      try {
        const result = await memoryApi.createEdge(
          pendingConnection.sourceId,
          pendingConnection.targetId,
          reason || null,
        ) as { id: string; weight: number; connection_count: number };

        const newEdge: FlowEdge = {
          id: result.id,
          type: 'memory',
          source: pendingConnection.sourceId,
          target: pendingConnection.targetId,
          markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(192, 132, 252, 0.8)' },
          data: {
            reason: reason || null,
            confidence: 1.0,
            weight: result.weight,
            connectionCount: result.connection_count,
          },
        };

        setEdges((eds) => addEdge(newEdge, eds) as FlowEdge[]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create connection');
      } finally {
        setIsCreatingEdge(false);
        setPendingConnection(null);
      }
    },
    [pendingConnection, setEdges]
  );

  // Context menu actions
  const handleLock = useCallback(async () => {
    if (!contextMenu) return;
    try {
      const result = await memoryApi.toggleLock(contextMenu.nodeId) as { is_locked: boolean };
      setNodes((nds) =>
        nds.map((n) =>
          n.id === contextMenu.nodeId
            ? { ...n, data: { ...n.data, isLocked: result.is_locked } }
            : n
        )
      );
    } catch {
      setError('Failed to toggle lock');
    }
    setContextMenu(null);
  }, [contextMenu, setNodes]);

  const handleDuplicate = useCallback(async () => {
    if (!contextMenu) return;
    try {
      const sourceNode = nodes.find((n) => n.id === contextMenu.nodeId);
      if (!sourceNode) return;

      const result = await memoryApi.duplicate(contextMenu.nodeId) as { id: string };
      const sourceData = sourceNode.data as NodeData;

      const newNode: FlowNode = {
        id: result.id,
        type: 'memory',
        position: {
          x: sourceNode.position.x + 50,
          y: sourceNode.position.y + 50,
        },
        data: {
          ...sourceData,
          id: result.id,
          isLocked: false,
        },
      };

      setNodes((nds) => [...nds, newNode]);
    } catch {
      setError('Failed to duplicate memory');
    }
    setContextMenu(null);
  }, [contextMenu, nodes, setNodes]);

  const handleDelete = useCallback(async () => {
    if (!contextMenu) return;
    try {
      await memoryApi.delete(contextMenu.nodeId);
      setNodes((nds) => nds.filter((n) => n.id !== contextMenu.nodeId));
      setEdges((eds) => eds.filter((e) => e.source !== contextMenu.nodeId && e.target !== contextMenu.nodeId));
      if (selectedMemoryId === contextMenu.nodeId) {
        setSelectedMemoryId(null);
        setSelectedMemoryDetail(null);
      }
    } catch {
      setError('Failed to delete memory');
    }
    setContextMenu(null);
  }, [contextMenu, selectedMemoryId, setNodes, setEdges]);

  // Connect from context menu (not used currently but needed for interface)
  const handleConnectFromMenu = useCallback(() => {
    if (!contextMenu) return;
    setNodes((currentNodes) => {
      const source = currentNodes.find((n) => n.id === contextMenu.nodeId);
      if (source) {
        const sourceData = source.data as NodeData;
        setConnectSource({ id: source.id, content: sourceData.content });
      }
      return currentNodes;
    });
    setContextMenu(null);
  }, [contextMenu, setNodes]);

  // Store new memory
  const handleStore = useCallback(async () => {
    if (!newMemory.trim()) return;

    setIsStoring(true);
    setError('');

    try {
      const result = await memoryApi.store(
        newMemory,
        activeLayer,
        selectedWorkspaceId || undefined
      ) as { id: string };

      const newNode: FlowNode = {
        id: result.id,
        type: 'memory',
        position: { x: 200 + Math.random() * 400, y: 150 + Math.random() * 300 },
        data: {
          id: result.id,
          content: newMemory,
          layer: activeLayer,
          confidence: 1.0,
          isLocked: false,
          onContextMenu: handleContextMenu,
          onSelect: handleNodeSelectWithConnect,
        },
      };

      setNodes((nds) => [...nds, newNode]);
      setStoreSuccess(true);
      setNewMemory('');
      setTimeout(() => {
        setStoreSuccess(false);
        setIsAddOpen(false);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to store memory');
    } finally {
      setIsStoring(false);
    }
  }, [newMemory, activeLayer, selectedWorkspaceId, handleContextMenu, handleNodeSelectWithConnect, setNodes]);

  // Close context menu on click outside
  useEffect(() => {
    const handleClick = () => setContextMenu(null);
    window.addEventListener('click', handleClick);
    return () => window.removeEventListener('click', handleClick);
  }, []);

  return (
    <div className="h-full flex">
      {/* Left Sidebar */}
      <div className="w-64 bg-black/30 border-r border-white/10 p-4 flex flex-col gap-4 backdrop-blur-xl">
        {/* Layer Selection */}
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-white/70 uppercase tracking-wider">Memory Layer</h3>
          <div className="space-y-1">
            <Button
              variant={activeLayer === 'personal' ? 'default' : 'ghost'}
              className={cn(
                'w-full justify-start',
                activeLayer === 'personal'
                  ? 'bg-gradient-to-r from-purple-500/30 to-fuchsia-500/30 text-purple-200'
                  : 'text-white/70 hover:bg-white/10'
              )}
              onClick={() => setActiveLayer('personal')}
            >
              <Brain className="w-4 h-4 mr-2" />
              Personal
            </Button>
            <Button
              variant={activeLayer === 'workspace' ? 'default' : 'ghost'}
              className={cn(
                'w-full justify-start',
                activeLayer === 'workspace'
                  ? 'bg-gradient-to-r from-blue-500/30 to-cyan-500/30 text-blue-200'
                  : 'text-white/70 hover:bg-white/10'
              )}
              onClick={() => setActiveLayer('workspace')}
            >
              <Users className="w-4 h-4 mr-2" />
              Workspace
            </Button>
          </div>
        </div>

        {/* Workspace Selector */}
        {activeLayer === 'workspace' && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-white/70 uppercase tracking-wider">Workspace</h3>
            <Select value={selectedWorkspaceId} onValueChange={setSelectedWorkspaceId}>
              <SelectTrigger className="w-full bg-black/30 border-white/10 text-white">
                <SelectValue placeholder="Select workspace" />
              </SelectTrigger>
              <SelectContent className="bg-[#0a0520] border-white/10">
                {workspaces.map((ws) => (
                  <SelectItem key={ws.id} value={ws.id} className="text-white">
                    {ws.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Divider */}
        <div className="border-t border-white/10" />

        {/* Stats */}
        <div className="space-y-2 text-sm">
          <div className="flex justify-between text-white/50">
            <span>Memories</span>
            <span className="text-white/80">{counts.nodes}</span>
          </div>
          <div className="flex justify-between text-white/50">
            <span>Connections</span>
            <span className="text-white/80">{counts.edges}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-2">
          <Button
            onClick={() => setIsAddOpen(true)}
            className="w-full bg-gradient-to-r from-purple-500 to-fuchsia-500 hover:from-purple-600 hover:to-fuchsia-600 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Memory
          </Button>
          <Button
            variant="outline"
            onClick={loadData}
            disabled={isLoading}
            className="w-full border-white/20 text-white hover:bg-white/10"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            Refresh
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-white/40 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search memories..."
            className="pl-10 bg-black/30 border-white/10 text-white placeholder:text-white/40"
          />
        </div>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 relative" ref={reactFlowRef}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          className="bg-[#0a0520]"
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="rgba(255,255,255,0.05)" />
          <Controls
            className="!bg-black/40 !border-white/10 !rounded-xl [&_button]:!bg-black/50 [&_button]:!border-white/10 [&_button]:!text-white/70 [&_button:hover]:!bg-purple-500/30"
          />
          <Panel position="top-center" className="bg-black/40 backdrop-blur-xl rounded-xl border border-white/10 px-4 py-2">
            <div className="flex items-center gap-3 text-sm">
              <span className={cn(
                'px-2 py-1 rounded-lg',
                activeLayer === 'personal' ? 'bg-purple-500/30 text-purple-200' : 'bg-blue-500/30 text-blue-200'
              )}>
                {activeLayer === 'personal' ? <Brain className="w-4 h-4 inline mr-1" /> : <Users className="w-4 h-4 inline mr-1" />}
                {activeLayer.charAt(0).toUpperCase() + activeLayer.slice(1)} Memory Canvas
              </span>
              {isLoading && <Loader2 className="w-4 h-4 animate-spin text-purple-400" />}
            </div>
          </Panel>
        </ReactFlow>

        {/* Error Toast */}
        {error && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/20 border border-red-500/30 text-red-200 backdrop-blur-xl">
            <AlertCircle className="w-4 h-4" />
            {error}
            <button onClick={() => setError('')} className="ml-2 text-red-200/70 hover:text-red-200">×</button>
          </div>
        )}
      </div>

      {/* Right Sidebar - Info Panel */}
      {selectedMemoryId && (
        <MemoryInfoPanel
          memory={selectedMemoryDetail}
          isLoading={isLoadingDetail}
          onClose={() => {
            setSelectedMemoryId(null);
            setSelectedMemoryDetail(null);
          }}
        />
      )}

      {/* Context Menu */}
      {contextMenu && (
        <MemoryContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          isLocked={contextMenu.isLocked}
          onLock={handleLock}
          onDuplicate={handleDuplicate}
          onDelete={handleDelete}
          onConnect={handleConnectFromMenu}
          onClose={() => setContextMenu(null)}
        />
      )}

      {/* Edge Reason Dialog */}
      {pendingConnection && (
        <EdgeReasonDialog
          sourceContent={pendingConnection.sourceContent}
          targetContent={pendingConnection.targetContent}
          isLoading={isCreatingEdge}
          onConfirm={handleEdgeConfirm}
          onCancel={() => setPendingConnection(null)}
        />
      )}

      {/* Add Memory Dialog */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-lg mx-4 bg-[#0d0620] border border-white/10 rounded-2xl p-6 shadow-2xl">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Plus className="w-5 h-5 text-purple-400" />
              Add New Memory
            </h2>
            <p className="text-white/60 text-sm mb-4">
              Store a new memory in your {activeLayer} layer.
            </p>
            <Input
              value={newMemory}
              onChange={(e) => setNewMemory(e.target.value)}
              placeholder="Enter memory content..."
              className="w-full bg-black/30 border-white/10 text-white placeholder:text-white/40 mb-4"
              disabled={isStoring}
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setIsAddOpen(false)}
                className="border-white/20 text-white hover:bg-white/10"
                disabled={isStoring}
              >
                Cancel
              </Button>
              <Button
                onClick={handleStore}
                disabled={isStoring || !newMemory.trim()}
                className="bg-gradient-to-r from-purple-500 to-fuchsia-500 hover:from-purple-600 hover:to-fuchsia-600 text-white"
              >
                {isStoring ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4 mr-2" />
                )}
                Store
              </Button>
            </div>
            {storeSuccess && (
              <p className="text-sm text-green-400 flex items-center gap-1 mt-3">
                <CheckCircle2 className="w-4 h-4" />
                Memory stored successfully!
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
