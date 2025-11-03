import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { GraphNode, GraphEdge } from '../types/graph';

interface GraphVisualizationProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode: GraphNode | null;
  onNodeClick: (node: GraphNode) => void;
  onNodeDoubleClick: (node: GraphNode) => void;
  highlightRisk: boolean;
  showInvestigationPath: boolean;
}

export default function GraphVisualization({
  nodes,
  edges,
  selectedNode,
  onNodeClick,
  onNodeDoubleClick,
  highlightRisk,
  showInvestigationPath,
}: GraphVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<d3.Simulation<GraphNode, undefined> | null>(null);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // Clear previous
    svg.selectAll('*').remove();

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Main group for all elements
    const g = svg.append('g');

    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink<GraphNode, GraphEdge>(edges)
        .id(d => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    simulationRef.current = simulation;

    // Draw edges
    const link = g.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('class', 'edge')
      .attr('stroke', (d: GraphEdge) => {
        if (d.is_anomalous) return '#ef4444';
        return '#475569';
      })
      .attr('stroke-width', (d: GraphEdge) => d.is_anomalous ? 2 : 1)
      .attr('stroke-opacity', 0.6)
      .attr('stroke-dasharray', (d: GraphEdge) => d.is_anomalous ? '5,5' : 'none');

    // Draw nodes
    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node')
      .call(drag(simulation) as any);

    // Node circles
    node.append('circle')
      .attr('r', (d: GraphNode) => {
        if (d.is_critical) return 12;
        if (d.is_flagged) return 10;
        return 8;
      })
      .attr('fill', (d: GraphNode) => {
        if (highlightRisk) {
          return getRiskColor(d.risk_score);
        }
        return getNodeTypeColor(d.type);
      })
      .attr('stroke', (d: GraphNode) => {
        if (selectedNode && d.id === selectedNode.id) return '#3b82f6';
        if (d.is_flagged) return '#fbbf24';
        return '#1e293b';
      })
      .attr('stroke-width', (d: GraphNode) => {
        if (selectedNode && d.id === selectedNode.id) return 3;
        if (d.is_flagged) return 2;
        return 1;
      })
      .style('cursor', 'pointer');

    // Critical marker
    node.filter((d: GraphNode) => d.is_critical)
      .append('text')
      .attr('dy', -15)
      .attr('text-anchor', 'middle')
      .text('⚠️')
      .style('font-size', '16px')
      .style('pointer-events', 'none');

    // Node labels
    node.append('text')
      .attr('dy', 25)
      .attr('text-anchor', 'middle')
      .text((d: GraphNode) => truncateLabel(d.label, 20))
      .style('fill', '#e2e8f0')
      .style('font-size', '10px')
      .style('pointer-events', 'none');

    // Node interactions
    node
      .on('click', (event: any, d: GraphNode) => {
        event.stopPropagation();
        onNodeClick(d);
      })
      .on('dblclick', (event: any, d: GraphNode) => {
        event.stopPropagation();
        onNodeDoubleClick(d);
      })
      .on('mouseover', function() {
        d3.select(this).select('circle')
          .transition()
          .duration(200)
          .attr('r', function(d: any) {
            const currentR = d3.select(this).attr('r');
            return parseFloat(currentR) * 1.3;
          });
      })
      .on('mouseout', function(event: any, d: GraphNode) {
        d3.select(this).select('circle')
          .transition()
          .duration(200)
          .attr('r', d.is_critical ? 12 : d.is_flagged ? 10 : 8);
      });

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: GraphNode) => `translate(${d.x},${d.y})`);
    });

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [nodes, edges, selectedNode, highlightRisk, showInvestigationPath]);

  // Drag behavior
  function drag(simulation: d3.Simulation<GraphNode, undefined>) {
    function dragstarted(event: any, d: GraphNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: GraphNode) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: GraphNode) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return d3.drag<any, GraphNode>()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  }

  return (
    <svg
      ref={svgRef}
      className="w-full h-full bg-slate-900"
      style={{ cursor: 'grab' }}
    />
  );
}

// Helper functions
function getNodeTypeColor(type: string): string {
  const colors: Record<string, string> = {
    custodian: '#3b82f6', // blue
    file: '#10b981',      // green
    channel: '#8b5cf6',   // purple
    email: '#f59e0b',     // yellow
    document: '#06b6d4',  // cyan
  };
  return colors[type] || '#6b7280';
}

function getRiskColor(riskScore: number): string {
  if (riskScore >= 0.8) return '#7c2d12'; // critical
  if (riskScore >= 0.6) return '#ef4444'; // high
  if (riskScore >= 0.4) return '#f59e0b'; // medium
  return '#10b981'; // low
}

function truncateLabel(label: string, maxLength: number): string {
  if (label.length <= maxLength) return label;
  return label.substring(0, maxLength - 3) + '...';
}
