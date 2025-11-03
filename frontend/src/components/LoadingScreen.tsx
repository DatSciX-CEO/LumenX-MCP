export default function LoadingScreen() {
  return (
    <div className="flex items-center justify-center h-screen bg-slate-900">
      <div className="text-center">
        <div className="mb-6">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent"></div>
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Loading GNN System</h2>
        <p className="text-gray-400">Initializing temporal knowledge graph...</p>
      </div>
    </div>
  );
}
