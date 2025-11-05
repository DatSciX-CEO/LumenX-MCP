import { useState, useEffect, useRef } from 'react';
import { GraphNode } from '../types/graph';
import { graphApi } from '../services/api';

interface CriticalFilePanelProps {
  height: number;
  onHeightChange: (height: number) => void;
  onNodeSelect: (node: GraphNode) => void;
}

export default function CriticalFilePanel({ height, onHeightChange, onNodeSelect }: CriticalFilePanelProps) {
  const [files, setFiles] = useState<GraphNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [isResizing, setIsResizing] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadCriticalFiles();
  }, []);

  const loadCriticalFiles = async () => {
    try {
      setLoading(true);
      const data = await graphApi.getCriticalFiles(20);
      setFiles(data.files);
    } catch (error) {
      console.error('Error loading critical files:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMouseDown = () => {
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !panelRef.current) return;
      
      const parentHeight = panelRef.current.parentElement?.clientHeight || 0;
      const newHeight = parentHeight - e.clientY;
      const clampedHeight = Math.max(150, Math.min(500, newHeight));
      onHeightChange(clampedHeight);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, onHeightChange]);

  const getRiskColor = (riskScore: number) => {
    if (riskScore >= 0.8) return 'text-red-400';
    if (riskScore >= 0.6) return 'text-orange-400';
    if (riskScore >= 0.4) return 'text-yellow-400';
    return 'text-green-400';
  };

  return (
    <div
      ref={panelRef}
      className="bg-slate-800 border-t border-slate-700 flex flex-col"
      style={{ height: `${height}px` }}
    >
      {/* Resize handle */}
      <div
        className="h-1 bg-slate-700 hover:bg-blue-500 cursor-row-resize transition"
        onMouseDown={handleMouseDown}
      />

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <span>🔥</span>
          <span>Critical File Watchlist</span>
        </h3>
        <button
          onClick={loadCriticalFiles}
          className="text-xs px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded transition"
        >
          Refresh
        </button>
      </div>

      {/* Files list */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="text-center text-gray-400 py-8">Loading critical files...</div>
        ) : files.length === 0 ? (
          <div className="text-center text-gray-400 py-8">No critical files found</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {files.map((file) => (
              <div
                key={file.id}
                className="bg-slate-700 hover:bg-slate-600 rounded-lg p-3 cursor-pointer transition group"
                onClick={() => onNodeSelect(file)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="text-sm font-medium text-white truncate flex-1 group-hover:text-blue-400">
                    {file.label}
                  </div>
                  {file.is_critical && (
                    <span className="text-xs bg-red-500 text-white px-2 py-0.5 rounded ml-2">
                      Critical
                    </span>
                  )}
                </div>
                
                <div className="text-xs text-gray-400 mb-2 truncate">
                  {file.metadata.file_type || 'unknown'}
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400">
                    Relevance: <span className="text-blue-400">{(file.relevance_score * 100).toFixed(0)}%</span>
                  </span>
                  <span className="text-gray-400">
                    Risk: <span className={getRiskColor(file.risk_score)}>{(file.risk_score * 100).toFixed(0)}%</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
