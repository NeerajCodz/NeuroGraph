import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Button } from '@/components/ui/button';
import { Maximize2, ZoomIn, ZoomOut, Activity, Radar } from 'lucide-react';

type GraphNode = d3.SimulationNodeDatum & {
  id: string;
  label: string;
  type: 'Core' | 'Team' | 'Project' | 'Risk';
  risk: number;
};

type GraphLink = d3.SimulationLinkDatum<GraphNode> & {
  source: string | GraphNode;
  target: string | GraphNode;
  weight: number;
  relation: string;
};

const nodeSeed: GraphNode[] = [
  { id: 'core-1', label: 'Orchestrator', type: 'Core', risk: 0.18 },
  { id: 'proj-452', label: 'Node 452', type: 'Project', risk: 0.73 },
  { id: 'proj-507', label: 'Node 507', type: 'Project', risk: 0.84 },
  { id: 'team-alpha', label: 'Team Alpha', type: 'Team', risk: 0.52 },
  { id: 'team-beta', label: 'Team Beta', type: 'Team', risk: 0.66 },
  { id: 'risk-iam', label: 'IAM Drift', type: 'Risk', risk: 0.78 },
  { id: 'risk-rollout', label: 'Rollout Gate', type: 'Risk', risk: 0.71 },
];

const linkSeed: GraphLink[] = [
  { source: 'core-1', target: 'proj-452', weight: 0.88, relation: 'routes' },
  { source: 'core-1', target: 'proj-507', weight: 0.75, relation: 'routes' },
  { source: 'proj-452', target: 'team-alpha', weight: 0.81, relation: 'owned_by' },
  { source: 'proj-507', target: 'team-beta', weight: 0.84, relation: 'owned_by' },
  { source: 'proj-452', target: 'risk-iam', weight: 0.78, relation: 'triggers' },
  { source: 'proj-507', target: 'risk-rollout', weight: 0.71, relation: 'triggers' },
  { source: 'team-alpha', target: 'team-beta', weight: 0.62, relation: 'conflicts_with' },
];

const nodeColor: Record<GraphNode['type'], string> = {
  Core: '#b084ff',
  Team: '#7fb5ff',
  Project: '#dd8cff',
  Risk: '#ff8d9d',
};

export default function GraphVisualization() {
  const svgRef = useRef<SVGSVGElement>(null);
  const zoomBehaviorRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const [selectedNode, setSelectedNode] = React.useState<GraphNode | null>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svgElement = svgRef.current;
    const svg = d3.select(svgRef.current);

    const renderGraph = () => {
      const width = svgElement.clientWidth;
      const height = svgElement.clientHeight;

      svg.selectAll('*').remove();

      const nodes: GraphNode[] = nodeSeed.map((node) => ({ ...node }));
      const links: GraphLink[] = linkSeed.map((link) => ({ ...link }));

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
        .selectAll('text')
        .data(links)
        .join('text')
        .text((d) => d.relation)
        .attr('fill', 'rgba(236, 220, 255, 0.62)')
        .attr('font-size', 10)
        .attr('text-anchor', 'middle')
        .attr('letter-spacing', '0.08em');

      const node = nodeLayer
        .selectAll<SVGGElement, GraphNode>('g')
        .data(nodes)
        .join('g')
        .attr('cursor', 'pointer')
        .on('click', (_, d) => setSelectedNode(d));

      node
        .append('circle')
        .attr('r', (d) => (d.type === 'Core' ? 24 : 18))
        .attr('fill', (d) => nodeColor[d.type])
        .attr('fill-opacity', 0.25)
        .attr('stroke', (d) => nodeColor[d.type])
        .attr('stroke-width', 1.2)
        .attr('filter', 'url(#node-glow)');

      node
        .append('circle')
        .attr('r', (d) => (d.type === 'Core' ? 12 : 9.5))
        .attr('fill', (d) => nodeColor[d.type]);

      node
        .append('text')
        .attr('dy', (d) => (d.type === 'Core' ? 38 : 31))
        .attr('fill', 'rgba(249, 239, 255, 0.9)')
        .attr('font-size', 11)
        .attr('font-weight', 600)
        .attr('text-anchor', 'middle')
        .text((d) => d.label);

      const simulation = d3
        .forceSimulation(nodes)
        .force(
          'link',
          d3
            .forceLink<GraphNode, GraphLink>(links)
            .id((d) => d.id)
            .distance((d) => 96 + (1 - d.weight) * 90)
            .strength(0.65)
        )
        .force('charge', d3.forceManyBody().strength(-350))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collide', d3.forceCollide<GraphNode>().radius((d) => (d.type === 'Core' ? 46 : 34)));

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
  }, []);

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

  return (
    <div className="group relative h-full w-full overflow-hidden rounded-3xl border border-white/10 bg-[#080513]/65">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(178,111,255,0.22),transparent_58%)]" />
      <svg ref={svgRef} className="h-full w-full" />

      <div className="absolute left-4 top-4 rounded-2xl border border-white/15 bg-black/35 px-3 py-2 backdrop-blur-md">
        <p className="text-[10px] uppercase tracking-[0.22em] text-purple-200/65">Graph Signal</p>
        <div className="mt-1 flex items-center gap-2 text-sm text-white/90">
          <Radar className="size-4 text-purple-300" />
          7 nodes • 7 relations
        </div>
      </div>

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
              <span className="flex items-center gap-1"><Activity className="size-3.5" />Risk Score</span>
              <strong className="text-fuchsia-200">{selectedNode.risk.toFixed(2)}</strong>
            </div>
          </div>
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

