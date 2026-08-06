export type MessageRole = "user" | "assistant" | "system"

export interface Message {
  id: string
  role: MessageRole
  content: string
  timestamp: Date
  imageUrl?: string
  codePreview?: string
}

export interface PromptPreset {
  name: string
  label: string
  description: string
  prompt: string
}

export interface Revision {
  id: string
  prompt: string
  modelName: string
  timestamp: Date
  parameters?: Record<string, unknown>
}

export type AutoFixStatus = "idle" | "running" | "complete" | "error"

export interface AutoFixLog {
  id: string
  timestamp: Date
  level: "info" | "warning" | "error" | "debug"
  message: string
}

export interface AutoFixState {
  status: AutoFixStatus
  logs: AutoFixLog[]
  currentIteration: number
  totalIterations: number
  lastError?: string
}