import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Button } from '@/components/ui/button';
import { Maximize2, ZoomIn, ZoomOut, Radar, Loader2, RefreshCw } from 'lucide-react';
import { graphApi } from '@/services/api';
import type { GraphVisualization as GraphVizData, GraphNode as ApiNode, GraphEdge as ApiEdge } from '@/types/api';

type GraphNode = d3.SimulationNodeDatum & {
  id: string;
  label: string;
  type: string;
  layer: string;
  confidence?: number;
};

type GraphLink = d3.SimulationLinkDatum<GraphNode> & {
  source: string | GraphNode;
  target: string | GraphNode;
  weight: number;
  relation: string;
  reason?: string | null;
};

const typeColors: Record<string, string> = {
  Person: '#7fb5ff',
  Organization: '#b084ff',
  Project: '#dd8cff',
  Technology: '#7bffa3',
  Concept: '#ff8d9d',
  default: '#b084ff',
};

const layerColors: Record<string, string> = {
  personal: '#b084ff',
  tenant: '#7fb5ff',
  global: '#7bffa3',
};

export default function GraphVisualization() {
  const svgRef = useRef<SVGSVGElement>(null);
  const zoomBehaviorRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchGraphData = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await graphApi.getVisualization(undefined, 3, 100) as GraphVizData;
      
      const nodes: GraphNode[] = (data.nodes || []).map((n: ApiNode) => ({
        id: n.id,
        label: n.name,
        type: n.type,
        layer: n.layer,
      }));

      const links: GraphLink[] = (data.edges || []).map((e: ApiEdge) => ({
        source: e.source,
        target: e.target,
        weight: e.confidence || 0.5,
        relation: e.type,
        reason: e.reason,
      }));

      setGraphData({ nodes, links });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load graph');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
  }, []);

  useEffect(() => {
    if (!svgRef.current || !graphData || graphData.nodes.length === 0) return;

    const svgElement = svgRef.current;
    const svg = d3.select(svgRef.current);

    const renderGraph = () => {
      const width = svgElement.clientWidth;
      const height = svgElement.clientHeight;

      svg.selectAll('*').remove();

      const nodes: GraphNode[] = graphData.nodes.map((node) => ({ ...node }));
      const links: GraphLink[] = graphData.links.map((link) => ({ ...link }));

      const defs = svg.append('defs');
      const glow = defs.append('filter').attr('id', 'node-glow').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%');
      glow.append('feGaussianBlur').attr('stdDeviation', 4).attr('result', 'coloredBlur');
      const merge = glow.append('feMerge');
      merge.append('feMergeNode').attr('in', 'coloredBlur');
      merge.append('feMergeNode').attr('in', 'SourceGraphic');

      const viewport = svg.append('g').attr('class', 'viewport');
      const linkLayer = viewport.append('g');
      const nodeLayer = viewport.append('g');
      const labelLayer = viewport.append('g');

      const zoomBehavior = d3
        .zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.4, 2.8])
        .on('zoom', (event) => {
          viewport.attr('transform', event.transform.toString());
        });

      zoomBehaviorRef.current = zoomBehavior;
      svg.call(zoomBehavior as d3.ZoomBehavior<SVGSVGElement, unknown>);

      const link = linkLayer
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke', 'rgba(210, 176, 255, 0.62)')
        .attr('stroke-width', (d) => 1.3 + d.weight * 2)
        .attr('stroke-linecap', 'round');

      const linkLabel = labelLayer
        .selectAll('text.link-label')
        .data(links)
        .join('text')
        .attr('class', 'link-label')
        .text((d) => d.relation)
        .attr('fill', 'rgba(236, 220, 255, 0.62)')
        .attr('font-size', 9)
        .attr('text-anchor', 'middle')
        .attr('letter-spacing', '0.08em');

      const getNodeColor = (d: GraphNode) => typeColors[d.type] || typeColors.default;

      const node = nodeLayer
        .selectAll<SVGGElement, GraphNode>('g')
        .data(nodes)
        .join('g')
        .attr('cursor', 'pointer')
        .on('click', (_, d) => setSelectedNode(d));

      node
        .append('circle')
        .attr('r', 20)
        .attr('fill', (d) => getNodeColor(d))
        .attr('fill-opacity', 0.25)
        .attr('stroke', (d) => getNodeColor(d))
        .attr('stroke-width', 1.2)
        .attr('filter', 'url(#node-glow)');

      node
        .append('circle')
        .attr('r', 10)
        .attr('fill', (d) => getNodeColor(d));

      node
        .append('text')
        .attr('dy', 34)
        .attr('fill', 'rgba(249, 239, 255, 0.9)')
        .attr('font-size', 10)
        .attr('font-weight', 600)
        .attr('text-anchor', 'middle')
        .text((d) => d.label.length > 15 ? d.label.slice(0, 15) + '...' : d.label);

      const simulation = d3
        .forceSimulation(nodes)
        .force(
          'link',
          d3
            .forceLink<GraphNode, GraphLink>(links)
            .id((d) => d.id)
            .distance((d) => 100 + (1 - d.weight) * 80)
            .strength(0.6)
        )
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collide', d3.forceCollide<GraphNode>().radius(40));

      const drag = d3
        .drag<SVGGElement, GraphNode>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.25).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        });

      node.call(drag);

      simulation.on('tick', () => {
        link
          .attr('x1', (d) => (d.source as GraphNode).x ?? 0)
          .attr('y1', (d) => (d.source as GraphNode).y ?? 0)
          .attr('x2', (d) => (d.target as GraphNode).x ?? 0)
          .attr('y2', (d) => (d.target as GraphNode).y ?? 0);

        node.attr('transform', (d) => `translate(${d.x ?? 0}, ${d.y ?? 0})`);

        linkLabel
          .attr('x', (d) => (((d.source as GraphNode).x ?? 0) + ((d.target as GraphNode).x ?? 0)) / 2)
          .attr('y', (d) => (((d.source as GraphNode).y ?? 0) + ((d.target as GraphNode).y ?? 0)) / 2 - 8);
      });

      return () => {
        simulation.stop();
      };
    };

    const cleanup = renderGraph();

    const handleResize = () => {
      cleanup();
      renderGraph();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cleanup();
    };
  }, [graphData]);

  const handleZoomIn = () => {
    if (!svgRef.current || !zoomBehaviorRef.current) return;
    d3.select(svgRef.current)
      .transition()
      .duration(220)
      .call(zoomBehaviorRef.current.scaleBy as never, 1.22);
  };

  const handleZoomOut = () => {
    if (!svgRef.current || !zoomBehaviorRef.current) return;
    d3.select(svgRef.current)
      .transition()
      .duration(220)
      .call(zoomBehaviorRef.current.scaleBy as never, 0.82);
  };

  const handleReset = () => {
    if (!svgRef.current || !zoomBehaviorRef.current) return;
    d3.select(svgRef.current)
      .transition()
      .duration(260)
      .call(zoomBehaviorRef.current.transform as never, d3.zoomIdentity);
  };

  if (isLoading) {
    return (
      <div className="relative h-full w-full overflow-hidden rounded-3xl border border-white/10 bg-[#080513]/65 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
          <p className="text-white/60">Loading knowledge graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="relative h-full w-full overflow-hidden rounded-3xl border border-white/10 bg-[#080513]/65 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center">
          <p className="text-red-300">{error}</p>
          <Button variant="outline" onClick={fetchGraphData} className="text-white border-white/20">
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="relative h-full w-full overflow-hidden rounded-3xl border border-white/10 bg-[#080513]/65 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center">
          <Radar className="w-12 h-12 text-purple-400/30" />
          <p className="text-white/60">No nodes in the knowledge graph yet</p>
          <p className="text-white/40 text-sm">Add memories to start building your graph</p>
        </div>
      </div>
    );
  }

  return (
    <div className="group relative h-full w-full overflow-hidden rounded-3xl border border-white/10 bg-[#080513]/65">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(178,111,255,0.22),transparent_58%)]" />
      <svg ref={svgRef} className="h-full w-full" />

      <div className="absolute left-4 top-4 rounded-2xl border border-white/15 bg-black/35 px-3 py-2 backdrop-blur-md">
        <p className="text-[10px] uppercase tracking-[0.22em] text-purple-200/65">Graph Signal</p>
        <div className="mt-1 flex items-center gap-2 text-sm text-white/90">
          <Radar className="size-4 text-purple-300" />
          {graphData.nodes.length} nodes • {graphData.links.length} relations
        </div>
      </div>

      <Button
        variant="ghost"
        size="icon"
        className="absolute left-4 bottom-4 h-9 w-9 rounded-full bg-black/30 text-white/80 hover:bg-white/12 hover:text-white backdrop-blur-md"
        onClick={fetchGraphData}
      >
        <RefreshCw className="h-4 w-4" />
      </Button>

      {selectedNode && (
        <div className="absolute right-4 top-4 w-64 rounded-2xl border border-white/15 bg-[#130b29]/92 p-3 text-white shadow-xl backdrop-blur-md">
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/45">Selected Node</p>
          <h3 className="mt-1 text-base font-semibold">{selectedNode.label}</h3>
          <div className="mt-3 space-y-2 text-xs text-white/75">
            <div className="flex items-center justify-between rounded-xl bg-white/5 px-2 py-1.5">
              <span>Type</span>
              <strong className="text-purple-100">{selectedNode.type}</strong>
            </div>
            <div className="flex items-center justify-between rounded-xl bg-white/5 px-2 py-1.5">
              <span>Layer</span>
              <strong style={{ color: layerColors[selectedNode.layer] || '#fff' }}>{selectedNode.layer}</strong>
            </div>
            <div className="flex items-center justify-between rounded-xl bg-white/5 px-2 py-1.5">
              <span>ID</span>
              <strong className="text-white/60 font-mono text-[10px]">{selectedNode.id.slice(0, 12)}...</strong>
            </div>
          </div>
          <button
            onClick={() => setSelectedNode(null)}
            className="mt-3 w-full text-center text-xs text-white/40 hover:text-white/60"
          >
            Click to dismiss
          </button>
        </div>
      )}

      <div className="absolute bottom-4 right-4 flex gap-2 rounded-full border border-white/15 bg-black/30 p-1.5 opacity-0 backdrop-blur-md transition-opacity group-hover:opacity-100">
        <Button variant="ghost" size="icon" className="h-9 w-9 rounded-full text-white/80 hover:bg-white/12 hover:text-white" onClick={handleZoomOut}>
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-9 w-9 rounded-full text-white/80 hover:bg-white/12 hover:text-white" onClick={handleZoomIn}>
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-9 w-9 rounded-full text-white/80 hover:bg-white/12 hover:text-white" onClick={handleReset}>
          <Maximize2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

