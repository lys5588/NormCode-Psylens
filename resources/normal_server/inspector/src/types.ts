export interface TableInfo {
  name: string;
  columns: { name: string; type: string }[];
  row_count: number;
}

export interface DatabaseOverview {
  run_id: string;
  path: string;
  size_bytes: number;
  tables: TableInfo[];
  total_executions: number;
  total_checkpoints: number;
}

export interface ExecutionRecord {
  id: number;
  run_id: string;
  cycle: number;
  flow_index: string;
  inference_type: string | null;
  status: string;
  concept_inferred: string | null;
  timestamp: string | null;
  log_content?: string | null;
}

export interface ExecutionsResponse {
  run_id: string;
  executions: ExecutionRecord[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface ExecutionLogsResponse {
  run_id: string;
  execution_id: number;
  log_content: string;
}

export interface RunStatistics {
  run_id: string;
  total_executions: number;
  completed: number;
  failed: number;
  in_progress: number;
  cycles_completed: number;
  unique_concepts_inferred: number;
  execution_by_type: Record<string, number>;
}

export interface CheckpointInfo {
  cycle: number;
  inference_count: number;
  timestamp: string | null;
  state_size: number;
}

export interface CheckpointsResponse {
  run_id: string;
  checkpoints: CheckpointInfo[];
  total_count: number;
}

export interface CheckpointStateResponse {
  run_id: string;
  cycle: number;
  inference_count: number;
  timestamp: string | null;
  blackboard: unknown;
  workspace: unknown;
  tracker: unknown;
  completed_concepts: unknown;
  signatures: unknown;
}

export interface BlackboardSummary {
  run_id: string;
  concept_statuses: Record<string, string>;
  item_statuses: Record<string, string>;
  item_results: Record<string, unknown>;
  concept_count: number;
  item_count: number;
  completed_concepts: number;
  completed_items: number;
}

export interface ConceptsResponse {
  run_id: string;
  concepts: Record<string, unknown>;
  count: number;
}

export type ViewMode = 'overview' | 'executions' | 'checkpoints' | 'blackboard' | 'concepts';
