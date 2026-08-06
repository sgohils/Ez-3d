"use client"

import { type AutoFixState, type AutoFixLog } from "./types"
import { Wrench, AlertCircle, CheckCircle2, Loader2, XCircle } from "lucide-react"

interface AutoFixIndicatorProps {
  state: AutoFixState
}

const levelIcons = {
  info: "text-blue-400",
  warning: "text-yellow-400",
  error: "text-red-400",
  debug: "text-gray-400",
} as const

const levelColors = {
  info: "bg-blue-100 text-blue-800",
  warning: "bg-yellow-100 text-yellow-800",
  error: "bg-red-100 text-red-800",
  debug: "bg-gray-100 text-gray-600",
} as const

export function AutoFixIndicator({ state }: AutoFixIndicatorProps) {
  const statusIcon = {
    idle: <Wrench className="w-4 h-4 text-gray-400" />,
    running: <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />,
    complete: <CheckCircle2 className="w-4 h-4 text-green-500" />,
    error: <XCircle className="w-4 h-4 text-red-500" />,
  }[state.status]

  const statusLabel = {
    idle: "Idle",
    running: "Auto-fixing...",
    complete: "Fix applied",
    error: "Fix failed",
  }[state.status]

  return (
    <div className="border-t border-gray-200 bg-white">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
          {statusIcon}
          <span>Auto-Fix</span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${
              state.status === "running"
                ? "bg-blue-100 text-blue-700"
                : state.status === "complete"
                  ? "bg-green-100 text-green-700"
                  : state.status === "error"
                    ? "bg-red-100 text-red-700"
                    : "bg-gray-100 text-gray-600"
            }`}
          >
            {statusLabel}
          </span>
        </div>
        {state.totalIterations > 0 && (
          <span className="text-xs text-gray-400">
            {state.currentIteration}/{state.totalIterations}
          </span>
        )}
      </div>

      {state.lastError && (
        <div className="px-4 py-2 bg-red-50 border-b border-red-100 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <span className="text-xs text-red-700">{state.lastError}</span>
        </div>
      )}

      {state.logs.length > 0 && (
        <div className="max-h-40 overflow-y-auto px-4 py-2 space-y-1">
          {state.logs.map((log) => (
            <div key={log.id} className="flex items-start gap-2 text-xs">
              <span className={`shrink-0 mt-0.5 ${levelIcons[log.level]}`}>
                {log.level === "error" ? (
                  <AlertCircle className="w-3 h-3" />
                ) : log.level === "warning" ? (
                  <AlertCircle className="w-3 h-3" />
                ) : (
                  <CheckCircle2 className="w-3 h-3" />
                )}
              </span>
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium uppercase ${levelColors[log.level]}`}>
                {log.level}
              </span>
              <span className="text-gray-600 font-mono">{log.message}</span>
              <span className="text-gray-400 ml-auto shrink-0">
                {log.timestamp.toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      )}

      {state.status === "idle" && state.logs.length === 0 && (
        <div className="px-4 py-3 text-xs text-gray-400 text-center">
          No diagnostic activity
        </div>
      )}
    </div>
  )
}