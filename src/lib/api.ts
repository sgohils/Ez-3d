import { APIError } from "@/lib/types"
import { ApiService } from "./api/client"

export interface ParameterSchema {
  name: string
  value: number
  min: number
  max: number
  step: number
}

export interface GenerateResponse {
  gltf_url: string
  stl_url: string
  step_url: string
  parameters: ParameterSchema[]
  code: string
  logs: string
  revision_id: string
}

export interface RecompileResponse {
  gltf_url: string
  stl_url: string
  step_url: string
  parameters: ParameterSchema[]
  code: string
  logs: string
  revision_id: string
}

class AppApiService extends ApiService {
  async generate(prompt: string, parameters?: Record<string, unknown>): Promise<GenerateResponse> {
    return this.request<GenerateResponse>("/api/v1/generate", "POST", { prompt, parameters })
  }

  async recompile(parameters: Record<string, number>): Promise<RecompileResponse> {
    return this.request<RecompileResponse>("/api/v1/recompile", "POST", { parameters })
  }

  async exportModel(format: "step" | "stl" | "gltf", tolerance?: number): Promise<Blob> {
    const params = new URLSearchParams()
    params.set("format", format)
    if (tolerance !== undefined) {
      params.set("tolerance", String(tolerance))
    }
    const response = await fetch(`${this.baseUrl}/api/v1/export?${params}`)
    if (!response.ok) {
      const text = await response.text().catch(() => "Export failed")
      throw new APIError("Export failed", response.status, text)
    }
    return response.blob()
  }
}

export const appApi = new AppApiService()
