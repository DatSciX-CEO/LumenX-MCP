export type NodeType = 'custodian' | 'file' | 'channel' | 'email' | 'document';
export type EdgeType = 'sent_email' | 'received_email' | 'accessed_file' | 'edited_file' | 'created_file' | 'member_of_channel' | 'shared_in_channel' | 'collaborated_with';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  last_accessed?: string;
  embedding?: number[];
  relevance_score: number;
  risk_level: RiskLevel;
  risk_score: number;
  degree: number;
  in_degree: number;
  out_degree: number;
  activity_trend?: number[];
  forecasted_risk?: number;
  is_flagged: boolean;
  is_critical: boolean;
  investigation_notes: string[];
  // D3 properties (added by force simulation)
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  vx?: number;
  vy?: number;
}

export interface GraphEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: EdgeType;
  timestamp: string;
  weight: number;
  confidence: number;
  metadata: Record<string, any>;
  is_anomalous: boolean;
  risk_contribution: number;
  // D3 properties
  source?: GraphNode | string;
  target?: GraphNode | string;
}

export interface TemporalGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  metadata: {
    total_nodes: number;
    total_edges: number;
    start_date?: string;
    end_date?: string;
  };
}

export interface GraphStats {
  total_nodes: number;
  total_edges: number;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  node_types: Record<string, number>;
  avg_risk_score: number;
  avg_relevance_score: number;
  critical_nodes: number;
  flagged_nodes: number;
  date_range?: {
    start: string;
    end: string;
  };
}

export interface NodeDetails {
  node: GraphNode;
  neighbors: GraphNode[];
  edges: GraphEdge[];
  metrics: {
    neighbor_count: number;
    edge_count: number;
    avg_neighbor_risk: number;
  };
}
