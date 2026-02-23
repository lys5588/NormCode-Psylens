import { useState } from 'react';
import { ChevronDown, ChevronRight, Layers, Search } from 'lucide-react';
import { T } from './utils';

interface ConceptsViewProps {
  concepts: Record<string, unknown>;
}

export function ConceptsView({ concepts }: ConceptsViewProps) {
  const [search, setSearch] = useState('');
  const [expandedConcept, setExpandedConcept] = useState<string | null>(null);

  const filteredConcepts = Object.entries(concepts).filter(([name]) =>
    name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-4">
      <div className={`${T.card} rounded-lg border ${T.border} p-4`}>
        <div className="flex items-center gap-2 mb-4">
          <h3 className={`text-sm font-semibold ${T.text} flex items-center gap-2`}>
            <Layers className="w-4 h-4 text-[#58a6ff]" />
            Completed Concepts ({Object.keys(concepts).length})
          </h3>
          <div className="flex-1" />
          <div className="relative">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search concepts..."
              className={`pl-8 pr-3 py-1 text-xs border ${T.border} rounded bg-[#0d1117] ${T.text} focus:ring-1 focus:ring-[#58a6ff]`}
            />
            <Search className={`absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 ${T.dim}`} />
          </div>
        </div>

        <div className="space-y-2 max-h-[500px] overflow-auto">
          {filteredConcepts.map(([name, data]) => (
            <div key={name} className={`border ${T.border} rounded`}>
              <button
                onClick={() => setExpandedConcept(expandedConcept === name ? null : name)}
                className={`w-full flex items-center gap-2 px-3 py-2 text-xs font-mono ${T.text} hover:bg-[#21262d]`}
              >
                {expandedConcept === name ? (
                  <ChevronDown className="w-3 h-3 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-3 h-3 flex-shrink-0" />
                )}
                <span className="truncate">{name}</span>
                {typeof data === 'object' && data !== null && 'shape' in data && (
                  <span className={`${T.dim} ml-auto flex-shrink-0`}>
                    shape: [{(data as { shape?: number[] }).shape?.join(', ')}]
                  </span>
                )}
              </button>
              {expandedConcept === name && (
                <div className="px-3 pb-3">
                  <pre className={`text-[10px] bg-[#0d1117] p-2 rounded overflow-auto max-h-48 font-mono ${T.text}`}>
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
          {filteredConcepts.length === 0 && (
            <div className={`text-center py-8 ${T.dim} text-xs`}>
              {search ? 'No concepts match your search' : 'No concepts found'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
