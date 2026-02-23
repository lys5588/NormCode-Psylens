import React from 'react';
import {
  Database,
  FileText,
  Clock,
  Box,
  Layers,
} from 'lucide-react';
import { T } from './utils';
import type { ViewMode, CheckpointInfo } from './types';

interface SidebarProps {
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;
  checkpoints: CheckpointInfo[];
  selectedCheckpoint: number | null;
  setSelectedCheckpoint: (cycle: number | null) => void;
  runId: string;
}

export function Sidebar({
  viewMode,
  setViewMode,
  checkpoints,
  selectedCheckpoint,
  setSelectedCheckpoint,
  runId,
}: SidebarProps) {
  return (
    <>
      <div className={`px-3 py-2 border-b ${T.border}`}>
        <div className={`text-[10px] uppercase tracking-wider ${T.dim} font-semibold mb-1`}>Run</div>
        <div className={`font-mono text-xs ${T.text} truncate`} title={runId}>
          {runId.slice(0, 16)}...
        </div>
      </div>

      <div className="p-2 space-y-0.5">
        <NavButton icon={Database} label="Overview" mode="overview" current={viewMode} onClick={setViewMode} />
        <NavButton icon={FileText} label="Executions" mode="executions" current={viewMode} onClick={setViewMode} />
        <NavButton icon={Clock} label="Checkpoints" mode="checkpoints" current={viewMode} onClick={setViewMode} />
        <NavButton icon={Box} label="Blackboard" mode="blackboard" current={viewMode} onClick={setViewMode} />
        <NavButton icon={Layers} label="Concepts" mode="concepts" current={viewMode} onClick={setViewMode} />
      </div>

      {checkpoints.length > 0 && (
        <div className={`p-3 border-t ${T.border}`}>
          <label className={`text-xs font-medium ${T.dim} mb-1 block`}>Checkpoint</label>
          <select
            value={selectedCheckpoint ?? ''}
            onChange={(e) =>
              setSelectedCheckpoint(e.target.value ? Number(e.target.value) : null)
            }
            className={`w-full text-xs ${T.border} border rounded px-2 py-1 ${T.text} bg-[#0d1117] focus:ring-1 focus:ring-[#58a6ff]`}
          >
            {checkpoints.map((cp) => (
              <option key={`${cp.cycle}-${cp.inference_count}`} value={cp.cycle}>
                Cycle {cp.cycle} ({cp.inference_count} infs)
              </option>
            ))}
          </select>
        </div>
      )}
    </>
  );
}

function NavButton({
  icon: Icon,
  label,
  mode,
  current,
  onClick,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  mode: ViewMode;
  current: ViewMode;
  onClick: (mode: ViewMode) => void;
}) {
  return (
    <button
      onClick={() => onClick(mode)}
      className={`w-full text-left px-2.5 py-1.5 text-xs rounded flex items-center gap-2 ${
        current === mode
          ? 'bg-[#58a6ff]/15 text-[#58a6ff]'
          : `${T.dim} hover:bg-[#21262d]`
      }`}
    >
      <Icon className="w-3.5 h-3.5" />
      {label}
    </button>
  );
}
