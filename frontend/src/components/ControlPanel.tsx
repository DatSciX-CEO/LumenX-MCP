interface ControlPanelProps {
  minRelevance: number;
  setMinRelevance: (value: number) => void;
  minRisk: number;
  setMinRisk: (value: number) => void;
  forecastMonths: number;
  setForecastMonths: (value: number) => void;
  highlightRisk: boolean;
  setHighlightRisk: (value: boolean) => void;
  showInvestigationPath: boolean;
  setShowInvestigationPath: (value: boolean) => void;
  flaggedOnly: boolean;
  setFlaggedOnly: (value: boolean) => void;
  criticalOnly: boolean;
  setCriticalOnly: (value: boolean) => void;
}

export default function ControlPanel(props: ControlPanelProps) {
  return (
    <div className="w-80 bg-slate-800 border-r border-slate-700 p-6 overflow-y-auto">
      <h2 className="text-lg font-bold mb-6 text-white">Control Panel</h2>

      {/* Filters Section */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Filters</h3>
        
        {/* Min Relevance */}
        <div className="mb-4">
          <label className="block text-sm text-gray-400 mb-2">
            Min Relevance: {props.minRelevance.toFixed(2)}
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={props.minRelevance}
            onChange={(e) => props.setMinRelevance(parseFloat(e.target.value))}
            className="w-full accent-blue-500"
          />
        </div>

        {/* Min Risk */}
        <div className="mb-4">
          <label className="block text-sm text-gray-400 mb-2">
            Min Risk: {props.minRisk.toFixed(2)}
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={props.minRisk}
            onChange={(e) => props.setMinRisk(parseFloat(e.target.value))}
            className="w-full accent-orange-500"
          />
        </div>

        {/* Forecast Months */}
        <div className="mb-4">
          <label className="block text-sm text-gray-400 mb-2">
            Forecast: {props.forecastMonths} months
          </label>
          <input
            type="range"
            min="1"
            max="12"
            step="1"
            value={props.forecastMonths}
            onChange={(e) => props.setForecastMonths(parseInt(e.target.value))}
            className="w-full accent-purple-500"
          />
        </div>
      </div>

      {/* Visualization Options */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Visualization</h3>
        
        <label className="flex items-center gap-2 mb-3 cursor-pointer">
          <input
            type="checkbox"
            checked={props.highlightRisk}
            onChange={(e) => props.setHighlightRisk(e.target.checked)}
            className="w-4 h-4 accent-red-500"
          />
          <span className="text-sm text-gray-300">Highlight Risk</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={props.showInvestigationPath}
            onChange={(e) => props.setShowInvestigationPath(e.target.checked)}
            className="w-4 h-4 accent-yellow-500"
          />
          <span className="text-sm text-gray-300">Show Investigation Path</span>
        </label>
      </div>

      {/* Node Filters */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Node Filters</h3>
        
        <label className="flex items-center gap-2 mb-3 cursor-pointer">
          <input
            type="checkbox"
            checked={props.flaggedOnly}
            onChange={(e) => props.setFlaggedOnly(e.target.checked)}
            className="w-4 h-4 accent-yellow-500"
          />
          <span className="text-sm text-gray-300">Flagged Only</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={props.criticalOnly}
            onChange={(e) => props.setCriticalOnly(e.target.checked)}
            className="w-4 h-4 accent-red-500"
          />
          <span className="text-sm text-gray-300">Critical Only</span>
        </label>
      </div>

      {/* Legend */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Legend</h3>
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-500"></div>
            <span className="text-gray-400">Custodian</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-gray-400">File</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-purple-500"></div>
            <span className="text-gray-400">Channel</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
            <span className="text-gray-400">Email</span>
          </div>
        </div>
      </div>
    </div>
  );
}
