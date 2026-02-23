import { useState } from 'react';
import { ChevronDown, ChevronRight, Clock } from 'lucide-react';
import { T } from './utils';
import type { CheckpointStateResponse } from './types';

interface CheckpointViewProps {
  checkpointState: CheckpointStateResponse;
}

export function CheckpointView({ checkpointState }: CheckpointViewProps) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  const toggleKey = (key: string) => {
    const newExpanded = new Set(expandedKeys);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedKeys(newExpanded);
  };

  const sections = ['blackboard', 'workspace', 'tracker', 'completed_concepts', 'signatures'] as const;

  return (
    <div className="space-y-4">
      <div className={`${T.card} rounded-lg border ${T.border} p-4`}>
        <h3 className={`text-sm font-semibold ${T.text} mb-3 flex items-center gap-2`}>
          <Clock className="w-4 h-4 text-[#58a6ff]" />
          Checkpoint: Cycle {checkpointState.cycle}, Inference {checkpointState.inference_count}
        </h3>
        <div className={`text-xs ${T.dim} mb-4`}>
          Timestamp: {checkpointState.timestamp ?? '—'}
        </div>

        <div className="space-y-3">
          {sections.map((key) => {
            const data = checkpointState[key];
            if (!data) return null;

            return (
              <div key={key} className={`border ${T.border} rounded`}>
                <button
                  onClick={() => toggleKey(key)}
                  className={`w-full flex items-center gap-2 px-3 py-2 text-xs font-medium ${T.text} hover:bg-[#21262d]`}
                >
                  {expandedKeys.has(key) ? (
                    <ChevronDown className="w-3 h-3" />
                  ) : (
                    <ChevronRight className="w-3 h-3" />
                  )}
                  {key}
                  <span className={`${T.dim} ml-auto`}>
                    {typeof data === 'object' ? Object.keys(data as object).length + ' keys' : ''}
                  </span>
                </button>
                {expandedKeys.has(key) && (
                  <div className="px-3 pb-3">
                    <pre className={`text-[10px] bg-[#0d1117] p-2 rounded overflow-auto max-h-64 font-mono ${T.text}`}>
                      {JSON.stringify(data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
