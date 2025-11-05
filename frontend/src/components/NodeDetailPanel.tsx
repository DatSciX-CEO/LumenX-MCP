import { useState, useEffect } from 'react';
import { GraphNode } from '../types/graph';
import { graphApi } from '../services/api';

interface NodeDetailPanelProps {
  node: GraphNode;
  onFlagToggle: (nodeId: string) => void;
  forecastMonths: number;
}

export default function NodeDetailPanel({ node, onFlagToggle, forecastMonths }: NodeDetailPanelProps) {
  const [forecast, setForecast] = useState<number | null>(null);
  const [loadingForecast, setLoadingForecast] = useState(false);

  useEffect(() => {
    loadForecast();
  }, [node.id, forecastMonths]);

  const loadForecast = async () => {
    try {
      setLoadingForecast(true);
      const result = await graphApi.forecastRisk(node.id, forecastMonths);
      setForecast(result.forecasted_risk);
    } catch (error) {
      console.error('Error loading forecast:', error);
    } finally {
      setLoadingForecast(false);
    }
  };

  return (
    <div className="p-4 space-y-4">
      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => onFlagToggle(node.id)}
          className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition ${
            node.is_flagged
              ? 'bg-yellow-500 hover:bg-yellow-600 text-white'
              : 'bg-slate-700 hover:bg-slate-600 text-gray-300'
          }`}
        >
          {node.is_flagged ? '🚩 Flagged' : 'Flag for Review'}
        </button>
      </div>

      {/* Risk & Relevance Details */}
      <div>
        <h4 className="text-sm font-semibold text-white mb-2">Risk Assessment</h4>
        <div className="bg-slate-700 rounded-lg p-3 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Risk Level:</span>
            <span className={`font-semibold ${getRiskLevelColor(node.risk_level)}`}>
              {node.risk_level.toUpperCase()}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Risk Score:</span>
            <span className="text-white">{(node.risk_score * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Relevance:</span>
            <span className="text-white">{(node.relevance_score * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Temporal Forecast */}
      <div>
        <h4 className="text-sm font-semibold text-white mb-2">
          Temporal Forecast ({forecastMonths} months)
        </h4>
        <div className="bg-slate-700 rounded-lg p-3">
          {loadingForecast ? (
            <div className="text-sm text-gray-400">Loading forecast...</div>
          ) : forecast !== null ? (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Current Risk:</span>
                <span className="text-white">{(node.risk_score * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Forecasted Risk:</span>
                <span className={getRiskColor(forecast)}>{(forecast * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Change:</span>
                <span className={forecast > node.risk_score ? 'text-red-400' : 'text-green-400'}>
                  {forecast > node.risk_score ? '↑' : '↓'} {Math.abs((forecast - node.risk_score) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-400">Forecast not available</div>
          )}
        </div>
      </div>

      {/* Graph Metrics */}
      <div>
        <h4 className="text-sm font-semibold text-white mb-2">Graph Metrics</h4>
        <div className="bg-slate-700 rounded-lg p-3 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Total Connections:</span>
            <span className="text-white">{node.degree}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Incoming:</span>
            <span className="text-white">{node.in_degree}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Outgoing:</span>
            <span className="text-white">{node.out_degree}</span>
          </div>
        </div>
      </div>

      {/* Metadata */}
      {Object.keys(node.metadata).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-white mb-2">Metadata</h4>
          <div className="bg-slate-700 rounded-lg p-3 space-y-2">
            {Object.entries(node.metadata).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-gray-400">{key}:</span>
                <span className="text-white truncate ml-2">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Timestamps */}
      <div>
        <h4 className="text-sm font-semibold text-white mb-2">Timeline</h4>
        <div className="bg-slate-700 rounded-lg p-3 space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-400">Created:</span>
            <span className="text-white">{new Date(node.created_at).toLocaleDateString()}</span>
          </div>
          {node.last_accessed && (
            <div className="flex justify-between">
              <span className="text-gray-400">Last Accessed:</span>
              <span className="text-white">{new Date(node.last_accessed).toLocaleDateString()}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function getRiskLevelColor(level: string): string {
  const colors: Record<string, string> = {
    low: 'text-green-400',
    medium: 'text-yellow-400',
    high: 'text-orange-400',
    critical: 'text-red-400',
  };
  return colors[level] || 'text-gray-400';
}

function getRiskColor(riskScore: number): string {
  if (riskScore >= 0.8) return 'text-red-400';
  if (riskScore >= 0.6) return 'text-orange-400';
  if (riskScore >= 0.4) return 'text-yellow-400';
  return 'text-green-400';
}
