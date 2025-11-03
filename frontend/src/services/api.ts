import axios from 'axios';
import { TemporalGraph, GraphNode, GraphStats, NodeDetails } from '../types/graph';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const graphApi = {
  async getGraph(filters?: {
    min_relevance?: number;
    min_risk?: number;
    flagged_only?: boolean;
    critical_only?: boolean;
  }): Promise<TemporalGraph> {
    const response = await api.get('/api/graph', { params: filters });
    return response.data;
  },

  async getNode(nodeId: string): Promise<NodeDetails> {
    const response = await api.get(`/api/nodes/${nodeId}`);
    return response.data;
  },

  async getCriticalFiles(topK: number = 10): Promise<{ files: GraphNode[] }> {
    const response = await api.get('/api/critical-files', { params: { top_k: topK } });
    return response.data;
  },

  async getInvestigationPath(
    startNodeId: string,
    maxDepth: number = 3,
    minRisk: number = 0.5
  ): Promise<{ path: GraphNode[] }> {
    const response = await api.post('/api/investigation-path', {
      start_node_id: startNodeId,
      max_depth: maxDepth,
      min_risk: minRisk,
    });
    return response.data;
  },

  async forecastRisk(
    nodeId: string,
    monthsAhead: number = 3
  ): Promise<{
    node_id: string;
    current_risk: number;
    forecasted_risk: number;
    months_ahead: number;
    change: number;
  }> {
    const response = await api.post('/api/forecast', {
      node_id: nodeId,
      months_ahead: monthsAhead,
    });
    return response.data;
  },

  async getStats(): Promise<GraphStats> {
    const response = await api.get('/api/stats');
    return response.data;
  },

  async analyzeNode(nodeId: string): Promise<{
    success: boolean;
    analysis: string;
    timestamp: string;
  }> {
    const response = await api.post('/api/analyze', { node_id: nodeId });
    return response.data;
  },

  async chat(
    message: string,
    nodeId?: string,
    useOllama: boolean = false
  ): Promise<{
    response: string;
    timestamp: string;
  }> {
    const response = await api.post('/api/chat', {
      message,
      node_id: nodeId,
      use_ollama: useOllama,
    });
    return response.data;
  },

  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
