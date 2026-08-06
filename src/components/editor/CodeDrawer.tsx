"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { X, Code2 } from "lucide-react"
import { MonacoWrapper } from "./MonacoWrapper"
import { extractVariables, updateVariableInCode, type CodeVariable } from "./LiveSync"
import { apiService } from "@/lib/api/client"

interface RecompileResult {
  code: string
  gltfUrl: string
  stlUrl: string
  stepUrl: string
  logs: string
}

interface CodeDrawerProps {
  isOpen: boolean
  onClose: () => void
  code: string
  onCodeChange: (code: string) => void
  onVariablesExtracted?: (variables: CodeVariable[]) => void
  onVariableUpdate?: (name: string, value: number) => void
  onRecompileSuccess?: (result: RecompileResult) => void
  readOnly?: boolean
}

export function CodeDrawer({
  isOpen,
  onClose,
  code,
  onCodeChange,
  onVariablesExtracted,
  onVariableUpdate,
  onRecompileSuccess,
  readOnly = true,
}: CodeDrawerProps) {
  const [internalCode, setInternalCode] = useState(code)
  const [isEditing, setIsEditing] = useState(false)
  const [isRecompiling, setIsRecompiling] = useState(false)
  const [recompileError, setRecompileError] = useState<string | null>(null)
  const debounceRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    setInternalCode(code)
  }, [code])

  useEffect(() => {
    if (isOpen) {
      const variables = extractVariables(code)
      onVariablesExtracted?.(variables)
    }
  }, [isOpen, code, onVariablesExtracted])

  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [])

  const doRecompile = useCallback(
    async (targetCode: string) => {
      const variables = extractVariables(targetCode)
      if (variables.length === 0) return

      const parameters: Record<string, number> = {}
      for (const v of variables) {
        parameters[v.name] = v.value
      }
      const result = await apiService.recompile(parameters)
      setInternalCode(result.code)
      onCodeChange(result.code)
      onRecompileSuccess?.({
        code: result.code,
        gltfUrl: result.gltf_url,
        stlUrl: result.stl_url,
        stepUrl: result.step_url,
        logs: result.logs,
      })
      return result
    },
    [onCodeChange, onRecompileSuccess],
  )

  const handleEditorChange = useCallback(
    (value: string | undefined) => {
      const newCode = value ?? ""
      setInternalCode(newCode)
      onCodeChange(newCode)

      if (!isEditing) {
        setIsEditing(true)
      }

      const variables = extractVariables(newCode)
      onVariablesExtracted?.(variables)
    },
    [onCodeChange, onVariablesExtracted, isEditing],
  )

  const handleSliderChange = useCallback(
    (name: string, value: number) => {
      const updatedCode = updateVariableInCode(internalCode, name, value)
      setInternalCode(updatedCode)
      onCodeChange(updatedCode)
      onVariableUpdate?.(name, value)

      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
      debounceRef.current = setTimeout(async () => {
        setIsRecompiling(true)
        setRecompileError(null)
        try {
          await doRecompile(updatedCode)
        } catch (err) {
          setRecompileError(err instanceof Error ? err.message : "Recompile failed")
        } finally {
          setIsRecompiling(false)
        }
      }, 500)
    },
    [internalCode, onCodeChange, onVariableUpdate, doRecompile],
  )

  const handleRecompile = useCallback(async () => {
    setIsRecompiling(true)
    setRecompileError(null)
    try {
      await doRecompile(internalCode)
    } catch (err) {
      setRecompileError(err instanceof Error ? err.message : "Recompile failed")
    } finally {
      setIsRecompiling(false)
    }
  }, [internalCode, doRecompile])

  if (!isOpen) return null

  return (
    <>
      <div
        className="fixed inset-0 bg-black/50 z-40 transition-opacity"
        onClick={onClose}
      />
      <div className="fixed top-0 right-0 h-full w-[520px] bg-gray-900 border-l border-gray-700 z-50 flex flex-col shadow-2xl transition-transform duration-300 ease-in-out">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <Code2 className="w-5 h-5 text-blue-400" />
            <h2 className="text-sm font-semibold text-gray-100">Code Editor</h2>
            {isEditing && (
              <span className="text-xs text-yellow-400 ml-2">unsaved</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {!readOnly && (
              <button
                onClick={handleRecompile}
                disabled={isRecompiling}
                className="px-3 py-1 text-xs font-medium bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white rounded transition-colors"
              >
                {isRecompiling ? "Recompiling..." : "Recompile"}
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-gray-700 rounded transition-colors"
              aria-label="Close drawer"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {recompileError && (
          <div className="px-4 py-2 bg-red-900/50 border-b border-red-700 text-xs text-red-300">
            {recompileError}
          </div>
        )}

        <div className="flex-1 overflow-hidden">
          <MonacoWrapper
            value={internalCode}
            onChange={handleEditorChange}
            language="python"
            readOnly={readOnly}
            height="100%"
          />
        </div>

        <LiveSyncPanel
          code={internalCode}
          onSliderChange={handleSliderChange}
        />
      </div>
    </>
  )
}

interface LiveSyncPanelProps {
  code: string
  onSliderChange: (name: string, value: number) => void
}

function LiveSyncPanel({ code, onSliderChange }: LiveSyncPanelProps) {
  const variables = extractVariables(code)

  if (variables.length === 0) {
    return (
      <div className="px-4 py-3 border-t border-gray-700 text-xs text-gray-500">
        No numeric variables detected in code
      </div>
    )
  }

  return (
    <div className="border-t border-gray-700 px-4 py-3">
      <div className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
        Live Variables
      </div>
      <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
        {variables.map((v) => (
          <div key={v.name} className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="text-xs text-gray-300 font-mono">{v.name}</label>
              <span className="text-xs text-gray-400 font-mono w-16 text-right">
                {v.value.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min={v.min}
              max={v.max}
              step={v.step}
              value={v.value}
              onChange={(e) => onSliderChange(v.name, parseFloat(e.target.value))}
              className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
            <div className="flex justify-between text-[10px] text-gray-600 font-mono">
              <span>{v.min}</span>
              <span>{v.max}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
