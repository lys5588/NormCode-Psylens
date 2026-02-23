import { useState, useEffect, useCallback } from 'react';
import { Loader2, Database } from 'lucide-react';
import { inspectorApi } from './api';
import { T } from './utils';
import type {
  ViewMode,
  DatabaseOverview,
  RunStatistics,
  ExecutionRecord,
  CheckpointInfo,
  CheckpointStateResponse,
  BlackboardSummary,
} from './types';
import { Sidebar } from './Sidebar';
import { OverviewView } from './OverviewView';
import { ExecutionsView } from './ExecutionsView';
import { CheckpointView } from './CheckpointView';
import { BlackboardView } from './BlackboardView';
import { ConceptsView } from './ConceptsView';

interface RunInspectorProps {
  runId: string;
}

export function RunInspector({ runId }: RunInspectorProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('overview');

  const [overview, setOverview] = useState<DatabaseOverview | null>(null);
  const [statistics, setStatistics] = useState<RunStatistics | null>(null);
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [checkpoints, setCheckpoints] = useState<CheckpointInfo[]>([]);
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<number | null>(null);

  const [checkpointState, setCheckpointState] = useState<CheckpointStateResponse | null>(null);
  const [blackboard, setBlackboard] = useState<BlackboardSummary | null>(null);
  const [concepts, setConcepts] = useState<Record<string, unknown> | null>(null);

  const loadInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [overviewData, statsData, cpData] = await Promise.all([
        inspectorApi.getOverview(runId),
        inspectorApi.getStatistics(runId),
        inspectorApi.getCheckpoints(runId),
      ]);
      setOverview(overviewData);
      setStatistics(statsData);
      setCheckpoints(cpData.checkpoints);

      if (cpData.checkpoints.length > 0) {
        setSelectedCheckpoint(cpData.checkpoints[cpData.checkpoints.length - 1].cycle);
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to load run data';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  useEffect(() => {
    const loadViewData = async () => {
      setLoading(true);
      try {
        switch (viewMode) {
          case 'executions': {
            const data = await inspectorApi.getExecutions(runId, { includeLogs: false, limit: 200 });
            setExecutions(data.executions);
            break;
          }
          case 'checkpoints': {
            if (selectedCheckpoint !== null) {
              const cpState = await inspectorApi.getCheckpointState(runId, selectedCheckpoint);
              setCheckpointState(cpState);
            }
            break;
          }
          case 'blackboard': {
            const bb = await inspectorApi.getBlackboard(runId, selectedCheckpoint ?? undefined);
            setBlackboard(bb);
            break;
          }
          case 'concepts': {
            const data = await inspectorApi.getConcepts(runId, selectedCheckpoint ?? undefined);
            setConcepts(data.concepts);
            break;
          }
        }
      } catch (e) {
        console.error('Failed to load view data:', e);
      } finally {
        setLoading(false);
      }
    };

    if (overview) {
      loadViewData();
    }
  }, [viewMode, selectedCheckpoint, runId, overview]);

  if (error && !overview) {
    return (
      <div className={`flex flex-col items-center justify-center h-full ${T.dim} p-8`}>
        <Database className="w-12 h-12 mb-2 opacity-30" />
        <p className={`text-sm ${T.red}`}>{error}</p>
      </div>
    );
  }

  return (
    <div className={`flex h-full ${T.bg}`}>
      <div className={`w-48 flex-shrink-0 border-r ${T.border} ${T.card} overflow-y-auto`}>
        <Sidebar
          viewMode={viewMode}
          setViewMode={setViewMode}
          checkpoints={checkpoints}
          selectedCheckpoint={selectedCheckpoint}
          setSelectedCheckpoint={setSelectedCheckpoint}
          runId={runId}
        />
      </div>

      <div className="flex-1 overflow-auto p-4">
        {loading && (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-8 h-8 text-[#58a6ff] animate-spin" />
          </div>
        )}

        {!loading && viewMode === 'overview' && overview && (
          <OverviewView overview={overview} statistics={statistics} />
        )}

        {!loading && viewMode === 'executions' && (
          <ExecutionsView
            executions={executions}
            statistics={statistics}
            runId={runId}
          />
        )}

        {!loading && viewMode === 'checkpoints' && checkpointState && (
          <CheckpointView checkpointState={checkpointState} />
        )}

        {!loading && viewMode === 'blackboard' && blackboard && (
          <BlackboardView blackboard={blackboard} />
        )}

        {!loading && viewMode === 'concepts' && concepts && (
          <ConceptsView concepts={concepts} />
        )}
      </div>
    </div>
  );
}
