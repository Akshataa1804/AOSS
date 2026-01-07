import { useState, useEffect } from "react";

export default function GraphPanel({ command }) {
  const [graphData, setGraphData] = useState(null);

  // For now show a placeholder panel — backend graph data will be added later
  useEffect(() => {
    if (command) {
      setGraphData({
        message: "Graph reasoning will display here once backend is connected.",
        command,
      });
    }
  }, [command]);

  if (!command) return null;

  return (
    <div className="mt-6 p-4 bg-base-200 rounded-lg border border-base-300 text-sm">
      <h3 className="font-semibold mb-2">Graph-based Reasoning Preview</h3>
      <p className="text-base-content/70 mb-3">
        Command detected for graph lookup:
      </p>
      <div className="px-3 py-2 rounded bg-base-100 border border-base-300 font-mono">
        {command}
      </div>

      {/* placeholder content until backend connects */}
      <div className="mt-4 p-3 bg-base-100 rounded border border-dashed border-base-300 text-base-content/60">
        Graph visualization will appear here after backend integration.
      </div>
    </div>
  );
}
