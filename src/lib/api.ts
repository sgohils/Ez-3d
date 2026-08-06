import { APIError } from "@/lib/types"
import { ApiService } from "./api/client"

export interface GenerateResponse {
  modelUrl: string
  code: string
  parameters: Record<string, number>
  message: string
  revisionId?: string
}

export interface RecompileResponse {
  modelUrl: string
  code: string
  parameters: Record<string, number>
}

class AppApiService extends ApiService {
  async generate(prompt: string, parameters?: Record<string, unknown>): Promise<GenerateResponse> {
    return this.request("/api/v1/generate", "POST", { prompt, parameters })
  }

  async recompile(parameters: Record<string, number>): Promise<RecompileResponse> {
    return this.request("/api/v1/recompile", "POST", { parameters })
  }

  async exportModel(format: "step" | "stl" | "gltf"): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/v1/export?format=${format}`)
    if (!response.ok) {
      const text = await response.text().catch(() => "Export failed")
      throw new APIError("Export failed", response.status, text)
    }
    return response.blob()
  }
}

export const appApi = new AppApiService()
