import { useState } from "react"
import { apiService, ApiService } from "@/lib/api/client"

export interface GenerateResult {
  step_url: string
  stl_url: string
  gltf_url: string
  parameters: Array<{ name: string; value: number; min: number; max: number; step: number }>
  code: string
  logs: string
}

export interface RecompileResult {
  step_url: string
  stl_url: string
  gltf_url: string
  parameters: Array<{ name: string; value: number; min: number; max: number; step: number }>
  code: string
  logs: string
}

export function useApi() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generate = async (prompt: string, parameters?: Record<string, unknown>): Promise<GenerateResult> => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiService.generate(prompt, parameters)
      return result as GenerateResult
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error"
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const recompile = async (parameters: Record<string, unknown>): Promise<RecompileResult> => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiService.recompile(parameters)
      return result as RecompileResult
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error"
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { generate, recompile, loading, error }
}
