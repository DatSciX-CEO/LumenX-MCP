import { useState, useEffect } from 'react';
import { graphApi } from './services/api';
import { GraphNode, TemporalGraph, GraphStats } from './types/graph';
import Header from './components/Header';
import ControlPanel from './components/ControlPanel';
import GraphVisualization from './components/GraphVisualization';
import RightSidebar from './components/RightSidebar';
import CriticalFilePanel from './components/CriticalFilePanel';
import LoadingScreen from './components/LoadingScreen';

type AppStatus = 'LOADING' | 'READY' | 'ERROR';

function App() {
  // Application state
  const [status, setStatus] = useState<AppStatus>('LOADING');
  const [graph, setGraph] = useState<TemporalGraph | null>(null);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  
  // Filter state
  const [minRelevance, setMinRelevance] = useState(0.0);
  const [minRisk, setMinRisk] = useState(0.0);
  const [forecastMonths, setForecastMonths] = useState(3);
  const [highlightRisk, setHighlightRisk] = useState(false);
  const [showInvestigationPath, setShowInvestigationPath] = useState(false);
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [criticalOnly, setCriticalOnly] = useState(false);
  
  // UI state
  const [showAboutModal, setShowAboutModal] = useState(false);
  const [criticalPanelHeight, setCriticalPanelHeight] = useState(200);

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  // Reload data when filters change
  useEffect(() => {
    if (status === 'READY') {
      loadGraph();
    }
  }, [minRelevance, minRisk, flaggedOnly, criticalOnly]);

  const loadData = async () => {
    try {
      setStatus('LOADING');
      
      // Load graph and stats in parallel
      const [graphData, statsData] = await Promise.all([
        graphApi.getGraph(),
        graphApi.getStats(),
      ]);
      
      setGraph(graphData);
      setStats(statsData);
      setStatus('READY');
    } catch (error) {
      console.error('Error loading data:', error);
      setStatus('ERROR');
    }
  };

  const loadGraph = async () => {
    try {
      const graphData = await graphApi.getGraph({
        min_relevance: minRelevance,
        min_risk: minRisk,
        flagged_only: flaggedOnly,
        critical_only: criticalOnly,
      });
      setGraph(graphData);
    } catch (error) {
      console.error('Error loading graph:', error);
    }
  };

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);
  };

  const handleNodeDoubleClick = (node: GraphNode) => {
    setSelectedNode(node);
    setShowInvestigationPath(true);
  };

  const handleFlagToggle = async (nodeId: string) => {
    if (!graph) return;
    
    // Update local state
    const updatedNodes = graph.nodes.map(n =>
      n.id === nodeId ? { ...n, is_flagged: !n.is_flagged } : n
    );
    
    setGraph({ ...graph, nodes: updatedNodes });
    
    if (selectedNode?.id === nodeId) {
      setSelectedNode({ ...selectedNode, is_flagged: !selectedNode.is_flagged });
    }
  };

  const handleRefresh = () => {
    loadData();
    setSelectedNode(null);
  };

  if (status === 'LOADING') {
    return <LoadingScreen />;
  }

  if (status === 'ERROR') {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-400 mb-4">
            Failed to Load Application
          </h1>
          <p className="text-gray-400 mb-6">
            Could not connect to the GNN backend service.
          </p>
          <button
            onClick={loadData}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-gray-100">
      {/* Header */}
      <Header
        stats={stats}
        onRefresh={handleRefresh}
        onAbout={() => setShowAboutModal(true)}
      />

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar - Control panel */}
        <ControlPanel
          minRelevance={minRelevance}
          setMinRelevance={setMinRelevance}
          minRisk={minRisk}
          setMinRisk={setMinRisk}
          forecastMonths={forecastMonths}
          setForecastMonths={setForecastMonths}
          highlightRisk={highlightRisk}
          setHighlightRisk={setHighlightRisk}
          showInvestigationPath={showInvestigationPath}
          setShowInvestigationPath={setShowInvestigationPath}
          flaggedOnly={flaggedOnly}
          setFlaggedOnly={setFlaggedOnly}
          criticalOnly={criticalOnly}
          setCriticalOnly={setCriticalOnly}
        />

        {/* Center - Graph visualization */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 relative" style={{ height: `calc(100% - ${criticalPanelHeight}px)` }}>
            {graph && (
              <GraphVisualization
                nodes={graph.nodes}
                edges={graph.edges}
                selectedNode={selectedNode}
                onNodeClick={handleNodeClick}
                onNodeDoubleClick={handleNodeDoubleClick}
                highlightRisk={highlightRisk}
                showInvestigationPath={showInvestigationPath}
              />
            )}
          </div>

          {/* Bottom - Critical files panel */}
          <CriticalFilePanel
            height={criticalPanelHeight}
            onHeightChange={setCriticalPanelHeight}
            onNodeSelect={handleNodeClick}
          />
        </div>

        {/* Right sidebar - Node details */}
        <RightSidebar
          selectedNode={selectedNode}
          onClose={() => setSelectedNode(null)}
          onFlagToggle={handleFlagToggle}
          forecastMonths={forecastMonths}
        />
      </div>

      {/* About Modal */}
      {showAboutModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setShowAboutModal(false)}
        >
          <div 
            className="bg-slate-800 rounded-lg p-6 max-w-2xl max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-2xl font-bold mb-4">Predictive Data Mapping GNN</h2>
            <p className="text-gray-300 mb-4">
              Version 1.0.0 - Production MVP
            </p>
            <div className="space-y-4 text-gray-400">
              <p>
                A Graph Neural Network (GNN) powered system for predictive data mapping,
                risk assessment, and investigation in eDiscovery and compliance workflows.
              </p>
              <p>
                <strong className="text-white">Key Features:</strong>
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Interactive temporal knowledge graph visualization</li>
                <li>AI-powered risk and relevance scoring</li>
                <li>Predictive temporal forecasting</li>
                <li>Investigation path analysis</li>
                <li>Local LLM integration (Ollama) and Google ADK support</li>
                <li>Production-ready, modular architecture</li>
              </ul>
              <p>
                <strong className="text-white">Technology Stack:</strong>
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Backend: Python, PyTorch, PyTorch Geometric, FastAPI</li>
                <li>Frontend: React, TypeScript, D3.js, Tailwind CSS</li>
                <li>AI: Google ADK, Ollama, Sentence Transformers</li>
              </ul>
            </div>
            <button
              onClick={() => setShowAboutModal(false)}
              className="mt-6 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
