"use client"

import { useState, useEffect, useCallback } from "react"
import { SlidersHorizontal, RefreshCw } from "lucide-react"
import { useApp } from "@/contexts/AppContext"
import type { CodeVariable } from "@/components/editor/LiveSync"

export function ParametricPanel() {
  const { variables, parameters, recompile, isRecompiling } = useApp()
  const [localParams, setLocalParams] = useState<Record<string, number>>({})

  useEffect(() => {
    const params: Record<string, number> = {}
    for (const v of variables) {
      params[v.name] = parameters[v.name] ?? v.value
    }
    setLocalParams(params)
  }, [variables, parameters])

  const handleSliderChange = useCallback((name: string, value: number) => {
    setLocalParams((prev) => ({ ...prev, [name]: value }))
  }, [])

  const handleSliderCommit = useCallback(
    (name: string, value: number) => {
      setLocalParams((prev) => ({ ...prev, [name]: value }))
      recompile({ ...localParams, [name]: value })
    },
    [localParams, recompile],
  )

  if (variables.length === 0) {
    return (
      <div className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <SlidersHorizontal className="w-4 h-4 text-gray-400" />
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Parameters
          </h3>
        </div>
        <div className="text-center py-8">
          <SlidersHorizontal className="w-8 h-8 mx-auto mb-2 text-gray-300" />
          <p className="text-xs text-gray-400">No parameters available</p>
          <p className="text-xs text-gray-300 mt-1">
            Generate a model to see parametric controls
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-gray-400" />
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Parameters
          </h3>
        </div>
        {isRecompiling && (
          <RefreshCw className="w-3.5 h-3.5 text-blue-400 animate-spin" />
        )}
      </div>
      <div className="space-y-4">
        {variables.map((variable) => {
          const currentValue = localParams[variable.name] ?? variable.value
          return (
            <div key={variable.name} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs text-gray-300 font-mono">
                  {variable.name}
                </label>
                <span className="text-xs text-gray-400 font-mono w-16 text-right">
                  {currentValue.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min={variable.min}
                max={variable.max}
                step={variable.step}
                value={currentValue}
                onChange={(e) => handleSliderChange(variable.name, parseFloat(e.target.value))}
                onMouseUp={() => handleSliderCommit(variable.name, currentValue)}
                onTouchEnd={() => handleSliderCommit(variable.name, currentValue)}
                disabled={isRecompiling}
                className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <div className="flex justify-between text-[10px] text-gray-600 font-mono">
                <span>{variable.min}</span>
                <span>{variable.max}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
