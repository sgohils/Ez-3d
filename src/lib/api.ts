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
  message?: string
  revisionId?: string
}

export interface RecompileResponse {
  gltf_url: string
  stl_url: string
  step_url: string
  parameters: ParameterSchema[]
  code: string
  logs: string
}

class AppApiService extends ApiService {
  async generate(prompt: string, parameters?: Record<string, unknown>): Promise<GenerateResponse> {
    return this.request("/api/v1/generate", "POST", { prompt, parameters })
  }

  async recompile(parameters: Record<string, number>): Promise<RecompileResponse> {
    return this.request("/api/v1/recompile", "POST", { parameters })
  }

  async exportModel(format: "step" | "stl" | "gltf", tolerance?: number): Promise<Blob> {
    let url = `${this.baseUrl}/api/v1/export?format=${format}`
    if (tolerance !== undefined) {
      url += `&tolerance=${tolerance}`
    }
    const response = await fetch(url)
    if (!response.ok) {
      const text = await response.text().catch(() => "Export failed")
      throw new APIError("Export failed", response.status, text)
    }
    return response.blob()
  }
}

export const appApi = new AppApiService()
