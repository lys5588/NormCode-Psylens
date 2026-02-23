import React from 'react';
import { CheckCircle2, XCircle, Play, Clock } from 'lucide-react';

const DB_LOG_LINE =
  /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - \[run_id:[^\]]+\] \[exec_id:\d+\] - ([\w._]+) - (\w+) - (.*)$/;

export function normalizeDbLogs(raw: string): string {
  if (!raw) return raw;
  return raw
    .split('\n')
    .map((line) => {
      const m = line.match(DB_LOG_LINE);
      if (m) {
        const [, timestamp, source, level, message] = m;
        return `${timestamp} | ${level} | ${source} | ${message}`;
      }
      return line;
    })
    .join('\n');
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(isoString: string | null): string {
  if (!isoString) return '—';
  const date = new Date(isoString);
  return date.toLocaleString();
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
    case 'complete':
      return 'text-green-400 bg-green-400/10';
    case 'failed':
      return 'text-red-400 bg-red-400/10';
    case 'in_progress':
    case 'pending':
      return 'text-yellow-400 bg-yellow-400/10';
    default:
      return 'text-gray-400 bg-gray-400/10';
  }
}

export function getStatusIcon(status: string): React.ReactNode {
  switch (status) {
    case 'completed':
    case 'complete':
      return <CheckCircle2 className="w-3 h-3" />;
    case 'failed':
      return <XCircle className="w-3 h-3" />;
    case 'in_progress':
      return <Play className="w-3 h-3" />;
    default:
      return <Clock className="w-3 h-3" />;
  }
}

/** Shared dark theme class tokens (matching server.css vars) */
export const T = {
  bg: 'bg-[#0d1117]',
  card: 'bg-[#161b22]',
  cardHover: 'hover:bg-[#21262d]',
  border: 'border-[#30363d]',
  text: 'text-[#c9d1d9]',
  dim: 'text-[#8b949e]',
  accent: 'text-[#58a6ff]',
  green: 'text-[#3fb950]',
  red: 'text-[#f85149]',
  yellow: 'text-[#d29922]',
  purple: 'text-[#a371f7]',
} as const;
