import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  FileText,
  BarChart3,
  Loader2,
} from 'lucide-react';
import { inspectorApi } from './api';
import { StepLogViewer } from './StepLogViewer';
import { formatDate, getStatusColor, getStatusIcon, normalizeDbLogs, T } from './utils';
import type { ExecutionRecord, RunStatistics } from './types';

interface ExecutionsViewProps {
  executions: ExecutionRecord[];
  statistics: RunStatistics | null;
  runId: string;
}

export function ExecutionsView({ executions, statistics, runId }: ExecutionsViewProps) {
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const [logsCache, setLogsCache] = useState<Record<number, string>>({});
  const [loadingLogs, setLoadingLogs] = useState<Set<number>>(new Set());

  const toggleExpand = async (execId: number) => {
    const newExpanded = new Set(expandedIds);

    if (newExpanded.has(execId)) {
      newExpanded.delete(execId);
    } else {
      newExpanded.add(execId);

      if (!logsCache[execId]) {
        setLoadingLogs((prev) => new Set(prev).add(execId));
        try {
          const result = await inspectorApi.getExecutionLogs(runId, execId);
          const normalized = result.log_content
            ? normalizeDbLogs(result.log_content)
            : '(No logs available)';
          setLogsCache((prev) => ({ ...prev, [execId]: normalized }));
        } catch (e) {
          console.error('Failed to load logs:', e);
          setLogsCache((prev) => ({ ...prev, [execId]: '(Failed to load logs)' }));
        } finally {
          setLoadingLogs((prev) => {
            const next = new Set(prev);
            next.delete(execId);
            return next;
          });
        }
      }
    }

    setExpandedIds(newExpanded);
  };

  return (
    <div className="space-y-4">
      {statistics && (
        <div className={`${T.card} rounded-lg border ${T.border} p-4`}>
          <h3 className={`text-sm font-semibold ${T.text} mb-3 flex items-center gap-2`}>
            <BarChart3 className="w-4 h-4 text-[#58a6ff]" />
            Run Statistics
          </h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-3 bg-[#21262d] rounded-lg">
              <div className={`text-2xl font-bold ${T.text}`}>{statistics.total_executions}</div>
              <div className={`text-xs ${T.dim}`}>Total</div>
            </div>
            <div className="text-center p-3 bg-[#3fb950]/10 rounded-lg">
              <div className="text-2xl font-bold text-[#3fb950]">{statistics.completed}</div>
              <div className="text-xs text-[#3fb950]">Completed</div>
            </div>
            <div className="text-center p-3 bg-[#f85149]/10 rounded-lg">
              <div className="text-2xl font-bold text-[#f85149]">{statistics.failed}</div>
              <div className="text-xs text-[#f85149]">Failed</div>
            </div>
            <div className="text-center p-3 bg-[#58a6ff]/10 rounded-lg">
              <div className="text-2xl font-bold text-[#58a6ff]">{statistics.cycles_completed}</div>
              <div className="text-xs text-[#58a6ff]">Cycles</div>
            </div>
          </div>
        </div>
      )}

      <div className={`${T.card} rounded-lg border ${T.border}`}>
        <div className={`px-4 py-3 border-b ${T.border}`}>
          <h3 className={`text-sm font-semibold ${T.text} flex items-center gap-2`}>
            <FileText className="w-4 h-4 text-[#58a6ff]" />
            Execution History ({executions.length})
          </h3>
          <p className={`text-xs ${T.dim} mt-1`}>Click a row to view structured logs</p>
        </div>
        <div className="max-h-[500px] overflow-auto">
          <table className="w-full text-xs">
            <thead className="bg-[#21262d] sticky top-0 z-10">
              <tr>
                <th className={`px-2 py-2 text-left ${T.dim} font-medium w-6`}></th>
                <th className={`px-3 py-2 text-left ${T.dim} font-medium`}>ID</th>
                <th className={`px-3 py-2 text-left ${T.dim} font-medium`}>Cycle</th>
                <th className={`px-3 py-2 text-left ${T.dim} font-medium`}>Flow</th>
                <th className={`px-3 py-2 text-left ${T.dim} font-medium`}>Type</th>
                <th className={`px-3 py-2 text-left ${T.dim} font-medium`}>Concept</th>
                <th className={`px-3 py-2 text-left ${T.dim} font-medium`}>Status</th>
                <th className={`px-3 py-2 text-left ${T.dim} font-medium`}>Time</th>
              </tr>
            </thead>
            <tbody className={`divide-y divide-[#30363d]`}>
              {executions.map((exec) => {
                const isExpanded = expandedIds.has(exec.id);
                const isLoading = loadingLogs.has(exec.id);
                const logContent = logsCache[exec.id];

                return (
                  <React.Fragment key={exec.id}>
                    <tr
                      className="hover:bg-[#21262d] cursor-pointer transition-colors"
                      onClick={() => toggleExpand(exec.id)}
                    >
                      <td className={`px-2 py-2 ${T.dim}`}>
                        {isExpanded ? (
                          <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5" />
                        )}
                      </td>
                      <td className={`px-3 py-2 font-mono ${T.dim}`}>{exec.id}</td>
                      <td className={`px-3 py-2 ${T.text}`}>{exec.cycle}</td>
                      <td className={`px-3 py-2 font-mono ${T.text}`}>{exec.flow_index}</td>
                      <td className={`px-3 py-2 ${T.text}`}>{exec.inference_type || '—'}</td>
                      <td className={`px-3 py-2 font-mono truncate max-w-[150px] ${T.text}`} title={exec.concept_inferred ?? ''}>
                        {exec.concept_inferred || '—'}
                      </td>
                      <td className="px-3 py-2">
                        <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded ${getStatusColor(exec.status)}`}>
                          {getStatusIcon(exec.status)}
                          {exec.status}
                        </span>
                      </td>
                      <td className={`px-3 py-2 ${T.dim}`}>{formatDate(exec.timestamp)}</td>
                    </tr>
                    {isExpanded && (
                      <tr className="bg-[#0d1117]">
                        <td colSpan={8} className="px-4 py-3">
                          {isLoading ? (
                            <div className={`flex items-center justify-center py-4 ${T.dim} text-xs`}>
                              <Loader2 className="w-4 h-4 animate-spin mr-2" />
                              Loading logs...
                            </div>
                          ) : logContent ? (
                            <div className={`rounded-lg border ${T.border} ${T.card} overflow-hidden h-[400px]`}>
                              <StepLogViewer
                                logText={logContent}
                                onClose={() => toggleExpand(exec.id)}
                              />
                            </div>
                          ) : (
                            <div className={`text-xs ${T.dim} italic text-center py-4`}>
                              No logs available
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
              {executions.length === 0 && (
                <tr>
                  <td colSpan={8} className={`px-3 py-8 text-center ${T.dim}`}>
                    No executions found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
