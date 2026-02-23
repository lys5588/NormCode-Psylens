import { Database, Table } from 'lucide-react';
import { formatBytes, T } from './utils';
import type { DatabaseOverview, RunStatistics } from './types';

interface OverviewViewProps {
  overview: DatabaseOverview;
  statistics: RunStatistics | null;
}

export function OverviewView({ overview, statistics }: OverviewViewProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className={`${T.card} rounded-lg border ${T.border} p-4`}>
          <h3 className={`text-sm font-semibold ${T.text} mb-3 flex items-center gap-2`}>
            <Database className="w-4 h-4 text-[#58a6ff]" />
            Database Info
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className={T.dim}>Run ID</span>
              <span className={`font-mono ${T.text}`}>{overview.run_id.slice(0, 16)}...</span>
            </div>
            <div className="flex justify-between">
              <span className={T.dim}>Size</span>
              <span className={T.text}>{formatBytes(overview.size_bytes)}</span>
            </div>
            <div className="flex justify-between">
              <span className={T.dim}>Executions</span>
              <span className={T.text}>{overview.total_executions}</span>
            </div>
            <div className="flex justify-between">
              <span className={T.dim}>Checkpoints</span>
              <span className={T.text}>{overview.total_checkpoints}</span>
            </div>
          </div>
        </div>

        {statistics && (
          <div className={`${T.card} rounded-lg border ${T.border} p-4`}>
            <h3 className={`text-sm font-semibold ${T.text} mb-3`}>Statistics</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center p-2 bg-[#21262d] rounded">
                <div className={`text-xl font-bold ${T.text}`}>{statistics.total_executions}</div>
                <div className={`text-[10px] ${T.dim}`}>Total</div>
              </div>
              <div className="text-center p-2 bg-[#3fb950]/10 rounded">
                <div className="text-xl font-bold text-[#3fb950]">{statistics.completed}</div>
                <div className="text-[10px] text-[#3fb950]">Completed</div>
              </div>
              <div className="text-center p-2 bg-[#f85149]/10 rounded">
                <div className="text-xl font-bold text-[#f85149]">{statistics.failed}</div>
                <div className="text-[10px] text-[#f85149]">Failed</div>
              </div>
              <div className="text-center p-2 bg-[#58a6ff]/10 rounded">
                <div className="text-xl font-bold text-[#58a6ff]">{statistics.cycles_completed}</div>
                <div className="text-[10px] text-[#58a6ff]">Cycles</div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className={`${T.card} rounded-lg border ${T.border} p-4`}>
        <h3 className={`text-sm font-semibold ${T.text} mb-3 flex items-center gap-2`}>
          <Table className="w-4 h-4 text-[#58a6ff]" />
          Tables
        </h3>
        <div className="space-y-3">
          {overview.tables.map((table) => (
            <div key={table.name} className={`border ${T.border} rounded p-3`}>
              <div className="flex items-center justify-between mb-2">
                <span className={`font-mono text-sm ${T.text}`}>{table.name}</span>
                <span className={`text-xs ${T.dim}`}>{table.row_count} rows</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {table.columns.map((col) => (
                  <span
                    key={col.name}
                    className="px-1.5 py-0.5 bg-[#21262d] rounded text-[10px] font-mono text-[#8b949e]"
                    title={col.type}
                  >
                    {col.name}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {statistics && Object.keys(statistics.execution_by_type).length > 0 && (
        <div className={`${T.card} rounded-lg border ${T.border} p-4`}>
          <h3 className={`text-sm font-semibold ${T.text} mb-3`}>By Inference Type</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(statistics.execution_by_type).map(([type, count]) => (
              <span key={type} className={`px-2 py-1 bg-[#21262d] rounded text-xs ${T.text}`}>
                {type}: {count}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
