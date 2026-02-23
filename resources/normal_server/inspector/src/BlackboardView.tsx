import { getStatusColor, getStatusIcon, T } from './utils';
import type { BlackboardSummary } from './types';

interface BlackboardViewProps {
  blackboard: BlackboardSummary;
}

export function BlackboardView({ blackboard }: BlackboardViewProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-4">
        <div className={`${T.card} rounded-lg border ${T.border} p-4 text-center`}>
          <div className={`text-2xl font-bold ${T.text}`}>{blackboard.concept_count}</div>
          <div className={`text-xs ${T.dim}`}>Concepts</div>
        </div>
        <div className={`${T.card} rounded-lg border ${T.border} p-4 text-center`}>
          <div className="text-2xl font-bold text-[#3fb950]">{blackboard.completed_concepts}</div>
          <div className="text-xs text-[#3fb950]">Completed</div>
        </div>
        <div className={`${T.card} rounded-lg border ${T.border} p-4 text-center`}>
          <div className={`text-2xl font-bold ${T.text}`}>{blackboard.item_count}</div>
          <div className={`text-xs ${T.dim}`}>Items</div>
        </div>
        <div className={`${T.card} rounded-lg border ${T.border} p-4 text-center`}>
          <div className="text-2xl font-bold text-[#3fb950]">{blackboard.completed_items}</div>
          <div className="text-xs text-[#3fb950]">Completed</div>
        </div>
      </div>

      <div className={`${T.card} rounded-lg border ${T.border}`}>
        <div className={`px-4 py-3 border-b ${T.border}`}>
          <h3 className={`text-sm font-semibold ${T.text}`}>Concept Statuses</h3>
        </div>
        <div className="max-h-64 overflow-auto p-2">
          <div className="flex flex-wrap gap-1">
            {Object.entries(blackboard.concept_statuses).map(([name, status]) => (
              <span
                key={name}
                className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${getStatusColor(status)}`}
                title={name}
              >
                {getStatusIcon(status)}
                <span className="font-mono truncate max-w-[120px]">{name}</span>
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className={`${T.card} rounded-lg border ${T.border}`}>
        <div className={`px-4 py-3 border-b ${T.border}`}>
          <h3 className={`text-sm font-semibold ${T.text}`}>Item Statuses</h3>
        </div>
        <div className="max-h-64 overflow-auto p-2">
          <div className="flex flex-wrap gap-1">
            {Object.entries(blackboard.item_statuses).map(([flowIndex, status]) => (
              <span
                key={flowIndex}
                className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${getStatusColor(status)}`}
              >
                {getStatusIcon(status)}
                <span className="font-mono">{flowIndex}</span>
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
