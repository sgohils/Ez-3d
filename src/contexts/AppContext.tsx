"use client"

import { createContext, useContext, useState, useCallback, type ReactNode } from "react"
import { appApi, type GenerateResponse, type RecompileResponse } from "@/lib/api"
import type { Message, Revision, AutoFixState } from "@/components/chat/types"
import type { CodeVariable } from "@/components/editor/LiveSync"

export interface AppState {
  modelUrl: string | null
  code: string
  parameters: Record<string, number>
  variables: CodeVariable[]
  loading: boolean
  isGenerating: boolean
  isRecompiling: boolean
  chatHistory: Message[]
  revisions: Revision[]
  autoFixState: AutoFixState
  errors: string[]
}

export interface AppActions {
  sendPrompt: (prompt: string) => Promise<void>
  recompile: (parameters: Record<string, number>) => Promise<void>
  updateCode: (code: string) => void
  updateVariable: (name: string, value: number) => void
  clearErrors: () => void
  removeError: (index: number) => void
  selectRevision: (revision: Revision) => void
  clearRevisions: () => void
}

export interface AppContextValue extends AppState, AppActions {}

const initialState: AppState = {
  modelUrl: null,
  code: "",
  parameters: {},
  variables: [],
  loading: false,
  isGenerating: false,
  isRecompiling: false,
  chatHistory: [],
  revisions: [],
  autoFixState: {
    status: "idle",
    logs: [],
    currentIteration: 0,
    totalIterations: 0,
    maxRetries: 3,
  },
  errors: [],
}

const AppContext = createContext<AppContextValue | null>(null)

export function useApp() {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error("useApp must be used within an AppProvider")
  }
  return context
}

interface AppProviderProps {
  children: ReactNode
}

