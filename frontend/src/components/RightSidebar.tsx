import { useState } from 'react';
import { GraphNode } from '../types/graph';
import NodeDetailPanel from './NodeDetailPanel';
import ChatAssistant from './ChatAssistant';

interface RightSidebarProps {
  selectedNode: GraphNode | null;
  onClose: () => void;
  onFlagToggle: (nodeId: string) => void;
  forecastMonths: number;
}

type Tab = 'overview' | 'chat' | 'analysis';

export default function RightSidebar({ selectedNode, onClose, onFlagToggle, forecastMonths }: RightSidebarProps) {
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  if (!selectedNode) {
    return (
      <div className="w-96 bg-slate-800 border-l border-slate-700 flex items-center justify-center">
        <div className="text-center text-gray-400 p-6">
          <div className="text-4xl mb-4">📊</div>
          <p>Select a node to view details</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-96 bg-slate-800 border-l border-slate-700 flex flex-col">
      {/* Header */}
      <div className="border-b border-slate-700 p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="font-semibold text-white truncate">{selectedNode.label}</h3>
            <p className="text-xs text-gray-400 mt-1">
              {selectedNode.type.toUpperCase()} • ID: {selectedNode.id.substring(0, 12)}...
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition ml-2"
          >
            ✕
          </button>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-2 mt-3">
          <div className="bg-slate-700 rounded p-2">
            <div className="text-xs text-gray-400">Risk Score</div>
            <div className={`text-lg font-bold ${getRiskColor(selectedNode.risk_score)}`}>
              {(selectedNode.risk_score * 100).toFixed(0)}%
            </div>
          </div>
          <div className="bg-slate-700 rounded p-2">
            <div className="text-xs text-gray-400">Relevance</div>
            <div className="text-lg font-bold text-blue-400">
              {(selectedNode.relevance_score * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-700">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex-1 py-3 text-sm font-medium transition ${
            activeTab === 'overview'
              ? 'text-white border-b-2 border-blue-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex-1 py-3 text-sm font-medium transition ${
            activeTab === 'chat'
              ? 'text-white border-b-2 border-blue-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Chat
        </button>
        <button
          onClick={() => setActiveTab('analysis')}
          className={`flex-1 py-3 text-sm font-medium transition ${
            activeTab === 'analysis'
              ? 'text-white border-b-2 border-blue-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Analysis
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'overview' && (
          <NodeDetailPanel
            node={selectedNode}
            onFlagToggle={onFlagToggle}
            forecastMonths={forecastMonths}
          />
        )}
        {activeTab === 'chat' && (
          <ChatAssistant node={selectedNode} />
        )}
        {activeTab === 'analysis' && (
          <div className="p-4">
            <h4 className="font-semibold text-white mb-3">AI Analysis</h4>
            <div className="bg-slate-700 rounded-lg p-4 text-sm text-gray-300">
              <p className="mb-2">
                This node has a <span className={getRiskColor(selectedNode.risk_score)}>
                  {selectedNode.risk_level}
                </span> risk level with {selectedNode.degree} connections.
              </p>
              {selectedNode.is_critical && (
                <p className="text-red-400 mb-2">⚠️ This is a critical entity requiring immediate attention.</p>
              )}
              {selectedNode.is_flagged && (
                <p className="text-yellow-400 mb-2">🚩 This entity has been flagged for review.</p>
              )}
              <p>Use the Chat tab to ask Agent X for detailed analysis.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function getRiskColor(riskScore: number): string {
  if (riskScore >= 0.8) return 'text-red-400';
  if (riskScore >= 0.6) return 'text-orange-400';
  if (riskScore >= 0.4) return 'text-yellow-400';
  return 'text-green-400';
}
