import { GraphStats } from '../types/graph';

interface HeaderProps {
  stats: GraphStats | null;
  onRefresh: () => void;
  onAbout: () => void;
}

export default function Header({ stats, onRefresh, onAbout }: HeaderProps) {
  return (
    <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span className="text-blue-400">⚡</span>
            GNN Discovery Platform
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Predictive Data Mapping for eDiscovery & Risk Management
          </p>
        </div>

        {stats && (
          <div className="flex gap-6 text-sm">
            <div className="text-center">
              <div className="text-gray-400">Nodes</div>
              <div className="text-xl font-bold text-white">{stats.total_nodes}</div>
            </div>
            <div className="text-center">
              <div className="text-gray-400">Edges</div>
              <div className="text-xl font-bold text-white">{stats.total_edges}</div>
            </div>
            <div className="text-center">
              <div className="text-gray-400">Avg Risk</div>
              <div className="text-xl font-bold text-orange-400">
                {(stats.avg_risk_score * 100).toFixed(0)}%
              </div>
            </div>
            <div className="text-center">
              <div className="text-gray-400">Critical</div>
              <div className="text-xl font-bold text-red-400">{stats.critical_nodes}</div>
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition flex items-center gap-2"
            title="Refresh data"
          >
            <span>🔄</span>
            <span>Refresh</span>
          </button>
          <button
            onClick={onAbout}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
            title="About"
          >
            About
          </button>
        </div>
      </div>
    </header>
  );
}