export function AppProvider({ children }: AppProviderProps) {
  const [state, setState] = useState<AppState>(initialState)

  const setPartial = useCallback((patch: Partial<AppState>) => {
    setState((prev) => ({ ...prev, ...patch }))
  }, [])

  const addError = useCallback((error: string) => {
    setState((prev) => ({
      ...prev,
      errors: [...prev.errors, error],
    }))
  }, [])

  const removeError = useCallback((index: number) => {
    setState((prev) => ({
      ...prev,
      errors: prev.errors.filter((_, i) => i !== index),
    }))
  }, [])

  const clearErrors = useCallback(() => {
    setState((prev) => ({ ...prev, errors: [] }))
  }, [])

  const sendPrompt = useCallback(async (prompt: string) => {
    const userMessage: Message = {
      id: `msg-${Date.now()}-user`,
      role: "user",
      content: prompt,
      timestamp: new Date(),
    }

    setState((prev) => ({
      ...prev,
      isGenerating: true,
      loading: true,
      chatHistory: [...prev.chatHistory, userMessage],
      errors: [],
    }))

    try {
      const result: GenerateResponse = await appApi.generate(prompt, state.parameters)

      const assistantMessage: Message = {
        id: `msg-${Date.now()}-assistant`,
        role: "assistant",
        content: result.message || `Generated model: ${prompt}`,
        timestamp: new Date(),
        codePreview: result.code.slice(0, 500) + (result.code.length > 500 ? "..." : ""),
      }

      const retryCount = result.retryCount ?? 0
      const maxRetries = result.maxRetries ?? 3
      const errorType = result.errorType
      const repairHints = result.repairHints ?? []

      const autofixLogs: { id: string; timestamp: Date; level: "info" | "warning" | "error" | "debug"; message: string }[] = []
      if (retryCount > 0) {
        autofixLogs.push({
          id: `autofix-${Date.now()}`,
          timestamp: new Date(),
          level: errorType ? "warning" : "info",
          message: `Auto-repair succeeded after ${retryCount} iteration(s)${errorType ? ` (${errorType})` : ""}.`,
        })
        if (repairHints.length > 0) {
          autofixLogs.push({
            id: `autofix-hints-${Date.now()}`,
            timestamp: new Date(),
            level: "info",
            message: `Targeted hints: ${repairHints.join("; ")}`,
          })
        }
      }

      setState((prev) => ({
        ...prev,
        modelUrl: result.gltf_url,
        code: result.code,
        parameters: result.parameters.reduce((acc, p) => ({ ...acc, [p.name]: p.value }), {} as Record<string, number>),
        variables: extractVariablesFromCode(result.code),
        chatHistory: [...prev.chatHistory, assistantMessage],
        revisions: result.revisionId
          ? [
              ...prev.revisions,
              {
                id: result.revisionId,
                prompt,
                modelName: result.gltf_url.split("/").pop() || "model",
                timestamp: new Date(),
                parameters: result.parameters.reduce((acc, p) => ({ ...acc, [p.name]: p.value }), {} as Record<string, number>),
              },
            ]
          : prev.revisions,
        autoFixState: {
          status: retryCount > 0 ? "complete" : "idle",
          logs: autofixLogs,
          currentIteration: retryCount,
          totalIterations: retryCount,
          maxRetries,
          lastError: errorType || undefined,
        },
      }))
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to generate model"
      addError(errorMessage)

      const errorMessageObj: Message = {
        id: `msg-${Date.now()}-error`,
        role: "system",
        content: `Error: ${errorMessage}`,
        timestamp: new Date(),
      }

      setState((prev) => ({
        ...prev,
        chatHistory: [...prev.chatHistory, errorMessageObj],
      }))
    } finally {
      setState((prev) => ({
        ...prev,
        isGenerating: false,
        loading: false,
      }))
    }
  }, [addError, state.parameters])

  const recompile = useCallback(async (parameters: Record<string, number>) => {
    setState((prev) => ({
      ...prev,
      isRecompiling: true,
      errors: [],
    }))

    try {
      const result: RecompileResponse = await appApi.recompile(parameters)

      setState((prev) => ({
        ...prev,
        modelUrl: result.gltf_url,
        code: result.code,
        parameters: result.parameters.reduce((acc, p) => ({ ...acc, [p.name]: p.value }), {} as Record<string, number>),
        variables: extractVariablesFromCode(result.code),
      }))
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to recompile model"
      addError(errorMessage)
    } finally {
      setState((prev) => ({
        ...prev,
        isRecompiling: false,
      }))
    }
  }, [addError])

  const updateCode = useCallback((code: string) => {
    const variables = extractVariablesFromCode(code)
    setState((prev) => ({
      ...prev,
      code,
      variables,
    }))
  }, [])

  const updateVariable = useCallback((name: string, value: number) => {
    setState((prev) => ({
      ...prev,
      parameters: { ...prev.parameters, [name]: value },
      variables: prev.variables.map((v) => (v.name === name ? { ...v, value } : v)),
    }))
  }, [])

  const selectRevision = useCallback((revision: Revision) => {
    setState((prev) => ({
      ...prev,
      parameters: (revision.parameters as Record<string, number>) || prev.parameters,
    }))
  }, [])

  const clearRevisions = useCallback(() => {
    setState((prev) => ({
      ...prev,
      revisions: [],
    }))
  }, [])

  const value: AppContextValue = {
    ...state,
    sendPrompt,
    recompile,
    updateCode,
    updateVariable,
    clearErrors,
    removeError,
    selectRevision,
    clearRevisions,
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

const VARIABLE_PATTERN =
  /^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*(?:#.*)?$/gm

const TYPE_ANNOTATION_PATTERN =
  /^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(float|int|Decimal)\s*=\s*([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*(?:#.*)?$/gm

function extractVariablesFromCode(code: string): CodeVariable[] {
  const variables: CodeVariable[] = []
  const seen = new Set<string>()

  let match: RegExpExecArray | null

  TYPE_ANNOTATION_PATTERN.lastIndex = 0
  while ((match = TYPE_ANNOTATION_PATTERN.exec(code)) !== null) {
    const name = match[1]
    const value = parseFloat(match[3])
    if (!seen.has(name) && Number.isFinite(value)) {
      seen.add(name)
      const { min, max, step } = inferRange(name, value)
      variables.push({ name, value, min, max, step, line: 0 })
    }
  }

  VARIABLE_PATTERN.lastIndex = 0
  while ((match = VARIABLE_PATTERN.exec(code)) !== null) {
    const name = match[1]
    const value = parseFloat(match[2])
    if (!seen.has(name) && Number.isFinite(value)) {
      seen.add(name)
      const { min, max, step } = inferRange(name, value)
      variables.push({ name, value, min, max, step, line: 0 })
    }
  }

  return variables.sort((a, b) => a.line - b.line)
}

function inferRange(name: string, value: number): { min: number; max: number; step: number } {
  const absValue = Math.abs(value)

  if (absValue === 0) {
    return { min: 0, max: 100, step: 1 }
  }

  let min: number
  let max: number
  let step: number

  if (absValue >= 1000) {
    min = 0
    max = Math.ceil(absValue * 2 / 1000) * 1000
    step = Math.max(1, Math.floor(max / 100))
  } else if (absValue >= 100) {
    min = 0
    max = Math.ceil(absValue * 2 / 100) * 100
    step = Math.max(1, Math.floor(max / 100))
  } else if (absValue >= 10) {
    min = 0
    max = Math.ceil(absValue * 2 / 10) * 10
    step = Math.max(0.1, Math.floor(max / 100) / 10)
  } else if (absValue >= 1) {
    min = 0
    max = Math.ceil(absValue * 2)
    step = 0.1
  } else {
    min = 0
    max = Math.ceil(absValue * 2 * 10) / 10
    step = 0.01
  }

  if (name.toLowerCase().includes("angle") || name.toLowerCase().includes("deg")) {
    min = 0
    max = 360
    step = 1
  } else if (name.toLowerCase().includes("radius") || name.toLowerCase().includes("diameter")) {
    min = 0
    max = Math.ceil(absValue * 3)
    step = 0.1
  } else if (name.toLowerCase().includes("height") || name.toLowerCase().includes("length")) {
    min = 0
    max = Math.ceil(absValue * 3)
    step = 0.1
  } else if (name.toLowerCase().includes("thick") || name.toLowerCase().includes("width")) {
    min = 0
    max = Math.ceil(absValue * 3)
    step = 0.1
  } else if (name.toLowerCase().includes("hole") || name.toLowerCase().includes("count")) {
    min = 1
    max = Math.max(100, Math.ceil(absValue * 3))
    step = 1
  }

  if (value < 0) {
    const tmp = min
    min = -max
    max = -tmp
  }

  step = Number(step.toFixed(10))

  return { min, max, step }
}
