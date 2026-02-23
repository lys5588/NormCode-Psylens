import type {
  DatabaseOverview,
  ExecutionsResponse,
  ExecutionLogsResponse,
  RunStatistics,
  CheckpointsResponse,
  CheckpointStateResponse,
  BlackboardSummary,
  ConceptsResponse,
} from './types';

const API = window.location.origin + '/api';

async function fetchJson<T>(url: string): Promise<T> {
  const resp = await fetch(url);
  if (!resp.ok) {
    const text = await resp.text().catch(() => resp.statusText);
    throw new Error(`${resp.status}: ${text}`);
  }
  return resp.json();
}

export const inspectorApi = {
  getOverview: (runId: string) =>
    fetchJson<DatabaseOverview>(`${API}/runs/${runId}/db/overview`),

  getExecutions: (runId: string, opts?: { includeLogs?: boolean; limit?: number }) =>
    fetchJson<ExecutionsResponse>(
      `${API}/runs/${runId}/db/executions?include_logs=${opts?.includeLogs ?? false}&limit=${opts?.limit ?? 200}`,
    ),

  getExecutionLogs: (runId: string, executionId: number) =>
    fetchJson<ExecutionLogsResponse>(
      `${API}/runs/${runId}/db/executions/${executionId}/logs`,
    ),

  getStatistics: (runId: string) =>
    fetchJson<RunStatistics>(`${API}/runs/${runId}/db/statistics`),

  getCheckpoints: (runId: string) =>
    fetchJson<CheckpointsResponse>(`${API}/runs/${runId}/db/checkpoints`),

  getCheckpointState: (runId: string, cycle: number) =>
    fetchJson<CheckpointStateResponse>(
      `${API}/runs/${runId}/db/checkpoints/${cycle}`,
    ),

  getBlackboard: (runId: string, cycle?: number) =>
    fetchJson<BlackboardSummary>(
      `${API}/runs/${runId}/db/blackboard${cycle != null ? `?cycle=${cycle}` : ''}`,
    ),

  getConcepts: (runId: string, cycle?: number) =>
    fetchJson<ConceptsResponse>(
      `${API}/runs/${runId}/db/concepts${cycle != null ? `?cycle=${cycle}` : ''}`,
    ),
};
