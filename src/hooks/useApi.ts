import { useState } from "react"
import { apiService, ApiService } from "@/lib/api/client"

export function useApi() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generate = async (prompt: string, parameters?: Record<string, unknown>) => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiService.generate(prompt, parameters)
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { generate, loading, error }
}
