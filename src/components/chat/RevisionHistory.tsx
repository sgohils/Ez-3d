"use client"

import { type Revision } from "./types"
import { RotateCcw, Trash2, Clock } from "lucide-react"

interface RevisionHistoryProps {
  revisions: Revision[]
  onSelectRevision: (revision: Revision) => void
  onClear: () => void
}

export function RevisionHistory({
  revisions,
  onSelectRevision,
  onClear,
}: RevisionHistoryProps) {
  if (revisions.length === 0) {
    return (
      <div className="border-t border-gray-800 p-4">
        <div className="flex items-center gap-2 text-gray-500 text-sm">
          <Clock className="w-4 h-4" />
          <span>No revision history yet</span>
        </div>
      </div>
    )
  }

  return (
    <div className="border-t border-gray-800 bg-gray-900">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <RotateCcw className="w-4 h-4" />
          Revision History
        </div>
        <button
          onClick={onClear}
          className="text-xs text-gray-400 hover:text-red-400 transition-colors flex items-center gap-1"
          aria-label="Clear revision history"
        >
          <Trash2 className="w-3 h-3" />
          Clear
        </button>
      </div>
      <div className="max-h-60 overflow-y-auto">
        {revisions.map((revision, index) => (
          <button
            key={revision.id}
            onClick={() => onSelectRevision(revision)}
            className="w-full text-left px-4 py-3 hover:bg-gray-800 border-b border-gray-800 last:border-b-0 transition-colors"
          >
            <div className="flex items-start gap-3">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-800 text-xs font-medium text-gray-400 shrink-0 mt-0.5">
                {index + 1}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-100 truncate">{revision.prompt}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs font-mono text-blue-400 bg-blue-900/40 px-1.5 py-0.5 rounded">
                    {revision.modelName}
                  </span>
                  <span className="text-xs text-gray-500">
                    {revision.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
