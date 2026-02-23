/**
 * StepLogViewer — lightweight log viewer for a single execution step.
 *
 * Reuses parsing and rendering components from the shared execution-log
 * package via the @execution-log alias.
 */

import { useMemo, useState } from 'react';
import { X, Eye, EyeOff, Zap, AlertTriangle, XCircle } from 'lucide-react';
import { parseAllEntries, buildCycles, computeStats } from '@execution-log/parsing';
import { LogEntryRow } from '@execution-log/LogEntryRow';
import { StepBlock } from '@execution-log/StepBlock';
import { LOG_LEVEL_BG } from '@execution-log/constants';
import { formatDuration, getSequenceColor } from '@execution-log/utils';
import type { LogLevel } from '@execution-log/types';
import { T } from './utils';

interface StepLogViewerProps {
  logText: string;
  onClose?: () => void;
}

export function StepLogViewer({ logText, onClose }: StepLogViewerProps) {
  const entries = useMemo(() => parseAllEntries(logText), [logText]);
  const cycles = useMemo(() => buildCycles(entries), [entries]);
  const stats = useMemo(() => computeStats(entries, cycles), [entries, cycles]);

  const cycle = cycles[0] ?? null;
  const seq = cycle?.sequenceExecution ?? null;
  const hasStructure = seq !== null && seq.steps.length > 0;

  const [levelFilters, setLevelFilters] = useState<Set<LogLevel>>(
    new Set(['INFO', 'WARNING', 'ERROR', 'CRITICAL']),
  );
  const [showRaw, setShowRaw] = useState(!hasStructure);

  const filteredEntries = useMemo(
    () => entries.filter((e) => levelFilters.has(e.level)),
    [entries, levelFilters],
  );

  const toggleLevel = (level: LogLevel) => {
    setLevelFilters((prev) => {
      const next = new Set(prev);
      if (next.has(level)) next.delete(level);
      else next.add(level);
      return next;
    });
  };

  if (!entries.length) {
    return (
      <div className={`flex flex-col h-full ${T.card}`}>
        <div className="flex-1 flex items-center justify-center">
          <pre className={`text-[11px] font-mono ${T.dim} whitespace-pre-wrap break-words p-3 max-h-full overflow-auto w-full`}>
            {logText || '(No logs available)'}
          </pre>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full ${T.card}`}>
      {/* Compact header bar */}
      <div className={`flex items-center gap-2 px-3 py-1.5 border-b ${T.border} bg-[#21262d] text-xs flex-shrink-0 flex-wrap`}>
        <span className={`${T.dim} font-medium`}>{stats.totalEntries} entries</span>

        {stats.timeSpanMs > 0 && (
          <span className={T.dim}>{formatDuration(stats.timeSpanMs)}</span>
        )}

        {seq && (
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded border flex-shrink-0 ${getSequenceColor(seq.sequenceType)}`}
          >
            {seq.sequenceType}
          </span>
        )}

        {stats.levels.ERROR > 0 && (
          <span className="flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-red-400/10 text-[#f85149] font-medium">
            <XCircle className="w-3 h-3" />
            {stats.levels.ERROR}
          </span>
        )}
        {stats.levels.WARNING > 0 && (
          <span className="flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-yellow-400/10 text-[#d29922] font-medium">
            <AlertTriangle className="w-3 h-3" />
            {stats.levels.WARNING}
          </span>
        )}

        <div className="flex-1" />

        {(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] as LogLevel[]).map((level) => (
          <button
            key={level}
            onClick={() => toggleLevel(level)}
            className={`px-1 py-0.5 text-[10px] rounded font-medium transition-colors ${
              levelFilters.has(level) ? LOG_LEVEL_BG[level] : 'bg-[#21262d] text-[#484f58] line-through'
            }`}
          >
            {level.slice(0, 4)}
          </button>
        ))}

        {onClose && (
          <button onClick={onClose} className={`ml-1 ${T.dim} hover:text-[#c9d1d9]`}>
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {hasStructure && (
          <div className="px-3 py-2">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-3 h-3 text-[#a371f7]" />
              <span className={`text-[10px] uppercase tracking-wider ${T.dim} font-semibold`}>
                {seq!.sequenceType} Sequence
              </span>
              <span className={`text-xs ${T.dim}`}>{seq!.steps.length} steps</span>
              {seq!.endTime - seq!.startTime > 0 && (
                <span className={`text-xs ${T.dim} ml-auto`}>
                  {formatDuration(seq!.endTime - seq!.startTime)}
                </span>
              )}
            </div>
            <div className="space-y-0.5">
              {seq!.steps.map((step, i) => (
                <StepBlock key={i} step={step} />
              ))}
            </div>
          </div>
        )}

        <div className={hasStructure ? `border-t ${T.border}` : ''}>
          <button
            onClick={() => setShowRaw(!showRaw)}
            className={`flex items-center gap-1 px-3 py-1.5 text-xs ${T.dim} hover:text-[#c9d1d9] w-full bg-[#21262d] hover:bg-[#30363d] transition-colors`}
          >
            {showRaw ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
            {showRaw ? 'Hide' : 'Show'} {hasStructure ? 'all ' : ''}
            {filteredEntries.length} entries
          </button>
          {showRaw && (
            <div className={`max-h-60 overflow-y-auto border-t ${T.border}`}>
              {filteredEntries.length === 0 ? (
                <div className={`text-xs ${T.dim} text-center py-4`}>
                  No entries match current level filters
                </div>
              ) : (
                filteredEntries.map((e, i) => (
                  <LogEntryRow key={i} entry={e} showSource={true} highlight="" />
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
